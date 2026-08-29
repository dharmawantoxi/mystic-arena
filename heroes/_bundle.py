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
        # Masterwork detail & boot swatches
        "mask_line":      (95, 88, 78),
        "hair_shine":     (255, 220, 130),
        "cloth_stitch":   (72, 22, 26),
        "ember":          (255, 190, 90),
        "gold_engrave":   (255, 210, 120),
        "boot_darkest":   (18, 14, 16),
        "boot_dark":      (42, 30, 28),
        "boot_mid":       (78, 52, 42),
        "boot_light":     (120, 82, 60),
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
        portrait_hd = bool(getattr(hero, "_portrait_hd", False))

        attacking = (
            getattr(hero, "_gj_attack_active", False)
            or getattr(hero, "timer", 0) > getattr(hero, "attack_cooldown", 40) - 15
        )

        # Q = Blade Fury, W = Healing Ward, E = Critical Strike, R = Omnislash
        # (sesuai hero_skills/grimjaw_skills.py)
        is_blade_fury = active_skill == "q"
        is_healing_ward = active_skill == "w"
        is_omnislash = active_skill == "r"

        # Portraits deliberately contain only the character rig.  Auras and
        # arena-sized skill effects would force the auto-crop to shrink the
        # mask, mane and armor detail.
        if not portrait_hd:
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

        if not portrait_hd:
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
        portrait = bool(getattr(hero, "_portrait_hd", False))
        if not portrait:
            _NS_grimjaw._draw_shadow(surface, x, y + 48)
            _NS_grimjaw._draw_fire_mist(surface, x, y + 35, hero.pulse)
        _NS_grimjaw._draw_grimjaw_body(surface, x, y + bob, hero.direction,
                                       hero.pulse, "idle", detail=portrait)


    def _draw_grimjaw_walk(surface, hero, x, y):
        phase = hero.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        portrait = bool(getattr(hero, "_portrait_hd", False))
        if not portrait:
            _NS_grimjaw._draw_shadow(surface, x + sway, y + 48)
            _NS_grimjaw._draw_fire_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=hero.direction)
        _NS_grimjaw._draw_grimjaw_body(surface, x + sway, y - bob, hero.direction,
                                       phase, "walk", detail=portrait)


    def _draw_grimjaw_attack(surface, hero, x, y):
        progress = getattr(hero, "_gj_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        crit = getattr(hero, "_gj_crit_active", False)
        portrait = bool(getattr(hero, "_portrait_hd", False))

        # Body lunge forward
        lunge = int(math.sin(progress * math.pi) * 4) * hero.direction

        if not portrait:
            _NS_grimjaw._draw_shadow(surface, x + lunge, y + 48)
            _NS_grimjaw._draw_fire_mist(surface, x + lunge, y + 35, hero.pulse, intense=True)
        _NS_grimjaw._draw_grimjaw_body(surface, x + lunge, y, hero.direction, hero.pulse,
                           "attack", progress, detail=portrait)

        if not portrait:
            # Fire slash arc
            _NS_grimjaw._draw_fire_slash_arc(surface, x + lunge, y, hero.direction, progress, crit)

            # Impact flash: a bright hit-pop + shockwave ring at the moment
            # the blade connects, so EVERY attack has a satisfying impact.
            _NS_grimjaw._draw_impact_flash(surface, x + lunge, y, hero.direction,
                                           progress, crit)

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

        # Draw ghost trails behind current position: full-rig afterimages
        # in different slash poses, so the teleport reads as a storm of
        # overlapping Grimjaw cuts rather than one blurred sticker.
        for i in range(4):
            ghost_alpha = 45 + i * 28
            gx = x - int(math.sin(flicker_phase - i * 0.5) * 18)
            gy = y + int(math.cos(flicker_phase - i * 0.5) * 6)
            ghost_ap = max(0.05, 0.85 - i * 0.22)
            _NS_grimjaw._draw_grimjaw_ghost(surface, gx, gy,
                                            hero.direction, phase,
                                            ghost_alpha, ghost_ap)

        # Main body (with attack pose)
        _NS_grimjaw._draw_grimjaw_body(surface, x + offset_x, y + offset_y, hero.direction,
                           phase, "attack", 0.6)


    def _draw_grimjaw_ghost(surface, cx, cy, facing, phase, alpha,
                            attack_progress=0.6):
        """Full-rig afterimage of Grimjaw for the omnislash trail.

        Renders the complete layered bone rig (mane, mask, blade, armor)
        into a transparent buffer at reduced alpha so the teleport leaves
        real body afterimages instead of crude rectangle stickers.
        """
        ghost = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        _NS_grimjaw._draw_grimjaw_elite(
            ghost, cx, cy, facing, phase, "attack",
            max(0.0, min(1.0, attack_progress)), 0.0, False)
        ghost.set_alpha(alpha)
        surface.blit(ghost, (0, 0))


    # ===================================================================
    # BODY RENDERING - HD detailed Juggernaut
    # ===================================================================

    # ===================================================================
    # MASTERWORK RIG - bone rig 2D berlapis (setara Kaizen/Thorne/Zephyr)
    #
    # Mengganti seluruh set "body-part sticker" lama (torso, pauldron,
    # head_mask, hair_back/front, left/sword arm, fire_sword) dengan SATU
    # rig pose-driven: mane api menyala, mask putih ber-strip darah,
    # sabuk + loincloth merah, kaki & boot yang benar-benar menapak, dan
    # flame blade melengkung yang sudutnya dihitung dari sendi. Semua
    # 100% primitif pygame - tanpa PNG, sprite sheet, ataupun image.load.
    # ===================================================================
    def _draw_grimjaw_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0, spin_phase=0, detail=False):
        """Thin wrapper that keeps the historical signature so the idle/walk/
        attack/blade-fury/omnislash entry points continue to work and now
        route every frame through the single layered bone rig."""
        _NS_grimjaw._draw_grimjaw_elite(
            surface, cx, cy, facing, phase, action,
            attack_progress, spin_phase, detail)


    # -------------------------------------------------------------------
    # Pose helpers (deterministic - shared by rig + skill FX anchors)
    # -------------------------------------------------------------------
    def _blade_angle(phase, action, attack_progress=0.0, spin_phase=0.0):
        """Radian dari garis lurus-bawah: 0 = blade menunjuk ke bawah;
        +pi/2 = menunjuk lurus ke depan; negatif = wind-up ke belakang."""
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < 0.25:
                t = ap / 0.25
                t = 1.0 - (1.0 - t) ** 2
                return -0.5 - t * 1.05
            if ap < 0.70:
                t = (ap - 0.25) / 0.45
                t = t ** 1.4
                return -1.55 + t * 2.90
            t = (ap - 0.70) / 0.30
            return 1.35 - t * 1.42
        if action == "spin":
            return spin_phase * 0.5 + math.sin(phase * 1.2) * 0.06
        if action == "walk":
            return 0.08 + math.sin(phase * 1.72) * 0.10
        return 0.12 + math.sin(phase * 0.5) * 0.05


    def _blade_grip_local(action, attack_progress=0.0, phase=0.0):
        """Posisi gagang/pegangan blade (ruang lokal, forward = +x)."""
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < 0.25:
                t = ap / 0.25
                return (9 + int(5 * t), 1 - int(19 * t))
            if ap < 0.70:
                t = (ap - 0.25) / 0.45
                return (15 + int(9 * t), -18 + int(23 * t))
            t = (ap - 0.70) / 0.30
            return (24 - int(7 * t), 5 - int(5 * t))
        if action == "spin":
            return (17, -3)
        if action == "walk":
            return (11 + int(math.sin(phase * 1.72) * 2), 2)
        return (11, 2)


    def _blade_len(action):
        return 36 if action != "attack" else 42


    def _blade_tip_local(phase, action, attack_progress=0.0, spin_phase=0.0):
        """Posisi ujung blade (ruang lokal) - dipakai sebagai anchor FX."""
        a = _NS_grimjaw._blade_angle(phase, action, attack_progress, spin_phase)
        gx, gy = _NS_grimjaw._blade_grip_local(action, attack_progress, phase)
        L = _NS_grimjaw._blade_len(action)
        return (int(gx + math.sin(a) * L), int(gy + math.cos(a) * L))


    def _draw_grimjaw_elite(surface, cx, cy, facing, phase, action,
                            attack_progress=0.0, spin_phase=0.0,
                            detail=False):
        p = _NS_grimjaw.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        spin = action == "spin"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.72)
        breath = math.sin(phase * 0.78)

        # Root lean / bob translates the whole rig as one unit.
        lean = int(stride * 2.5 if walk else 0.0)
        if attack:
            lean += int(math.sin(ap * math.pi) * 6.0)
        # Idle weight-shift: slow side-to-side rock so the stance reads as
        # alive (planted feet, swaying torso) instead of a frozen statue.
        if action == "idle":
            lean += int(math.sin(phase * 0.5) * 3)
        root_y = int(breath * 0.8)
        if action == "idle":
            root_y += int(math.sin(phase * 0.78) * 2)
        if walk:
            root_y -= int(abs(stride) * 2.5)
        if attack:
            root_y += int(math.sin(ap * math.pi) * 2)
        if spin:
            root_y -= 2

        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_grimjaw._poly(surface, p["shadow_deep"],
                                  [(qx + f, qy + 1) for qx, qy in pts])
            _NS_grimjaw._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_grimjaw._aaline(surface, p["shadow_deep"],
                                (aa[0] + f, aa[1] + 1),
                                (bb[0] + f, bb[1] + 1), width + 3)
            _NS_grimjaw._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_grimjaw._aaline(surface, light,
                                    (aa[0] + off, aa[1] - 1),
                                    (bb[0] + off, bb[1] - 1),
                                    max(1, width // 3))

        def dot(color, dx, dy, r, outline=True):
            x, y = pt(dx, dy)
            if outline:
                _NS_grimjaw._aacircle(surface, p["shadow_deep"],
                                      (x + f, y + 1), r + 1)
            _NS_grimjaw._aacircle(surface, color, (x, y), r)

        # Back flame mane: connected crest hugging the skull (drawn first).
        _NS_grimjaw._draw_elite_flame_mane(surface, pt, poly, f, phase, action)

        # Rear arm (free fist): bare muscular arm, kept attached to torso.
        rear_shoulder = (-12, -9)
        if attack:
            rear_elbow = (-17, -1)
            rear_hand = (-21, 6)
        elif walk:
            rear_elbow = (-16, -1 + int(stride * 4))
            rear_hand = (-19, 7 + int(stride * 6))
        elif spin:
            rear_elbow = (-18, -4)
            rear_hand = (-22, -8)
        else:
            rear_elbow = (-16, -1)
            rear_hand = (-18, 7 + int(breath))
        limb(rear_shoulder, rear_elbow, 7, p["skin_dark"], p["skin_mid"])
        limb(rear_elbow, rear_hand, 6, p["skin_mid"], p["skin_high"])
        dot(p["skin_darkest"], *rear_hand, 4)
        dot(p["skin_mid"], *rear_hand, 3)
        dot(p["skin_high"], rear_hand[0] - 1, rear_hand[1] - 1, 1, False)

        # Back war-skirt: a wide red panel hanging behind the legs (drawn
        # BEFORE them) so the waist reads as fully wrapped in cloth rather
        # than only a front loincloth. Its hem sways out of phase with the
        # front sash for a heavier, layered silhouette.
        skirt_sway = int(math.sin(phase * 0.9 + 1.2) * 2)
        poly(p["red_darkest"], [(-11, 13), (11, 13), (9 + skirt_sway, 34),
             (4, 39), (0, 37), (-5, 40), (-9 + skirt_sway, 33)])
        poly(p["red_dark"], [(-9, 14), (9, 14), (7 + skirt_sway, 31),
             (3, 35), (0, 33), (-4, 36), (-7 + skirt_sway, 30)], False)
        _NS_grimjaw._aaline(surface, p["red_mid"], pt(-4, 16),
                            pt(-6 + skirt_sway, 32), 1)
        _NS_grimjaw._aaline(surface, p["red_mid"], pt(3, 16),
                            pt(4 + skirt_sway, 31), 1)

        # Legs: longer, wider planted stance with metal shin guards.
        # v2 (animasi): kaki terangkat bergantian saat melangkah (foot-lift)
        # + lutut ikut naik, supaya jalan tidak "meluncur" di tanah.
        front_step = int(stride * 5) if walk else 0
        rear_step = -front_step
        if attack:
            front_step += int(ap * 6)
            rear_step -= int(ap * 3)
        # Kecepatan stride menentukan kapan tiap kaki berada di fase
        # "swing" (maju) -> kaki itu terangkat. Dua kaki saling berlawanan:
        # satu menapak, satu terangkat.
        stride_vel = math.cos(phase * 1.72) if walk else 0.0
        front_lift = int(max(0.0, stride_vel) * 8) if walk else 0
        rear_lift = int(max(0.0, -stride_vel) * 8) if walk else 0
        legs = ((-9, rear_step, p["boot_dark"], rear_lift),
                (9, front_step, p["boot_mid"], front_lift))
        for side, step, boot, lift in legs:
            tx = side + step
            # The knee rises with the lift so the thigh shortens up to meet
            # the raised shin (proper knee-bend, no gap).
            poly(p["skin_darkest"], [(tx - 6, 14), (tx + 6, 14),
                 (tx + 5, 30 - lift), (tx - 5, 30 - lift)])
            poly(p["skin_dark"], [(tx - 5, 15), (tx + 5, 15),
                 (tx + 4, 29 - lift), (tx - 4, 29 - lift)], False)
            poly(p["skin_mid"], [(tx - 3, 16), (tx + 2, 16),
                 (tx + 1, 27 - lift), (tx - 2, 27 - lift)], False)
            # Whole lower leg (shin guard + boot + foot) rises by `lift`
            # so the knee actually bends instead of the leg shrinking.
            poly(p["metal_darkest"], [(tx - 5, 29 - lift), (tx + 5, 29 - lift),
                 (tx + 6, 44 - lift), (tx - 5, 44 - lift)])
            poly(p["metal_dark"], [(tx - 4, 30 - lift), (tx + 4, 30 - lift),
                 (tx + 5, 43 - lift), (tx - 4, 43 - lift)], False)
            _NS_grimjaw._aaline(surface, p["metal_light"],
                                pt(tx - 2, 31 - lift), pt(tx - 2, 42 - lift), 1)
            # Gold trim: knee cap line + ankle cuff on the shin guard.
            _NS_grimjaw._aaline(surface, p["gold_dark"],
                                pt(tx - 5, 31 - lift), pt(tx + 5, 31 - lift), 2)
            _NS_grimjaw._aaline(surface, p["gold_mid"],
                                pt(tx - 5, 30 - lift), pt(tx + 5, 30 - lift), 1)
            _NS_grimjaw._aaline(surface, p["gold_dark"],
                                pt(tx - 5, 43 - lift), pt(tx + 5, 43 - lift), 1)
            _NS_grimjaw._aacircle(surface, p["gold_light"],
                                  pt(tx, 31 - lift), 1)
            poly(boot, [(tx - 6, 43 - lift), (tx + 5, 43 - lift),
                 (tx + 6, 48 - lift), (tx - 7, 48 - lift)], False)
            toe = 6 * f
            foot = pt(tx + (4 if f > 0 else -4), 47 - lift)
            _NS_grimjaw._aaline(surface, p["shadow_deep"],
                                (foot[0] - toe, foot[1] + 1),
                                (foot[0] + toe, foot[1] + 1), 4)
            _NS_grimjaw._aaline(surface, p["boot_light"],
                                (foot[0] - toe, foot[1]),
                                (foot[0] + toe, foot[1]), 2)

        # Torso: bare muscular chest with V-taper + diagonal red sash.
        poly(p["skin_darkest"], [(-14, -12), (14, -12), (11, 10),
             (-11, 10)])
        poly(p["skin_dark"], [(-12, -10), (12, -10), (9, 9),
             (-9, 9)], False)
        poly(p["skin_mid"], [(-10, -9), (10, -9), (7, 8), (-7, 8)], False)
        poly(p["skin_light"], [(-8, -9), (8, -9), (5, -3), (-6, -3)], False)
        _NS_grimjaw._aaline(surface, p["skin_darkest"], pt(0, -6),
                            pt(0, 3), 1)
        _NS_grimjaw._aaline(surface, p["skin_dark"], pt(-5, -2),
                            pt(-1, -1), 1)
        _NS_grimjaw._aaline(surface, p["skin_dark"], pt(1, -1),
                            pt(5, -2), 1)
        _NS_grimjaw._aaline(surface, p["skin_dark"], pt(-4, 4),
                            pt(4, 4), 1)
        _NS_grimjaw._aaline(surface, p["skin_dark"], pt(-3, 7),
                            pt(3, 7), 1)
        poly(p["red_darkest"], [(-13, -11), (-8, -13), (11, 6),
             (9, 10), (-13, -7)])
        poly(p["red_dark"], [(-12, -10), (-8, -12), (10, 6),
             (8, 9)], False)
        _NS_grimjaw._aaline(surface, p["red_light"], pt(-10, -10),
                            pt(8, 7), 1)

        # Cross-body leather harness: opposite diagonal to the sash, with
        # a gold buckle at the shoulder and studs down the strap.
        _NS_grimjaw._aaline(surface, p["armor_darkest"], pt(10, -11),
                            pt(-9, 8), 4)
        _NS_grimjaw._aaline(surface, p["armor_mid"], pt(10, -11),
                            pt(-9, 8), 2)
        _NS_grimjaw._aaline(surface, p["armor_light"], pt(9, -11),
                            pt(-8, 8), 1)
        for i in range(3):
            t = 0.25 + i * 0.25
            sx = int(10 + (-9 - 10) * t)
            sy = int(-11 + (8 + 11) * t)
            _NS_grimjaw._aacircle(surface, p["gold_mid"], pt(sx, sy), 1)
        _NS_grimjaw._rect(surface, p["gold_dark"],
                          (pt(9, -12)[0] - 2, pt(9, -12)[1] - 2, 4, 4))
        _NS_grimjaw._rect(surface, p["gold_mid"],
                          (pt(9, -12)[0] - 1, pt(9, -12)[1] - 1, 2, 2))
        # Sternum medallion: a small gold boss on the chest centre.
        dot(p["gold_darkest"], 0, -4, 3)
        dot(p["gold_dark"], 0, -4, 2)
        dot(p["gold_mid"], 0, -4, 1)
        dot(p["gold_shine"], 0, -5, 1, False)

        # Belt + gold buckle + studs.
        poly(p["armor_darkest"], [(-12, 9), (12, 9), (12, 15), (-12, 15)])
        poly(p["red_darkest"], [(-11, 10), (11, 10), (11, 14),
             (-11, 14)], False)
        for bx in (-9, -5, 5, 9):
            dot(p["gold_dark"], bx, 12, 1, False)
            dot(p["gold_mid"], bx, 12, 1, False)
        dot(p["gold_darkest"], 0, 12, 4)
        dot(p["gold_dark"], 0, 12, 3)
        dot(p["gold_mid"], 0, 12, 2)
        dot(p["gold_light"], 0, 12, 1)

        # Front loincloth with jagged war-sash hem.
        cloth_sway = int(math.sin(phase * 1.1) * 2)
        poly(p["red_darkest"], [(-7, 14), (7, 14), (8 + cloth_sway, 28),
             (6, 34), (3, 29), (1, 37), (-2, 31), (-5, 36),
             (-8 + cloth_sway, 27)])
        poly(p["red_dark"], [(-6, 15), (6, 15), (7 + cloth_sway, 27),
             (4, 32), (2, 28), (0, 34), (-2, 29), (-4, 33),
             (-7 + cloth_sway, 26)], False)
        poly(p["red_mid"], [(-3, 16), (3, 16), (3 + cloth_sway, 26),
             (0, 31), (-2 + cloth_sway, 26), (-3, 24)], False)
        _NS_grimjaw._aaline(surface, p["blood_dark"], pt(-3, 17),
                            pt(1 + cloth_sway, 29), 1)

        # Hip tassets: three overlapping leather plates per side that taper
        # to a point, with a gold rivet at each plate tip.
        for side in (-1, 1):
            hx = side * 11
            for i, (y0, y1, tip) in enumerate(((11, 19, 22),
                                               (12, 18, 20),
                                               (13, 17, 18))):
                dx = (2 - i)
                poly(p["armor_darkest"], [(hx - 3 - dx, y0), (hx + 3 - dx, y0),
                     (hx + 2 - dx, y1), (hx - 1, tip),
                     (hx - 4 - dx, y1)], False)
                poly(p["armor_dark"], [(hx - 2 - dx, y0 + 1),
                     (hx + 2 - dx, y0 + 1), (hx + 1 - dx, y1 - 1),
                     (hx - 1, tip - 1)], False)
                _NS_grimjaw._aacircle(surface, p["gold_dark"],
                                      pt(hx - 1, tip), 1)
                _NS_grimjaw._aacircle(surface, p["gold_light"],
                                      pt(hx - 1, tip - 1), 1)

        # Shoulder pauldrons: layered steel plates, gold rim, spike.
        for side in (-1, 1):
            sx = side * 15
            poly(p["metal_darkest"], [(sx - 7, -16), (sx + 7, -16),
                 (sx + 7, -7), (sx, -4), (sx - 7, -7)])
            poly(p["metal_dark"], [(sx - 6, -15), (sx + 6, -15),
                 (sx + 6, -8), (sx, -5), (sx - 6, -8)], False)
            poly(p["metal_mid"], [(sx - 4, -14), (sx + 4, -14),
                 (sx + 4, -9), (sx, -7), (sx - 4, -9)], False)
            poly(p["gold_mid"], [(sx - 6, -8), (sx + 6, -8),
                 (sx + 2, -5), (sx - 2, -5)], False)
            poly(p["metal_darkest"], [(sx - 2, -15), (sx, -24),
                 (sx + 2, -15)])
            poly(p["metal_dark"], [(sx - 1, -15), (sx, -23),
                 (sx + 1, -15)], False)
            dot(p["metal_shine"], sx, -19, 1, False)
            # Plate segmentation: two curved seams + rivets along the rim
            # so the pauldron reads as layered steel, not one flat blob.
            _NS_grimjaw._aaline(surface, p["metal_darkest"],
                                pt(sx - 5, -12), pt(sx + 5, -12), 1)
            _NS_grimjaw._aaline(surface, p["metal_darkest"],
                                pt(sx - 4, -9), pt(sx + 4, -9), 1)
            _NS_grimjaw._aaline(surface, p["metal_light"],
                                pt(sx - 5, -11), pt(sx + 5, -11), 1)
            for rx in (-4, -1, 1, 4):
                _NS_grimjaw._aacircle(surface, p["metal_darkest"],
                                      pt(sx + rx, -7), 1)
                _NS_grimjaw._aacircle(surface, p["metal_shine"],
                                      pt(sx + rx, -7), 1)

        # Neck + traps.
        poly(p["skin_darkest"], [(-7, -16), (7, -16), (10, -10),
             (-10, -10)])
        poly(p["skin_mid"], [(-4, -15), (4, -15), (6, -11), (-6, -11)],
             False)

        # Front blade arm: muscular, fist derived from pose grip.
        grip = _NS_grimjaw._blade_grip_local(action, ap, phase)
        front_shoulder = (12, -9)
        if attack:
            front_elbow = (grip[0] - 3, grip[1] + 5)
        elif walk:
            front_elbow = (grip[0] - 4, grip[1] + 5 + int(stride * 2))
        else:
            front_elbow = (grip[0] - 4, grip[1] + 6)
        limb(front_shoulder, front_elbow, 7, p["skin_dark"], p["skin_mid"])
        limb(front_elbow, grip, 6, p["skin_mid"], p["skin_high"])
        dot(p["skin_darkest"], *grip, 4)
        dot(p["skin_mid"], *grip, 3)
        dot(p["skin_high"], grip[0] - 1, grip[1] - f, 1, False)

        # Pose-driven curved flame blade (longer scimitar sweep).
        angle = _NS_grimjaw._blade_angle(phase, action, ap, spin_phase)
        length = _NS_grimjaw._blade_len(action)

        # Attack motion trail: blade "afterimages" at earlier sweep angles
        # make the swing read fast instead of a single static scimitar.
        if attack and 0.30 < ap < 0.85:
            for back, al in ((0.12, 80), (0.24, 45)):
                ap_back = max(0.0, ap - back)
                a_back = _NS_grimjaw._blade_angle(phase, action, ap_back,
                                                  spin_phase)
                g_back = _NS_grimjaw._blade_grip_local(action, ap_back, phase)
                trail = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                _NS_grimjaw._draw_elite_flame_blade(
                    trail, pt, f, g_back, a_back, length, phase, False)
                trail.set_alpha(al)
                surface.blit(trail, (0, 0))

        # Blade Fury spin trail: a full circular flame sweep behind the
        # blade makes the whirl read as one continuous ring of fire.
        if spin:
            for back, al in ((0.25, 90), (0.55, 55)):
                sp_back = spin_phase - back
                a_back = _NS_grimjaw._blade_angle(phase, action, ap,
                                                  sp_back)
                g_back = _NS_grimjaw._blade_grip_local(action, ap, phase)
                trail = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                _NS_grimjaw._draw_elite_flame_blade(
                    trail, pt, f, g_back, a_back, length, phase, False)
                trail.set_alpha(al)
                surface.blit(trail, (0, 0))

            # Radial ember sparks: flung outward every revolution so the
            # whirl reads as a violent blaze, not just two ghost blades.
            for i in range(8):
                a = spin_phase + i * math.tau / 8
                t = (phase * 0.6 + i * 0.125) % 1.0
                r = 18 + t * 26
                ex = int(math.cos(a) * r)
                ey = int(math.sin(a) * r) - 4
                alpha = int(210 * (1.0 - t))
                _NS_grimjaw._aacircle(surface, (*p["fire_dark"], alpha),
                                      pt(ex, ey), 2)
                _NS_grimjaw._aacircle(surface, (*p["fire_hot"], alpha),
                                      pt(ex, ey), 1)
            # Spin shockwave: a bright ring pulsing at the waist that
            # makes the blade fury feel like it tears the air around him.
            ring_t = (spin_phase % math.tau) / math.tau
            ring_r = int(20 + ring_t * 12)
            ring_alpha = int(150 * (1.0 - ring_t))
            _NS_grimjaw._aacircle(surface, (*p["fire_mid"], ring_alpha),
                                  pt(0, 0), ring_r, 1)
            _NS_grimjaw._aacircle(surface, (*p["fire_hot"], ring_alpha),
                                  pt(0, 0), max(1, ring_r - 3), 1)

        _NS_grimjaw._draw_elite_flame_blade(
            surface, pt, f, grip, angle, length, phase, detail)

        # White Juggernaut mask + head.
        _NS_grimjaw._draw_elite_mask(surface, pt, poly, dot, f, phase,
                                     action, ap, detail)

        # Front fringe + side locks of the fire mane.
        _NS_grimjaw._draw_elite_mane_front(surface, pt, poly, f, phase, action)

        if detail:
            _NS_grimjaw._draw_grimjaw_masterwork_details(
                surface, pt, poly, f, phase, action)


    # -------------------------------------------------------------------
    # Flame mane (back crest) + front fringe + side locks
    # -------------------------------------------------------------------
    def _draw_elite_flame_mane(surface, pt, poly, f, phase, action):
        p = _NS_grimjaw.PALETTE
        wave = int(math.sin(phase * 1.2) * 2)
        # Solid crest volume WIDER than the mask so the hair mass frames
        # the skull instead of hiding behind it.
        poly(p["hair_darkest"], [(-14, -20), (-16, -30), (-12, -40),
             (0, -47), (12, -40), (16, -30), (14, -20), (7, -14),
             (-7, -14)])
        poly(p["hair_dark"], [(-12, -22), (-14, -30), (-10, -38),
             (0, -44), (10, -38), (14, -30), (12, -22), (6, -16),
             (-6, -16)], False)
        poly(p["hair_mid"], [(-9, -24), (-11, -31), (-8, -37),
             (0, -42), (8, -37), (11, -31), (9, -24), (4, -18),
             (-4, -18)], False)
        poly(p["fire_dark"], [(-6, -26), (-8, -32), (-5, -37),
             (0, -40), (5, -37), (8, -32), (6, -26), (3, -20),
             (-3, -20)], False)
        # Flame licks: short, thick, swept up/out from the crown only -
        # bases hidden inside the volume so nothing floats.
        strands = [
            (-12, -30, -19, -40, 4),
            (-9, -35, -14, -50, 5),
            (-4, -39, -6, -56, 5),
            (1, -41, 1, -60, 6),
            (6, -38, 9, -54, 5),
            (10, -34, 15, -46, 4),
            (13, -29, 20, -38, 3),
        ]
        for bx, by, tx, ty, wd in strands:
            tw = wave if bx > 0 else -wave
            tx2 = tx + tw
            ty2 = ty + int(abs(wave) * 0.4)
            poly(p["hair_darkest"], [(bx - wd, by), (tx2, ty2),
                 (bx + wd, by)])
            poly(p["fire_dark"], [(bx - wd + 1, by), (tx2, ty2),
                 (bx + wd - 1, by)], False)
            poly(p["fire_mid"], [(bx - wd // 2, by), (tx2, ty2),
                 (bx + wd // 2, by)], False)
            _NS_grimjaw._aaline(surface, p["hair_mid"], pt(bx - 1, by),
                                pt(tx2, ty2), 1)
            _NS_grimjaw._rect(surface, p["fire_hot"],
                              (pt(tx2, ty2)[0] - 1, pt(tx2, ty2)[1] - 1, 2, 2))


    def _draw_elite_mane_front(surface, pt, poly, f, phase, action):
        p = _NS_grimjaw.PALETTE
        wave = int(math.sin(phase * 1.2) * 2)
        fringe = [(-6, -42, -8, -48), (-2, -44, -3, -51),
                  (2, -44, 2, -51), (6, -42, 7, -48)]
        for i, (sx, sy, ex, ey) in enumerate(fringe):
            wig = wave if i % 2 else -wave
            poly(p["hair_darkest"], [(sx - 2, sy), (sx + 2, sy),
                 (ex + wig, ey)], False)
            poly(p["hair_mid"], [(sx - 1, sy), (sx + 1, sy),
                 (ex + wig, ey)], False)
            _NS_grimjaw._aaline(surface, p["hair_light"], pt(sx, sy),
                                pt(ex + wig, ey), 1)
        for side in (-1, 1):
            sway = int(math.sin(phase * 1.0 + side) * 1)
            sx = side * 12
            poly(p["hair_darkest"], [(sx - 2, -34), (sx + 2, -34),
                 (sx + 4 * side + sway, -26), (sx + 2 * side, -23),
                 (sx - 1 * side, -28)], False)
            poly(p["fire_dark"], [(sx - 1, -33), (sx + 1, -33),
                 (sx + 3 * side + sway, -26), (sx + 1 * side, -24)],
                 False)
            _NS_grimjaw._aaline(surface, p["hair_mid"],
                                pt(sx, -32), pt(sx + 3 * side + sway, -25), 1)


    def _draw_elite_mask(surface, pt, poly, dot, f, phase, action, ap, detail):
        p = _NS_grimjaw.PALETTE
        eyes_glow = action in ("attack", "spin") or ap > 0.35
        poly(p["mask_shadow"], [(-8, -44), (0, -47), (8, -44),
             (12, -37), (13, -29), (10, -21), (6, -16),
             (0, -14), (-6, -16), (-10, -21), (-13, -29),
             (-12, -37)])
        poly(p["mask_dark"], [(-7, -42), (0, -45), (7, -42),
             (10, -36), (11, -29), (8, -22), (5, -17),
             (0, -16), (-5, -17), (-8, -22), (-11, -29),
             (-10, -36)], False)
        poly(p["mask_mid"], [(-5, -41), (0, -43), (5, -41),
             (8, -35), (8, -29), (6, -23), (3, -18),
             (0, -17), (-3, -18), (-6, -23), (-8, -29),
             (-8, -35)], False)
        poly(p["mask_light"], [(-4, -39), (0, -41), (4, -39),
             (6, -34), (6, -28), (4, -23), (2, -20),
             (-2, -20), (-4, -23), (-6, -28), (-6, -34),
             (-7, -39)], False)
        _NS_grimjaw._aacircle(surface, p["mask_shine"], pt(2, -37), 2)

        # Forehead crest: small gold diamond emblem (signature masterwork).
        poly(p["gold_darkest"], [(-1, -44), (2, -44), (3, -40),
             (0, -38), (-2, -40)])
        poly(p["gold_mid"], [(0, -43), (1, -43), (2, -40), (0, -39),
             (-1, -40)], False)
        _NS_grimjaw._aacircle(surface, p["gold_shine"], pt(0, -41), 1)

        # Brow ridge: angled shadow slashes above each eye socket so the
        # gaze reads angry instead of a blank stare.
        _NS_grimjaw._aaline(surface, p["mask_shadow"], pt(-8, -32),
                            pt(-3, -35), 2)
        _NS_grimjaw._aaline(surface, p["mask_shadow"], pt(8, -32),
                            pt(3, -35), 2)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(-9, -33),
                            pt(-4, -36), 1)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(9, -33),
                            pt(4, -36), 1)

        # Nose bridge: faint vertical ridge down the centre.
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(0, -39),
                            pt(0, -26), 1)

        # Blood stripes: thick centre (with a drip tail) + two thin side
        # slashes that taper to points.
        poly(p["blood_darkest"], [(-1, -43), (2, -43), (2, -20),
             (1, -17), (-1, -20)])
        poly(p["blood_dark"], [(0, -42), (1, -42), (1, -21),
             (0, -19)], False)
        poly(p["blood_mid"], [(0, -21), (1, -21), (1, -17),
             (0, -17)], False)
        _NS_grimjaw._aaline(surface, p["blood_light"], pt(1, -40),
                            pt(1, -22), 1)
        _NS_grimjaw._aaline(surface, p["blood_dark"], pt(-8, -39),
                            pt(-4, -25), 2)
        _NS_grimjaw._aaline(surface, p["blood_mid"], pt(-7, -38),
                            pt(-4, -26), 1)
        _NS_grimjaw._aaline(surface, p["blood_dark"], pt(8, -39),
                            pt(4, -25), 2)
        _NS_grimjaw._aaline(surface, p["blood_mid"], pt(7, -38),
                            pt(4, -26), 1)

        # Eyes: angular dark sockets (not round blobs) with a glowing red
        # core while attacking.
        for ex in (-5, 5):
            x, y = pt(ex, -30)
            # Angular socket: a slanted diamond, wider toward the temple.
            poly(p["dark_eye"], [(ex - f * 2, y - 2), (ex + f * 3, y - 3),
                 (ex + f * 2, y + 2), (ex - f * 3, y + 3)])
            if eyes_glow:
                _NS_grimjaw._aacircle(surface, p["eye_glow"], (x, y), 2)
                _NS_grimjaw._aacircle(surface, p["white"], (x - f, y - 1), 1)
            else:
                _NS_grimjaw._aacircle(surface, p["eye_glow"], (x, y), 1)

        # Mouth grille: upper jaw line + individual teeth bars.
        _NS_grimjaw._aaline(surface, p["shadow"], pt(-4, -20), pt(4, -20), 3)
        for tx in (-3, -1, 1, 3):
            _NS_grimjaw._aaline(surface, p["shadow"], pt(tx, -20),
                                pt(tx, -18), 2)
            _NS_grimjaw._aaline(surface, p["mask_light"], pt(tx, -20),
                                pt(tx, -19), 1)
        # Lower jaw separation (mandible line).
        _NS_grimjaw._aaline(surface, p["mask_shadow"], pt(-6, -17),
                            pt(6, -17), 1)


    def _draw_elite_flame_blade(surface, pt, f, grip, angle, length, phase,
                                detail):
        p = _NS_grimjaw.PALETTE
        s = math.sin(angle)
        c = math.cos(angle)
        segs = 6
        centers = []
        for i in range(segs + 1):
            t = i / segs
            curve = 7.5 * (t * t)
            centers.append((grip[0] + s * length * t + c * curve,
                            grip[1] + c * length * t - s * curve))
        n_x, n_y = c, -s
        left, right = [], []
        for i, (x, y) in enumerate(centers):
            t = i / segs
            wd = 3.8 * (1.0 - t) + 0.9 * t
            left.append((x + n_x * wd, y + n_y * wd))
            right.append((x - n_x * wd, y - n_y * wd))
        outline = left + right[::-1]

        grip_s = pt(*grip)

        def scr(p_local):
            return pt(*p_local)

        flat = [scr(o) for o in outline]
        _NS_grimjaw._poly(surface, p["shadow_deep"],
                          [(x + f, y + 1) for x, y in flat])
        _NS_grimjaw._poly(surface, p["fire_darkest"], flat)
        # Bright gradient of fire layers, shrinking toward the grip so the
        # blade stays a vivid orange flame instead of a dark silhouette.
        for shrink, col in ((0.0, p["fire_dark"]),
                            (0.10, p["fire_mid"]),
                            (0.22, p["fire_light"])):
            pts = []
            for (x, y) in flat:
                dx = (x - grip_s[0]) * shrink
                dy = (y - grip_s[1]) * shrink
                pts.append((int(x - dx), int(y - dy)))
            _NS_grimjaw._poly(surface, col, pts)
        # Hot core line.
        core = [scr(q) for q in centers]
        for i in range(len(core) - 1):
            _NS_grimjaw._aaline(surface, p["fire_hot"], core[i], core[i + 1], 2)
            _NS_grimjaw._aaline(surface, p["fire_core"], core[i], core[i + 1], 1)
        # Leading-edge highlight.
        edge = [scr(q) for q in left]
        for i in range(len(edge) - 1):
            _NS_grimjaw._aaline(surface, p["fire_hot"], edge[i],
                                edge[i + 1], 1)
            _NS_grimjaw._aaline(surface, p["white"], edge[i],
                                edge[i + 1], 1)

        # Flickering flame licks shed from the convex edge, so the blade
        # reads as living fire rather than a smooth metal scimitar.
        flick = math.sin(phase * 3.1) * 2.0
        for i, t in enumerate((0.18, 0.40, 0.62, 0.82)):
            ci = centers[int(t * segs)]
            lic = 4 + int((1.0 - t) * 5) + int(math.sin(phase * 4 + i) * 1.5)
            ex = ci[0] + n_x * (lic + flick)
            ey = ci[1] + n_y * (lic + flick)
            _NS_grimjaw._poly(surface, p["fire_dark"], [
                pt(ci[0] - n_x * 2, ci[1] - n_y * 2),
                pt(ci[0] + n_x * 2, ci[1] + n_y * 2),
                pt(ex, ey)])
            _NS_grimjaw._poly(surface, p["fire_light"], [
                pt(ci[0] - n_x * 1, ci[1] - n_y * 1),
                pt(ci[0] + n_x * 1, ci[1] + n_y * 1),
                pt(ex - n_x * 1, ey - n_y * 1)])
            _NS_grimjaw._aacircle(surface, p["fire_hot"],
                                  pt(ex, ey), 1)

        gx, gy = grip_s
        # Pommel (behind the hand, opposite the blade) + wrapped grip.
        pommel = pt(grip[0] - s * 4, grip[1] - c * 4)
        _NS_grimjaw._aacircle(surface, p["gold_darkest"], pommel, 3)
        _NS_grimjaw._aacircle(surface, p["gold_dark"], pommel, 2)
        _NS_grimjaw._aacircle(surface, p["gold_light"], pommel, 1)
        _NS_grimjaw._aacircle(surface, p["armor_darkest"], (gx, gy), 3)
        _NS_grimjaw._aacircle(surface, p["armor_mid"], (gx, gy), 2)
        # Crossguard: a gold quillon bar perpendicular to the blade so the
        # weapon reads as a proper flame scimitar with a real hilt.
        for off, col, wd in ((0, p["gold_darkest"], 5),
                             (0, p["gold_dark"], 3),
                             (0, p["gold_mid"], 2)):
            _NS_grimjaw._aaline(surface, col,
                                pt(grip[0] - n_x * 5 + off,
                                   grip[1] - n_y * 5 + off),
                                pt(grip[0] + n_x * 5 + off,
                                   grip[1] + n_y * 5 + off), wd)
        _NS_grimjaw._aacircle(surface, p["gold_light"],
                              pt(grip[0] + n_x * 5, grip[1] + n_y * 5), 1)
        _NS_grimjaw._aacircle(surface, p["gold_light"],
                              pt(grip[0] - n_x * 5, grip[1] - n_y * 5), 1)

        # Ember particles + hot core read well in both the arena and the
        # portrait LOD (they hug the blade tip, so they do not enlarge the
        # portrait auto-crop the way an aura would).
        pulse = math.sin(phase * 1.4) * 0.3 + 0.7
        tip = scr(centers[-1])
        for i in range(4 if not detail else 2):
            t = (phase * 0.7 + i * 0.25) % 1.0
            ex = tip[0] + int(math.sin(phase * 5 + i) * 3)
            ey = tip[1] - int(t * 14)
            alpha = max(0, int(190 * (1.0 - t) * pulse))
            if alpha > 0:
                _NS_grimjaw._aacircle(
                    surface, (*p["fire_light"], alpha), (ex, ey), 2)
                _NS_grimjaw._aacircle(
                    surface, (*p["fire_hot"], alpha), (ex, ey), 1)
        _NS_grimjaw._aacircle(surface, p["fire_core"], tip, 2)
        _NS_grimjaw._aacircle(surface, p["white"], tip, 1)


    # -------------------------------------------------------------------
    # Portrait-only LOD pass (extra material detail; arena LOD stays cheap)
    # -------------------------------------------------------------------
    def _draw_grimjaw_masterwork_details(surface, pt, poly, f, phase, action):
        p = _NS_grimjaw.PALETTE
        for i in range(6):
            bx = -10 + i * 4
            by = -36
            tx = bx - 2 - int(math.sin(phase + i) * 2)
            ty = by - 14 - i
            _NS_grimjaw._aaline(surface, p["hair_shine"], pt(bx, by),
                                pt(tx, ty), 1)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(-6, -30),
                            pt(-2, -33), 1)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(-2, -33),
                            pt(1, -27), 1)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(3, -34),
                            pt(6, -30), 1)
        for i in range(3):
            yy = 18 + i * 5
            _NS_grimjaw._aaline(surface, p["cloth_stitch"],
                                pt(-3, yy), pt(3, yy), 1)
        for side in (-1, 1):
            _NS_grimjaw._aaline(surface, p["gold_engrave"],
                                pt(side * 12, -12), pt(side * 17, -13), 1)
            _NS_grimjaw._aaline(surface, p["gold_engrave"],
                                pt(side * 11, -9), pt(side * 16, -9), 1)
        _NS_grimjaw._aacircle(surface, p["gold_engrave"], pt(0, 12), 1)
        for i in range(2):
            _NS_grimjaw._aaline(surface, p["armor_high"],
                                pt(-11 + i * 8, 10), pt(-7 + i * 8, 13), 1)
        for i in range(4):
            t = (phase * 0.35 + i / 4.0) % 1.0
            dx = -9 + i * 6 + int(math.sin(phase * 1.3 + i) * 2)
            dy = 10 - int(t * 44)
            _NS_grimjaw._aacircle(surface,
                                  (*p["ember"], int(180 * (1 - t))),
                                  pt(dx, dy), 1)
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


    def _draw_impact_flash(surface, x, y, facing, progress, crit=False):
        """Bright hit-pop + shockwave ring when the blade connects.

        Runs for every basic attack (crit just makes it bigger), so the
        swing always reads with a satisfying impact instead of a silent
        crescent. Kept tight around the blade tip so it does not enlarge
        the portrait auto-crop or the sprite-cache canvas.
        """
        if progress < 0.45 or progress > 0.75:
            return
        t = (progress - 0.45) / 0.30
        t = max(0.0, min(1.0, t))
        intensity = math.sin(t * math.pi)

        # Impact point: out in front, where the scimitar tip lands.
        tip_x = x + (34 if crit else 30) * facing
        tip_y = y - 4

        # Shockwave ring expanding outward.
        ring_r = int(4 + intensity * (20 if crit else 15))
        _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_dark"],
                                        int(140 * intensity)),
                              (tip_x, tip_y), ring_r, 2)
        _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_hot"],
                                        int(180 * intensity)),
                              (tip_x, tip_y), max(1, ring_r - 3), 1)

        # Central flash (additive-looking stack of hot cores).
        for radius, color, alpha in ((14, "fire_dark", 90),
                                     (9, "fire_mid", 160),
                                     (5, "fire_light", 220),
                                     (3, "fire_hot", 255)):
            _NS_grimjaw._aacircle(
                surface,
                (*_NS_grimjaw.PALETTE[color], int(alpha * intensity)),
                (tip_x, tip_y), radius)

        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_core"],
                              (tip_x, tip_y), max(1, int(2 * intensity)))
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["white"],
                              (tip_x, tip_y), max(1, int(1 * intensity)))

        # Radial spark streaks that shoot out at peak.
        for i in range(6):
            angle = (i * math.pi / 3) + progress * 2.0
            r0 = int(6 * intensity)
            r1 = int((14 if crit else 11) * intensity)
            sx = tip_x + int(math.cos(angle) * r0)
            sy = tip_y + int(math.sin(angle) * r0)
            ex = tip_x + int(math.cos(angle) * r1)
            ey = tip_y + int(math.sin(angle) * r1)
            _NS_grimjaw._aaline(surface,
                                (*_NS_grimjaw.PALETTE["fire_hot"],
                                 int(220 * intensity)),
                                (sx, sy), (ex, ey), 1)


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
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
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
        # v2 (animasi): perpindahan berat badan saat idle — goyang kiri-kanan.
        sway = int(math.sin(phase * .8) * 3) * f if not (walk or attack or windrun) else 0
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 2)
        if windrun:
            root_y += 2 - int(abs(math.sin(phase * 2.0)) * 2)
        if attack:
            lean = int(math.sin(ap * math.pi) * 3) * f
            root_y += int(math.sin(ap * math.pi) * 1.5)

        def pt(dx, dy):
            return (int(cx + dx * f + lean + sway), int(cy + dy + root_y))

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
        # v2 (animasi): foot-lift bergantian saat jalan — kaki yang melangkah
        # maju terangkat (lutut + telapak naik), kaki tumpuan tetap menapak.
        leg_phase = stride if (walk or windrun) else 0.0
        stride_vel = math.cos(phase * 1.7) if walk else 0.0
        rear_lift = int(max(0.0, -stride_vel) * 9) if walk else 0
        front_lift = int(max(0.0, stride_vel) * 9) if walk else 0
        if windrun:
            rear_foot = (-13 - int(leg_phase * 7), 38)
            front_foot = (14 + int(leg_phase * 8), 38)
        else:
            rear_foot = (-7 - int(leg_phase * 5),
                         40 - int(abs(leg_phase) * 2) - rear_lift)
            front_foot = (9 + int(leg_phase * 6), 40 - front_lift)
        for hip, knee, foot, shade, lift in (
                ((-6, 11), (-9, 26), rear_foot, p["cloth_darkest"], rear_lift),
                ((6, 11), (9, 25), front_foot, p["cloth_dark"], front_lift)):
            knee = (knee[0], knee[1] - lift)
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
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
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
        # v2 (animasi): perpindahan berat badan saat idle — badan bergoyang
        # ke kiri-kanan (bukan sekadar naik-turun nafas), memberi kesan hidup.
        sway = int(math.sin(phase * .8) * 3) * f if not (walk or attack) else 0
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 2)
        if attack:
            ap = max(0.0, min(1.0, attack_progress))
            lean = int(math.sin(ap * math.pi) * 7) * f
            root_y += int(math.sin(ap * math.pi) * 2)

        def pt(dx, dy):
            return (int(cx + dx * f + lean + sway), int(cy + dy + root_y))

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
        # v2 (animasi): foot-lift bergantian — kaki yang melangkah maju
        # terangkat (lutut + telapak naik), kaki tumpuan tetap menapak.
        # Kecepatan stride menentukan fase swing tiap kaki.
        leg_phase = stride if walk else 0.0
        stride_vel = math.cos(phase * 1.7) if walk else 0.0
        rear_lift = int(max(0.0, -stride_vel) * 9) if walk else 0
        front_lift = int(max(0.0, stride_vel) * 9) if walk else 0
        rear_foot = (-8 - int(leg_phase * 5),
                     40 - int(abs(leg_phase) * 2) - rear_lift)
        front_foot = (11 + int(leg_phase * 6), 40 - front_lift)
        for hip, knee, foot, shade, lift in (
                ((-5, 12), (-9, 27), rear_foot, p["pants_dark"], rear_lift),
                ((6, 12), (9, 26), front_foot, p["pants_mid"], front_lift)):
            # Knee rises with the lift so the thigh folds up to meet the
            # raised shin (proper knee-bend, no gap between segments).
            knee = (knee[0], knee[1] - lift)
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
        _NS_kaizen._draw_elite_katana(surface, cx + lean + sway, cy, f,
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
            # v2 (animasi): afterimage gerak pisau — beberapa siluet katana
            # memudar di belakang ayunan, memunculkan kesan kecepatan slash.
            # Setiap ghost adalah blade utuh (guard + bilah) pada sudut
            # sebelumnya, warnanya makin transparan makin jauh dari pisau.
            for k in (1, 2, 3):
                ga = angle - 0.38 * k
                gux, guy = math.cos(ga) * f, math.sin(ga)
                gtx, gty = hx + gux * length, hy + guy * length
                gpx, gpy = -guy, gux
                gmx = hx + gux * 23 + gpx * 2
                gmy = hy + guy * 23 + gpy * 2
                ghost = [(hx + gpx * 2, hy + gpy * 2),
                         (gmx + gpx, gmy + gpy), (gtx, gty),
                         (gmx - gpx, gmy - gpy),
                         (hx - gpx * 2, hy - gpy * 2)]
                _NS_kaizen._poly(surface, (*p["wind_mid"],
                                           90 - k * 22), ghost)
                _NS_kaizen._poly(surface, (*p["wind_light"],
                                           140 - k * 30), ghost)
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
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
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

        # Masterwork detail & shadow-face swatches
        "face_dark":      (16, 14, 28),
        "crown_tip":      (235, 255, 250),
        "crown_rim":      (95, 225, 220),
        "orb_satellite":  (155, 245, 235),
        "rune_trace":     (140, 235, 230),
        "robe_weave":     (60, 48, 92),

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
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
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
        # Orb spawns from the pose-driven staff tip (shared with the rig).
        sx, sy = _NS_vex._staff_orb_position(
            x, y, facing, float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_vx_attack_progress", 0.0)))
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
        sx, sy = _NS_vex._staff_orb_position(
            x, y, facing, float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_vx_attack_progress", 0.0)))
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
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_vx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # Portraits deliberately contain only the character rig.  Auras and
        # arena-sized skill effects would force the auto-crop to shrink the
        # crown, hood, robe material, and staff orb.
        if not portrait_hd:
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

        if not portrait_hd:
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
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_vex._draw_shadow(surface, x, y + 48)
            _NS_vex._draw_floating_void(surface, x, y + 35, boss.pulse)
        _NS_vex._draw_vex_body(surface, x, y + bob, boss.direction,
                               boss.pulse, "idle", detail=portrait)


    def _draw_vex_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_vex._draw_shadow(surface, x + sway, y + 48)
            _NS_vex._draw_floating_void(surface, x + sway, y + 35, phase, trail=True,
                               facing=boss.direction)
        _NS_vex._draw_vex_body(surface, x + sway, y - bob, boss.direction,
                               phase, "walk", detail=portrait)


    def _draw_vex_attack(surface, boss, x, y):
        progress = getattr(boss, "_vx_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        portrait = bool(getattr(boss, "_portrait_hd", False))

        # Basic attack TIDAK spawn renderer projectile (pakai generic
        # _entity.py yang homing & terarah). Arcane orb renderer hanya
        # saat skill aktif.
        if (getattr(boss, "active_skill", None) is not None
                and 0.5 < progress < 0.6
                and not getattr(boss, "_vx_proj_spawned", False)
                and not portrait):
            _NS_vex._spawn_arcane_orb(boss, x, y)
            boss._vx_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._vx_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        if not portrait:
            _NS_vex._draw_shadow(surface, x + recoil, y + 48)
            _NS_vex._draw_floating_void(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_vex._draw_vex_body(surface, x + recoil, y, boss.direction, boss.pulse,
                       "attack", progress, detail=portrait)
        if not portrait:
            _NS_vex._draw_orb_release_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING - HD void mage
    # ===================================================================

    # ===================================================================
    # MASTERWORK RIG - bone rig 2D berlapis (setara Kaizen/Thorne/Zephyr)
    #
    # Mengganti seluruh set "body-part sticker" lama (cloak, lower_robe,
    # torso, idle/attack arms, arm_segment, hand, staff, head_crown,
    # body_particles) dengan SATU rig pose-driven: crown void menyala
    # dengan ujung cyan, hood berwajah shadow dengan celah mata menyala,
    # pauldron spiky, robe robek yang mengambang, dan staff surgawi yang
    # posisi orb dihitung dari sendi sehingga Arcane Orb / Astral
    # Imprisonment muncul dari ujung staff (bukan pinggang). Semua 100%
    # primitif pygame - tanpa PNG, sprite sheet, ataupun image.load.
    # ===================================================================
    def _draw_vex_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0, detail=False):
        """Wrapper agar idle/walk/attack/skill meneruskan setiap frame ke
        satu rig tulang berlapis (bone rig) tanpa mengubah kontrak."""
        _NS_vex._draw_vex_elite(
            surface, cx, cy, facing, phase, action,
            attack_progress, detail)


    # -------------------------------------------------------------------
    # Pose helpers (deterministic; dipakai rig + anchor skill)
    # -------------------------------------------------------------------
    def _orb_tip_local(phase, action="idle", attack_progress=0.0):
        """Posisi ujung orb staff (ruang lokal, forward = +x).

        Menyambungkan staff ke sendi: saat wind-up orb ditarik ke
        belakang/atas, saat release didorong ke depan, recovery kembali.
        """
        wave = math.sin(phase * 1.3) * 1.5
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < .38:
                t = ap / .38
                return (int(26 - 12 * t), int(-40 - 14 * t + wave))
            if ap < .62:
                t = (ap - .38) / .24
                return (int(14 + 38 * t), int(-54 + 18 * t + wave))
            t = (ap - .62) / .38
            return (int(52 - 20 * t), int(-36 + 4 * t + wave))
        if action == "walk":
            return (int(32 + math.sin(phase * 1.72) * 3),
                    int(-44 + wave))
        return (32, int(-44 + wave))


    def _staff_butt_local(phase, action="idle", attack_progress=0.0):
        ox, oy = _NS_vex._orb_tip_local(phase, action, attack_progress)
        return (int(ox - 30), int(oy + 40))


    def _staff_grip_local(phase, action="idle", attack_progress=0.0):
        ox, oy = _NS_vex._orb_tip_local(phase, action, attack_progress)
        bx, by = _NS_vex._staff_butt_local(phase, action, attack_progress)
        return (int(bx + (ox - bx) * .5), int(by + (oy - by) * .5))


    def _staff_orb_position(cx, cy, facing, phase=0.0, action="idle",
                            attack_progress=0.0):
        """Posisi orb (ruang dunia/canvas) untuk efek skill."""
        tx, ty = _NS_vex._orb_tip_local(phase, action, attack_progress)
        f = 1 if facing >= 0 else -1
        return int(cx + tx * f), int(cy + ty)


    # -------------------------------------------------------------------
    # The layered bone rig
    # -------------------------------------------------------------------
    def _draw_vex_elite(surface, cx, cy, facing, phase, action,
                        attack_progress=0.0, detail=False):
        p = _NS_vex.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.72)
        breath = math.sin(phase * .8)

        lean = int(stride * 2.0 if walk else 0.0)
        if attack:
            lean += int(math.sin(ap * math.pi) * 5.0)
        root_y = int(breath * .8)
        if walk:
            root_y -= int(abs(stride) * 2.0)
        if attack:
            root_y += int(math.sin(ap * math.pi) * 2)

        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_vex._poly(surface, p["shadow_deep"],
                              [(qx + f, qy + 1) for qx, qy in pts])
            _NS_vex._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_vex._aaline(surface, p["shadow_deep"],
                            (aa[0] + f, aa[1] + 1),
                            (bb[0] + f, bb[1] + 1), width + 3)
            _NS_vex._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_vex._aaline(surface, light,
                                (aa[0] + off, aa[1] - 1),
                                (bb[0] + off, bb[1] - 1),
                                max(1, width // 3))

        def dot(color, dx, dy, r, outline=True):
            x, y = pt(dx, dy)
            if outline:
                _NS_vex._aacircle(surface, p["shadow_deep"],
                                  (x + f, y + 1), r + 1)
            _NS_vex._aacircle(surface, color, (x, y), r)

        # Tattered back-cape flare (balances the staff silhouette).
        cape_wave = int(math.sin(phase * .8) * 2)
        poly(p["robe_darkest"], [(-12, -16), (-4, -18), (-6, -2),
             (-10 + cape_wave, 12), (-16, 26), (-22 + cape_wave, 34),
             (-26, 26), (-24, 12), (-20 + cape_wave, -2)])
        poly(p["robe_dark"], [(-11, -14), (-5, -16), (-7, -2),
             (-11 + cape_wave, 10), (-16, 22), (-20 + cape_wave, 28),
             (-23, 22), (-21, 10), (-18 + cape_wave, -2)], False)
        _NS_vex._aaline(surface, p["robe_light"], pt(-19, 0),
                        pt(-23 + cape_wave, 24), 1)
        _NS_vex._aaline(surface, (*p["void_dark"], 160),
                        pt(-21, 6), pt(-25 + cape_wave, 26), 1)

        # Dark crown flames behind the hood.
        _NS_vex._draw_elite_crown(surface, pt, poly, dot, f, phase,
                                  action, back=True, detail=detail)

        # Rear arm (free claw) behind the torso.
        rear_shoulder = (-11, -14)
        if attack:
            rear_elbow = (-16, -2)
            rear_hand = (-17, 9)
        elif walk:
            rear_elbow = (-16, int(stride * 4))
            rear_hand = (-17, 9 + int(stride * 5))
        else:
            rear_elbow = (-16, 0)
            rear_hand = (-17, 9 + int(breath * 2))
        limb(rear_shoulder, rear_elbow, 6, p["robe_dark"], p["robe_mid"])
        limb(rear_elbow, rear_hand, 5, p["skin_dark"], p["skin_mid"])
        rhx, rhy = pt(*rear_hand)
        _NS_vex._aacircle(surface, p["skin_darkest"], (rhx, rhy), 4)
        _NS_vex._aacircle(surface, p["skin_mid"], (rhx, rhy), 3)
        _NS_vex._aacircle(surface, p["skin_light"], (rhx - f, rhy - 1), 1)
        for finger in (-2, 0, 2):
            _NS_vex._aaline(surface, p["skin_light"],
                            (rhx + f, rhy + finger),
                            (rhx + f * 5, rhy + finger - 3), 1)

        # Tattered floating robe / ghost tail (no legs).
        tail_wave = int(math.sin(phase * .9) * 2)
        poly(p["robe_darkest"], [(-15, -8), (15, -8),
             (16 + tail_wave, 10), (13, 24), (7, 36),
             (2 + tail_wave, 44), (-3, 46), (-8, 38),
             (-13, 24), (-16 + tail_wave, 10)])
        poly(p["robe_dark"], [(-13, -6), (13, -6),
             (13 + tail_wave, 10), (10, 22), (5, 33),
             (0, 40), (-5, 34), (-9, 22),
             (-13 + tail_wave, 10)], False)
        poly(p["robe_mid"], [(-9, -4), (9, -4),
             (8 + tail_wave, 8), (6, 18), (2, 28),
             (-1, 33), (-4, 27), (-7, 16),
             (-9 + tail_wave, 8)], False)
        _NS_vex._aaline(surface, p["robe_weave"], pt(-5, 0),
                        pt(-4 + tail_wave, 20), 1)
        _NS_vex._aaline(surface, p["robe_weave"], pt(5, 0),
                        pt(4 + tail_wave, 20), 1)
        _NS_vex._aaline(surface, p["robe_light"], pt(-13, -4),
                        pt(-15 + tail_wave, 10), 1)
        _NS_vex._aaline(surface, p["robe_high"], pt(-9, -2),
                        pt(-11 + tail_wave, 8), 1)
        for i in range(7):
            tx = -12 + i * 4
            ty = 30 + int(math.sin(phase * 1.2 + i) * 2)
            ln = 8 + (i % 3) * 3
            poly(p["robe_darkest"], [(tx - 2, 26), (tx + 2, 26),
                 (tx + 1, ty + ln), (tx - 1, ty + ln)], False)
            _NS_vex._aacircle(surface, (*p["void_dark"], 150),
                              pt(tx, ty + ln), 1)
        # glowing runes down the robe front
        for i, off in enumerate((-7, 0, 7)):
            gx, gy = off, 14
            _NS_vex._aaline(surface, (*p["void_mid"], 200),
                            pt(gx, gy - 4), pt(gx, gy + 4), 1)
            _NS_vex._aacircle(surface, p["void_hot"], pt(gx, gy), 2)

        # Torso armor with central void gem.
        poly(p["armor_darkest"], [(-13, -18), (13, -18),
             (12, 8), (5, 14), (-5, 14), (-12, 8)])
        poly(p["armor_dark"], [(-11, -16), (11, -16),
             (10, 6), (4, 12), (-4, 12), (-10, 6)], False)
        poly(p["armor_mid"], [(-8, -13), (8, -13),
             (7, 4), (3, 9), (-3, 9), (-7, 4)], False)
        _NS_vex._aaline(surface, p["armor_light"], pt(-11, -16),
                        pt(-10, 4), 1)
        _NS_vex._aaline(surface, p["armor_shine"], pt(-9, -15),
                        pt(-2, -15), 1)
        _NS_vex._aaline(surface, p["shadow_deep"], pt(-6, -15),
                        pt(0, -2), 2)
        _NS_vex._aaline(surface, p["shadow_deep"], pt(6, -15),
                        pt(0, -2), 2)
        gem_pulse = math.sin(phase * 1.5) * .3 + .7
        dot(p["armor_darkest"], 0, 2, 5, False)
        _NS_vex._aacircle(surface, (*p["void_dark"], int(200 * gem_pulse)),
                          pt(0, 2), 4)
        _NS_vex._aacircle(surface, (*p["void_mid"], int(235 * gem_pulse)),
                          pt(0, 2), 3)
        _NS_vex._aacircle(surface, p["void_hot"], pt(0, 1), 2)
        _NS_vex._aacircle(surface, p["white"], pt(0, 1), 1)

        # Spiky pauldrons (armor plating with rising spike + rune).
        for side in (-1, 1):
            sx = side * 14
            poly(p["armor_darkest"], [(sx - 6, -20), (sx + 6, -20),
                 (sx + 7, -10), (sx, -6), (sx - 7, -10)])
            poly(p["armor_dark"], [(sx - 5, -19), (sx + 5, -19),
                 (sx + 6, -11), (sx, -8), (sx - 6, -11)], False)
            poly(p["armor_mid"], [(sx - 3, -18), (sx + 3, -18),
                 (sx + 4, -12), (sx, -10), (sx - 4, -12)], False)
            poly(p["armor_darkest"], [(sx - 2, -20), (sx, -33),
                 (sx + 2, -20)])
            _NS_vex._aaline(surface, p["armor_shine"],
                            pt(sx - 1, -20), pt(sx, -30), 1)
            _NS_vex._aacircle(surface, (*p["void_bright"], 180),
                              pt(sx, -13), 1)

        # Neck.
        poly(p["skin_darkest"], [(-4, -18), (4, -18), (4, -10), (-3, -10)])
        poly(p["skin_mid"], [(-2, -18), (3, -18), (3, -11), (-2, -11)],
             False)

        # Pose-driven diagonal void staff.
        butt = _NS_vex._staff_butt_local(phase, action, ap)
        orb = _NS_vex._orb_tip_local(phase, action, ap)
        grip = _NS_vex._staff_grip_local(phase, action, ap)
        _NS_vex._draw_elite_staff(surface, pt, poly, dot, f, butt, orb,
                                  grip, phase, detail)

        # Front staff arm: the fist is derived from the pose-driven grip.
        front_shoulder = (11, -14)
        if attack:
            front_elbow = (grip[0] - 6, grip[1] + 6)
        elif walk:
            front_elbow = (grip[0] - 7, grip[1] + 5 + int(stride * 2))
        else:
            front_elbow = (grip[0] - 7, grip[1] + 6)
        limb(front_shoulder, front_elbow, 6, p["robe_mid"], p["robe_light"])
        limb(front_elbow, grip, 5, p["skin_dark"], p["skin_light"])
        ghx, ghy = pt(*grip)
        _NS_vex._aacircle(surface, p["skin_darkest"], (ghx, ghy), 4)
        _NS_vex._aacircle(surface, p["skin_mid"], (ghx, ghy), 3)

        # Hooded head with shadowed face + glowing eye slit.
        _NS_vex._draw_elite_hood(surface, pt, poly, dot, f, phase,
                                 action, ap, detail)

        # Bright front crown flames (cyan tips).
        _NS_vex._draw_elite_crown(surface, pt, poly, dot, f, phase,
                                  action, back=False, detail=detail)

        if detail:
            _NS_vex._draw_vex_masterwork_details(
                surface, pt, poly, dot, f, phase, action)


    # -------------------------------------------------------------------
    # Void-flame crown
    # -------------------------------------------------------------------
    def _draw_elite_crown(surface, pt, poly, dot, f, phase, action,
                          back=False, detail=False):
        """Void-flame crown: connected burning crest hugging the hood."""
        p = _NS_vex.PALETTE
        if back:
            # Solid void volume behind the hood so the flames never float.
            poly(p["void_darkest"], [(-15, -24), (-17, -34), (-12, -44),
                 (0, -50), (12, -44), (17, -34), (15, -24), (8, -18),
                 (-8, -18)])
            poly(p["void_dark"], [(-12, -26), (-14, -34), (-10, -42),
                 (0, -47), (10, -42), (14, -34), (12, -26), (6, -20),
                 (-6, -20)], False)
            poly(p["void_mid"], [(-8, -28), (-10, -34), (-7, -40),
                 (0, -44), (7, -40), (10, -34), (8, -28), (4, -22),
                 (-4, -22)], False)
            return
        # ONE connected flaming crest silhouette (bukan jarum terpisah):
        # gelombang api menyapu ke belakang dengan 4 puncakan berlekuk.
        crest = [(-16, -26), (-18, -34), (-13, -40), (-11, -48),
                 (-8, -41), (-5, -52), (-2, -43), (1, -56), (4, -44),
                 (7, -50), (9, -40), (13, -44), (15, -34), (16, -26),
                 (10, -20), (-10, -20)]
        sway = int(math.sin(phase * 1.1) * 1)

        def lift(q):
            return (q[0] + (sway if q[1] < -40 else 0), q[1])

        poly(p["void_darkest"], [lift(q) for q in crest])

        def inner(scale):
            out = []
            for x, y in crest:
                out.append((int(x * scale), int(-28 + (y + 28) * scale)))
            return out

        poly(p["void_dark"], inner(0.82), False)
        poly(p["void_mid"], inner(0.62), False)
        poly(p["void_light"], inner(0.40), False)
        # flame licks on the two tallest notches + bright beads
        for tx, ty in ((-5, -52), (1, -56)):
            x, y = pt(tx + sway, ty)
            _NS_vex._aacircle(surface, p["crown_tip"], (x, y), 1)
        # side horns curving out from the temples
        for side in (-1, 1):
            poly(p["void_darkest"], [(side * 14, -30), (side * 24, -27),
                 (side * 20, -22), (side * 13, -24)])
            poly(p["void_mid"], [(side * 15, -28), (side * 22, -26),
                 (side * 18, -24)], False)
        _NS_vex._aaline(surface, p["crown_rim"], pt(-12, -31),
                        pt(6, -33), 1)


    # -------------------------------------------------------------------
    # Diagonal void staff
    # -------------------------------------------------------------------
    def _draw_elite_staff(surface, pt, poly, dot, f, butt, orb, grip,
                          phase, detail):
        p = _NS_vex.PALETTE
        bx, by = pt(*butt)
        ox, oy = pt(*orb)
        _NS_vex._aaline(surface, p["shadow_deep"], (bx + f * 2, by + 1),
                        (ox + f * 2, oy + 1), 7)
        _NS_vex._aaline(surface, p["staff_dark"], (bx, by), (ox, oy), 5)
        _NS_vex._aaline(surface, p["staff_mid"], (bx, by), (ox, oy), 3)
        _NS_vex._aaline(surface, p["staff_light"], (bx, by), (ox, oy), 1)
        _NS_vex._aaline(surface, (*p["rune_mid"], 170),
                        (bx + f, by - 1), (ox + f, oy - 1), 1)
        for t in (.3, .62):
            rx = int(bx + (ox - bx) * t)
            ry = int(by + (oy - by) * t)
            _NS_vex._aacircle(surface, p["armor_darkest"], (rx, ry), 3)
            _NS_vex._aacircle(surface, p["void_bright"], (rx, ry), 1)
        # crescent claw cradle around the orb (tight, hugging the gem)
        for side in (-1, 1):
            prev = (int(bx + (ox - bx) * .9), int(by + (oy - by) * .9))
            for i in range(1, 6):
                t = i / 5.0
                cx2 = ox + side * math.sin(t * math.pi) * 6
                cy2 = oy + (1 - t) * 9 - t * 2
                _NS_vex._aaline(surface, p["staff_dark"], prev,
                                (cx2 + f, cy2), 3)
                _NS_vex._aaline(surface, p["staff_light"], prev,
                                (cx2, cy2), 1)
                prev = (cx2, cy2)
        pulse = .72 + math.sin(phase * 2.5) * .18
        for radius, color, alpha in ((10, p["void_dark"], 50),
                                     (7, p["void_mid"], 105),
                                     (5, p["void_light"], 180)):
            _NS_vex._aacircle(surface, (*color, int(alpha * pulse)),
                              (ox, oy), radius)
        _NS_vex._aacircle(surface, p["void_hot"], (ox, oy), 3)
        _NS_vex._aacircle(surface, p["void_white"], (ox - 1, oy - 1), 2)
        _NS_vex._aacircle(surface, p["white"], (ox - f, oy - 1), 1)
        for i in range(3):
            a = phase * 2 + i * math.tau / 3
            sx = int(ox + math.cos(a) * 9)
            sy = int(oy + math.sin(a) * 9)
            _NS_vex._aacircle(surface, p["orb_satellite"], (sx, sy), 1)


    # -------------------------------------------------------------------
    # Hooded head + shadowed face
    # -------------------------------------------------------------------
    def _draw_elite_hood(surface, pt, poly, dot, f, phase, action, ap,
                         detail):
        p = _NS_vex.PALETTE
        poly(p["robe_darkest"], [(-11, -46), (0, -52), (11, -46),
             (15, -34), (14, -22), (7, -16), (0, -14),
             (-7, -16), (-14, -22), (-15, -34)])
        poly(p["robe_dark"], [(-9, -44), (0, -49), (9, -44),
             (12, -34), (11, -24), (6, -19), (0, -17),
             (-6, -19), (-11, -24), (-12, -34)], False)
        poly(p["robe_mid"], [(-6, -42), (0, -46), (6, -42),
             (8, -34), (7, -26), (2, -21), (-2, -21),
             (-7, -26), (-8, -34)], False)
        peak = int(math.sin(phase * 1.1) * 2)
        poly(p["robe_darkest"], [(0, -51), (4, -54),
             (-8, -53 + peak), (-16, -46 + peak), (-8, -44)])
        _NS_vex._aaline(surface, p["robe_light"], pt(-12, -34),
                        pt(-7, -17), 1)
        _NS_vex._aaline(surface, p["robe_high"], pt(-10, -42),
                        pt(-13, -30), 1)
        # shadowed void face
        poly(p["face_dark"], [(-7, -38), (0, -41), (7, -38),
             (9, -30), (7, -24), (0, -22), (-7, -24), (-9, -30)])
        # glowing cyan eye SLIT (brighter while attacking)
        glow = action in ("attack",) or ap > .35
        ex, ey = pt(0, -30)
        _NS_vex._aacircle(surface, (*p["void_dark"], 140), (ex, ey), 5)
        _NS_vex._aaline(surface, p["eye_glow"], pt(-4, -30), pt(4, -30), 3)
        _NS_vex._aaline(surface, p["void_hot"], pt(-3, -30), pt(3, -30), 1)
        if glow:
            _NS_vex._aaline(surface, p["eye_bright"], pt(-2, -30),
                            pt(2, -30), 1)
            _NS_vex._aacircle(surface, p["white"], (ex - f, ey - 1), 1)
        _NS_vex._aaline(surface, p["robe_darkest"], pt(-3, -24),
                        pt(3, -24), 2)


    # -------------------------------------------------------------------
    # Portrait-only LOD pass (extra material detail; arena LOD stays cheap)
    # -------------------------------------------------------------------
    def _draw_vex_masterwork_details(surface, pt, poly, dot, f, phase,
                                     action):
        p = _NS_vex.PALETTE
        for i in range(4):
            _NS_vex._aaline(surface, p["crown_rim"],
                            pt(-12 + i * 8, -29),
                            pt(-12 + i * 8, -34 - (i % 2) * 5), 1)
        for yy in (-40, -35, -30):
            _NS_vex._aacircle(surface, p["robe_light"], pt(-9, yy), 1)
            _NS_vex._aacircle(surface, p["robe_light"], pt(9, yy), 1)
        for i in range(4):
            y = 4 + i * 6
            _NS_vex._aaline(surface, p["robe_mid"], pt(-6, y),
                            pt(6, y + 2), 1)
        for t in (.3, .62):
            ox, oy = _NS_vex._orb_tip_local(phase, action)
            bx, by = _NS_vex._staff_butt_local(phase, action)
            rx = int(bx + (ox - bx) * t)
            ry = int(by + (oy - by) * t)
            _NS_vex._aacircle(surface, p["rune_trace"], pt(rx, ry), 1)
        for i in range(4):
            t = (phase * .4 + i / 4.0) % 1.0
            dx = -10 + i * 6 + int(math.sin(phase * 1.3 + i) * 2)
            dy = 10 - int(t * 48)
            _NS_vex._aacircle(surface,
                              (*p["void_bright"], int(180 * (1 - t))),
                              pt(dx, dy), 1)
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
        # Warm fey skin — contrast is deliberately strong enough to survive
        # the arena downscale while retaining the reference's porcelain tone.
        "skin_darkest":   ( 83,  38,  52),
        "skin_dark":      (151,  76,  88),
        "skin_mid":       (218, 135, 142),
        "skin_light":     (248, 188, 181),
        "skin_high":      (255, 220, 208),

        # Crimson thorn-crown hair.
        "hair_darkest":   ( 50,   8,  28),
        "hair_dark":      (111,  18,  51),
        "hair_mid":       (181,  38,  78),
        "hair_light":     (232,  82, 123),
        "hair_shine":     (255, 142, 173),
        "hair_tip":       (255, 202, 221),

        # Layered plum/pink gown and fitted corset.
        "dress_darkest":  ( 25,   8,  38),
        "dress_dark":     ( 55,  17,  69),
        "dress_mid":      (108,  35, 112),
        "dress_light":    (166,  63, 148),
        "dress_high":     (220, 112, 188),
        "corset_dark":    ( 20,   7,  31),
        "corset_mid":     ( 59,  20,  70),
        "corset_light":   (124,  54, 130),
        "cloak_darkest":  ( 18,   7,  31),
        "cloak_dark":     ( 48,  19,  69),
        "cloak_mid":      ( 88,  41, 119),
        "cloak_light":    (157,  93, 185),
        "boot_darkest":   ( 19,  10,  30),
        "boot_dark":      ( 48,  25,  61),
        "boot_mid":       ( 91,  49, 104),
        "boot_light":     (174, 111, 178),
        "thread_light":   (240, 150, 210),

        # Moth wings: opaque ink rim plus translucent violet membranes.
        "wing_darkest":   ( 34,  12,  58),
        "wing_dark":      ( 76,  35, 119),
        "wing_mid":       (137,  78, 180),
        "wing_light":     (196, 135, 220),
        "wing_shine":     (244, 198, 250),
        "wing_vein":      ( 92,  45, 135),
        "wing_glass":     (229, 176, 241),

        # Living blackwood staff, amethyst jewel and thorn metal.
        "staff_dark":     ( 29,  15,  38),
        "staff_mid":      ( 72,  41,  70),
        "staff_light":    (133,  90, 126),
        "staff_vine":     (104,  43,  99),
        "staff_glow":     (255, 155, 221),
        "jewel_dark":     ( 80,  12,  73),
        "jewel_mid":      (191,  44, 151),
        "jewel_light":    (255, 159, 220),
        "thorn_dark":     ( 45,  13,  57),
        "thorn_mid":      ( 99,  35, 104),
        "thorn_light":    (190,  80, 161),
        # Retained names are used by established gameplay projectile code.
        "bramble_dark":   ( 45,  13,  57),
        "bramble_mid":    ( 99,  35, 104),
        "bramble_light":  (190,  80, 161),

        # Spell and rune values.
        "magic_darkest":  ( 42,   4,  42),
        "magic_dark":     (103,  13,  86),
        "magic_mid":      (181,  34, 141),
        "magic_light":    (234,  83, 181),
        "magic_bright":   (255, 139, 211),
        "magic_hot":      (255, 203, 238),
        "magic_white":    (255, 244, 252),
        "rune_dark":      ( 70,  22,  92),
        "rune_mid":       (157,  50, 156),
        "rune_light":     (242, 138, 218),

        # Antique gold circlet/corset hardware.
        "gold_dark":      ( 84,  55,  18),
        "gold_mid":       (162, 112,  36),
        "gold_light":     (236, 194,  92),

        # Violet-pink eyes and rose lips; the cool glow echoes the reference
        # while preserving a readable light iris at small arena scale.
        "eye_white":      (255, 236, 230),
        "eye_iris":       (153,  41, 104),
        "eye_iris_light": (255, 157, 211),
        "eye_pupil":      ( 20,   7,  15),
        "lips_dark":      (134,  22,  62),
        "lips_mid":       (218,  69, 119),

        "butterfly_dark": ( 59,  13,  68),
        "butterfly_mid":  (159,  49, 143),
        "butterfly_light":(245, 143, 218),
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   5,  13),
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
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
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
        # The bolt starts at the same pose-driven orb the rig renders.
        # Keeping this shared anchor prevents the spell from appearing to
        # emerge from Zephyr's waist after the masterwork staff upgrade.
        sx, sy = _NS_zephyr._staff_orb_position(
            x, y, facing, float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_zp_attack_progress", 0.0)))
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
        sx, sy = _NS_zephyr._staff_orb_position(
            x, y, facing, float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_zp_attack_progress", 0.0)))
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
    # ZEPHYR MASTERWORK — MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_zephyr(surface, boss, x, y):
        """Render Zephyr's procedural masterwork rig.

        The gameplay contract (Q/W/E/R timers, casket projectile and cache
        pipeline) intentionally stays unchanged.  Only the former collection
        of independent body stickers is replaced by one pose-driven rig.
        """
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zephyr._detect_moving(boss)
        _NS_zephyr._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_zp_attack_active", False)
            or getattr(boss, "timer", 0) >
            getattr(boss, "attack_cooldown", 42) - 15
        )

        # Portraits deliberately contain only the character rig.  Auras and
        # arena-sized skill effects would force auto-crop to shrink Zephyr's
        # face, gown, wing material, and staff details.
        if not portrait_hd:
            _NS_zephyr._draw_fey_rim_light(surface, x, y - 13, pulse)
            _NS_zephyr._draw_fey_aura(surface, x, y, pulse)
            _NS_zephyr._draw_fey_platform(surface, x, y + 43, pulse,
                                          active_skill)

            if active_skill == "q":
                _NS_zephyr._draw_bramble_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                _NS_zephyr._draw_shadow_realm_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                _NS_zephyr._draw_bedlam_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                _NS_zephyr._draw_casket_indicator(
                    surface, boss, x, y, skill_timer, pulse)

        if attacking:
            _NS_zephyr._draw_zephyr_attack(surface, boss, x, y)
        elif moving:
            _NS_zephyr._draw_zephyr_walk(surface, boss, x, y)
        else:
            _NS_zephyr._draw_zephyr_idle(surface, boss, x, y)

        if not portrait_hd:
            _NS_zephyr._manage_projectiles(boss, surface, pulse)

            if active_skill == "q":
                _NS_zephyr._draw_bramble_maze(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                _NS_zephyr._draw_shadow_realm(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                _NS_zephyr._handle_casket_skill(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                _NS_zephyr._draw_bedlam(
                    surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE ENTRY POINTS
    # ===================================================================
    def _draw_zephyr_idle(surface, boss, x, y):
        phase = float(getattr(boss, "pulse", 0.0))
        bob = int(math.sin(phase * .78) * 2)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        if not portrait_hd:
            _NS_zephyr._draw_shadow(surface, x, y + 47)
            _NS_zephyr._draw_floating_sparkles(surface, x, y + 34, phase)
        _NS_zephyr._draw_zephyr_body(
            surface, x, y + bob, getattr(boss, "direction", 1), phase,
            "idle", detail=portrait_hd)


    def _draw_zephyr_walk(surface, boss, x, y):
        phase = float(getattr(boss, "pulse", 0.0)) * 2.0
        stride = math.sin(phase * 1.72)
        bob = int(abs(stride) * 3)
        sway = int(stride * 2)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        if not portrait_hd:
            _NS_zephyr._draw_shadow(surface, x + sway, y + 47)
            _NS_zephyr._draw_floating_sparkles(
                surface, x + sway, y + 35, phase, trail=True,
                facing=getattr(boss, "direction", 1))
        _NS_zephyr._draw_zephyr_body(
            surface, x + sway, y - bob, getattr(boss, "direction", 1),
            phase, "walk", detail=portrait_hd)


    def _draw_zephyr_attack(surface, boss, x, y):
        progress = max(0.0, min(1.0,
            float(getattr(boss, "_zp_attack_progress", 0.0))))
        phase = float(getattr(boss, "pulse", 0.0))
        facing = getattr(boss, "direction", 1)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        # The gameplay projectile remains authoritative in _entity.py.  This
        # renderer-only bolt is emitted only while a hero skill is active, so
        # it cannot double the normal ranged attack visual.
        if (getattr(boss, "active_skill", None) is not None
                and .48 < progress < .60
                and not getattr(boss, "_zp_proj_spawned", False)
                and not portrait_hd):
            _NS_zephyr._spawn_magic_bolt(boss, x, y)
            boss._zp_proj_spawned = True
        if progress < .15 or progress > .9:
            boss._zp_proj_spawned = False

        lunge = int(math.sin(progress * math.pi) * 4)
        recoil = -lunge * (1 if facing >= 0 else -1)
        if not portrait_hd:
            _NS_zephyr._draw_shadow(surface, x + recoil, y + 47)
            _NS_zephyr._draw_floating_sparkles(
                surface, x + recoil, y + 34, phase, intense=True,
                facing=facing)
        _NS_zephyr._draw_zephyr_body(
            surface, x + recoil, y, facing, phase, "attack", progress,
            detail=portrait_hd)
        if not portrait_hd:
            _NS_zephyr._draw_cast_flash(surface, x + recoil, y, facing,
                                        progress, phase)


    # ===================================================================
    # MASTERWORK RIG
    # ===================================================================
    def _staff_tip_local(phase, action="idle", attack_progress=0.0):
        """Pose-driven local orb position for Zephyr's thorn staff.

        Reference alignment: the crystal sits beside the face/forward
        shoulder rather than hovering above her head.  The shaft therefore
        reads as a crooked faerie wand in idle, then pulls back into the
        silhouette before thrusting forward for a bolt release.
        """
        wave = math.sin(phase * 1.35) * 1.4
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < .40:
                # Wind-up: tuck the orb toward the hair and lift it.
                t = ap / .40
                return (int(42 - 22 * t), int(-19 - 18 * t + wave))
            if ap < .62:
                # Release: an unmistakable forward-pointing wand pose.
                t = (ap - .40) / .22
                return (int(20 + 47 * t), int(-37 + 17 * t + wave))
            # Recovery retains a slight forward reach instead of snapping.
            t = (ap - .62) / .38
            return (int(67 - 24 * t), int(-20 + 3 * t + wave))
        if action == "walk":
            return (int(42 + math.sin(phase * 1.72) * 3),
                    int(-19 + wave))
        return (42, int(-19 + wave))


    def _staff_orb_position(cx, cy, facing, phase=0.0, action="idle",
                            attack_progress=0.0):
        """World/canvas position of the staff orb for spell effects."""
        tx, ty = _NS_zephyr._staff_tip_local(phase, action, attack_progress)
        f = 1 if facing >= 0 else -1
        return int(cx + tx * f), int(cy + ty)


    def _draw_zephyr_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0.0, detail=False):
        """Render the replacement Zephyr masterwork body.

        Every visible material is generated from pygame primitives.  Unlike
        the retired torso/arms/skirt stickers, wings, hair, hands, gown and
        staff share the same `pt()` transform and thus react together to the
        walk, idle and casting pose.
        """
        _NS_zephyr._draw_zephyr_elite(
            surface, cx, cy, facing, phase, action, attack_progress, detail)


    def _draw_zephyr_rig(surface, cx, cy, facing, phase, action,
                         attack_progress=0.0, detail=False):
        """Explicit rig alias used by visual tooling and future cosmetics."""
        _NS_zephyr._draw_zephyr_elite(
            surface, cx, cy, facing, phase, action, attack_progress, detail)


    def _draw_zephyr_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False):
        """Layered dark-fey bone rig: crown, moth wings, gown and staff."""
        p = _NS_zephyr.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.72)
        breath = math.sin(phase * .78)

        lean = int((3.5 * stride if walk else 0.0) +
                   (math.sin(ap * math.pi) * 7.0 if attack else 0.0))
        root_y = int(breath * .9)
        if walk:
            root_y -= int(abs(stride) * 2.5)
        if attack:
            root_y += int(math.sin(ap * math.pi) * 2)

        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                  [(qx + f, qy + 1) for qx, qy in pts])
            _NS_zephyr._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_zephyr._aaline(surface, p["shadow_deep"],
                                (aa[0] + f, aa[1] + 1),
                                (bb[0] + f, bb[1] + 1), width + 3)
            _NS_zephyr._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_zephyr._aaline(surface, light,
                                    (aa[0] + off, aa[1] - 1),
                                    (bb[0] + off, bb[1] - 1),
                                    max(1, width // 3))

        # ── back layer: wings and animated thorn-hair silhouette ──
        _NS_zephyr._draw_elite_wings(surface, pt, f, phase, action, detail)
        _NS_zephyr._draw_zephyr_crown(surface, pt, f, phase, detail)

        # A long asymmetric mantle makes the fairy readable from a 3/4 angle.
        mantle_wave = int(math.sin(phase * 1.18) * 3)
        mantle_push = 7 if walk or attack else 0
        poly(p["cloak_darkest"], [(-8, -23), (-18, -16),
             (-27 - mantle_push, -2 + mantle_wave),
             (-31 - mantle_push, 19 + mantle_wave), (-21, 15),
             (-10, 4), (-3, -12)])
        poly(p["cloak_dark"], [(-9, -21), (-17, -14),
             (-24 - mantle_push, 0 + mantle_wave),
             (-26 - mantle_push, 14 + mantle_wave), (-18, 10),
             (-8, 0)], False)
        _NS_zephyr._aaline(surface, p["cloak_light"], pt(-13, -17),
                            pt(-25 - mantle_push, 10 + mantle_wave), 1)

        # ── planted legs, tights and ankle boots ──
        front_step = int(stride * 4) if walk else 0
        rear_step = -front_step
        if attack:
            front_step += int(ap * 5)
            rear_step -= int(ap * 3)
        legs = ((-7, rear_step, p["boot_dark"], p["boot_mid"]),
                (7, front_step, p["boot_mid"], p["boot_light"]))
        for i, (side, step, boot_base, boot_light) in enumerate(legs):
            thigh_x = side + step
            # visible striped tights above the boot
            poly(p["dress_darkest"], [(thigh_x - 5, 15),
                 (thigh_x + 5, 15), (thigh_x + 4, 29),
                 (thigh_x - 4, 29)])
            poly(p["dress_mid"], [(thigh_x - 3, 17),
                 (thigh_x + 3, 17), (thigh_x + 2, 28),
                 (thigh_x - 3, 28)], False)
            _NS_zephyr._aaline(surface, p["dress_light"],
                                pt(thigh_x - 1, 18), pt(thigh_x - 1, 27), 1)
            # pointed cuff, heel and toe establish ground contact.
            poly(p["boot_darkest"], [(thigh_x - 6, 27),
                 (thigh_x + 5, 27), (thigh_x + 6, 40),
                 (thigh_x - 5, 40)])
            poly(boot_base, [(thigh_x - 4, 28), (thigh_x + 3, 28),
                 (thigh_x + 4, 38), (thigh_x - 4, 38)], False)
            _NS_zephyr._aaline(surface, boot_light,
                                pt(thigh_x - 2, 30), pt(thigh_x - 1, 37), 1)
            toe = 4 * f
            foot = pt(thigh_x + (3 if f > 0 else -3), 40)
            _NS_zephyr._aaline(surface, p["shadow_deep"],
                                (foot[0] - toe, foot[1] + 1),
                                (foot[0] + toe, foot[1] + 1), 4)
            _NS_zephyr._aaline(surface, p["boot_light"],
                                (foot[0] - toe, foot[1]),
                                (foot[0] + toe, foot[1]), 2)

        # ── four independent petal panels of the gown ──
        skirt_wave = math.sin(phase * 1.1) * 2
        for i, (base_x, width, length) in enumerate(
                ((-13, 9, 27), (-4, 10, 31), (5, 10, 29), (14, 8, 24))):
            sway = int(skirt_wave * (1.0 + (i % 2) * .35) +
                       (stride * (i - 1.5) if walk else 0))
            dark = p["dress_darkest"] if i in (0, 3) else p["dress_dark"]
            mid = p["dress_mid"] if i != 1 else p["dress_light"]
            panel = [(base_x - width // 2, 0), (base_x + width // 2, 0),
                     (base_x + width // 2 + sway, length - 5),
                     (base_x + sway, length),
                     (base_x - width // 2 + sway - 2, length - 5)]
            poly(dark, panel)
            inset = [(base_x - width // 2 + 2, 2),
                     (base_x + width // 2 - 2, 2),
                     (base_x + width // 2 - 1 + sway, length - 7),
                     (base_x + sway, length - 3),
                     (base_x - width // 2 + 1 + sway, length - 7)]
            poly(mid, inset, False)
            _NS_zephyr._aaline(surface, p["dress_high"],
                                pt(base_x - 1, 4),
                                pt(base_x + sway, length - 5), 1)
            if i == 1:
                _NS_zephyr._aacircle(surface, p["jewel_light"],
                                      pt(base_x, 13), 1)

        # ── fitted torso, corset and shoulder mantle ──
        poly(p["dress_darkest"], [(-12, -26), (-4, -31), (8, -30),
             (14, -22), (11, 3), (4, 8), (-8, 6), (-13, -5)])
        poly(p["dress_mid"], [(-9, -25), (-3, -28), (7, -28),
             (11, -21), (8, 2), (2, 5), (-6, 4), (-10, -5)], False)
        # armored petal shoulder / collar
        poly(p["cloak_dark"], [(-13, -25), (-17, -31), (-12, -36),
             (-4, -31), (-7, -24)])
        poly(p["cloak_mid"], [(-13, -27), (-15, -31), (-11, -33),
             (-6, -30), (-8, -26)], False)
        poly(p["cloak_dark"], [(8, -29), (15, -33), (20, -28),
             (16, -21), (10, -23)])
        _NS_zephyr._aaline(surface, p["cloak_light"], pt(10, -29),
                            pt(17, -28), 1)

        # Corset is deliberately dark, then laced over high-value purple.
        poly(p["corset_dark"], [(-7, -20), (8, -20), (8, 1),
             (3, 5), (-5, 4), (-8, 0)])
        poly(p["corset_mid"], [(-5, -18), (6, -18), (6, 0),
             (2, 3), (-4, 2), (-6, 0)], False)
        _NS_zephyr._aaline(surface, p["corset_light"], pt(-3, -17),
                            pt(3, 1), 1)
        for j in range(4):
            yy = -15 + j * 4
            _NS_zephyr._aaline(surface, p["rune_light"], pt(-3, yy),
                                pt(3, yy + 2), 1)
            _NS_zephyr._aaline(surface, p["rune_light"], pt(3, yy),
                                pt(-3, yy + 2), 1)
        _NS_zephyr._aaline(surface, p["gold_dark"], pt(-11, 4),
                            pt(11, 4), 4)
        _NS_zephyr._aaline(surface, p["gold_mid"], pt(-10, 4),
                            pt(10, 4), 2)
        buckle = pt(1, 4)
        _NS_zephyr._aacircle(surface, p["gold_light"], buckle, 3)
        _NS_zephyr._aacircle(surface, p["jewel_mid"], buckle, 1)

        # ── pose-driven thorn staff ──
        staff_top = _NS_zephyr._staff_tip_local(phase, action, ap)
        # Crooked wand silhouette from the reference: low near the hip,
        # crystal forward beside Zephyr's shoulder rather than a vertical pole.
        staff_bottom = (2 + int(stride * 2 if walk else 0), 25)
        grip = (int(staff_bottom[0] * .48 + staff_top[0] * .52),
                int(staff_bottom[1] * .48 + staff_top[1] * .52))
        _NS_zephyr._draw_elite_staff(surface, pt, f, staff_bottom, staff_top,
                                     phase, action, detail)

        # ── rear arm first: free hand becomes a casting claw ──
        rear_shoulder = (-8, -22)
        if attack:
            rear_hand = (staff_top[0] - 7, staff_top[1] + 14)
            rear_elbow = (rear_hand[0] - 10, rear_hand[1] + 7)
        elif walk:
            rear_hand = (-14, -3 + int(stride * 5))
            rear_elbow = (-16, -13 - int(stride * 3))
        else:
            rear_hand = (-13, -3 + int(breath * 2))
            rear_elbow = (-17, -14 + int(breath))
        limb(rear_shoulder, rear_elbow, 6, p["cloak_dark"], p["cloak_mid"])
        limb(rear_elbow, rear_hand, 5, p["skin_dark"], p["skin_mid"])
        rhx, rhy = pt(*rear_hand)
        _NS_zephyr._aacircle(surface, p["skin_darkest"], (rhx, rhy), 4)
        _NS_zephyr._aacircle(surface, p["skin_mid"], (rhx, rhy), 3)
        _NS_zephyr._aacircle(surface, p["skin_light"], (rhx - f, rhy - 1), 1)
        # delicate fingers make the spellcasting silhouette legible.
        for finger in (-2, 0, 2):
            _NS_zephyr._aaline(surface, p["skin_light"],
                                (rhx + f, rhy + finger),
                                (rhx + f * 4, rhy + finger - 2), 1)

        # ── head and expressive face ──
        # Neck appears before face and collar to keep proportions grounded.
        poly(p["skin_darkest"], [(-4, -33), (5, -33), (5, -24),
                                  (-3, -23)])
        poly(p["skin_mid"], [(-2, -33), (3, -33), (3, -25),
                              (-1, -24)], False)
        # Face is a 3/4 wedge: cheek and nose sit toward facing direction.
        poly(p["skin_darkest"], [(-10, -52), (2, -57), (11, -51),
             (13, -40), (8, -31), (-2, -29), (-10, -36), (-13, -45)])
        poly(p["skin_dark"], [(-8, -50), (2, -54), (9, -49),
             (10, -40), (6, -33), (-1, -31), (-8, -37), (-10, -45)],
             False)
        poly(p["skin_mid"], [(-5, -49), (2, -52), (7, -48),
             (8, -41), (4, -34), (-1, -33), (-6, -38)], False)
        poly(p["skin_light"], [(0, -50), (5, -48), (6, -42),
             (2, -38), (-2, -40)], False)
        # ear, nose, two bright amber eyes and mischievous mouth.
        _NS_zephyr._aacircle(surface, p["skin_mid"], pt(-9, -42), 3)
        _NS_zephyr._aacircle(surface, p["skin_light"], pt(-10, -43), 1)
        for ex, ey, radius in ((-2, -43, 2), (6, -43, 3)):
            px, py = pt(ex, ey)
            _NS_zephyr._aacircle(surface, p["eye_white"], (px, py), radius)
            _NS_zephyr._aacircle(surface, p["eye_iris"],
                                  (px + f, py), max(1, radius - 1))
            _NS_zephyr._aacircle(surface, p["eye_iris_light"],
                                  (px + f, py - 1), 1)
            _NS_zephyr._aacircle(surface, p["eye_pupil"],
                                  (px + f, py), 1)
            _NS_zephyr._aacircle(surface, p["white"],
                                  (px, py - 1), 1)
        _NS_zephyr._aaline(surface, p["hair_darkest"], pt(-5, -47),
                            pt(1, -48), 1)
        _NS_zephyr._aaline(surface, p["hair_darkest"], pt(3, -48),
                            pt(10, -47), 1)
        _NS_zephyr._aacircle(surface, p["skin_darkest"], pt(11, -39), 1)
        _NS_zephyr._aaline(surface, p["lips_dark"], pt(3, -34),
                            pt(8, -34), 2)
        _NS_zephyr._aaline(surface, p["lips_mid"], pt(4, -34),
                            pt(7, -34), 1)

        # Fringe overlaps the brow while the crown remains behind it.
        hair_sway = int(math.sin(phase * 1.28) * 2)
        poly(p["hair_darkest"], [(-11, -52), (-7, -62), (1, -65),
             (10, -59), (13, -51), (7, -48), (4, -52), (1, -47),
             (-2, -53), (-6, -48)])
        poly(p["hair_dark"], [(-8, -53), (-5, -60), (1, -62),
             (8, -57), (10, -52), (5, -50), (1, -55), (-3, -50)], False)
        # five irregular bangs avoid a helmet silhouette.
        bangs = [(-7, -56, -8, -47), (-3, -59, -4, -49),
                 (1, -61, 0, -49), (5, -58, 4, -48),
                 (9, -55, 8, -48)]
        for i, (sx, sy, ex, ey) in enumerate(bangs):
            wiggle = hair_sway if i % 2 else -hair_sway
            poly(p["hair_mid"], [(sx - 2, sy), (sx + 2, sy),
                 (ex + wiggle, ey), (ex - 2 + wiggle, ey + 2)], False)
            _NS_zephyr._aaline(surface, p["hair_light"], pt(sx, sy + 1),
                                pt(ex + wiggle, ey), 1)
        _NS_zephyr._aacircle(surface, p["hair_shine"], pt(2, -61), 1)

        # ── front staff arm: grip is derived from staff endpoints ──
        front_shoulder = (8, -22)
        if attack:
            front_elbow = (grip[0] - 5, grip[1] + 8)
        elif walk:
            front_elbow = (grip[0] - 7, grip[1] + 5 + int(stride * 2))
        else:
            front_elbow = (grip[0] - 7, grip[1] + 6)
        limb(front_shoulder, front_elbow, 6, p["cloak_mid"], p["cloak_light"])
        limb(front_elbow, grip, 5, p["skin_dark"], p["skin_light"])
        ghx, ghy = pt(*grip)
        _NS_zephyr._aacircle(surface, p["skin_darkest"], (ghx, ghy), 4)
        _NS_zephyr._aacircle(surface, p["skin_mid"], (ghx, ghy), 3)
        _NS_zephyr._aacircle(surface, p["skin_high"], (ghx - f, ghy - 1), 1)
        # cuff and two rings on the staff hand.
        _NS_zephyr._aaline(surface, p["gold_dark"],
                            pt(front_elbow[0], front_elbow[1]),
                            pt((front_elbow[0] + grip[0]) // 2,
                               (front_elbow[1] + grip[1]) // 2), 4)
        _NS_zephyr._aaline(surface, p["gold_light"],
                            pt(front_elbow[0], front_elbow[1] - 1),
                            pt((front_elbow[0] + grip[0]) // 2,
                               (front_elbow[1] + grip[1]) // 2 - 1), 1)
        _NS_zephyr._aacircle(surface, p["gold_light"],
                              (ghx + f * 2, ghy), 1)

        # foreground side locks and small thorn earrings.
        poly(p["hair_dark"], [(-8, -49), (-13, -45),
             (-17 - hair_sway, -31), (-11, -28), (-5, -39)], False)
        _NS_zephyr._aaline(surface, p["hair_light"], pt(-10, -46),
                            pt(-14 - hair_sway, -32), 1)
        _NS_zephyr._aacircle(surface, p["jewel_light"], pt(-10, -39), 2)
        _NS_zephyr._aacircle(surface, p["jewel_mid"], pt(-10, -39), 1)

        # Clothing runes / body motes are lower-cost in arena and richer in
        # portrait mode.  They are tied to the root transform, not screen.
        for i in range(3 if not detail else 6):
            t = (phase * .22 + i / 6.0) % 1.0
            dx = -22 + i * 8 + int(math.sin(phase * 1.4 + i) * 2)
            dy = 22 - int(t * 58)
            _NS_zephyr._aacircle(surface,
                                  (*p["magic_bright"], int(145 * (1 - t))),
                                  pt(dx, dy), 1 if i % 2 else 2)
        if attack:
            orb_x, orb_y = pt(*staff_top)
            for i in range(6):
                ang = phase * 2.1 + i * math.pi / 3
                r = 7 + int(math.sin(phase + i) * 2)
                _NS_zephyr._aacircle(surface, (*p["magic_hot"], 190),
                                      (orb_x + int(math.cos(ang) * r),
                                       orb_y + int(math.sin(ang) * r)), 1)

        if detail:
            _NS_zephyr._draw_zephyr_masterwork_details(
                surface, pt, f, phase, action)


    def _draw_elite_wings(surface, pt, f, phase, action, detail=False):
        """Two pairs of translucent moth wings with independently moving tips."""
        p = _NS_zephyr.PALETTE
        flap = math.sin(phase * 3.0) * .12 + .88
        if action == "attack":
            flap += .08
        if action == "walk":
            flap += math.sin(phase * 1.72) * .05

        def wing_poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                  [(x + f, y + 1) for x, y in pts])
            _NS_zephyr._poly(surface, color, pts)

        for side in (-1, 1):
            lift = int((1.0 - flap) * 22)
            # Tall upper wing: pointed like a thorned moth leaf.
            upper = [(side * 3, -25), (side * 12, -44 + lift),
                     (side * 28, -61 + lift), (side * 39, -53 + lift),
                     (side * 33, -32), (side * 19, -17), (side * 6, -18)]
            wing_poly(p["wing_darkest"], upper)
            wing_poly((*p["wing_dark"], 220), [
                (side * 5, -25), (side * 14, -43 + lift),
                (side * 27, -57 + lift), (side * 34, -51 + lift),
                (side * 29, -34), (side * 17, -20), (side * 7, -20)],
                False)
            wing_poly((*p["wing_mid"], 165), [
                (side * 7, -25), (side * 17, -42 + lift),
                (side * 27, -53 + lift), (side * 29, -46 + lift),
                (side * 24, -34), (side * 15, -22)], False)
            # Lower wing is shorter, rounder, and has a different cadence.
            low_lift = int(math.sin(phase * 2.2 + side) * 2)
            lower = [(side * 4, -17), (side * 20, -18 + low_lift),
                     (side * 34, -5 + low_lift), (side * 28, 9),
                     (side * 13, 8), (side * 5, -4)]
            wing_poly(p["wing_darkest"], lower)
            wing_poly((*p["wing_dark"], 220), [
                (side * 6, -16), (side * 20, -16 + low_lift),
                (side * 30, -5 + low_lift), (side * 25, 5),
                (side * 14, 5), (side * 7, -4)], False)
            wing_poly((*p["wing_mid"], 150), [
                (side * 8, -14), (side * 20, -12 + low_lift),
                (side * 26, -4 + low_lift), (side * 21, 2),
                (side * 13, 1)], False)

            root = pt(side * 5, -21)
            tips = (pt(side * 28, -56 + lift),
                    pt(side * 31, -8 + low_lift),
                    pt(side * 24, -33 + lift))
            for tx, ty in tips:
                _NS_zephyr._aaline(surface, p["wing_vein"], root, (tx, ty), 2)
                _NS_zephyr._aaline(surface, p["wing_light"],
                                    (root[0] - f, root[1]),
                                    (tx - f, ty), 1)
            # A bright edge catches enough pixels to survive arena scaling.
            edge_a = pt(side * 28, -56 + lift)
            edge_b = pt(side * 34, -51 + lift)
            _NS_zephyr._aaline(surface, p["wing_shine"], edge_a, edge_b, 1)
            if detail:
                for j in range(3):
                    u = .32 + j * .18
                    vx = int(root[0] + (tips[0][0] - root[0]) * u)
                    vy = int(root[1] + (tips[0][1] - root[1]) * u)
                    _NS_zephyr._aacircle(surface, p["wing_glass"], (vx, vy), 1)


    def _draw_zephyr_crown(surface, pt, f, phase, detail=False):
        """Swept crimson petal-hair silhouette from the Zephyr reference.

        The large mass flows backward from the face (negative local X), with
        only a few forward thorns.  This keeps the sprite's 3/4 facing clear
        instead of reading as a symmetric crown pasted above the head.
        """
        p = _NS_zephyr.PALETTE

        def crown_poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                  [(x + f, y + 1) for x, y in pts])
            _NS_zephyr._poly(surface, color, pts)

        # Broad petal mass curves away from the face just like a living fey
        # plume; the outer silhouette remains dense at arena scale.
        crown_poly(p["hair_darkest"], [(-13, -47), (-27, -48),
                   (-35, -57), (-30, -66), (-38, -71), (-24, -74),
                   (-25, -84), (-12, -79), (-6, -91), (3, -78),
                   (12, -70), (16, -59), (11, -50), (3, -54),
                   (-5, -52)])
        crown_poly(p["hair_dark"], [(-11, -49), (-24, -51),
                   (-30, -58), (-25, -64), (-31, -69), (-20, -70),
                   (-20, -78), (-10, -74), (-5, -85), (1, -74),
                   (9, -67), (12, -59), (8, -52), (1, -56)], False)
        crown_poly(p["hair_mid"], [(-15, -52), (-25, -57),
                   (-22, -65), (-14, -68), (-9, -79), (-4, -70),
                   (3, -70), (7, -61), (3, -57)], False)

        # Seven separate locks give the reference's bristling petals genuine
        # secondary motion.  Most lean back; two retain the sharp front rim.
        spikes = [(-13, -54, -32, -62), (-17, -57, -38, -75),
                  (-15, -62, -29, -85), (-9, -65, -15, -90),
                  (-2, -66, -4, -94), (4, -62, 8, -82),
                  (9, -57, 20, -70)]
        for i, (sx, sy, ex, ey) in enumerate(spikes):
            wave = int(math.sin(phase * 1.18 + i * .73) * (1 + i % 3))
            crown_poly(p["hair_darkest"], [(sx - 3, sy + 2),
                       (sx + 3, sy + 2), (ex + wave, ey),
                       (sx + 1, sy - 4)])
            crown_poly(p["hair_mid"], [(sx - 1, sy), (sx + 2, sy),
                       (ex + wave, ey + 4), (sx, sy - 2)], False)
            _NS_zephyr._aaline(surface, p["hair_light"], pt(sx, sy - 1),
                                pt(ex + wave, ey + 4), 1)
            if i in (1, 3, 5):
                _NS_zephyr._aacircle(surface, p["hair_tip"],
                                      pt(ex + wave, ey + 3), 1)

        # A dark thorn circlet and amethyst pins retain the mischievous royal
        # accent without competing with the magenta hair at gameplay scale.
        _NS_zephyr._aaline(surface, p["gold_dark"], pt(-12, -56),
                            pt(11, -58), 3)
        _NS_zephyr._aaline(surface, p["gold_mid"], pt(-11, -57),
                            pt(10, -59), 1)
        for dx in (-7, -1, 6):
            bx, by = pt(dx, -57)
            _NS_zephyr._poly(surface, p["thorn_dark"],
                              [(bx, by), (bx + f * 3, by - 5),
                               (bx + f * 5, by)])
            _NS_zephyr._aacircle(surface, p["jewel_light"],
                                  (bx + f, by), 1)
        if detail:
            for dx, dy in ((-24, -60), (-20, -69), (-13, -76),
                           (-6, -82), (2, -73)):
                _NS_zephyr._aaline(surface, p["hair_shine"], pt(dx, dy),
                                    pt(dx + 3, dy - 5), 1)

    def _draw_elite_staff(surface, pt, f, bottom, top, phase, action,
                          detail=False):
        """Living thorn staff whose shaft and crystal are tied to the pose."""
        p = _NS_zephyr.PALETTE
        bx, by = pt(*bottom)
        tx, ty = pt(*top)
        _NS_zephyr._aaline(surface, p["shadow_deep"],
                            (bx + f * 2, by + 1), (tx + f * 2, ty + 1), 8)
        _NS_zephyr._aaline(surface, p["staff_dark"], (bx, by), (tx, ty), 6)
        _NS_zephyr._aaline(surface, p["staff_mid"], (bx - f, by),
                            (tx - f, ty), 4)
        _NS_zephyr._aaline(surface, p["staff_light"], (bx - f * 2, by - 1),
                            (tx - f * 2, ty - 1), 1)

        dx, dy = tx - bx, ty - by
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        # A vine coils around the shaft and terminates in tiny thorns.
        for i in range(5):
            t = .14 + i * .15
            sx, sy = bx + dx * t, by + dy * t
            swirl = math.sin(phase * 1.8 + i * 1.7) * 2.0
            ex, ey = sx + nx * (5 + swirl), sy + ny * (5 + swirl)
            _NS_zephyr._aaline(surface, p["staff_vine"],
                                (int(sx), int(sy)), (int(ex), int(ey)), 2)
            _NS_zephyr._aaline(surface, p["thorn_light"],
                                (int(ex), int(ey)),
                                (int(ex + nx * 3 + dx / length * 2),
                                 int(ey + ny * 3 + dy / length * 2)), 1)
        # Crystal orb: dark halo -> faceted gem -> concentrated white core.
        orb_pulse = .72 + math.sin(phase * 2.5) * .18
        for radius, color, alpha in ((14, p["magic_dark"], 48),
                                     (10, p["magic_mid"], 100),
                                     (7, p["magic_bright"], 180)):
            _NS_zephyr._aacircle(surface, (*color, int(alpha * orb_pulse)),
                                  (tx, ty), radius)
        _NS_zephyr._poly(surface, p["jewel_dark"],
                          [(tx, ty - 7), (tx + f * 6, ty - 1),
                           (tx + f * 2, ty + 7), (tx - f * 5, ty + 2)])
        _NS_zephyr._poly(surface, p["jewel_mid"],
                          [(tx, ty - 5), (tx + f * 4, ty - 1),
                           (tx + f, ty + 5), (tx - f * 3, ty + 1)])
        _NS_zephyr._aaline(surface, p["staff_glow"], (tx, ty - 5),
                            (tx + f * 3, ty + 1), 2)
        _NS_zephyr._aacircle(surface, p["jewel_light"],
                              (tx - f * 2, ty - 2), 2)
        _NS_zephyr._aacircle(surface, p["magic_white"],
                              (tx - f * 2, ty - 3), 1)
        # forked thorn crown around the orb
        for side in (-1, 1):
            _NS_zephyr._aaline(surface, p["thorn_dark"],
                                (tx, ty + 3),
                                (tx + f * side * 7, ty - 8), 3)
            _NS_zephyr._aaline(surface, p["thorn_light"],
                                (tx + f * side, ty + 1),
                                (tx + f * side * 6, ty - 7), 1)
        if detail:
            for i in range(4):
                t = .24 + i * .15
                rx, ry = int(bx + dx * t), int(by + dy * t)
                _NS_zephyr._aacircle(surface, p["rune_light"], (rx, ry), 1)


    def _draw_zephyr_masterwork_details(surface, pt, f, phase, action):
        """Portrait-only material pass: seams, wing spots and jewelry."""
        p = _NS_zephyr.PALETTE
        # fine corset stitching and embroidery on the central petal
        for yy in range(-18, 2, 3):
            _NS_zephyr._aacircle(surface, p["gold_light"], pt(0, yy), 1)
        for i in range(3):
            y = 10 + i * 6
            _NS_zephyr._aaline(surface, p["dress_high"], pt(-3, y),
                                pt(2, y + 3), 1)
            _NS_zephyr._aacircle(surface, p["jewel_light"],
                                  pt(3, y + 2), 1)
        # collar rivets and wing-root jewelry
        for dx, dy in ((-11, -25), (11, -24), (-5, -28), (6, -28)):
            _NS_zephyr._aacircle(surface, p["gold_mid"], pt(dx, dy), 1)
        _NS_zephyr._aacircle(surface, p["jewel_light"], pt(-13, -19), 2)
        # face shadow, lashes and a tiny beauty mark retain the reference's
        # mischievous personality when viewed in Hero Shop.
        _NS_zephyr._aaline(surface, p["skin_high"], pt(1, -50),
                            pt(5, -49), 1)
        _NS_zephyr._aaline(surface, p["hair_darkest"], pt(5, -46),
                            pt(10, -47), 1)
        _NS_zephyr._aacircle(surface, p["lips_dark"], pt(8, -37), 1)
        # hem stitch rhythm follows the moving gown rather than screen space.
        hem_phase = int(math.sin(phase * 1.1) * 2)
        for dx in (-12, -6, 0, 6, 12):
            _NS_zephyr._aacircle(surface, p["thread_light"],
                                  pt(dx + hem_phase, 26 + abs(dx) // 5), 1)


    # ===================================================================
    # ARENA AMBIENCE
    # ===================================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((112, 28), pygame.SRCALPHA)
        for radius in range(22, 3, -4):
            alpha = max(0, int((24 - radius) * 4.5))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (56 - radius * 2, 13 - radius // 3,
                                 radius * 4, max(3, radius // 2)))
        pygame.draw.ellipse(shadow, (*_NS_zephyr.PALETTE["magic_dark"], 38),
                            (15, 10, 82, 10))
        surface.blit(shadow, (int(x - 56), int(y - 14)))


    def _draw_fey_rim_light(surface, x, y, phase):
        """Low-alpha silhouette halo kept behind the wing material."""
        p = _NS_zephyr.PALETTE
        pulse = .72 + math.sin(phase * 1.25) * .16
        halo = pygame.Surface((120, 132), pygame.SRCALPHA)
        center = (60, 66)
        for radius, alpha in ((54, 8), (43, 13), (31, 20)):
            _NS_zephyr._aacircle(halo, (*p["magic_dark"], int(alpha * pulse)),
                                  center, radius)
        _NS_zephyr._aaline(halo, (*p["wing_mid"], int(36 * pulse)),
                            (33, 84), (18, 36), 2)
        _NS_zephyr._aaline(halo, (*p["wing_mid"], int(36 * pulse)),
                            (87, 84), (102, 36), 2)
        surface.blit(halo, (int(x - 60), int(y - 66)))


    def _draw_fey_aura(surface, x, y, phase):
        p = _NS_zephyr.PALETTE
        pulse = .72 + math.sin(phase * .55) * .20
        aura = pygame.Surface((164, 142), pygame.SRCALPHA)
        for radius in range(58, 7, -5):
            alpha = int((61 - radius) * 1.15 * pulse)
            if alpha > 0:
                _NS_zephyr._aacircle(aura, (*p["magic_darkest"], alpha),
                                      (82, 67), radius)
        surface.blit(aura, (int(x - 82), int(y - 72)))


    def _draw_fey_platform(surface, x, y, phase, skill=None):
        p = _NS_zephyr.PALETTE
        pulse = .76 + math.sin(phase * 1.2) * .18
        ring = pygame.Surface((142, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*p["magic_dark"], int(160 * pulse)),
                            (4, 12, 134, 25), 3)
        pygame.draw.ellipse(ring, (*p["rune_mid"], int(180 * pulse)),
                            (17, 16, 108, 17), 2)
        pygame.draw.ellipse(ring, (*p["magic_bright"], int(145 * pulse)),
                            (29, 19, 84, 11), 1)
        for i in range(8):
            ang = phase * .7 + i * math.pi / 4
            px = 71 + int(math.cos(ang) * 54)
            py = 25 + int(math.sin(ang) * 9)
            _NS_zephyr._aacircle(ring, p["rune_light"], (px, py), 1)
        if skill:
            pygame.draw.ellipse(ring, (*p["magic_hot"], int(150 * pulse)),
                                (11, 9, 120, 30), 1)
        surface.blit(ring, (int(x - 71), int(y - 24)))


    def _draw_floating_sparkles(surface, cx, cy, phase, trail=False,
                                 facing=1, intense=False):
        p = _NS_zephyr.PALETTE
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((118, 36), pygame.SRCALPHA)
        for radius in range(25, 4, -4):
            alpha = int((27 - radius) * 3.0 * strength)
            pygame.draw.ellipse(mist, (*p["magic_dark"], alpha),
                                (59 - radius * 2, 18 - radius // 3,
                                 radius * 4, max(3, radius // 2)))
        surface.blit(mist, (int(cx - 59), int(cy - 9)))
        for i, offset in enumerate((-23, -10, 4, 18)):
            t = (phase * .48 + i * .23) % 1.0
            sx = int(cx + offset + math.sin(phase + i) * 3)
            sy = int(cy + 5 - t * 31)
            alpha = int(215 * (1 - t) * strength)
            _NS_zephyr._aacircle(surface, (*p["magic_mid"], alpha),
                                  (sx, sy), 3)
            _NS_zephyr._aacircle(surface, (*p["magic_bright"], alpha),
                                  (sx, sy - 1), 1)
        for i in range(2):
            angle = phase * 1.08 + i * math.pi
            bx = int(cx + math.cos(angle) * 24)
            by = int(cy - 6 + math.sin(angle * 1.3) * 8)
            _NS_zephyr._draw_butterfly(surface, bx, by, 3, phase + i)
        if trail:
            f = 1 if facing >= 0 else -1
            for i in range(5):
                alpha = 140 - i * 23
                _NS_zephyr._aacircle(surface, (*p["magic_mid"], alpha),
                                      (int(cx - f * (13 + i * 10)),
                                       int(cy + math.sin(phase + i) * 2)),
                                      max(1, 4 - i // 2))


    def _draw_cast_flash(surface, x, y, facing, progress, phase=0.0):
        if progress < .37 or progress > .72:
            return
        p = _NS_zephyr.PALETTE
        t = (progress - .37) / .35
        intensity = math.sin(t * math.pi)
        fx, fy = _NS_zephyr._staff_orb_position(
            x, y, facing, phase, "attack", progress)
        for radius, color, alpha in ((24, p["magic_dark"], 65),
                                     (16, p["magic_mid"], 150),
                                     (9, p["magic_bright"], 220)):
            _NS_zephyr._aacircle(surface, (*color, int(alpha * intensity)),
                                  (fx, fy), int(radius * intensity) + 1)
        _NS_zephyr._aacircle(surface, p["magic_white"], (fx, fy),
                              max(1, int(3 * intensity)))
        for i in range(6):
            angle = phase * 2.0 + i * math.pi / 3
            ray = int(10 + 18 * intensity)
            ex = fx + int(math.cos(angle) * ray)
            ey = fy + int(math.sin(angle) * ray)
            _NS_zephyr._aaline(surface, (*p["magic_hot"],
                                          int(220 * intensity)),
                                (fx, fy), (ex, ey), 1)


    # ===================================================================
    # SKILL Q — BRAMBLE MAZE
    # ===================================================================
    def _draw_fey_arc(surface, cx, cy, rx, ry, start, end, color,
                      width=1, segments=18):
        """Draw an elliptical procedural arc without relying on image assets."""
        previous = None
        for i in range(segments + 1):
            t = i / float(max(1, segments))
            angle = start + (end - start) * t
            point = (int(cx + math.cos(angle) * rx),
                     int(cy + math.sin(angle) * ry))
            if previous is not None:
                _NS_zephyr._aaline(surface, color, previous, point, width)
            previous = point


    def _draw_bramble_ground(surface, boss, x, y, timer, phase):
        origin = getattr(boss, "_bramble_origin", None)
        if origin:
            tx, ty = _NS_zephyr._world_to_local(boss, x, y,
                                                 origin[0], origin[1])
        else:
            tx, ty = _NS_zephyr._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 240.0))
        radius = int(22 + min(1.0, progress * 3.5) * 34)
        pulse = .7 + math.sin(phase * 3.0) * .2
        _NS_zephyr._ellipse(surface,
                             (*_NS_zephyr.PALETTE["magic_darkest"],
                              int(145 * pulse)),
                             (int(tx - radius), int(ty + 15 - radius * .32),
                              radius * 2, max(4, int(radius * .64))))
        _NS_zephyr._draw_fey_arc(surface, tx, ty + 15, radius, int(radius * .32),
                                  phase, phase + math.pi * 1.45,
                                  (*_NS_zephyr.PALETTE["rune_mid"], 190), 2)


    def _draw_bramble_maze(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        origin = getattr(boss, "_bramble_origin", None)
        if origin:
            tx, ty = _NS_zephyr._world_to_local(boss, x, y,
                                                 origin[0], origin[1])
        else:
            tx, ty = _NS_zephyr._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 240.0))
        grow = min(1.0, progress * 4.0)
        fade = min(1.0, (1.0 - progress) * 7.0)
        if grow <= .02:
            return
        ring_r = int(30 + grow * 28)
        for i in range(12):
            angle = i * math.tau / 12.0 + phase * .10
            bx = tx + int(math.cos(angle) * ring_r)
            by = ty + 15 + int(math.sin(angle) * ring_r * .34)
            # The vines lean inward, leaving a readable hostile ring.
            curl = math.sin(phase * 1.8 + i * 1.7) * 4
            tip_x = bx - int(math.cos(angle) * (10 + grow * 10)) + int(curl)
            tip_y = by - int((24 + (i % 3) * 5) * grow)
            px, py = -math.sin(angle) * 4, math.cos(angle) * 4
            _NS_zephyr._poly(surface, p["thorn_dark"], [
                (int(bx + px), int(by + py)), (int(bx - px), int(by - py)),
                (tip_x, tip_y)])
            _NS_zephyr._poly(surface, p["thorn_mid"], [
                (int(bx + px * .62), int(by + py * .62)),
                (int(bx - px * .62), int(by - py * .62)), (tip_x, tip_y)],)
            _NS_zephyr._aaline(surface, p["thorn_light"], (bx, by),
                                (tip_x, tip_y), 1)
            for t in (.32, .58, .80):
                vx = int(bx + (tip_x - bx) * t)
                vy = int(by + (tip_y - by) * t)
                side = -1 if i % 2 else 1
                _NS_zephyr._draw_petal(surface, vx, vy, 5,
                    angle + side * 1.6, p["thorn_dark"], p["thorn_mid"],
                    p["thorn_light"], p["jewel_light"])
            _NS_zephyr._aacircle(surface, p["jewel_mid"], (tip_x, tip_y), 3)
            _NS_zephyr._aacircle(surface, p["jewel_light"],
                                  (tip_x - 1, tip_y - 1), 1)
        alpha = int(205 * fade)
        _NS_zephyr._draw_fey_arc(surface, tx, ty + 15, ring_r + 4,
                                  int((ring_r + 4) * .34), phase,
                                  phase + math.tau, (*p["rune_mid"], alpha), 2)
        _NS_zephyr._draw_fey_arc(surface, tx, ty + 15, ring_r - 5,
                                  int((ring_r - 5) * .34), -phase,
                                  -phase + math.tau, (*p["magic_bright"], alpha), 1)
        for i in range(4):
            t = (phase * .45 + i * .25) % 1.0
            _NS_zephyr._draw_butterfly(surface,
                int(tx + math.sin(phase + i) * (18 + t * 20)),
                int(ty + 10 - t * 28), 3, phase + i,
                alpha=int(220 * (1 - t)))


    # ===================================================================
    # SKILL W — SHADOW REALM
    # ===================================================================
    def _draw_shadow_realm_ground(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 180.0))
        radius = int(34 + min(1.0, progress * 5) * 17)
        _NS_zephyr._ellipse(surface, (*p["magic_darkest"], 155),
                             (x - radius, y + 31 - radius // 3,
                              radius * 2, max(5, radius * 2 // 3)))
        _NS_zephyr._draw_fey_arc(surface, x, y + 31, radius, radius * .32,
                                  phase, phase + math.tau,
                                  (*p["rune_mid"], 210), 2)
        for i in range(6):
            a = phase * .7 + i * math.tau / 6
            _NS_zephyr._aacircle(surface, p["rune_light"],
                                  (int(x + math.cos(a) * (radius - 5)),
                                   int(y + 31 + math.sin(a) * radius * .30)), 1)


    def _draw_shadow_realm(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 180.0))
        envelope = min(1.0, progress * 8.0, (1.0 - progress) * 8.0)
        radius = max(3, int(47 * envelope))
        if radius <= 3:
            return
        cx, cy = x, y - 12
        pulse = .78 + math.sin(phase * 2.6) * .16
        # The realm is a crescent glass dome, not an opaque circle over Zephyr.
        _NS_zephyr._aacircle(surface, (*p["magic_dark"], int(42 * pulse)),
                              (cx, cy), radius)
        for off, alpha, width in ((0, 180, 2), (4, 120, 2), (9, 75, 1)):
            _NS_zephyr._draw_fey_arc(surface, cx, cy, radius - off,
                                      radius - off, .18, math.pi - .18,
                                      (*p["magic_bright"], int(alpha * pulse)),
                                      width, 22)
        _NS_zephyr._draw_fey_arc(surface, cx, cy, radius - 3, radius - 3,
                                  math.pi + .20, math.tau - .20,
                                  (*p["wing_mid"], int(145 * pulse)), 1, 20)
        # glass highlight and drifting petal reflections
        _NS_zephyr._aacircle(surface, p["magic_hot"],
                              (cx - radius // 2, cy - radius // 2), 3)
        for i in range(7):
            a = phase * 2.0 + i * math.tau / 7
            r = radius * (.52 + (i % 2) * .16)
            sx = int(cx + math.cos(a) * r)
            sy = int(cy + math.sin(a) * r)
            _NS_zephyr._aacircle(surface, (*p["wing_shine"], 170),
                                  (sx, sy), 1 if i % 2 else 2)
        _NS_zephyr._draw_fey_arc(surface, cx, cy + 30, radius,
                                  radius * .22, phase, phase + math.pi,
                                  (*p["rune_light"], 190), 1)


    # ===================================================================
    # SKILL E — CASKET CURSE
    # ===================================================================
    def _draw_casket_indicator(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        tx, ty = _NS_zephyr._target_position(boss, x, y)
        sx, sy = _NS_zephyr._staff_orb_position(
            x, y, getattr(boss, "direction", 1), phase)
        # segmented thorn tether makes the target relationship explicit.
        dx, dy = tx - sx, ty - sy
        dist = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / dist, dx / dist
        for i in range(9):
            t1 = i / 9.0
            t2 = min(1.0, (i + .54) / 9.0)
            wobble1 = math.sin(phase * 3 + i) * 3
            wobble2 = math.sin(phase * 3 + i + .6) * 3
            a = (int(sx + dx * t1 + nx * wobble1),
                 int(sy + dy * t1 + ny * wobble1))
            b = (int(sx + dx * t2 + nx * wobble2),
                 int(sy + dy * t2 + ny * wobble2))
            _NS_zephyr._aaline(surface, (*p["magic_dark"], 180), a, b, 3)
            _NS_zephyr._aaline(surface, (*p["magic_bright"], 210), a, b, 1)
        _NS_zephyr._aacircle(surface, (*p["jewel_mid"], 190), (tx, ty), 9, 2)
        _NS_zephyr._aacircle(surface, p["jewel_light"], (tx, ty), 2)


    def _handle_casket_skill(surface, boss, x, y, timer, phase):
        if not getattr(boss, "_zp_casket_spawned", False):
            _NS_zephyr._spawn_casket(boss, x, y)
            boss._zp_casket_spawned = True
        if timer < 5:
            boss._zp_casket_spawned = False


    # ===================================================================
    # SKILL R — BEDLAM
    # ===================================================================
    def _draw_bedlam_ground(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 240.0))
        radius = int(45 + min(1.0, progress * 4) * 20)
        _NS_zephyr._ellipse(surface, (*p["magic_darkest"], 170),
                             (x - radius, y + 31 - radius // 3,
                              radius * 2, max(6, radius * 2 // 3)))
        for i in range(3):
            rr = radius - i * 9
            _NS_zephyr._draw_fey_arc(surface, x, y + 31, rr, rr * .29,
                                      phase * (1.0 + i * .25) + i,
                                      phase * (1.0 + i * .25) + i + math.tau,
                                      (*p["magic_mid"], 190 - i * 38),
                                      2 if i == 0 else 1)
        for i in range(10):
            a = phase * .95 + i * math.tau / 10
            _NS_zephyr._aacircle(surface, p["rune_light"],
                                  (int(x + math.cos(a) * (radius - 4)),
                                   int(y + 31 + math.sin(a) * radius * .28)), 2)


    def _draw_bedlam(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 240.0))
        envelope = min(1.0, progress * 5.0, (1.0 - progress) * 5.0)
        for i in range(6):
            angle = phase * 2.35 + i * math.tau / 6.0
            orbit_r = 43 + int(math.sin(phase * 1.7 + i) * 6)
            dx = int(x + math.cos(angle) * orbit_r)
            dy = int(y - 11 + math.sin(angle) * orbit_r * .42)
            alpha = max(50, min(235, int((174 + math.sin(phase * 2 + i) * 48)
                                         * max(.28, envelope))))
            _NS_zephyr._draw_mini_fairy(surface, dx, dy, phase + i * .33,
                                         alpha,
                                         facing=1 if math.cos(angle) >= 0 else -1)
            # trailing glitter marks the orbit direction.
            for tail in range(3):
                ta = angle - .22 * (tail + 1)
                _NS_zephyr._aacircle(surface,
                    (*p["magic_bright"], max(20, alpha - tail * 55)),
                    (int(x + math.cos(ta) * orbit_r),
                     int(y - 11 + math.sin(ta) * orbit_r * .42)),
                    max(1, 3 - tail))
        # Three discontinuous spell ribbons make the clone circle feel alive.
        for i in range(3):
            _NS_zephyr._draw_fey_arc(surface, x, y - 10,
                                      46 - i * 5, 16 - i * 2,
                                      phase * 1.9 + i * 2.1,
                                      phase * 1.9 + i * 2.1 + 1.52,
                                      (*p["magic_hot"], 190 - i * 38), 1, 13)
        for i in range(12):
            a = phase * 1.4 + i * math.tau / 12
            r = 49 + int(math.sin(phase * 2 + i) * 6)
            _NS_zephyr._aacircle(surface, p["magic_white"],
                                  (int(x + math.cos(a) * r),
                                   int(y - 8 + math.sin(a) * r * .45)), 1)


    def _draw_mini_fairy(surface, cx, cy, phase, alpha, facing=1):
        """Compact masterwork silhouette used by the Bedlam orbit."""
        p = _NS_zephyr.PALETTE
        f = 1 if facing >= 0 else -1
        flap = int(math.sin(phase * 3) * 2)
        for side in (-1, 1):
            _NS_zephyr._poly(surface, (*p["wing_dark"], alpha // 2), [
                (cx + f * 2, cy - 6), (cx + f * side * 11, cy - 16 + flap),
                (cx + f * side * 14, cy - 8), (cx + f * side * 6, cy - 2)])
            _NS_zephyr._aaline(surface, (*p["wing_shine"], alpha // 2),
                                (cx + f * 2, cy - 6),
                                (cx + f * side * 10, cy - 14 + flap), 1)
        _NS_zephyr._poly(surface, (*p["dress_dark"], alpha), [
            (cx - 5, cy - 2), (cx + 5, cy - 2), (cx + 7, cy + 10),
            (cx, cy + 14), (cx - 6, cy + 9)])
        _NS_zephyr._poly(surface, (*p["corset_mid"], alpha), [
            (cx - 3, cy - 3), (cx + 3, cy - 3), (cx + 3, cy + 3),
            (cx - 3, cy + 3)])
        _NS_zephyr._aacircle(surface, (*p["skin_mid"], alpha),
                              (cx + f, cy - 9), 5)
        for i in range(3):
            _NS_zephyr._aaline(surface, (*p["hair_mid"], alpha),
                                (cx + f * (i - 1), cy - 12),
                                (cx + f * (i - 2), cy - 19 - (i % 2) * 2), 2)
        _NS_zephyr._aacircle(surface, (*p["eye_iris_light"], alpha),
                              (cx + f * 2, cy - 9), 1)
        _NS_zephyr._aaline(surface, (*p["staff_light"], alpha),
                            (cx + f * 5, cy + 8), (cx + f * 10, cy - 15), 2)
        _NS_zephyr._aacircle(surface, (*p["jewel_light"], alpha),
                              (cx + f * 10, cy - 16), 2)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_zephyr.draw_zephyr(surface, boss, x, y)
