"""
bosses/level2.py - Semua boss Level 2

Gabungan dari 4 file terpisah:
  - razak                (mini boss)
  - khalros              (mini boss)
  - gorath               (mini boss)
  - alchemist            (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

== Level 2 Masterwork (pass animasi) ==
Namespace sudah disesuaikan mengikuti standar rig Level 1
(Kaizen/Gornak Masterwork):

  * SKILL_DUR per boss DIKUNCI sama `active_skill_timer`
    AI di base_boss.py - FX tidak lagi terpotong di tengah
    dan gerbang spawn proyektil selalu terbuka di frame
    pertama (bug lama: Q/R Khalros & W Gorath tidak pernah
    men-spawn apa pun).
  * Idle/walk: bobbing + sway diperkuat; attack: root
    motion 4 fase (antisipasi -> lunge -> impact hold +
    getar -> recovery) dengan body lift.
  * Razak: pose aim 2 tangan saat Q/W, moncong napalm/api
    keluar dari muzzle senapan; Flamebreak punya fade-out.
  * Khalros: pose lempar untuk Wild Axes; summon boar/wolf
    naik lalu TENGGELAM (tidak pop/hilang mendadak).
  * Gorath: indikator rage persisten (aura + mata + uap
    darah); envelope di Bloodrage/Thirst.
  * Alchemist (true boss): goblin rider digambar SEBELUM
    kepala ogre (dulu menindih helm), cheer botol + pile
    emas tumbuh-tenggelam untuk R, aura Chemical Rage tidak
    lagi menutupi badan, mata menyala selama buff.

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
# RAZAK
# ====================================================================
class _NS_razak:
    """Namespace razak - Level 2 Masterwork animation pass."""

    # ── Level 2 Masterwork ──────────────────────────────────────────
    # Durasi FX skill DIKUNCI sama `active_skill_timer` yang dipasang
    # AI di bosses/base_boss.py supaya animasi TIDAK terpotong di
    # tengah dan gerbang spawn proyektil (`progress < 0.1`) selalu
    # terbuka pada frame pertama cast.
    SKILL_DUR = {"q": 40, "w": 60, "e": 35, "r": 100}
    SHADOW_DY = 52      # tanah visual (bayangan) relatif anchor boss

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ---------------------------------------------------------------------------
    # HD Palette - Fire orange / green goblin / red bat mount
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Goblin skin - green
        "gob_darkest":    (25,  45,  20),
        "gob_dark":       (55,  95,  38),
        "gob_mid":        (95, 145,  55),
        "gob_light":      (140, 190, 78),
        "gob_high":       (185, 225, 120),
        "gob_shine":      (225, 250, 175),

        # Bat/dragon mount - red-orange
        "bat_darkest":    (35,  15,  10),
        "bat_dark":       (95,  32,  18),
        "bat_mid":        (155, 62,  25),
        "bat_light":      (210, 95,  38),
        "bat_high":       (240, 140, 65),
        "bat_shine":      (255, 180, 100),

        # Bat belly (lighter)
        "belly_dark":     (105, 55,  25),
        "belly_mid":      (170, 105, 55),
        "belly_light":    (215, 155, 85),

        # Wing membrane
        "wing_darkest":   (30,  12,   8),
        "wing_dark":      (75,  25,  15),
        "wing_mid":       (135, 45,  22),
        "wing_light":     (190, 78,  35),

        # Leather / gear
        "leather_darkest": (22, 14,  8),
        "leather_dark":   (50,  32,  18),
        "leather_mid":    (95,  62,  32),
        "leather_light":  (150, 100, 55),

        # Metal
        "metal_darkest":  (18,  15,  18),
        "metal_dark":     (48,  42,  48),
        "metal_mid":      (95,  88,  95),
        "metal_light":    (160, 152, 165),
        "metal_shine":    (225, 220, 225),

        # Brass / bronze (gun parts)
        "brass_dark":     (80,  50,  15),
        "brass_mid":      (155, 108, 40),
        "brass_light":    (210, 170, 80),
        "brass_shine":    (250, 220, 140),

        # Fire - orange/yellow
        "fire_darkest":   (55,  12,   5),
        "fire_dark":      (135, 30,   8),
        "fire_mid":       (215, 80,  15),
        "fire_bright":    (255, 130, 30),
        "fire_hot":       (255, 180, 60),
        "fire_glow":      (255, 220, 130),
        "fire_white":     (255, 250, 210),

        # Blue (goggles)
        "blue_dark":      (15,  35,  75),
        "blue_mid":       (45,  95, 165),
        "blue_light":     (95, 165, 230),
        "blue_shine":     (170, 220, 255),

        # Eyes
        "eye_dark":       (15,  25,   8),
        "eye_bright":     (255, 220, 100),
        "eye_hot":        (255, 250, 200),

        # Teeth / claws
        "bone_dark":      (110, 95,  70),
        "bone_light":     (220, 210, 175),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_razak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_razak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_razak._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 8
            h = abs(ey - sy) + width * 4 + 8
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_razak._clamp(color)
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
        color = _NS_razak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])), width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_razak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, int(rw), int(rh)),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3],
                         (rect[0], rect[1], int(rect[2]), int(rect[3])),
                         border_radius=border_radius)


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


    # ---------------------------------------------------------------------------
    # FIRE PARTICLE / FLAME DRAWING
    # ---------------------------------------------------------------------------
    def _draw_flame(surface, cx, cy, size, phase, alpha=255):
        """Draw a single flame with layered fire colors."""
        height = int(size * 2)
        for h in range(height):
            t = h / max(1, height)
            w = int(size * (1 - t * 0.7))
            fx = cx + int(math.sin(phase * 3 + t * 4) * 2)
            fy = cy - h
            a = int(alpha * (1 - t * 0.4))
            if t < 0.3:
                color = _NS_razak.PALETTE["fire_darkest"]
            elif t < 0.55:
                color = _NS_razak.PALETTE["fire_mid"]
            elif t < 0.8:
                color = _NS_razak.PALETTE["fire_bright"]
            else:
                color = _NS_razak.PALETTE["fire_hot"]
            _NS_razak._aacircle(surface, (*color, a), (fx, fy), max(1, w))
        # Bright core near base
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], alpha), (cx, cy - height // 3), size // 2)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], alpha), (cx, cy - height // 4), max(1, size // 4))


    def _draw_ember(surface, cx, cy, size=2, alpha=255):
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], alpha), (cx, cy), size + 1)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha), (cx, cy), size)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha), (cx, cy), max(1, size - 1))
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], min(255, alpha)), (cx, cy), 1)


    def _draw_fire_ground_patch(surface, cx, cy, radius, phase, alpha=255):
        """Ground fire patch - Sticky Napalm effect."""
        # Base scorch
        _NS_razak._ellipse(surface, (*_NS_razak.PALETTE["fire_darkest"], int(alpha * 0.9)),
                 (cx - radius, cy - radius // 3, radius * 2, radius // 1.5))
        _NS_razak._ellipse(surface, (*_NS_razak.PALETTE["fire_dark"], int(alpha * 0.8)),
                 (cx - radius + 3, cy - radius // 3 + 2,
                  radius * 2 - 6, radius // 1.5 - 4))

        # Flames on top
        flame_count = max(3, radius // 4)
        for i in range(flame_count):
            angle = i * math.pi * 2 / flame_count + phase * 0.3
            r = radius - 4
            fx = cx + int(math.cos(angle) * r)
            fy = cy + int(math.sin(angle) * r // 3)
            size = 3 + (i % 3)
            _NS_razak._draw_flame(surface, fx, fy, size, phase + i, alpha=alpha)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class NapalmProjectile:
        """Sticky napalm — arcing fireball."""
        def __init__(self, sx, sy, tx, ty, arc_height=40):
            self.start_x = float(sx)
            self.start_y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.arc_height = arc_height
            self.alive = True
            self.age = 0
            self.max_age = 40
            self.x = float(sx)
            self.y = float(sy)
            self.spin = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.3
            t = self.age / self.max_age
            if t >= 1.0:
                self.alive = False
                self.x, self.y = self.tx, self.ty
                return
            self.x = self.start_x + (self.tx - self.start_x) * t
            # Parabolic arc
            arc = -4 * self.arc_height * t * (1 - t)
            self.y = self.start_y + (self.ty - self.start_y) * t + arc
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)

        def draw(self, surface, phase):
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(60 + i * 15)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], alpha), (tx, ty), r + 2)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha), (tx, ty), r)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha), (tx, ty), max(1, r - 1))
            if self.alive:
                px, py = int(self.x), int(self.y)
                # Fireball
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], 200), (px, py), 8)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_mid"], 220), (px, py), 6)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], 240), (px, py), 5)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], 255), (px, py), 3)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255), (px, py), 2)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], 255), (px - 1, py - 1), 1)
                # Flame licks
                for i in range(3):
                    angle = self.spin + i * math.pi * 2 / 3
                    fx = px + int(math.cos(angle) * 5)
                    fy = py + int(math.sin(angle) * 5)
                    _NS_razak._draw_ember(surface, fx, fy, 2, 220)


    class NapalmPatch:
        """Persistent burning ground patch."""
        def __init__(self, x, y, radius=25, life=90):
            self.x = x
            self.y = y
            self.radius = radius
            self.age = 0
            self.life = life
            self.alive = True

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            t = self.age / self.life
            # Grow then fade
            if t < 0.15:
                r = int(self.radius * (t / 0.15))
                alpha = int(255 * (t / 0.15))
            elif t < 0.7:
                r = self.radius
                alpha = 255
            else:
                r = self.radius
                alpha = int(255 * (1 - (t - 0.7) / 0.3))
            if r <= 0 or alpha <= 0:
                return
            _NS_razak._draw_fire_ground_patch(surface, self.x, self.y, r, phase, alpha=alpha)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_razak_last_x"):
            boss._razak_last_x = boss.x
            boss._razak_last_y = boss.y
            return False
        dx = abs(boss.x - boss._razak_last_x)
        dy = abs(boss.y - boss._razak_last_y)
        boss._razak_last_x = boss.x
        boss._razak_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_razak_prev_timer", 0))
        active = bool(getattr(boss, "_razak_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._razak_attack_active = True
            boss._razak_attack_frame = 0
            active = True
        elif active:
            boss._razak_attack_frame = int(getattr(boss, "_razak_attack_frame", 0)) + 1
            if boss._razak_attack_frame > cooldown:
                boss._razak_attack_active = False
                boss._razak_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._razak_attack_active = False
            boss._razak_attack_frame = 0
            active = False

        boss._razak_prev_timer = timer
        boss._razak_attack_progress = (
            min(1.0, getattr(boss, "_razak_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        if not hasattr(boss, "_razak_patches"):
            boss._razak_patches = []

        for proj in boss._razak_projectiles:
            proj.update()
            if not proj.alive:
                # Spawn napalm patch at landing point
                boss._razak_patches.append(
                    _NS_razak.NapalmPatch(int(proj.x), int(proj.y), radius=28, life=100))
            proj.draw(surface, phase)
        boss._razak_projectiles = [p for p in boss._razak_projectiles
                                    if p.alive or p.age < 3]

        # Draw patches BEHIND everything (but they're called from foreground here)
        for patch in boss._razak_patches:
            patch.update()
            patch.draw(surface, phase)
        boss._razak_patches = [p for p in boss._razak_patches if p.alive]


    def _spawn_napalm(boss, sx, sy, tx, ty, arc_height=40):
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        boss._razak_projectiles.append(
            _NS_razak.NapalmProjectile(sx, sy, tx, ty, arc_height=arc_height))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_razak(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_razak._detect_moving(boss)
        _NS_razak._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_razak_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # Background
        _NS_razak._draw_fire_aura(surface, x, y, pulse, active_skill)

        # Ground patches (behind character)
        if hasattr(boss, "_razak_patches"):
            for patch in boss._razak_patches:
                patch.draw(surface, pulse)

        # Skill ground effects
        if active_skill == "r":
            _NS_razak._draw_firestorm_ground(surface, boss, x, y, skill_timer, pulse)

        # Character - saat Q/W aktif, goblin mengangkat penyembur api
        # (pose aim dua tangan) supaya sumber api nyambung dengan FX.
        aim = active_skill in ("q", "w")
        if active_skill == "e":
            _NS_razak._draw_razak_dashing(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_razak._draw_razak_attack(surface, boss, x, y)
        elif moving:
            _NS_razak._draw_razak_walk(surface, boss, x, y, aim=aim)
        else:
            _NS_razak._draw_razak_idle(surface, boss, x, y, aim=aim)

        # Update / draw projectiles
        _NS_razak._manage_projectiles_no_patches(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "q":
            _NS_razak._draw_sticky_napalm(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_razak._draw_flamebreak(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_razak._draw_firestorm(surface, boss, x, y, skill_timer, pulse)


    def _manage_projectiles_no_patches(boss, surface, phase):
        """Same as manage_projectiles but patches are drawn separately (before character)."""
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        if not hasattr(boss, "_razak_patches"):
            boss._razak_patches = []

        for proj in boss._razak_projectiles:
            proj.update()
            if not proj.alive and proj.age > 0:
                # Spawn napalm patch at landing point
                boss._razak_patches.append(
                    _NS_razak.NapalmPatch(int(proj.tx), int(proj.ty), radius=28, life=100))
                proj.age = -1  # prevent re-spawn
            if proj.age >= 0:
                proj.draw(surface, phase)
        boss._razak_projectiles = [p for p in boss._razak_projectiles
                                    if p.alive]

        # Update patches (drawing was done earlier)
        for patch in boss._razak_patches:
            patch.update()
        boss._razak_patches = [p for p in boss._razak_patches if p.alive]


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_razak_idle(surface, boss, x, y, aim=False):
        # Napas berat + melayang jelas (amplitudo 4 px, dulu cuma 3)
        bob = int(math.sin(boss.pulse * 0.8) * 4)
        _NS_razak._draw_shadow(surface, x, y + _NS_razak.SHADOW_DY)
        _NS_razak._draw_fire_wisps(surface, x, y + 38, boss.pulse)
        _NS_razak._draw_razak_full(surface, x, y + bob, boss.direction,
                                   boss.pulse, "idle", aim=aim)

    def _draw_razak_walk(surface, boss, x, y, aim=False):
        phase = boss.pulse * 2.5
        bob = int(math.sin(phase * 1.2) * 5)
        sway = int(math.sin(phase * 0.5) * 3)
        _NS_razak._draw_shadow(surface, x + sway, y + _NS_razak.SHADOW_DY)
        _NS_razak._draw_fire_wisps(surface, x + sway, y + 38, phase, trail=True,
                         facing=boss.direction)
        _NS_razak._draw_razak_full(surface, x + sway, y + bob, boss.direction,
                                   phase, "walk", aim=aim)

    def _draw_razak_attack(surface, boss, x, y):
        progress = getattr(boss, "_razak_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        d = boss.direction
        # ── Root motion berfase (standar Level 1) ──
        # wind-up menarik mundur, tembakan mendorong maju, lalu
        # recoil-hold bergetar dan recovery mulus.
        if progress < 0.30:
            k = progress / 0.30
            lunge = int(-4 * k)
        elif progress < 0.55:
            k = (progress - 0.30) / 0.25
            lunge = int(-4 + 10 * (1 - (1 - k) ** 2))
        elif progress < 0.70:
            lunge = 6 + int(math.sin(progress * 42) * 1.5)
        else:
            k = (progress - 0.70) / 0.30
            lunge = int(6 * (1 - k))
        lunge = lunge * d

        # ─── Fireball serangan biasa ───
        # Razak itu unit RANGED (range 130) tapi dulu animasi
        # serangannya cuma ayunan machete tanpa proyektil apa pun,
        # jadi damage terasa datang entah dari mana. Spawn fireball
        # kecil di puncak ayunan, pola sama seperti boss ranged lain.
        if 0.34 < progress < 0.46 and not getattr(
                boss, "_razak_proj_spawned", False):
            tx, ty = _NS_razak._target_position(boss, x, y)
            sx = x + 28 * d + lunge
            sy = y + bob - 16          # muzzle moncong senapan
            _NS_razak._spawn_napalm(boss, sx, sy, tx, ty, arc_height=22)
            boss._razak_proj_spawned = True
        if progress < 0.12 or progress > 0.9:
            boss._razak_proj_spawned = False

        _NS_razak._draw_shadow(surface, x + lunge, y + _NS_razak.SHADOW_DY)
        _NS_razak._draw_fire_wisps(surface, x + lunge, y + 38, boss.pulse, intense=True)
        # Selama ayunan, goblin ikut mengangkat senapan (aim) supaya
        # kapak + muzzle flash terbaca sebagai satu gerakan.
        _NS_razak._draw_razak_full(surface, x + lunge, y + bob, d, boss.pulse,
                         "attack", progress, aim=True)
        _NS_razak._draw_machete_swing_arc(surface, x + lunge, y + bob, d, progress)

    def _draw_razak_dashing(surface, boss, x, y, timer, phase):
        """Firefly dash - bat flies forward with flame trail."""
        bob = int(math.sin(phase * 1.5) * 3)
        _NS_razak._draw_shadow(surface, x, y + _NS_razak.SHADOW_DY)
        _NS_razak._draw_fire_wisps(surface, x, y + 38, phase, intense=True)

        # Motion blur behind (3 ghost saja; 4 bikin frame jadi riuh)
        for i in range(3):
            offset = (i + 1) * 10 * -boss.direction
            alpha = int(120 - i * 35)
            temp = pygame.Surface((160, 160), pygame.SRCALPHA)
            _NS_razak._draw_razak_full(temp, 80, 80, boss.direction, phase,
                                       "dash")
            temp.set_alpha(alpha)
            surface.blit(temp, (x + offset - 80, y + bob - 80))

        _NS_razak._draw_razak_full(surface, x, y + bob, boss.direction, phase,
                                   "dash")


    # ===================================================================
    # FULL COMPOSITE
    # ===================================================================
    def _draw_razak_full(surface, cx, cy, facing, phase, action,
                         attack_progress=0, aim=False):
        """Draw bat mount + goblin rider."""
        # Wings behind body first
        _NS_razak._draw_bat_wings(surface, cx, cy, facing, phase, action)

        # Bat body
        _NS_razak._draw_bat_body(surface, cx, cy + 5, facing, phase)

        # Bat head
        _NS_razak._draw_bat_head(surface, cx + 18 * facing, cy + 3, facing, phase)

        # Goblin rider on top of bat
        _NS_razak._draw_goblin_rider(surface, cx - 2, cy - 12, facing, phase, action,
                           attack_progress, aim=aim)

        # Front wings overlay (bring wings forward if attack)
        if action == "attack":
            _NS_razak._draw_bat_wings_front(surface, cx, cy, facing, phase)


    def _draw_bat_wings(surface, cx, cy, facing, phase, action):
        """Bat mount wings (background, spread out).

        Amplitudo flap per-aksi: santai saat idle, rapat saat walk,
        mengepak keras untuk brace saat attack, full-speed saat dash.
        """
        flap = math.sin(phase * (2.6 if action == "walk" else 1.1)) * 0.45
        if action == "dash":
            flap = math.sin(phase * 4.2) * 0.55
        elif action == "attack":
            flap = math.sin(phase * 2.2) * 0.5

        for side in (-1, 1):
            wing_base_x = cx + side * 8
            wing_base_y = cy - 2
            wing_tip_x = cx + side * (32 + int(math.cos(flap) * 6))
            wing_tip_y = cy - 15 + int(math.sin(flap) * 8)
            wing_mid_x = cx + side * 24
            wing_mid_y = cy - 6 + int(math.sin(flap) * 6)
            wing_low_x = cx + side * 20
            wing_low_y = cy + 12 + int(math.sin(flap) * 3)

            # Wing membrane (large triangle)
            wing_shape = [
                (wing_base_x, wing_base_y),
                (wing_tip_x, wing_tip_y),
                (cx + side * 30, cy - 4 + int(math.sin(flap) * 5)),
                (wing_mid_x, wing_mid_y),
                (cx + side * 27, cy + 3 + int(math.sin(flap) * 4)),
                (wing_low_x, wing_low_y),
                (cx + side * 4, cy + 8),
            ]

            # Shadow
            _NS_razak._poly(surface, _NS_razak.PALETTE["shadow_deep"],
                  [(p[0] + 2, p[1] + 2) for p in wing_shape])
            _NS_razak._poly(surface, _NS_razak.PALETTE["wing_darkest"], wing_shape)
            # Inner membrane (lighter)
            inner_shape = [
                (wing_base_x + side, wing_base_y + 1),
                (wing_tip_x - side * 2, wing_tip_y + 1),
                (wing_mid_x - side, wing_mid_y),
                (wing_low_x - side, wing_low_y - 1),
                (cx + side * 4, cy + 7),
            ]
            _NS_razak._poly(surface, _NS_razak.PALETTE["wing_dark"], inner_shape)
            _NS_razak._poly(surface, _NS_razak.PALETTE["wing_mid"], [
                (wing_base_x + side * 2, wing_base_y + 2),
                (cx + side * 20, wing_mid_y + 1),
                (wing_low_x - side * 2, wing_low_y - 2),
                (cx + side * 5, cy + 6),
            ])

            # Wing bones (finger struts)
            _NS_razak._aaline(surface, _NS_razak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (wing_tip_x, wing_tip_y), 2)
            _NS_razak._aaline(surface, _NS_razak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (wing_mid_x, wing_mid_y), 2)
            _NS_razak._aaline(surface, _NS_razak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (wing_low_x, wing_low_y), 2)

            # Claw at wing tip
            _NS_razak._poly(surface, _NS_razak.PALETTE["bone_dark"], [
                (wing_tip_x, wing_tip_y),
                (wing_tip_x + side * 3, wing_tip_y - 2),
                (wing_tip_x + side * 1, wing_tip_y + 1),
            ])
            _NS_razak._aacircle(surface, _NS_razak.PALETTE["bone_light"],
                      (wing_tip_x + side * 2, wing_tip_y - 1), 1)


    def _draw_bat_wings_front(surface, cx, cy, facing, phase):
        """Overlay wing detail during attack."""
        # Just add some highlights
        for side in (-1, 1):
            _NS_razak._aaline(surface, _NS_razak.PALETTE["wing_light"],
                    (cx + side * 10, cy),
                    (cx + side * 25, cy - 8), 1)


    def _draw_bat_body(surface, cx, cy, facing, phase):
        """Red bat/dragon body."""
        # Shadow
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["shadow_deep"],
                 (cx - 15, cy - 3, 32, 20))

        # Main body (elongated)
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_darkest"], (cx - 14, cy - 5, 30, 18))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_dark"], (cx - 12, cy - 4, 26, 15))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_mid"], (cx - 10, cy - 3, 22, 12))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_light"], (cx - 8, cy - 4, 18, 8))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_high"], (cx - 6, cy - 4, 12, 4))

        # Belly (lighter underside)
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["belly_dark"], (cx - 8, cy + 6, 18, 6))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["belly_mid"], (cx - 6, cy + 7, 14, 4))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["belly_light"], (cx - 4, cy + 7, 10, 2))

        # Back spikes
        for i, sx_off in enumerate((-6, -2, 2, 6)):
            _NS_razak._poly(surface, _NS_razak.PALETTE["bat_darkest"], [
                (cx + sx_off - 1, cy - 4),
                (cx + sx_off + 1, cy - 4),
                (cx + sx_off, cy - 8),
            ])
            _NS_razak._poly(surface, _NS_razak.PALETTE["bat_mid"], [
                (cx + sx_off, cy - 4),
                (cx + sx_off + 1, cy - 4),
                (cx + sx_off, cy - 7),
            ])

        # Legs (small, tucked)
        for side in (-1, 1):
            lx = cx + side * 7
            ly = cy + 10
            _NS_razak._aacircle(surface, _NS_razak.PALETTE["bat_darkest"], (lx, ly), 3)
            _NS_razak._aacircle(surface, _NS_razak.PALETTE["bat_dark"], (lx, ly), 2)
            # Claws
            for c in (-1, 0, 1):
                _NS_razak._poly(surface, _NS_razak.PALETTE["bone_dark"], [
                    (lx + c, ly + 2),
                    (lx + c + side, ly + 4),
                    (lx + c, ly + 3),
                ])

        # Tail
        tail_end_x = cx - 18 * facing
        tail_end_y = cy + 4
        _NS_razak._aaline(surface, _NS_razak.PALETTE["bat_darkest"], (cx - facing * 12, cy + 2),
                (tail_end_x, tail_end_y), 4)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["bat_dark"], (cx - facing * 12, cy + 2),
                (tail_end_x, tail_end_y), 2)
        # Arrow-tipped tail
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_darkest"], [
            (tail_end_x, tail_end_y - 2),
            (tail_end_x - facing * 4, tail_end_y),
            (tail_end_x, tail_end_y + 2),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_mid"], [
            (tail_end_x, tail_end_y - 1),
            (tail_end_x - facing * 3, tail_end_y),
            (tail_end_x, tail_end_y + 1),
        ])


    def _draw_bat_head(surface, cx, cy, facing, phase):
        """Dragon-like bat head."""
        # Shadow
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["shadow_deep"], (cx + 1, cy + 1), 8)

        # Head base (elongated snout)
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_darkest"], (cx - 7, cy - 5, 14, 12))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_dark"], (cx - 6, cy - 4, 12, 10))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_mid"], (cx - 5, cy - 3, 10, 7))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_light"], (cx - 4, cy - 3, 8, 4))

        # Snout extending forward
        snout = [
            (cx, cy - 1),
            (cx + facing * 8, cy - 2),
            (cx + facing * 10, cy + 1),
            (cx + facing * 8, cy + 3),
            (cx, cy + 3),
        ]
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_darkest"], snout)
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_dark"], [
            (cx + 1, cy),
            (cx + facing * 7, cy - 1),
            (cx + facing * 9, cy + 1),
            (cx + facing * 7, cy + 2),
            (cx + 1, cy + 2),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_mid"], [
            (cx + 2, cy),
            (cx + facing * 6, cy),
            (cx + facing * 8, cy + 1),
            (cx + facing * 6, cy + 2),
        ])

        # Fangs
        for tooth_off in (0, 3):
            _NS_razak._poly(surface, _NS_razak.PALETTE["bone_light"], [
                (cx + facing * (5 + tooth_off), cy + 2),
                (cx + facing * (5 + tooth_off) + facing, cy + 4),
                (cx + facing * (6 + tooth_off), cy + 2),
            ])

        # Nostril
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["shadow_deep"],
                  (cx + facing * 8, cy - 1), 1)

        # Glowing yellow eye
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["shadow_deep"],
                  (cx + facing * 2, cy - 2), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["fire_dark"], (cx + facing * 2, cy - 2), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["fire_hot"], (cx + facing * 2, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["fire_glow"], (cx + facing * 2, cy - 2), 1)

        # Horns / ears on top
        for i, off in enumerate((-3, 0, 3)):
            _NS_razak._poly(surface, _NS_razak.PALETTE["bat_darkest"], [
                (cx + off - 1, cy - 4),
                (cx + off + 1, cy - 4),
                (cx + off, cy - 8 - i % 2),
            ])
            _NS_razak._poly(surface, _NS_razak.PALETTE["bat_dark"], [
                (cx + off, cy - 4),
                (cx + off + 1, cy - 4),
                (cx + off, cy - 7),
            ])


    def _draw_goblin_rider(surface, cx, cy, facing, phase, action,
                           attack_progress, aim=False):
        """Goblin sitting on bat, holding weapon.

        `aim=True` (atau action "dash") -> goblin mencengkeram
        penyembur api dengan DUA tangan dan muzzle menyala, sehingga
        FX Flamebreak/Napalm keluar dari moncong senapan, bukan dari
        kosong.
        """
        sway = int(math.sin(phase * 0.6) * 1.5)
        if action == "walk":
            sway += int(math.sin(phase * 2) * 1.5)

        # Legs (straddling bat)
        for side in (-1, 1):
            lx = cx + side * 4
            ly = cy + 10
            # Thigh
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (lx - 2, ly, 4, 6),
                  border_radius=1)
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (lx - 2, ly, 4, 5))
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_mid"], (lx - 1, ly + 1, 3, 3))
            # Boot
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (lx - 3, ly + 6, 6, 4),
                  border_radius=1)
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (lx - 3, ly + 6, 6, 3))
            _NS_razak._rect(surface, _NS_razak.PALETTE["brass_dark"], (lx - 3, ly + 6, 6, 1))

        # Torso
        _NS_razak._draw_goblin_torso(surface, cx + sway, cy, facing, phase)

        # Head
        _NS_razak._draw_goblin_head(surface, cx + sway, cy - 12, facing, phase)

        # Backpack / fuel tanks
        _NS_razak._draw_fuel_tanks(surface, cx + sway - facing * 6, cy - 4, phase)

        # Arms with weapons
        if action == "attack":
            _NS_razak._draw_goblin_attack_arms(surface, cx + sway, cy - 4, facing, phase,
                                     attack_progress)
        elif aim or action in ("q_cast", "w_cast", "dash"):
            _NS_razak._draw_goblin_gun_arms(surface, cx + sway, cy - 4, facing, phase)
        else:
            _NS_razak._draw_goblin_idle_arms(surface, cx + sway, cy - 4, facing, phase)


    def _draw_goblin_torso(surface, cx, cy, facing, phase):
        """Small goblin torso in armor/vest."""
        # Shadow
        _NS_razak._poly(surface, _NS_razak.PALETTE["shadow_deep"], [
            (cx - 7 + 1, cy - 5 + 1), (cx + 7 + 1, cy - 5 + 1),
            (cx + 6 + 1, cy + 10 + 1), (cx - 6 + 1, cy + 10 + 1),
        ])

        # Torso base (green skin)
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_darkest"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 6, cy + 10), (cx - 6, cy + 10),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_dark"], [
            (cx - 6, cy - 4), (cx + 6, cy - 4),
            (cx + 5, cy + 9), (cx - 5, cy + 9),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_mid"], [
            (cx - 5, cy - 3), (cx + 5, cy - 3),
            (cx + 4, cy + 7), (cx - 4, cy + 7),
        ])

        # Leather chest armor
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (cx - 8, cy - 2, 16, 8),
              border_radius=2)
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (cx - 7, cy - 1, 14, 6),
              border_radius=1)
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_mid"], (cx - 6, cy, 12, 3))

        # Chest strap X
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_darkest"], (cx - 6, cy - 2), (cx + 6, cy + 4), 2)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_darkest"], (cx + 6, cy - 2), (cx - 6, cy + 4), 2)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_mid"], (cx - 6, cy - 2), (cx + 6, cy + 4), 1)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_mid"], (cx + 6, cy - 2), (cx - 6, cy + 4), 1)

        # Brass buckle center
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_dark"], (cx, cy + 1), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_mid"], (cx, cy + 1), 1)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_shine"], (cx, cy), 1)


    def _draw_goblin_head(surface, cx, cy, facing, phase):
        """Goblin head with pilot goggles."""
        # Shadow
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["shadow_deep"], (cx + 1, cy + 1), 8)

        # Head base
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_darkest"], (cx, cy), 7)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_dark"], (cx - 1, cy - 1), 6)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_mid"], (cx - 1, cy - 2), 4)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_light"], (cx - 2, cy - 3), 2)

        # Long pointy ears
        for side in (-1, 1):
            _NS_razak._poly(surface, _NS_razak.PALETTE["gob_darkest"], [
                (cx + side * 6, cy - 1),
                (cx + side * 11, cy - 4),
                (cx + side * 7, cy + 2),
            ])
            _NS_razak._poly(surface, _NS_razak.PALETTE["gob_dark"], [
                (cx + side * 6, cy),
                (cx + side * 9, cy - 3),
                (cx + side * 7, cy + 1),
            ])
            _NS_razak._poly(surface, _NS_razak.PALETTE["gob_mid"], [
                (cx + side * 7, cy),
                (cx + side * 9, cy - 2),
                (cx + side * 7, cy),
            ])

        # Big nose (goblin trait)
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_dark"], [
            (cx + facing * 2, cy),
            (cx + facing * 5, cy + 1),
            (cx + facing * 5, cy + 3),
            (cx + facing * 2, cy + 3),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_mid"], [
            (cx + facing * 2, cy + 1),
            (cx + facing * 4, cy + 2),
            (cx + facing * 2, cy + 2),
        ])

        # Mouth with fang
        _NS_razak._rect(surface, _NS_razak.PALETTE["shadow_deep"], (cx - 2, cy + 4, 4, 1))
        _NS_razak._poly(surface, _NS_razak.PALETTE["bone_light"], [
            (cx + 1, cy + 4),
            (cx + 2, cy + 6),
            (cx + 2, cy + 4),
        ])

        # Blue goggles (Batrider signature!)
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (cx - 6, cy - 5, 12, 4),
              border_radius=1)
        # Left goggle lens
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["leather_dark"], (cx - 3, cy - 3), 3)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_dark"], (cx - 3, cy - 3), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_mid"], (cx - 3, cy - 3), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_light"], (cx - 4, cy - 4), 1)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_shine"], (cx - 4, cy - 4), 1)
        # Right goggle lens
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["leather_dark"], (cx + 3, cy - 3), 3)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_dark"], (cx + 3, cy - 3), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_mid"], (cx + 3, cy - 3), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_light"], (cx + 2, cy - 4), 1)

        # Helmet on top
        _NS_razak._poly(surface, _NS_razak.PALETTE["leather_darkest"], [
            (cx - 7, cy - 5),
            (cx - 5, cy - 8),
            (cx + 5, cy - 8),
            (cx + 7, cy - 5),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["leather_dark"], [
            (cx - 6, cy - 5),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 6, cy - 5),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["leather_mid"], [
            (cx - 5, cy - 5),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 5),
        ])
        # Rivets
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_light"], (cx - 4, cy - 6), 1)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_light"], (cx + 4, cy - 6), 1)


    def _draw_fuel_tanks(surface, cx, cy, phase):
        """Fuel tanks on goblin's back."""
        # Two brass tanks
        for i, off in enumerate((-2, 2)):
            _NS_razak._rect(surface, _NS_razak.PALETTE["shadow_deep"],
                  (cx - 2 + off + 1, cy - 4 + 1, 3, 10), border_radius=1)
            _NS_razak._rect(surface, _NS_razak.PALETTE["brass_dark"], (cx - 2 + off, cy - 4, 3, 10),
                  border_radius=1)
            _NS_razak._rect(surface, _NS_razak.PALETTE["brass_mid"], (cx - 1 + off, cy - 3, 2, 8))
            _NS_razak._rect(surface, _NS_razak.PALETTE["brass_light"], (cx - 1 + off, cy - 3, 1, 6))
            # Cap on top
            _NS_razak._rect(surface, _NS_razak.PALETTE["metal_dark"], (cx - 2 + off, cy - 5, 3, 2))
            _NS_razak._rect(surface, _NS_razak.PALETTE["metal_light"], (cx - 2 + off, cy - 5, 3, 1))

        # Connecting hose
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_darkest"], (cx - 1, cy - 3), (cx + 3, cy - 2), 2)


    def _draw_goblin_idle_arms(surface, cx, cy, facing, phase):
        """Idle - holding gun in one arm, machete in other."""
        sway = math.sin(phase * 0.7) * 1

        # Back arm - holding machete
        back_side = -facing
        bs_x = cx + back_side * 5
        bs_y = cy - 2
        bh_x = bs_x + back_side * 4
        bh_y = cy + 4 + int(sway)
        _NS_razak._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)
        _NS_razak._draw_machete_held(surface, bh_x, bh_y, back_side, phase)

        # Front arm - gun
        fs_x = cx + facing * 5
        fs_y = cy - 2
        fh_x = fs_x + facing * 8
        fh_y = cy - 1 + int(sway)
        _NS_razak._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)
        _NS_razak._draw_flame_gun(surface, fh_x, fh_y, facing, phase)


    def _draw_goblin_gun_arms(surface, cx, cy, facing, phase):
        """Both arms holding gun forward, firing."""
        fs_x = cx + facing * 5
        fs_y = cy - 2
        fh_x = fs_x + facing * 10
        fh_y = cy - 1
        _NS_razak._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)

        # Back arm supporting gun
        bs_x = cx - facing * 3
        bs_y = cy - 1
        bh_x = fh_x - facing * 4
        bh_y = fh_y
        _NS_razak._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)

        _NS_razak._draw_flame_gun(surface, fh_x, fh_y, facing, phase, firing=True)


    def _draw_goblin_attack_arms(surface, cx, cy, facing, phase, progress):
        """One arm swings machete, other holds gun."""
        # Back arm - gun at rest
        back_side = -facing
        bs_x = cx + back_side * 3
        bs_y = cy - 2
        bh_x = bs_x + back_side * 6
        bh_y = cy + 1
        _NS_razak._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)
        _NS_razak._draw_flame_gun(surface, bh_x, bh_y, back_side, phase)

        # Front arm swings machete
        fs_x = cx + facing * 5
        fs_y = cy - 2

        if progress < 0.25:
            t = progress / 0.25
            t = t * t * (3 - 2 * t)
            arm_angle = -1.3 + 0.3 * t
        elif progress < 0.55:
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3
            arm_angle = -1.0 + 2.2 * t
        else:
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 1.0 * t

        arm_len = 10
        fh_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fh_y = fs_y + int(math.sin(arm_angle) * arm_len)

        _NS_razak._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)

        # Machete swinging
        blade_angle = arm_angle + math.pi / 4 * facing
        _NS_razak._draw_machete_swinging(surface, fh_x, fh_y, facing, blade_angle)


    def _draw_goblin_arm(surface, x1, y1, x2, y2):
        """Small goblin arm."""
        _NS_razak._aaline(surface, _NS_razak.PALETTE["shadow_deep"], (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 5)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["gob_darkest"], (x1, y1), (x2, y2), 4)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["gob_dark"], (x1, y1), (x2, y2), 3)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["gob_mid"], (x1, y1), (x2, y2), 1)
        # Hand
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_darkest"], (x2, y2), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_mid"], (x2, y2), 1)


    def _draw_flame_gun(surface, hx, hy, facing, phase, firing=False):
        """Brass flamethrower / rifle."""
        # Handle/grip
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (hx - 1, hy - 2, 3, 5),
              border_radius=1)
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (hx - 1, hy - 2, 3, 4))

        # Barrel (extending forward)
        barrel_len = 12
        end_x = hx + facing * barrel_len
        end_y = hy - 1

        # Wide brass barrel
        _NS_razak._rect(surface, _NS_razak.PALETTE["shadow_deep"],
              (min(hx, end_x) + 1, hy - 3 + 1, barrel_len, 5), border_radius=1)
        _NS_razak._rect(surface, _NS_razak.PALETTE["brass_dark"],
              (min(hx, end_x), hy - 3, barrel_len, 5), border_radius=1)
        _NS_razak._rect(surface, _NS_razak.PALETTE["brass_mid"],
              (min(hx, end_x), hy - 2, barrel_len, 3))
        _NS_razak._rect(surface, _NS_razak.PALETTE["brass_light"],
              (min(hx, end_x), hy - 2, barrel_len, 1))

        # Muzzle (flared)
        _NS_razak._poly(surface, _NS_razak.PALETTE["brass_dark"], [
            (end_x, hy - 4),
            (end_x + facing * 4, hy - 5),
            (end_x + facing * 4, hy + 3),
            (end_x, hy + 2),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["brass_mid"], [
            (end_x, hy - 3),
            (end_x + facing * 3, hy - 4),
            (end_x + facing * 3, hy + 2),
            (end_x, hy + 1),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["brass_light"], [
            (end_x + facing * 1, hy - 2),
            (end_x + facing * 3, hy - 3),
            (end_x + facing * 3, hy + 1),
        ])

        # Ignition pilot flame at muzzle
        if not firing:
            px = end_x + facing * 5
            py = hy - 1
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], 200), (px, py), 2)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], 220), (px, py), 1)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255), (px, py - 1), 1)


    def _draw_machete_held(surface, hx, hy, side, phase):
        """Machete at rest (blade forward)."""
        # Blade
        blade_end_x = hx + side * 14
        blade_end_y = hy - 6

        _NS_razak._aaline(surface, _NS_razak.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (blade_end_x + 1, blade_end_y + 1), 4)
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_darkest"], [
            (hx, hy - 1),
            (hx + side * 3, hy - 3),
            (blade_end_x, blade_end_y),
            (blade_end_x - side * 2, blade_end_y + 2),
            (hx, hy + 1),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_dark"], [
            (hx + side, hy - 1),
            (hx + side * 3, hy - 2),
            (blade_end_x - side, blade_end_y + 1),
            (hx + side, hy),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_mid"], [
            (hx + side * 2, hy - 1),
            (blade_end_x - side * 2, blade_end_y + 1),
            (hx + side * 2, hy),
        ])
        _NS_razak._aaline(surface, _NS_razak.PALETTE["metal_shine"],
                (hx + side * 3, hy - 2), (blade_end_x - side, blade_end_y + 1), 1)

        # Handle
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (hx - 1, hy, 3, 4))
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (hx, hy, 2, 3))


    def _draw_machete_swinging(surface, hx, hy, facing, angle):
        """Machete in motion — angled with fire trail."""
        blade_len = 20
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle) * facing

        end_x = hx + int(dx * blade_len)
        end_y = hy + int(dy * blade_len)

        # Shadow
        _NS_razak._aaline(surface, _NS_razak.PALETTE["shadow_deep"], (hx + 2, hy + 2),
                (end_x + 2, end_y + 2), 4)

        # Blade shape
        blade_pts = [
            (hx + int(perp_x * 2), hy + int(perp_y * 2)),
            (hx + int(dx * blade_len * 0.5) + int(perp_x * 3),
             hy + int(dy * blade_len * 0.5) + int(perp_y * 3)),
            (end_x, end_y),
            (hx + int(dx * blade_len * 0.5) - int(perp_x * 1),
             hy + int(dy * blade_len * 0.5) - int(perp_y * 1)),
            (hx - int(perp_x * 1), hy - int(perp_y * 1)),
        ]
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_darkest"], blade_pts)
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_dark"], [
            (hx + int(perp_x), hy + int(perp_y)),
            (hx + int(dx * blade_len * 0.5) + int(perp_x * 2),
             hy + int(dy * blade_len * 0.5) + int(perp_y * 2)),
            (end_x, end_y),
            (hx + int(dx * blade_len * 0.5), hy + int(dy * blade_len * 0.5)),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_mid"], [
            (hx + int(perp_x * 2), hy + int(perp_y * 2)),
            (hx + int(dx * blade_len * 0.4) + int(perp_x * 2),
             hy + int(dy * blade_len * 0.4) + int(perp_y * 2)),
            (end_x, end_y),
        ])

        # Sharp edge
        _NS_razak._aaline(surface, _NS_razak.PALETTE["metal_shine"],
                (hx + int(perp_x * 3), hy + int(perp_y * 3)),
                (end_x, end_y), 1)

        # FIRE aura on blade (Batrider machete on fire!)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], 180), (end_x, end_y), 5)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], 220), (end_x, end_y), 3)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255), (end_x, end_y), 1)


    # ===================================================================
    # EFFECTS - Wisps, aura, shadow
    # ===================================================================
    def _draw_fire_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Fire wisps below bat (replaces legs)."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((140, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.5) * 0.25 + 0.75
        for radius in range(34, 3, -4):
            alpha = int((34 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_razak.PALETTE["fire_darkest"], min(255, alpha)),
                    (70 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 70, cy - 11))

        # Rising fire wisps
        for i, offset in enumerate((-24, -10, 6, 20)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 26)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], alpha), (sx, sy), 5)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha), (sx, sy - 2), 3)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha), (sx, sy - 3), 2)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], alpha), (sx, sy - 3), 1)

        # Ember particles
        for i in range(7):
            angle = phase * 1.0 + i * math.pi * 2 / 7
            r = 25 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 8)
            _NS_razak._draw_ember(surface, sx, sy, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 13 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 150 - i * 25)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha),
                          (sx, sy), max(1, 4 - i))
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha // 2),
                          (sx, sy), max(1, 2 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (11 - radius, 11 - radius, 88 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_razak.PALETTE["fire_dark"], 60), (10, 5, 90, 12))
        surface.blit(shadow, (x - 55, y - 11))


    def _draw_fire_aura(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("q", "w", "r") else 1.0
        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(80, 5, -4):
            alpha = int((80 - radius) * 1.2 * pulse * strength)
            if alpha > 0:
                _NS_razak._aacircle(aura, (*_NS_razak.PALETTE["fire_darkest"], min(255, alpha)),
                          (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))


    def _draw_machete_swing_arc(surface, x, y, facing, progress):
        """Fire trail of machete swing."""
        if progress < 0.28 or progress > 0.75:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.25
        visibility = max(0.0, min(1.0, visibility))

        arc = pygame.Surface((140, 100), pygame.SRCALPHA)
        for i in range(18):
            t = i / 17
            angle = -math.pi * 0.85 + t * math.pi
            px = 70 + int(math.cos(angle) * 48) * facing
            py = 50 + int(math.sin(angle) * 36)
            alpha = int((220 - i * 10) * visibility)
            if alpha <= 0:
                continue
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_darkest"], alpha), (px, py), 8)
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_mid"], alpha), (px, py), 6)
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_bright"], alpha), (px, py), 4)
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_hot"], alpha), (px, py), 2)
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_glow"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 70, y - 50))


    # ===================================================================
    # SKILL Q: STICKY NAPALM (arcing fire projectile)
    # ===================================================================
    def _draw_sticky_napalm(surface, boss, x, y, timer, phase):
        duration = _NS_razak.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_razak._target_position(boss, x, y)

        # Spawn projectile at start
        if progress < 0.15 and not getattr(boss, "_razak_napalm_spawned", False):
            sx = x + 26 * boss.direction
            sy = y - 16            # keluar dari moncong, bukan dari perut
            _NS_razak._spawn_napalm(boss, sx, sy, tx, ty)
            boss._razak_napalm_spawned = True
        if progress > 0.7:
            boss._razak_napalm_spawned = False

        # Muzzle flash while casting
        if progress < 0.3:
            flash_intensity = 1 - progress / 0.3
            fx = x + 26 * boss.direction
            fy = y - 16
            alpha = int(230 * flash_intensity)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha), (fx, fy), 8)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha), (fx, fy), 5)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], alpha), (fx, fy), 3)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], min(255, alpha)), (fx, fy), 1)

            # Sparks
            for i in range(5):
                angle = progress * 6 + i * math.pi * 2 / 5
                ex = fx + int(math.cos(angle) * 10)
                ey = fy + int(math.sin(angle) * 10)
                _NS_razak._draw_ember(surface, ex, ey, 2, alpha)


    # ===================================================================
    # SKILL W: FLAMEBREAK (flame cone/stream)
    # ===================================================================
    def _draw_flamebreak(surface, boss, x, y, timer, phase):
        duration = _NS_razak.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_razak._target_position(boss, x, y)

        # ── Napas akhir: stream memudar di 15% terakhir, bukan hilang ──
        if progress >= 0.85:
            fade = max(0.0, (1.0 - progress) / 0.15)
        else:
            fade = 1.0
        stream_w = 1.0 if progress < 0.85 else max(0.25, fade)

        # Continuous flame stream forward
        if progress < 0.98:
            start_x = x + 28 * boss.direction
            start_y = y - 16        # moncong penyembur api = tangan goblin

            # Direction toward target
            dx = tx - start_x
            dy = ty - start_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1:
                dist = 1
            dir_x = dx / dist
            dir_y = dy / dist
            perp_x = -dir_y
            perp_y = dir_x

            # Cone length grows quickly, then stays
            if progress < 0.2:
                flame_len = int(180 * (progress / 0.2))
            else:
                flame_len = 180

            # Draw many flame particles in a cone
            for i in range(35):
                t = i / 35
                # Base position along cone
                base_x = start_x + dir_x * flame_len * t
                base_y = start_y + dir_y * flame_len * t
                # Spread perpendicular (wider at end)
                spread = t * 18
                offset = math.sin(phase * 4 + i * 1.7) * spread
                fx = int(base_x + perp_x * offset)
                fy = int(base_y + perp_y * offset)

                size = int((6 + t * 4) * stream_w)
                alpha_t = 1 - t * 0.3
                alpha = int(220 * alpha_t * fade)
                if alpha <= 0:
                    continue

                # Layer flame colors based on distance
                if t < 0.15:
                    color_outer = _NS_razak.PALETTE["fire_white"]
                    color_inner = _NS_razak.PALETTE["fire_glow"]
                elif t < 0.4:
                    color_outer = _NS_razak.PALETTE["fire_hot"]
                    color_inner = _NS_razak.PALETTE["fire_bright"]
                elif t < 0.75:
                    color_outer = _NS_razak.PALETTE["fire_bright"]
                    color_inner = _NS_razak.PALETTE["fire_mid"]
                else:
                    color_outer = _NS_razak.PALETTE["fire_dark"]
                    color_inner = _NS_razak.PALETTE["fire_darkest"]

                _NS_razak._aacircle(surface, (*color_outer, alpha), (fx, fy), size)
                _NS_razak._aacircle(surface, (*color_inner, alpha), (fx, fy), max(1, size - 2))

            # Extra bright core near muzzle
            core_a = int(255 * fade)
            if core_a > 0:
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], core_a),
                          (int(start_x), int(start_y)), 5)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], core_a),
                          (int(start_x + dir_x * 5), int(start_y + dir_y * 5)), 4)


    # ===================================================================
    # SKILL R: FIRESTORM (columns of fire around target)
    # ===================================================================
    def _draw_firestorm_ground(surface, boss, x, y, timer, phase):
        """Ground circle warning."""
        tx, ty = _NS_razak._target_position(boss, x, y)
        duration = _NS_razak.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        radius = int(45 + progress * 20)
        _NS_razak._ellipse(surface, (*_NS_razak.PALETTE["fire_darkest"], int(200 * pulse)),
                 (tx - radius, ty - radius // 3, radius * 2, radius // 1.5), 3)
        _NS_razak._ellipse(surface, (*_NS_razak.PALETTE["fire_dark"], int(180 * pulse)),
                 (tx - radius + 5, ty - radius // 3 + 2,
                  radius * 2 - 10, radius // 1.5 - 4), 2)
        # Rune-like marks
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.2
            rx = tx + int(math.cos(angle) * (radius - 5))
            ry = ty + int(math.sin(angle) * (radius // 3 - 2))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], int(200 * pulse)), (rx, ry), 2)


    def _draw_firestorm(surface, boss, x, y, timer, phase):
        """Multiple pillars of fire rising around target."""
        tx, ty = _NS_razak._target_position(boss, x, y)
        duration = _NS_razak.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            return

        # 6 fire pillars around target
        for i in range(6):
            angle = i * math.pi * 2 / 6 + phase * 0.15
            r = 35
            px = tx + int(math.cos(angle) * r)
            py = ty + int(math.sin(angle) * r * 0.5)

            # Delay each pillar
            pillar_progress = (progress - 0.15 - i * 0.05) / 0.5
            if pillar_progress <= 0:
                continue
            pillar_progress = min(1.0, pillar_progress)

            # Grow then shrink
            if pillar_progress < 0.3:
                height_ratio = pillar_progress / 0.3
            elif pillar_progress < 0.7:
                height_ratio = 1.0
            else:
                height_ratio = 1.0 - (pillar_progress - 0.7) / 0.3

            pillar_h = int(45 * height_ratio)
            if pillar_h <= 0:
                continue

            # Draw fire pillar (tall flame)
            for h in range(pillar_h):
                t = h / max(1, pillar_h)
                w = int(6 * (1 - t * 0.5))
                fx = px + int(math.sin(phase * 4 + h * 0.3 + i) * 2)
                fy = py - h
                alpha = int(240 * (1 - t * 0.3))
                if t < 0.25:
                    color = _NS_razak.PALETTE["fire_darkest"]
                elif t < 0.5:
                    color = _NS_razak.PALETTE["fire_mid"]
                elif t < 0.75:
                    color = _NS_razak.PALETTE["fire_bright"]
                else:
                    color = _NS_razak.PALETTE["fire_hot"]
                _NS_razak._aacircle(surface, (*color, alpha), (fx, fy), max(1, w))

            # Bright core
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 230),
                      (px, py - pillar_h // 2), 3)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], 255),
                      (px, py - pillar_h // 3), 2)

            # Embers around base
            for j in range(3):
                ea = phase * 2 + j * 2
                ex = px + int(math.cos(ea) * 8)
                ey = py + int(math.sin(ea) * 3)
                _NS_razak._draw_ember(surface, ex, ey, 2, 200)

        # Central big flame
        center_h = int(60 * min(1.0, progress / 0.4) *
                        (1.0 if progress < 0.7 else 1 - (progress - 0.7) / 0.3))
        if center_h > 0:
            for h in range(center_h):
                t = h / max(1, center_h)
                w = int(9 * (1 - t * 0.4))
                fx = tx + int(math.sin(phase * 3 + h * 0.2) * 2)
                fy = ty - h
                alpha = int(240 * (1 - t * 0.3))
                if t < 0.25:
                    color = _NS_razak.PALETTE["fire_dark"]
                elif t < 0.55:
                    color = _NS_razak.PALETTE["fire_bright"]
                else:
                    color = _NS_razak.PALETTE["fire_hot"]
                _NS_razak._aacircle(surface, (*color, alpha), (fx, fy), max(1, w))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255), (tx, ty - center_h // 2), 5)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], 255), (tx, ty - center_h // 3), 3)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_razak.draw_razak(surface, boss, x, y)


# ====================================================================
# KHALROS
# ====================================================================
class _NS_khalros:
    """Namespace khalros - Level 2 Masterwork animation pass."""

    # Durasi FX DIKUNCI sama active_skill_timer AI (base_boss.py).
    # Q/R dulu tidak pernah menembak karena gerbang spawn
    # `progress < 0.1` tertutup permanen (AI lebih cepat dari
    # denominator renderer); W/E muncul di tengah animasi (pop-in).
    SKILL_DUR = {"q": 60, "w": 80, "e": 70, "r": 80}
    SHADOW_DY = 48

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ---------------------------------------------------------------------------
    # HD Palette - Rustic barbarian browns / orange fire
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - rugged tan
        "skin_darkest":   (55,  30,  20),
        "skin_dark":      (115, 68,  45),
        "skin_mid":       (170, 108, 72),
        "skin_light":     (215, 158, 108),
        "skin_high":      (240, 200, 155),
        "skin_shine":     (255, 230, 195),

        # Hair - dark brown
        "hair_darkest":   (18,  12,   8),
        "hair_dark":      (48,  32,  20),
        "hair_mid":       (85,  58,  35),
        "hair_high":      (135, 95,  55),

        # Leather / clothing
        "leather_darkest": (25, 15,  8),
        "leather_dark":   (55,  32,  15),
        "leather_mid":    (95,  62,  32),
        "leather_light":  (150, 100, 55),
        "leather_high":   (200, 148, 88),

        # Metal (axes, buckles)
        "metal_darkest":  (18,  16,  18),
        "metal_dark":     (52,  48,  55),
        "metal_mid":      (105, 100, 108),
        "metal_light":    (170, 165, 175),
        "metal_shine":    (225, 220, 225),
        "metal_edge":     (250, 245, 250),

        # Gold accents
        "gold_dark":      (90,  60,  15),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 190, 80),
        "gold_shine":     (255, 230, 150),

        # Fire / rage - orange
        "fire_dark":      (75,  20,   5),
        "fire_mid":       (185, 60,  15),
        "fire_bright":    (235, 120, 30),
        "fire_hot":       (255, 180, 60),
        "fire_glow":      (255, 220, 130),
        "fire_white":     (255, 245, 200),

        # Red horns / warpaint
        "red_dark":       (85,  15,  12),
        "red_mid":        (170, 30,  25),
        "red_bright":     (225, 55,  45),
        "red_hot":        (255, 100, 80),

        # Beast fur - boar (dark brown)
        "boar_darkest":   (30,  18,  12),
        "boar_dark":      (65,  40,  22),
        "boar_mid":       (110, 72,  42),
        "boar_light":     (160, 110, 68),
        "boar_high":      (200, 150, 100),

        # Beast fur - wolf (gray)
        "wolf_darkest":   (25,  22,  25),
        "wolf_dark":      (55,  52,  58),
        "wolf_mid":       (95,  92, 100),
        "wolf_light":     (150, 148, 155),
        "wolf_high":      (200, 198, 205),

        # Hawk (brown/tan)
        "hawk_darkest":   (28,  18,  12),
        "hawk_dark":      (65,  42,  22),
        "hawk_mid":       (120, 78,  42),
        "hawk_light":     (175, 128, 78),
        "hawk_high":      (225, 180, 130),
        "hawk_beak":      (245, 210, 100),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_khalros._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_khalros.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_khalros._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 8
            h = abs(ey - sy) + width * 4 + 8
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
        color = _NS_khalros._clamp(color)
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
        color = _NS_khalros._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])), width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_khalros._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, int(rw), int(rh)),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3],
                         (rect[0], rect[1], int(rect[2]), int(rect[3])),
                         border_radius=border_radius)


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
        return int(x + 150 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM (Wild Axes + Hawk)
    # ---------------------------------------------------------------------------
    class AxeProjectile:
        """Spinning axe projectile."""
        def __init__(self, sx, sy, tx, ty, speed=7.0, facing=1):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.facing = facing
            self.alive = True
            self.age = 0
            self.spin = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.55
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 8:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Trail (fire streak)
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(60 + i * 15)
                r = max(1, 4 - (len(self.trail) - i))
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], alpha), (tx, ty), r + 2)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], alpha), (tx, ty), r)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha), (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_khalros._draw_spinning_axe(surface, px, py, self.spin, size=1.0)

                # Fire glow
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], 120), (px, py), 12)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], 80), (px, py), 8)


    class HawkProjectile:
        """Diving hawk projectile."""
        def __init__(self, sx, sy, tx, ty, speed=5.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.wing_phase = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.wing_phase += 0.4
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 6:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 6:
                self.trail.pop(0)
            # Curve path slightly (predator style)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed + math.sin(self.age * 0.2) * 0.8

        def draw(self, surface, phase):
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 3 - (len(self.trail) - i))
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["hawk_dark"], alpha), (tx, ty), r)

            if self.alive:
                dx = self.tx - self.x
                facing = 1 if dx > 0 else -1
                _NS_khalros._draw_flying_hawk(surface, int(self.x), int(self.y),
                                  facing, self.wing_phase, size=1.0)


    def _draw_spinning_axe(surface, cx, cy, spin, size=1.0):
        """A thrown axe that spins."""
        handle_len = int(10 * size)
        head_size = int(7 * size)

        # Handle
        ex = cx + int(math.cos(spin) * handle_len)
        ey = cy + int(math.sin(spin) * handle_len)
        hx = cx - int(math.cos(spin) * handle_len * 0.5)
        hy = cy - int(math.sin(spin) * handle_len * 0.5)

        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_darkest"], (hx, hy), (ex, ey), 4)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_dark"], (hx, hy), (ex, ey), 3)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_mid"], (hx, hy), (ex, ey), 1)

        # Axe head
        perp_x = -math.sin(spin)
        perp_y = math.cos(spin)

        axe_pts = [
            (ex + int(perp_x * head_size), ey + int(perp_y * head_size)),
            (ex + int(math.cos(spin) * head_size * 0.6) + int(perp_x * head_size * 0.6),
             ey + int(math.sin(spin) * head_size * 0.6) + int(perp_y * head_size * 0.6)),
            (ex + int(math.cos(spin) * head_size * 0.6) - int(perp_x * head_size * 0.6),
             ey + int(math.sin(spin) * head_size * 0.6) - int(perp_y * head_size * 0.6)),
            (ex - int(perp_x * head_size), ey - int(perp_y * head_size)),
            (ex - int(math.cos(spin) * head_size * 0.3), ey - int(math.sin(spin) * head_size * 0.3)),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_darkest"], axe_pts)
        # Inner brighter
        inner_pts = [
            (ex + int(perp_x * (head_size - 2)), ey + int(perp_y * (head_size - 2))),
            (ex, ey),
            (ex - int(perp_x * (head_size - 2)), ey - int(perp_y * (head_size - 2))),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_mid"], inner_pts)

        # Sharp edge
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_shine"],
                (ex + int(perp_x * head_size), ey + int(perp_y * head_size)),
                (ex - int(perp_x * head_size), ey - int(perp_y * head_size)), 1)

        # Fire trailing on axe
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], 200), (ex, ey), 3)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], 220), (ex, ey), 1)


    def _draw_flying_hawk(surface, cx, cy, facing, wing_phase, size=1.0):
        """Draw a hawk in flight."""
        wing_y_off = int(math.sin(wing_phase) * 5)

        # Body
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (cx + 1, cy + 1), int(5 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_darkest"], (cx, cy), int(5 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_dark"], (cx - 1, cy - 1), int(4 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_mid"], (cx - 1, cy - 1), int(3 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_light"], (cx - 2, cy - 2), int(2 * size))

        # Head (small, forward)
        hx = cx + int(4 * facing * size)
        hy = cy - 1
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_dark"], (hx, hy), int(3 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_mid"], (hx, hy), int(2 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_light"], (hx - int(facing), hy - 1), 1)

        # Beak
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_beak"], [
            (hx + int(3 * facing), hy),
            (hx + int(6 * facing), hy + 1),
            (hx + int(3 * facing), hy + 2),
        ])

        # Eye
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_hot"], (hx + int(facing), hy - 1), 1)

        # Wings (top view / spread)
        # Upper wing
        wing_upper = [
            (cx, cy - 2),
            (cx - int(12 * size), cy - 4 + wing_y_off),
            (cx - int(9 * size), cy + wing_y_off),
            (cx, cy + 1),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_darkest"], wing_upper)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_dark"], [
            (cx, cy - 1),
            (cx - int(10 * size), cy - 2 + wing_y_off),
            (cx - int(7 * size), cy + 1 + wing_y_off),
            (cx, cy + 1),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_mid"], [
            (cx, cy),
            (cx - int(7 * size), cy - 1 + wing_y_off),
            (cx - int(5 * size), cy + 1 + wing_y_off),
        ])

        # Lower / other wing
        wing_lower = [
            (cx, cy - 1),
            (cx + int(10 * size) * facing - int(3 * facing), cy - 3 - wing_y_off),
            (cx + int(7 * size) * facing - int(2 * facing), cy - wing_y_off),
            (cx, cy + 1),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_darkest"], wing_lower)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_dark"], [
            (cx, cy),
            (cx + int(8 * size) * facing - int(3 * facing), cy - 1 - wing_y_off),
            (cx + int(5 * size) * facing - int(2 * facing), cy + 1 - wing_y_off),
        ])

        # Tail feathers
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_dark"], [
            (cx - int(3 * facing), cy + 1),
            (cx - int(7 * facing), cy + 3),
            (cx - int(5 * facing), cy + 1),
        ])


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_khal_last_x"):
            boss._khal_last_x = boss.x
            boss._khal_last_y = boss.y
            return False
        dx = abs(boss.x - boss._khal_last_x)
        dy = abs(boss.y - boss._khal_last_y)
        boss._khal_last_x = boss.x
        boss._khal_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_khal_prev_timer", 0))
        active = bool(getattr(boss, "_khal_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._khal_attack_active = True
            boss._khal_attack_frame = 0
            active = True
        elif active:
            boss._khal_attack_frame = int(getattr(boss, "_khal_attack_frame", 0)) + 1
            if boss._khal_attack_frame > cooldown:
                boss._khal_attack_active = False
                boss._khal_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._khal_attack_active = False
            boss._khal_attack_frame = 0
            active = False

        boss._khal_prev_timer = timer
        boss._khal_attack_progress = (
            min(1.0, getattr(boss, "_khal_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        for proj in boss._khal_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._khal_projectiles = [p for p in boss._khal_projectiles
                                   if p.alive or p.age < 5]


    def _spawn_axe(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        boss._khal_projectiles.append(
            _NS_khalros.AxeProjectile(sx, sy, tx, ty, speed=7.0, facing=boss.direction))


    def _spawn_hawk(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        boss._khal_projectiles.append(_NS_khalros.HawkProjectile(sx, sy, tx, ty, speed=5.5))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_khalros(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_khalros._detect_moving(boss)
        _NS_khalros._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_khal_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        _NS_khalros._draw_primal_aura(surface, x, y, pulse, active_skill)
        _NS_khalros._draw_ground_runes(surface, x, y + _NS_khalros.SHADOW_DY - 3,
                                       pulse, active_skill)

        # Ground skill effects
        if active_skill == "w":
            _NS_khalros._draw_call_of_wild_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_khalros._draw_boar_ground(surface, boss, x, y, skill_timer, pulse)

        # Character
        # Saat Q dilempar (0-45% durasi) Khalros memegang pose
        # lemparan: kapak terangkat -> terlempar, bukan diam berdiri.
        throw_p = None
        if active_skill == "q" and not attacking:
            tp = 1.0 - skill_timer / _NS_khalros.SKILL_DUR["q"]
            if tp < 0.45:
                throw_p = tp / 0.45
        if attacking:
            _NS_khalros._draw_khalros_attack(surface, boss, x, y)
        elif throw_p is not None:
            _NS_khalros._draw_khalros_throw(surface, boss, x, y, throw_p)
        elif moving:
            _NS_khalros._draw_khalros_walk(surface, boss, x, y)
        else:
            _NS_khalros._draw_khalros_idle(surface, boss, x, y)

        _NS_khalros._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "q":
            _NS_khalros._draw_wild_axes(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_khalros._draw_call_of_wild(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_khalros._draw_boar_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_khalros._draw_hawk_summon(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_khalros_idle(surface, boss, x, y):
        # Napas terasa: bob 2 -> 3.5 px + sway lembut
        bob = int(math.sin(boss.pulse * 0.7) * 3.5)
        _NS_khalros._draw_shadow(surface, x, y + _NS_khalros.SHADOW_DY)
        _NS_khalros._draw_wild_wisps(surface, x, y + 32, boss.pulse)
        _NS_khalros._draw_khalros_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")

    def _draw_khalros_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 5)
        sway = int(math.sin(phase) * 3)
        _NS_khalros._draw_shadow(surface, x + sway, y + _NS_khalros.SHADOW_DY)
        _NS_khalros._draw_wild_wisps(surface, x + sway, y + 32, phase, trail=True,
                         facing=boss.direction)
        _NS_khalros._draw_khalros_body(surface, x + sway, y - bob, boss.direction, phase, "walk")

    def _khal_root_motion(progress, d):
        """Root motion berfase: mundur-naik (anticipation) -> lunge
        (swing) -> tanam kaki + getar (impact hold) -> recovery.
        Return (lunge_dx, lift_dy)."""
        if progress < 0.25:            # anticipation: mundur + sedikit naik
            k = progress / 0.25
            return int(-5 * k), -int(2.5 * k)
        if progress < 0.55:            # swing: dorong 10 px ke depan
            k = (progress - 0.25) / 0.30
            e = 1 - (1 - k) ** 2
            return int(-5 + 15 * e), int(-2.5 + 5 * e)
        if progress < 0.70:            # impact hold: getar pendek
            return 10, 2 + int(math.sin(progress * 42) * 1.5)
        k = (progress - 0.70) / 0.30   # recovery
        return int(10 * (1 - k)), int(2 * (1 - k))

    def _draw_khalros_attack(surface, boss, x, y):
        progress = getattr(boss, "_khal_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        lunge, lift = _NS_khalros._khal_root_motion(progress, boss.direction)
        lunge = lunge * boss.direction

        _NS_khalros._draw_shadow(surface, x + lunge, y + _NS_khalros.SHADOW_DY)
        _NS_khalros._draw_wild_wisps(surface, x + lunge, y + 32, boss.pulse, intense=True)
        _NS_khalros._draw_khalros_body(surface, x + lunge, y + lift, boss.direction, boss.pulse,
                           "attack", progress)
        _NS_khalros._draw_axe_swing_arc(surface, x + lunge, y + lift, boss.direction, progress)
        _NS_khalros._draw_swing_impact(surface, x + lunge, y + lift, boss.direction, progress)

    def _draw_khalros_throw(surface, boss, x, y, t):
        """Pose melempar kapak (skill Q) - reuse swing timeline."""
        lunge, lift = _NS_khalros._khal_root_motion(0.25 + 0.35 * t, boss.direction)
        lunge = lunge * boss.direction
        _NS_khalros._draw_shadow(surface, x + lunge, y + _NS_khalros.SHADOW_DY)
        _NS_khalros._draw_wild_wisps(surface, x + lunge, y + 32, boss.pulse, intense=True)
        _NS_khalros._draw_khalros_body(surface, x + lunge, y + lift, boss.direction,
                                       boss.pulse, "attack", 0.25 + 0.35 * t)


    # ===================================================================
    # BODY RENDERING
    # ===================================================================
    def _draw_khalros_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        _amp = {"idle": 2, "walk": 4, "attack": 2}.get(action, 2)
        sway = int(math.sin(phase * 0.6) * _amp)

        _NS_khalros._draw_loincloth(surface, cx, cy + 8, phase, sway)
        _NS_khalros._draw_torso(surface, cx, cy - 5, phase, sway)
        _NS_khalros._draw_shoulders(surface, cx, cy - 12, phase)

        if action == "attack":
            _NS_khalros._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_khalros._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        _NS_khalros._draw_khalros_head(surface, cx, cy - 26, facing, phase)


    def _draw_loincloth(surface, cx, cy, phase, sway):
        """Tattered fur / leather loincloth."""
        # Belt
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_darkest"], (cx - 16, cy - 4, 32, 7))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_dark"], (cx - 15, cy - 3, 30, 5))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_mid"], (cx - 14, cy - 2, 28, 3))

        # Belt buckle - gold beast head
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["gold_dark"], (cx, cy - 1), 5)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["gold_mid"], (cx, cy - 1), 4)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["gold_light"], (cx - 1, cy - 2), 2)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["gold_shine"], (cx - 1, cy - 2), 1)
        # Buckle horns
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["gold_dark"], [
            (cx - 5, cy - 2), (cx - 7, cy - 5), (cx - 3, cy - 3),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["gold_dark"], [
            (cx + 5, cy - 2), (cx + 7, cy - 5), (cx + 3, cy - 3),
        ])

        # Fur strips
        for i, offset in enumerate([-12, -6, 0, 6, 12]):
            wave = math.sin(phase * 1.2 + i) * 2
            length = 22 + (i % 2) * 3

            # Base strip
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [
                (cx + offset - 4, cy + 3),
                (cx + offset + 4, cy + 3),
                (cx + offset + 3 + int(wave), cy + length),
                (cx + offset - 3 + int(wave), cy + length),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_darkest"], [
                (cx + offset - 4, cy + 2),
                (cx + offset + 4, cy + 2),
                (cx + offset + 3 + int(wave), cy + length - 1),
                (cx + offset - 3 + int(wave), cy + length - 1),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_dark"], [
                (cx + offset - 3, cy + 3),
                (cx + offset + 3, cy + 3),
                (cx + offset + 2 + int(wave), cy + length - 3),
                (cx + offset - 2 + int(wave), cy + length - 3),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_mid"], [
                (cx + offset - 2, cy + 4),
                (cx + offset + 2, cy + 4),
                (cx + offset + 1 + int(wave), cy + length - 5),
                (cx + offset - 1 + int(wave), cy + length - 5),
            ])
            # Fur tuft highlight
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_high"],
                    (cx + offset, cy + 5),
                    (cx + offset + int(wave * 0.5), cy + length - 6), 1)


    def _draw_torso(surface, cx, cy, phase, sway):
        """Muscular torso with leather chest strap."""
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [
            (cx - 14 + 2, cy - 8 + 2), (cx + 14 + 2, cy - 8 + 2),
            (cx + 13 + 2, cy + 14 + 2), (cx + 6 + 2, cy + 18 + 2),
            (cx - 6 + 2, cy + 18 + 2), (cx - 13 + 2, cy + 14 + 2),
        ])

        torso = [
            (cx - 14, cy - 8), (cx + 14, cy - 8),
            (cx + 13, cy + 14), (cx + 6, cy + 18),
            (cx - 6, cy + 18), (cx - 13, cy + 14),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_darkest"], torso)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_dark"], [
            (cx - 12, cy - 7), (cx + 12, cy - 7),
            (cx + 11, cy + 12), (cx + 5, cy + 16),
            (cx - 5, cy + 16), (cx - 11, cy + 12),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_mid"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5),
            (cx + 8, cy + 10), (cx + 3, cy + 14),
            (cx - 3, cy + 14), (cx - 8, cy + 10),
        ])

        # Chest highlights (pectorals)
        for side in (-1, 1):
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_light"],
                      (cx + side * 5, cy - 2), 4)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_high"],
                      (cx + side * 5 - 1, cy - 3), 2)

        # Abs
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_darkest"], (cx, cy + 2), (cx, cy + 14), 1)
        for yoff in (4, 8, 12):
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_darkest"],
                    (cx - 5, cy + yoff), (cx + 5, cy + yoff), 1)

        # Leather chest strap (diagonal)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_darkest"], [
            (cx - 12, cy - 4), (cx - 9, cy - 6),
            (cx + 12, cy + 10), (cx + 9, cy + 12),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_dark"], [
            (cx - 11, cy - 4), (cx - 9, cy - 5),
            (cx + 11, cy + 9), (cx + 9, cy + 10),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_mid"], [
            (cx - 10, cy - 3), (cx - 9, cy - 4),
            (cx + 10, cy + 8), (cx + 9, cy + 9),
        ])

        # Chest emblem - beast head badge
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_darkest"], (cx - 4, cy + 4, 8, 9),
              border_radius=2)
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_dark"], (cx - 3, cy + 5, 6, 7),
              border_radius=1)
        # Red beast face
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_dark"], (cx, cy + 8), 3)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_mid"], (cx, cy + 8), 2)
        # Beast horns
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_mid"], (cx - 3, cy + 6, 1, 2))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_mid"], (cx + 2, cy + 6, 1, 2))


    def _draw_shoulders(surface, cx, cy, phase):
        """Muscular shoulders with fur pauldrons."""
        for side in (-1, 1):
            sx = cx + side * 14
            # Shadow
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (sx + 2, cy + 2), 10)

            # Fur pauldron (spiky)
            for i in range(4):
                fx = sx + side * (i - 2) - side * 3
                fy = cy - 4 + (i % 2) * 2
                _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_darkest"], [
                    (fx - 3, fy + 3),
                    (fx + 3, fy + 3),
                    (fx + int(math.sin(phase * 0.5 + i) * 1), fy - 4),
                ])
                _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_dark"], [
                    (fx - 2, fy + 3),
                    (fx + 2, fy + 3),
                    (fx + int(math.sin(phase * 0.5 + i) * 1), fy - 3),
                ])
                _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_high"],
                        (fx, fy + 2), (fx, fy - 3), 1)

            # Shoulder muscle
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_darkest"], (sx, cy + 2), 8)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_dark"], (sx - side, cy + 1), 7)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_mid"], (sx - side * 2, cy), 5)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_light"], (sx - side * 3, cy - 1), 3)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_high"], (sx - side * 3, cy - 2), 1)

            # Metal band on upper arm
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["metal_darkest"], (sx - 5, cy + 4, 10, 3),
                  border_radius=1)
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["metal_mid"], (sx - 4, cy + 5, 8, 1))
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["gold_mid"], (sx - 1, cy + 5, 2, 1))


    def _draw_khalros_head(surface, cx, cy, facing, phase):
        """Barbarian head with horned helm and beard."""
        # Neck
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["skin_darkest"], (cx - 4, cy + 8, 8, 6))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["skin_dark"], (cx - 3, cy + 8, 6, 5))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["skin_mid"], (cx - 2, cy + 8, 4, 3))

        # Head shadow
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (cx + 2, cy + 2), 12)

        # Head base
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_darkest"], (cx, cy), 11)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_dark"], (cx - 1, cy - 1), 9)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_mid"], (cx - 2, cy - 2), 7)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_light"], (cx - 3, cy - 4), 3)

        # Beard (bushy, lower half of face)
        beard = [
            (cx - 9, cy + 1),
            (cx - 10, cy + 6),
            (cx - 6, cy + 12),
            (cx, cy + 14),
            (cx + 6, cy + 12),
            (cx + 10, cy + 6),
            (cx + 9, cy + 1),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_darkest"], beard)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_dark"], [
            (cx - 8, cy + 2),
            (cx - 9, cy + 6),
            (cx - 5, cy + 11),
            (cx, cy + 13),
            (cx + 5, cy + 11),
            (cx + 9, cy + 6),
            (cx + 8, cy + 2),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_mid"], [
            (cx - 6, cy + 3),
            (cx - 6, cy + 6),
            (cx - 3, cy + 10),
            (cx, cy + 11),
            (cx + 3, cy + 10),
            (cx + 6, cy + 6),
            (cx + 6, cy + 3),
        ])

        # Beard hair strands highlight
        for xoff in (-5, -2, 2, 5):
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["hair_high"],
                    (cx + xoff, cy + 4), (cx + xoff, cy + 10), 1)

        # Fierce eyes (small red glow)
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 1
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (ex, ey), 2)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_dark"], (ex, ey), 1)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_hot"], (ex, ey), 1)
            # Angry eyebrow above
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["hair_darkest"],
                    (ex - 2, ey - 3), (ex + 2, ey - 2), 2)

        # Nose
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_dark"], [
            (cx, cy + 1),
            (cx - 2, cy + 4),
            (cx + 2, cy + 4),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_mid"], [
            (cx, cy + 2),
            (cx - 1, cy + 4),
            (cx + 1, cy + 4),
        ])

        # HELM with horns (Beastmaster signature)
        _NS_khalros._draw_helm(surface, cx, cy - 5, phase)

        # Red war paint stripe on forehead
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_dark"], (cx - 4, cy - 4, 8, 2))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_bright"], (cx - 3, cy - 4, 6, 1))


    def _draw_helm(surface, cx, cy, phase):
        """Horned barbarian helm."""
        # Helm cap
        helm = [
            (cx - 11, cy + 2),
            (cx - 9, cy - 4),
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx + 9, cy - 4),
            (cx + 11, cy + 2),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in helm])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_darkest"], helm)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_dark"], [
            (cx - 10, cy + 1),
            (cx - 8, cy - 3),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 8, cy - 3),
            (cx + 10, cy + 1),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_mid"], [
            (cx - 8, cy),
            (cx - 6, cy - 3),
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 6, cy - 3),
            (cx + 8, cy),
        ])
        # Helm highlight
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_light"],
                (cx - 5, cy - 4), (cx + 5, cy - 4), 1)

        # Gold trim rim
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["gold_mid"], (cx - 11, cy + 2), (cx + 11, cy + 2), 1)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["gold_light"], (cx - 10, cy + 2), (cx + 10, cy + 2), 1)

        # HORNS (huge bull-like horns going outward)
        for side in (-1, 1):
            # Horn base
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [
                (cx + side * 8 + 1, cy - 3 + 1),
                (cx + side * 16 + 1, cy - 8 + 1),
                (cx + side * 20 + 1, cy - 4 + 1),
                (cx + side * 15 + 1, cy - 1 + 1),
            ])
            # Main horn
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_darkest"], [
                (cx + side * 8, cy - 3),
                (cx + side * 16, cy - 8),
                (cx + side * 20, cy - 4),
                (cx + side * 15, cy - 1),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_dark"], [
                (cx + side * 9, cy - 3),
                (cx + side * 15, cy - 7),
                (cx + side * 18, cy - 4),
                (cx + side * 14, cy - 1),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["bone_dark" if False else "leather_high"], [
                (cx + side * 10, cy - 3),
                (cx + side * 14, cy - 6),
                (cx + side * 16, cy - 4),
                (cx + side * 13, cy - 2),
            ]) if False else None

            # Highlight on horn
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["hair_mid"],
                    (cx + side * 10, cy - 4),
                    (cx + side * 18, cy - 5), 1)

            # Horn tip (sharper, lighter)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hair_high"], (cx + side * 20, cy - 4), 1)

        # HAIR (spiky mohawk between horns)
        for i in range(3):
            sx = cx - 3 + i * 3
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_darkest"], [
                (sx - 2, cy - 6),
                (sx + 2, cy - 6),
                (sx + int(math.sin(phase * 0.3 + i) * 1), cy - 13),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_dark"], [
                (sx - 1, cy - 6),
                (sx + 1, cy - 6),
                (sx + int(math.sin(phase * 0.3 + i) * 1), cy - 12),
            ])


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms holding axes at ready."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            sh_x = cx + side * 13
            sh_y = cy + 2
            elbow_x = sh_x + side * 10
            elbow_y = cy + 12 + int(sway)
            hand_x = elbow_x + side * 6
            hand_y = elbow_y + 10

            _NS_khalros._draw_arm_segment(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_khalros._draw_arm_segment(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_khalros._draw_hand(surface, hand_x, hand_y)
            # Axe held vertically
            _NS_khalros._draw_axe_held(surface, hand_x, hand_y, side, phase)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """One arm swings axe."""
        sway = math.sin(phase * 0.7) * 1

        # Back arm - just holds axe
        back_side = -facing
        bs_x = cx + back_side * 13
        bs_y = cy + 2
        be_x = bs_x + back_side * 8
        be_y = cy + 12
        bh_x = be_x + back_side * 6
        bh_y = be_y + 9
        _NS_khalros._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y)
        _NS_khalros._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y)
        _NS_khalros._draw_hand(surface, bh_x, bh_y)
        _NS_khalros._draw_axe_held(surface, bh_x, bh_y, back_side, phase)

        # Front arm swings
        fs_x = cx + facing * 13
        fs_y = cy + 2

        if progress < 0.25:
            # Wind up
            t = progress / 0.25
            t = t * t * (3 - 2 * t)
            arm_angle = -1.4 + 0.2 * t
        elif progress < 0.55:
            # Swing
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3
            arm_angle = -1.2 + 2.4 * t
        else:
            # Recovery
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 0.9 * t

        arm_len = 16
        fe_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * arm_len)
        fh_x = fe_x + int(math.cos(arm_angle) * 10) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 10)

        _NS_khalros._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_khalros._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_khalros._draw_hand(surface, fh_x, fh_y)

        # Large swinging axe
        axe_angle = arm_angle + math.pi / 4 * facing
        _NS_khalros._draw_axe_swinging(surface, fh_x, fh_y, facing, axe_angle, size=1.2)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 7)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_dark"], (x1, y1), (x2, y2), 5)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_mid"], (x1, y1), (x2, y2), 3)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_light"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_hand(surface, x, y):
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (x + 1, y + 1), 5)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_darkest"], (x, y), 4)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_dark"], (x, y), 3)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_mid"], (x - 1, y - 1), 2)
        # Leather wrap
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_dark"], (x - 4, y - 5, 8, 3),
              border_radius=1)
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_mid"], (x - 3, y - 5, 6, 1))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_mid"], (x - 3, y - 4, 6, 1))


    def _draw_axe_held(surface, hx, hy, side, phase):
        """Axe held vertically at rest."""
        # Handle (down from hand)
        handle_bot_x = hx + int(side * 1)
        handle_bot_y = hy + 16
        handle_top_y = hy - 12

        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["shadow_deep"],
                (hx + 1, handle_top_y + 1), (handle_bot_x + 1, handle_bot_y + 1), 4)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_darkest"],
                (hx, handle_top_y), (handle_bot_x, handle_bot_y), 3)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_dark"],
                (hx, handle_top_y), (handle_bot_x, handle_bot_y), 2)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_mid"],
                (hx, handle_top_y), (handle_bot_x, handle_bot_y), 1)

        # Red wrap on handle
        for i in range(3):
            wy = hy - 6 + i * 5
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_dark"], (hx - 2, wy, 4, 2))
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_mid"], (hx - 1, wy, 3, 1))

        # Axe head at top
        ax = hx
        ay = handle_top_y

        # Main axe head (large curved blade)
        head_pts = [
            (ax - side * 2, ay + 2),
            (ax - side * 8, ay - 2),
            (ax - side * 10, ay - 6),
            (ax - side * 8, ay - 10),
            (ax - side * 3, ay - 8),
            (ax, ay - 4),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_darkest"], head_pts)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_dark"], [
            (ax - side * 3, ay + 1),
            (ax - side * 7, ay - 2),
            (ax - side * 9, ay - 6),
            (ax - side * 7, ay - 9),
            (ax - side * 3, ay - 7),
            (ax - side * 1, ay - 4),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_mid"], [
            (ax - side * 4, ay),
            (ax - side * 6, ay - 3),
            (ax - side * 7, ay - 6),
            (ax - side * 6, ay - 8),
            (ax - side * 4, ay - 7),
        ])

        # Sharp edge highlight
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_shine"],
                (ax - side * 8, ay - 2), (ax - side * 8, ay - 10), 1)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_edge"],
                (ax - side * 9, ay - 6), (ax - side * 9, ay - 8), 1)

        # Handle top cap
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["metal_darkest"], (ax, ay - 1), 2)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["metal_mid"], (ax, ay - 1), 1)


    def _draw_axe_swinging(surface, hx, hy, facing, angle, size=1.0):
        """Big axe in motion — angled."""
        handle_len = int(20 * size)
        dx = math.cos(angle) * facing
        dy = math.sin(angle)

        # Handle from hand to axe head
        head_x = hx + int(dx * handle_len)
        head_y = hy + int(dy * handle_len)

        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["shadow_deep"],
                (hx + 2, hy + 2), (head_x + 2, head_y + 2), 5)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_darkest"], (hx, hy), (head_x, head_y), 4)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_dark"], (hx, hy), (head_x, head_y), 3)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_mid"], (hx, hy), (head_x, head_y), 1)

        # Red wraps
        for i in range(3):
            t = 0.3 + i * 0.2
            wx = hx + int(dx * handle_len * t)
            wy = hy + int(dy * handle_len * t)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_dark"], (wx, wy), 2)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_mid"], (wx, wy), 1)

        # Axe head
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle) * facing
        head_size = int(11 * size)

        head_pts = [
            (head_x + int(perp_x * head_size), head_y + int(perp_y * head_size)),
            (head_x + int(dx * head_size * 0.4) + int(perp_x * head_size * 0.9),
             head_y + int(dy * head_size * 0.4) + int(perp_y * head_size * 0.9)),
            (head_x + int(dx * head_size * 0.4) - int(perp_x * head_size * 0.9),
             head_y + int(dy * head_size * 0.4) - int(perp_y * head_size * 0.9)),
            (head_x - int(perp_x * head_size), head_y - int(perp_y * head_size)),
            (head_x - int(dx * head_size * 0.3), head_y - int(dy * head_size * 0.3)),
        ]

        _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_darkest"], head_pts)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_dark"], [
            (head_x + int(perp_x * (head_size - 2)), head_y + int(perp_y * (head_size - 2))),
            (head_x + int(dx * head_size * 0.3), head_y + int(dy * head_size * 0.3)),
            (head_x - int(perp_x * (head_size - 2)), head_y - int(perp_y * (head_size - 2))),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_mid"], [
            (head_x + int(perp_x * (head_size - 4)), head_y + int(perp_y * (head_size - 4))),
            (head_x, head_y),
            (head_x - int(perp_x * (head_size - 4)), head_y - int(perp_y * (head_size - 4))),
        ])

        # Sharp edge highlight
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_shine"],
                (head_x + int(perp_x * head_size), head_y + int(perp_y * head_size)),
                (head_x - int(perp_x * head_size), head_y - int(perp_y * head_size)), 1)

        # Fire aura on head
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], 150), (head_x, head_y), 4)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], 180), (head_x, head_y), 2)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_wild_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Primal dust wisps."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_khalros.PALETTE["leather_darkest"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising fire/energy wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], alpha), (sx, sy), 5)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], alpha), (sx, sy - 2), 3)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha), (sx, sy - 3), 1)

        # Ember particles
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 8)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_bright"], (sx, sy), 2)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_hot"], (sx, sy), 1)

        if trail:
            for i in range(4):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["leather_dark"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_khalros.PALETTE["fire_dark"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_primal_aura(surface, x, y, phase, active_skill):
        """Background aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.4 if active_skill in ("q", "r") else 1.0
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.2 * pulse * strength)
            if alpha > 0:
                _NS_khalros._aacircle(aura, (*_NS_khalros.PALETTE["fire_dark"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ground_runes(surface, x, y, phase, active_skill):
        """Ground runes."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_khalros.PALETTE["fire_dark"], 140),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_khalros.PALETTE["fire_mid"], 170),
                            (20, 14, 90, 16), 2)

        # Tribal rune marks
        for i in range(8):
            angle = phase * 0.15 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_khalros.PALETTE["fire_hot"], 160),
                             (x1, y1), (x2, y2), 1)

        if active_skill:
            pygame.draw.ellipse(ring, (*_NS_khalros.PALETTE["fire_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_axe_swing_arc(surface, x, y, facing, progress):
        """Axe swing motion trail (fire orange)."""
        if progress < 0.28 or progress > 0.75:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.25
        visibility = max(0.0, min(1.0, visibility))

        arc = pygame.Surface((140, 110), pygame.SRCALPHA)
        for i in range(16):
            t = i / 15
            angle = -math.pi * 0.9 + t * math.pi * 1.1
            px = 70 + int(math.cos(angle) * 52) * facing
            py = 55 + int(math.sin(angle) * 40)
            alpha = int((200 - i * 10) * visibility)
            if alpha <= 0:
                continue
            _NS_khalros._aacircle(arc, (*_NS_khalros.PALETTE["fire_dark"], alpha), (px, py), 8)
            _NS_khalros._aacircle(arc, (*_NS_khalros.PALETTE["fire_bright"], alpha), (px, py), 5)
            _NS_khalros._aacircle(arc, (*_NS_khalros.PALETTE["fire_hot"], alpha), (px, py), 3)
            _NS_khalros._aacircle(arc, (*_NS_khalros.PALETTE["fire_glow"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 70, y - 55))


    def _draw_swing_impact(surface, x, y, facing, progress):
        if progress < 0.45 or progress > 0.85:
            return
        t = (progress - 0.45) / 0.40
        intensity = math.sin(t * math.pi)

        impact_x = x + 38 * facing
        impact_y = y + 3
        alpha = int(230 * intensity)
        radius = int(8 + intensity * 22)

        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], alpha // 2),
                  (impact_x, impact_y), radius + 4)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], alpha),
                  (impact_x, impact_y), radius, 3)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha),
                  (impact_x, impact_y), max(1, radius - 5), 2)

        # Sparks
        for i in range(10):
            angle = i * math.pi / 5 + progress * 3
            dx = impact_x + int(math.cos(angle) * radius * 1.3)
            dy = impact_y + int(math.sin(angle) * radius * 0.9)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_hot"], (dx, dy), 2)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_glow"], (dx, dy), 1)


    # ===================================================================
    # SKILL Q: WILD AXES
    # ===================================================================
    def _draw_wild_axes(surface, boss, x, y, timer, phase):
        """Two axes thrown - spawn projectiles."""
        duration = _NS_khalros.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khalros._target_position(boss, x, y)

        if progress < 0.15 and not getattr(boss, "_khal_axes_spawned", False):
            # Spawn 2 axes with slight spread
            for i, offset in enumerate((-10, 10)):
                angle_off = math.atan2(ty - y, (tx - x) * boss.direction) + i * 0.15
                sx = x + 12 * boss.direction
                sy = y - 10 + offset
                _NS_khalros._spawn_axe(boss, sx, sy, tx + offset * 0.5, ty)
            boss._khal_axes_spawned = True
        if progress > 0.5:
            boss._khal_axes_spawned = False

        # Aim line
        if progress < 0.4:
            alpha = int(150 * (1 - progress / 0.4))
            start_x = x + 15 * boss.direction
            start_y = y - 10
            for i in range(0, 100, 8):
                t = i / 100
                px = int(start_x + (tx - start_x) * t)
                py = int(start_y + (ty - start_y) * t)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], alpha), (px, py), 2)


    # ===================================================================
    # SKILL W: CALL OF THE WILD (Summon boar + wolf)
    # ===================================================================
    def _draw_call_of_wild_ground(surface, boss, x, y, timer, phase):
        """Summon circles beside Khalros."""
        duration = _NS_khalros.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Lingkaran memudar bersama beast yang tenggelam (0.72 -> 1.0)
        fade = 1.0 if progress <= 0.72 else max(0.0, 1.0 - (progress - 0.72) / 0.28)

        for side, off in [(-1, -40), (1, 40)]:
            sx = x + off
            sy = y + 32
            radius = int(20 + progress * 10)
            _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["fire_dark"], int(180 * pulse * fade)),
                     (sx - radius, sy - radius // 3, radius * 2, radius // 1.5))
            _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["fire_bright"], int(150 * pulse * fade)),
                     (sx - radius + 4, sy - radius // 3 + 2,
                      radius * 2 - 8, radius // 1.5 - 4))

            # Rune symbols
            for i in range(4):
                angle = phase * 0.3 + i * math.pi / 2
                rx = sx + int(math.cos(angle) * (radius - 3))
                ry = sy + int(math.sin(angle) * (radius // 3))
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], int(200 * pulse * fade)),
                          (rx, ry), 2)


    def _draw_call_of_wild(surface, boss, x, y, timer, phase):
        """Boar (left) and wolf (right) rising from summon circles.

        Timeline penuh: NAIK (0.2-0.55) -> BERDIRI penuh (0.55-0.72)
        -> TENGGELAM + pudar (0.72-1.0) supaya tidak hilang mendadak
        saat active_skill_timer habis."""
        duration = _NS_khalros.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))

        def _rise(start):
            if progress <= start:
                return 0.0, 0.0
            t = min(1.0, (progress - start) / 0.35)
            t = t * t * (3 - 2 * t)          # smoothstep, lebih halus
            sink = 0.0
            if progress > 0.72:
                sink = min(1.0, (progress - 0.72) / 0.28)
            return t, sink

        # Boar on left
        boar_x = x - 40
        boar_y = y + 20
        if progress > 0.2:
            rise_t, sink = _rise(0.2)
            _NS_khalros._draw_boar(surface, boar_x,
                       boar_y - int(22 * rise_t) + int(14 * sink), -1, phase,
                       alpha=int(255 * rise_t * (1 - sink * 0.9)))

        # Wolf on right
        wolf_x = x + 40
        wolf_y = y + 20
        if progress > 0.3:
            rise_t, sink = _rise(0.3)
            _NS_khalros._draw_wolf(surface, wolf_x,
                       wolf_y - int(22 * rise_t) + int(14 * sink), 1, phase,
                       alpha=int(255 * rise_t * (1 - sink * 0.9)))


    def _draw_boar(surface, cx, cy, facing, phase, alpha=255):
        """Draw a boar creature."""
        # Body shadow
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["shadow_deep"], alpha),
                 (cx - 16, cy - 4, 32, 16))

        # Body
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha),
                 (cx - 15, cy - 6, 30, 15))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["boar_dark"], alpha),
                 (cx - 13, cy - 5, 26, 12))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["boar_mid"], alpha),
                 (cx - 11, cy - 4, 22, 9))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["boar_light"], alpha),
                 (cx - 9, cy - 5, 18, 5))

        # Head (front)
        hx = cx + facing * 13
        hy = cy - 3
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha), (hx, hy), 6)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["boar_dark"], alpha), (hx, hy), 5)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["boar_mid"], alpha), (hx - facing, hy - 1), 3)

        # Snout
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha), [
            (hx + facing * 4, hy - 1),
            (hx + facing * 8, hy),
            (hx + facing * 8, hy + 3),
            (hx + facing * 4, hy + 2),
        ])
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["boar_dark"], alpha), [
            (hx + facing * 5, hy),
            (hx + facing * 7, hy + 1),
            (hx + facing * 7, hy + 2),
            (hx + facing * 5, hy + 2),
        ])

        # Tusks (curved white)
        for side_off in (-1, 1):
            tusk_y = hy + 1 + side_off
            _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["metal_light"], alpha), [
                (hx + facing * 6, tusk_y),
                (hx + facing * 10, tusk_y - 2 * side_off),
                (hx + facing * 8, tusk_y - side_off),
            ])
            _NS_khalros._aaline(surface, (*_NS_khalros.PALETTE["metal_shine"], alpha),
                    (hx + facing * 7, tusk_y - side_off),
                    (hx + facing * 9, tusk_y - 2 * side_off), 1)

        # Eye
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha), (hx - facing, hy - 2), 1)

        # Ears
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha), [
            (hx - facing * 2, hy - 5),
            (hx + facing, hy - 8),
            (hx + facing * 3, hy - 5),
        ])

        # Legs
        for lx in (cx - 8, cx - 4, cx + 4, cx + 8):
            offset_y = int(math.sin(phase * 2 + lx) * 1)
            _NS_khalros._rect(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha),
                  (lx - 1, cy + 6, 3, 6 + offset_y))
            _NS_khalros._rect(surface, (*_NS_khalros.PALETTE["boar_dark"], alpha),
                  (lx, cy + 6, 2, 5 + offset_y))

        # Spiky back mane
        for i, mx in enumerate([-8, -4, 0, 4, 8]):
            _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["hair_darkest"], alpha), [
                (cx + mx - 1, cy - 6),
                (cx + mx + 1, cy - 6),
                (cx + mx, cy - 10 - (i % 2)),
            ])

        # Tail
        _NS_khalros._aaline(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha),
                (cx - facing * 14, cy - 2),
                (cx - facing * 18, cy - 5), 2)


    def _draw_wolf(surface, cx, cy, facing, phase, alpha=255):
        """Draw a wolf creature."""
        # Body shadow
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["shadow_deep"], alpha),
                 (cx - 15, cy - 3, 30, 14))

        # Body (leaner than boar)
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha),
                 (cx - 14, cy - 5, 28, 13))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha),
                 (cx - 12, cy - 4, 24, 10))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["wolf_mid"], alpha),
                 (cx - 10, cy - 3, 20, 7))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["wolf_light"], alpha),
                 (cx - 8, cy - 4, 16, 4))

        # Head
        hx = cx + facing * 12
        hy = cy - 3
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha), (hx, hy), 6)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha), (hx, hy), 5)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["wolf_mid"], alpha), (hx - facing, hy - 1), 3)

        # Snout (pointier than boar)
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha), [
            (hx + facing * 3, hy),
            (hx + facing * 9, hy),
            (hx + facing * 8, hy + 3),
            (hx + facing * 3, hy + 2),
        ])
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha), [
            (hx + facing * 4, hy + 1),
            (hx + facing * 8, hy + 1),
            (hx + facing * 7, hy + 2),
            (hx + facing * 4, hy + 2),
        ])

        # Nose
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["shadow_deep"], alpha),
                  (hx + facing * 8, hy + 1), 1)

        # Fangs
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["white"], alpha), [
            (hx + facing * 5, hy + 2),
            (hx + facing * 6, hy + 4),
            (hx + facing * 7, hy + 2),
        ])

        # Glowing red eye (feral)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha), (hx - facing, hy - 2), 1)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["red_bright"], alpha), (hx - facing, hy - 2), 1)

        # Pointy ears
        for ear_off in (-3, 1):
            _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha), [
                (hx + facing * ear_off, hy - 5),
                (hx + facing * (ear_off + 1), hy - 9),
                (hx + facing * (ear_off + 3), hy - 5),
            ])
            _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha), [
                (hx + facing * (ear_off + 1), hy - 5),
                (hx + facing * (ear_off + 2), hy - 8),
                (hx + facing * (ear_off + 3), hy - 5),
            ])

        # Legs (longer than boar)
        for lx in (cx - 8, cx - 3, cx + 3, cx + 8):
            offset_y = int(math.sin(phase * 2.5 + lx) * 1)
            _NS_khalros._rect(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha),
                  (lx - 1, cy + 5, 3, 7 + offset_y))
            _NS_khalros._rect(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha),
                  (lx, cy + 5, 2, 6 + offset_y))

        # Bushy tail
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha), [
            (cx - facing * 12, cy - 2),
            (cx - facing * 20, cy - 4),
            (cx - facing * 18, cy + 2),
            (cx - facing * 12, cy),
        ])
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha), [
            (cx - facing * 13, cy - 2),
            (cx - facing * 18, cy - 3),
            (cx - facing * 16, cy + 1),
            (cx - facing * 13, cy),
        ])

        # Fur tuft on back
        _NS_khalros._aaline(surface, (*_NS_khalros.PALETTE["wolf_high"], alpha),
                (cx - 5, cy - 5), (cx + 5, cy - 5), 1)


    # ===================================================================
    # SKILL E: BOAR (fast charging boar)
    # ===================================================================
    def _draw_boar_ground(surface, boss, x, y, timer, phase):
        """Trail of dust as boar charges."""
        tx, ty = _NS_khalros._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / _NS_khalros.SKILL_DUR["e"]))

        # Charging trail
        start_x = x + 15 * boss.direction
        start_y = y + 25
        for i in range(6):
            t = max(0, progress - i * 0.08)
            px = int(start_x + (tx - start_x) * t)
            py = int(start_y + (ty - start_y) * t)
            alpha = int(150 - i * 22)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["leather_dark"], alpha), (px, py), 5)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["leather_mid"], alpha), (px, py), 3)


    def _draw_boar_charge(surface, boss, x, y, timer, phase):
        """Boar charging toward target."""
        tx, ty = _NS_khalros._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / _NS_khalros.SKILL_DUR["e"]))
        start_x = x + 15 * boss.direction
        start_y = y + 25

        bx = int(start_x + (tx - start_x) * progress)
        by = int(start_y + (ty - start_y) * progress)

        facing = 1 if tx > x else -1

        # Trail of dust/sparks
        for i in range(5):
            trail_t = max(0.0, progress - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], 150 - i * 25),
                      (px, py), max(2, 6 - i))
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], 100 - i * 15),
                      (px, py), max(1, 4 - i))

        # The boar itself
        _NS_khalros._draw_boar(surface, bx, by, facing, phase * 2)

        # Impact at end
        if progress > 0.85:
            t = (progress - 0.85) / 0.15
            intensity = 1 - t
            radius = int(20 * intensity)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], int(230 * intensity)),
                      (tx, ty), radius, 3)
            for i in range(8):
                angle = i * math.pi / 4
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], int(200 * intensity)),
                          (ex, ey), 2)


    # ===================================================================
    # SKILL R: HAWK (flying projectile)
    # ===================================================================
    def _draw_hawk_summon(surface, boss, x, y, timer, phase):
        """Hawk flies from Khalros toward target."""
        duration = _NS_khalros.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khalros._target_position(boss, x, y)

        # Spawn hawk projectile at start
        if progress < 0.1 and not getattr(boss, "_khal_hawk_spawned", False):
            sx = x + 5 * boss.direction
            sy = y - 30
            _NS_khalros._spawn_hawk(boss, sx, sy, tx, ty - 20)
            boss._khal_hawk_spawned = True
        if progress > 0.5:
            boss._khal_hawk_spawned = False

        # Feathers falling from spawn point
        if progress < 0.4:
            for i in range(3):
                angle = phase + i * math.pi * 2 / 3
                fx = x + int(math.cos(angle) * 20)
                fy = y - 30 + int(progress * 30) + int(math.sin(angle) * 5)
                alpha = int(180 * (1 - progress / 0.4))
                _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["hawk_dark"], alpha), [
                    (fx, fy),
                    (fx + 2, fy + 4),
                    (fx - 2, fy + 4),
                ])
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["hawk_mid"], alpha), (fx, fy + 2), 1)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_khalros.draw_khalros(surface, boss, x, y)


# ====================================================================
# GORATH
# ====================================================================
class _NS_gorath:
    """Namespace gorath - Level 2 Masterwork animation pass."""

    # Durasi FX DIKUNCI sama active_skill_timer AI (base_boss.py).
    # Dulu W tidak pernah men-spawn blood spike (gerbang progress
    # terlewat) dan burst-nya terpotong sesaat sebelum hilang.
    SKILL_DUR = {"q": 90, "w": 70, "e": 35, "r": 100}
    SHADOW_DY = 46

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ---------------------------------------------------------------------------
    # HD Blood Palette - Deep crimson / dark red / bone
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - reddish demon flesh
        "skin_darkest":   (35,  10,  10),
        "skin_dark":      (78,  22,  20),
        "skin_mid":       (125, 45,  35),
        "skin_light":     (175, 78,  55),
        "skin_high":      (215, 130, 90),
        "skin_shine":     (245, 185, 140),

        # Blood
        "blood_darkest":  (25,   3,   5),
        "blood_dark":     (72,   6,  10),
        "blood_mid":      (135, 15,  20),
        "blood_bright":   (195, 25,  30),
        "blood_hot":      (235, 55,  50),
        "blood_glow":     (255, 100, 85),
        "blood_light":    (255, 165, 140),

        # Hair - dark spiky
        "hair_darkest":   (10,   8,  12),
        "hair_dark":      (28,  22,  30),
        "hair_mid":       (55,  45,  58),
        "hair_high":      (95,  82, 100),

        # Leather / cloth
        "leather_darkest": (18, 12,  8),
        "leather_dark":   (45,  28,  18),
        "leather_mid":    (85,  55,  30),
        "leather_light":  (135, 90,  50),
        "leather_high":   (185, 135, 80),

        # Bone / claws
        "bone_darkest":   (55,  45,  35),
        "bone_dark":      (115, 100, 78),
        "bone_mid":       (175, 160, 130),
        "bone_light":     (220, 210, 180),
        "bone_shine":     (245, 240, 220),

        # Metal (blades)
        "metal_darkest":  (18,  15,  18),
        "metal_dark":     (48,  42,  48),
        "metal_mid":      (95,  88,  95),
        "metal_light":    (155, 148, 155),
        "metal_shine":    (215, 210, 215),

        # Eyes - glowing red
        "eye_dark":       (80,   5,   8),
        "eye_mid":        (180, 20,  25),
        "eye_bright":     (240, 55,  50),
        "eye_hot":        (255, 130, 100),
        "eye_white":      (255, 220, 200),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   2,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        """Clamp color channels, supports both RGB and RGBA."""
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gorath._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_gorath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_gorath._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 8
            h = abs(ey - sy) + width * 4 + 8
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
        color = _NS_gorath._clamp(color)
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
        color = _NS_gorath._clamp(color)
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
        color = _NS_gorath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


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
        return int(x + 150 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Blood splatter & droplet helpers
    # ---------------------------------------------------------------------------
    def _draw_blood_splatter(surface, cx, cy, size=8, seed=0, alpha=255):
        """Draw a chaotic blood splatter."""
        color_outer = (*_NS_gorath.PALETTE["blood_dark"], alpha)
        color_inner = (*_NS_gorath.PALETTE["blood_bright"], alpha)
        color_hot = (*_NS_gorath.PALETTE["blood_hot"], alpha)

        _NS_gorath._aacircle(surface, color_outer, (cx, cy), size)
        _NS_gorath._aacircle(surface, color_inner, (cx - 1, cy - 1), max(1, size - 2))
        _NS_gorath._aacircle(surface, color_hot, (cx - 1, cy - 2), max(1, size - 4))

        for i in range(6):
            angle = (seed * 0.7 + i * math.pi / 3) % (math.pi * 2)
            dist = size + 2 + (i % 3) * 2
            dx = cx + int(math.cos(angle) * dist)
            dy = cy + int(math.sin(angle) * dist)
            r = max(1, 3 - i % 3)
            _NS_gorath._aacircle(surface, color_outer, (dx, dy), r)
            _NS_gorath._aacircle(surface, color_inner, (dx, dy), max(1, r - 1))


    def _draw_blood_droplet(surface, x, y, size=3, alpha=255):
        """Draw a single blood droplet (teardrop shape)."""
        _NS_gorath._poly(surface, (*_NS_gorath.PALETTE["blood_darkest"], alpha), [
            (x, y - size),
            (x - size, y + size),
            (x + size, y + size),
        ])
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_mid"], alpha), (x, y + size // 2), size)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                  (x, y + size // 2), max(1, size - 1))
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], alpha),
                  (x - 1, y + size // 2 - 1), max(1, size - 2))


    def _draw_blood_streak(surface, sx, sy, ex, ey, width=3, alpha=255):
        """Blood streak with dripping effect."""
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_darkest"], alpha), (sx, sy), (ex, ey), width + 2)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_mid"], alpha), (sx, sy), (ex, ey), width)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha), (sx, sy), (ex, ey), max(1, width - 1))


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM (for Bloodrite / Thirst effects)
    # ---------------------------------------------------------------------------
    class BloodProjectile:
        """A blood-based projectile for ranged skills."""
        def __init__(self, sx, sy, tx, ty, speed=7.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 + i * 15)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], alpha), (tx, ty), r + 2)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha), (tx, ty), r)
            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], 100), (px, py), 10)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_mid"], 180), (px, py), 7)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], 230), (px, py), 5)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], 250), (px, py), 3)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_light"], 255), (px, py - 1), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_gor_last_x"):
            boss._gor_last_x = boss.x
            boss._gor_last_y = boss.y
            return False
        dx = abs(boss.x - boss._gor_last_x)
        dy = abs(boss.y - boss._gor_last_y)
        boss._gor_last_x = boss.x
        boss._gor_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        """Track melee attack timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gor_prev_timer", 0))
        active = bool(getattr(boss, "_gor_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._gor_attack_active = True
            boss._gor_attack_frame = 0
            active = True
        elif active:
            boss._gor_attack_frame = int(getattr(boss, "_gor_attack_frame", 0)) + 1
            if boss._gor_attack_frame > cooldown:
                boss._gor_attack_active = False
                boss._gor_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._gor_attack_active = False
            boss._gor_attack_frame = 0
            active = False

        boss._gor_prev_timer = timer
        boss._gor_attack_progress = (
            min(1.0, getattr(boss, "_gor_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_gor_projectiles"):
            boss._gor_projectiles = []
        for proj in boss._gor_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._gor_projectiles = [p for p in boss._gor_projectiles if p.alive or p.age < 8]


    def _spawn_projectile(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_gor_projectiles"):
            boss._gor_projectiles = []
        boss._gor_projectiles.append(_NS_gorath.BloodProjectile(sx, sy, tx, ty, speed=6.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_gorath(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_gorath._detect_moving(boss)
        _NS_gorath._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_gor_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 44) - 15
        )

        # Rage (Blood Rage buff) berjalan 300 frame setelah cast -
        # selama itu ada glow persisten, bukan cuma saat FX cast.
        rage = bool(getattr(boss, "rage_active", False))

        # Background
        _NS_gorath._draw_blood_aura(surface, x, y, pulse, active_skill, rage)
        _NS_gorath._draw_ground_blood_pool(surface, x, y + _NS_gorath.SHADOW_DY - 2,
                                           pulse, active_skill)

        # Skill ground effects
        if active_skill == "w":
            _NS_gorath._draw_bloodrite_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gorath._draw_rupture_ground(surface, boss, x, y, skill_timer, pulse)

        # Character
        if attacking:
            _NS_gorath._draw_gorath_attack(surface, boss, x, y)
        elif moving:
            _NS_gorath._draw_gorath_walk(surface, boss, x, y, rage)
        else:
            _NS_gorath._draw_gorath_idle(surface, boss, x, y, rage)

        if rage:
            # setetes darah menguap di sekitar tubuh selama rage
            _NS_gorath._draw_wisps_gore(surface, x, y + 30, pulse)

        # Projectiles
        _NS_gorath._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "q":
            _NS_gorath._draw_bloodrage(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_gorath._draw_bloodrite(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_gorath._draw_thirst(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gorath._draw_rupture(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_gorath_idle(surface, boss, x, y, rage=False):
        # Napas demo - 2 -> 3.5 px supaya jelas hidup
        bob = int(math.sin(boss.pulse * 0.7) * 3.5)
        _NS_gorath._draw_shadow(surface, x, y + _NS_gorath.SHADOW_DY)
        _NS_gorath._draw_blood_wisps(surface, x, y + 30, boss.pulse,
                                     intense=rage)
        _NS_gorath._draw_gorath_body(surface, x, y + bob, boss.direction,
                                     boss.pulse, "idle", rage=rage)

    def _draw_gorath_walk(surface, boss, x, y, rage=False):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 5)
        sway = int(math.sin(phase) * 3)
        _NS_gorath._draw_shadow(surface, x + sway, y + _NS_gorath.SHADOW_DY)
        _NS_gorath._draw_blood_wisps(surface, x + sway, y + 30, phase, trail=True, facing=boss.direction,
                                     intense=rage)
        _NS_gorath._draw_gorath_body(surface, x + sway, y - bob, boss.direction, phase, "walk",
                                     rage=rage)
        _NS_gorath._draw_blood_trail(surface, x + sway, y + _NS_gorath.SHADOW_DY - 14,
                                     phase, boss.direction)

    def _gor_root_motion(progress):
        """Antisipasi -> lunge -> impact hold (getar) -> recovery."""
        if progress < 0.25:
            k = progress / 0.25
            return int(-5 * k), -int(3 * k)
        if progress < 0.55:
            k = (progress - 0.25) / 0.30
            e = 1 - (1 - k) ** 2
            return int(-5 + 16 * e), int(-3 + 5.5 * e)
        if progress < 0.70:
            return 11, 2 + int(math.sin(progress * 42) * 1.5)
        k = (progress - 0.70) / 0.30
        return int(11 * (1 - k)), int(2.5 * (1 - k))

    def _draw_gorath_attack(surface, boss, x, y):
        progress = getattr(boss, "_gor_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        lunge, lift = _NS_gorath._gor_root_motion(progress)
        lunge = lunge * boss.direction

        _NS_gorath._draw_shadow(surface, x + lunge, y + _NS_gorath.SHADOW_DY)
        _NS_gorath._draw_blood_wisps(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_gorath._draw_gorath_body(surface, x + lunge, y + lift, boss.direction, boss.pulse,
                          "attack", progress)
        _NS_gorath._draw_blade_swing_arc(surface, x + lunge, y + lift, boss.direction, progress)
        _NS_gorath._draw_swing_impact(surface, x + lunge, y + lift, boss.direction, progress)

    def _draw_wisps_gore(surface, cx, cy, phase):
        """Percikan darah kecil melayang - indikator rage persisten."""
        for i in range(6):
            t = (phase * 0.5 + i * 0.17) % 1.0
            px = cx + int(math.sin(phase * 0.8 + i * 2.1) * 26)
            py = cy - int(t * 34)
            alpha = int(160 * (1 - t))
            if alpha > 10:
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                          (px, py), 2)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], alpha),
                          (px, py - 1), 1)


    # ===================================================================
    # BODY RENDERING
    # ===================================================================
    def _draw_gorath_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, rage=False):
        _amp = {"idle": 2, "walk": 4, "attack": 2}.get(action, 2)
        sway = int(math.sin(phase * 0.6) * _amp)

        # Lower floating body (loincloth / robe)
        _NS_gorath._draw_loincloth(surface, cx, cy + 8, phase, sway)

        # Torso
        _NS_gorath._draw_torso(surface, cx, cy - 5, phase, sway)

        # Head with hair (rage -> mata menyala lebih panas)
        _NS_gorath._draw_gorath_head(surface, cx, cy - 26, facing, phase, rage)

        # Shoulders
        _NS_gorath._draw_shoulders(surface, cx, cy - 12, phase)

        # Arms with blades
        if action == "attack":
            _NS_gorath._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_gorath._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Blood dripping from body
        _NS_gorath._draw_body_blood_drips(surface, cx, cy, phase)


    def _draw_loincloth(surface, cx, cy, phase, sway):
        """Floating lower body — tattered loincloth with blood."""
        # Waist belt
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_darkest"], (cx - 15, cy - 4, 30, 6))
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_dark"], (cx - 14, cy - 3, 28, 4))
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_mid"], (cx - 13, cy - 2, 26, 2))

        # Belt buckle - blood symbol
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_darkest"], (cx, cy - 1), 4)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_mid"], (cx, cy - 1), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_bright"], (cx, cy - 2), 2)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"], (cx, cy - 2), 1)

        # Tattered loincloth strips
        for i, offset in enumerate([-11, -6, -1, 5, 10]):
            wave = math.sin(phase * 1.2 + i) * 2
            length = 20 + (i % 2) * 4
            # Shadow
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["shadow_deep"], [
                (cx + offset - 3, cy + 3),
                (cx + offset + 3, cy + 3),
                (cx + offset + 2 + int(wave), cy + length),
                (cx + offset - 2 + int(wave), cy + length),
            ])
            # Main strip
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["leather_darkest"], [
                (cx + offset - 3, cy + 2),
                (cx + offset + 3, cy + 2),
                (cx + offset + 2 + int(wave), cy + length - 1),
                (cx + offset - 2 + int(wave), cy + length - 1),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["leather_dark"], [
                (cx + offset - 2, cy + 3),
                (cx + offset + 2, cy + 3),
                (cx + offset + 1 + int(wave), cy + length - 3),
                (cx + offset - 1 + int(wave), cy + length - 3),
            ])
            # Blood stain on some strips
            if i % 2 == 0:
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_darkest"],
                          (cx + offset, cy + length - 8), 3)
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_dark"],
                          (cx + offset, cy + length - 8), 2)
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_mid"],
                          (cx + offset, cy + length - 9), 1)


    def _draw_torso(surface, cx, cy, phase, sway):
        """Muscular red-skinned torso."""
        # Shadow
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["shadow_deep"], [
            (cx - 14 + 2, cy - 8 + 2), (cx + 14 + 2, cy - 8 + 2),
            (cx + 13 + 2, cy + 14 + 2), (cx + 6 + 2, cy + 18 + 2),
            (cx - 6 + 2, cy + 18 + 2), (cx - 13 + 2, cy + 14 + 2),
        ])

        # Main torso
        torso = [
            (cx - 14, cy - 8), (cx + 14, cy - 8),
            (cx + 13, cy + 14), (cx + 6, cy + 18),
            (cx - 6, cy + 18), (cx - 13, cy + 14),
        ]
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["skin_darkest"], torso)
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["skin_dark"], [
            (cx - 12, cy - 7), (cx + 12, cy - 7),
            (cx + 11, cy + 12), (cx + 5, cy + 16),
            (cx - 5, cy + 16), (cx - 11, cy + 12),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["skin_mid"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5),
            (cx + 8, cy + 10), (cx + 3, cy + 14),
            (cx - 3, cy + 14), (cx - 8, cy + 10),
        ])

        # Chest highlights (pectorals)
        for side in (-1, 1):
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_light"],
                      (cx + side * 5, cy - 2), 4)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_high"],
                      (cx + side * 5 - 1, cy - 3), 2)

        # Abs definition
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_darkest"], (cx, cy + 2), (cx, cy + 14), 1)
        for yoff in (4, 8, 12):
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_darkest"],
                    (cx - 5, cy + yoff), (cx + 5, cy + yoff), 1)

        # Blood stains on chest
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_darkest"], (cx - 4, cy + 8), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_dark"], (cx - 4, cy + 8), 2)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_bright"], (cx + 6, cy + 5), 2)

        # Necklace / trophy cord
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["bone_darkest"], (cx - 8, cy - 6), (cx + 8, cy - 6), 1)
        for i, xoff in enumerate([-6, -2, 2, 6]):
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["bone_dark"], (cx + xoff, cy - 4), 2)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["bone_mid"], (cx + xoff, cy - 4), 1)


    def _draw_shoulders(surface, cx, cy, phase):
        """Muscular shoulders with leather straps."""
        for side in (-1, 1):
            sx = cx + side * 13
            # Shadow
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["shadow_deep"], (sx + 2, cy + 2), 8)
            # Shoulder
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_darkest"], (sx, cy), 8)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_dark"], (sx - side, cy - 1), 7)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_mid"], (sx - side * 2, cy - 2), 5)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_light"], (sx - side * 3, cy - 3), 3)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_high"], (sx - side * 3, cy - 4), 1)

            # Leather shoulder strap
            _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_darkest"], (sx - 5, cy - 3, 10, 6),
                  border_radius=1)
            _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_dark"], (sx - 4, cy - 2, 8, 4))
            _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_mid"], (sx - 3, cy - 1, 6, 1))

            # Blood drip on shoulder
            if side == -1:
                _NS_gorath._draw_blood_streak(surface, sx - 2, cy + 5, sx - 3, cy + 12, 2, 200)


    def _draw_gorath_head(surface, cx, cy, facing, phase, rage=False):
        """Demon head with spiky hair and glowing red eyes.

        Saat `rage` (buff Blood Rage aktif) mata + halo membara
        lebih besar dan berdenyut - indikator status persisten.
        """
        # Neck
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["skin_darkest"], (cx - 4, cy + 8, 8, 6))
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["skin_dark"], (cx - 3, cy + 8, 6, 5))
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["skin_mid"], (cx - 2, cy + 8, 4, 3))

        # Head shadow
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["shadow_deep"], (cx + 2, cy + 2), 12)

        # Base head
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_darkest"], (cx, cy), 11)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_dark"], (cx - 1, cy - 1), 9)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_mid"], (cx - 2, cy - 2), 7)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_light"], (cx - 3, cy - 4), 3)

        # Blood face-paint (Bloodseeker style - across the face)
        face_paint = [
            (cx - 8, cy - 2),
            (cx + 8, cy - 2),
            (cx + 7, cy + 4),
            (cx - 7, cy + 4),
        ]
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_darkest"], face_paint)
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_dark"], [
            (cx - 7, cy - 1), (cx + 7, cy - 1),
            (cx + 6, cy + 3), (cx - 6, cy + 3),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_mid"], [
            (cx - 5, cy), (cx + 5, cy),
            (cx + 4, cy + 2), (cx - 4, cy + 2),
        ])

        # Blood drips from face paint
        for offset in (-5, 0, 5):
            _NS_gorath._draw_blood_streak(surface, cx + offset, cy + 4,
                              cx + offset, cy + 8 + (offset % 2), 1, 200)

        # Glowing red eyes
        eye_pulse = math.sin(phase * (3.0 if rage else 2)) * 0.3 + 0.7
        _er = 3 if rage else 2
        _hr = 6 if rage else 5
        for side in (-1, 1):
            ex = cx + side * 4
            ey = cy + 1
            # Eye socket
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["shadow_deep"], (ex, ey), 3)
            # Glowing eye
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["eye_dark"], (ex, ey), 2)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["eye_bright"], (ex, ey),
                      max(1, int(_er * eye_pulse)))
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["eye_hot"], (ex, ey), 1)
            # Glow halo
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["eye_bright"], int((120 if not rage else 190) * eye_pulse)),
                      (ex, ey), _hr)

        # Mouth - fanged
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["shadow_deep"], (cx - 4, cy + 6, 8, 2))
        # Fangs
        for tooth in (-3, -1, 1, 3):
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["bone_light"], [
                (cx + tooth, cy + 6),
                (cx + tooth + 1, cy + 8),
                (cx + tooth + 2, cy + 6),
            ])

        # SPIKY HAIR (Bloodseeker signature)
        _NS_gorath._draw_spiky_hair(surface, cx, cy - 6, phase)

        # Bone/tribal decorations on head
        for side in (-1, 1):
            # Side bone ornament
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["bone_dark"], [
                (cx + side * 9, cy - 4),
                (cx + side * 13, cy - 2),
                (cx + side * 12, cy + 2),
                (cx + side * 9, cy),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["bone_mid"], [
                (cx + side * 10, cy - 3),
                (cx + side * 12, cy - 1),
                (cx + side * 11, cy + 1),
                (cx + side * 10, cy),
            ])


    def _draw_spiky_hair(surface, cx, cy, phase):
        """Spiky mohawk/hair like Bloodseeker."""
        # Main hair mass
        hair_base = [
            (cx - 10, cy + 4),
            (cx - 8, cy - 2),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 8, cy - 2),
            (cx + 10, cy + 4),
        ]
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["hair_darkest"], hair_base)
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["hair_dark"], [
            (cx - 8, cy + 3),
            (cx - 6, cy - 1),
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 6, cy - 1),
            (cx + 8, cy + 3),
        ])

        # Individual spikes
        spikes = [
            (cx - 9, cy - 2, -13),
            (cx - 5, cy - 5, -10),
            (cx - 2, cy - 6, -14),
            (cx + 2, cy - 6, -13),
            (cx + 5, cy - 5, -11),
            (cx + 9, cy - 2, -14),
        ]
        for sx, sy, tip_y in spikes:
            sway = int(math.sin(phase * 0.5 + sx) * 1)
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (sx + 2, sy),
                (sx + sway, cy + tip_y),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (sx + 1, sy),
                (sx + sway, cy + tip_y + 2),
            ])
            # Highlight
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["hair_mid"],
                    (sx, sy), (sx + sway, cy + tip_y + 3), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms holding blades at rest."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy + 2
            elbow_x = sh_x + side * 10
            elbow_y = cy + 12 + int(sway)
            hand_x = elbow_x + side * 6
            hand_y = elbow_y + 8

            _NS_gorath._draw_arm_segment(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_gorath._draw_arm_segment(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_gorath._draw_hand(surface, hand_x, hand_y)
            # Curved blade
            _NS_gorath._draw_curved_blade(surface, hand_x, hand_y, side, 0.3, phase)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Arms swinging blades in attack."""
        sway = math.sin(phase * 0.7) * 1

        # Back arm (non-active, held ready)
        back_side = -facing
        bs_x = cx + back_side * 12
        bs_y = cy + 2
        be_x = bs_x + back_side * 8
        be_y = cy + 12
        bh_x = be_x + back_side * 6
        bh_y = be_y + 8
        _NS_gorath._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y)
        _NS_gorath._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y)
        _NS_gorath._draw_hand(surface, bh_x, bh_y)
        _NS_gorath._draw_curved_blade(surface, bh_x, bh_y, back_side, 0.4, phase)

        # Front arm - swinging blade
        fs_x = cx + facing * 12
        fs_y = cy + 2

        # Swing arc: wind up → swing → recovery
        if progress < 0.25:
            # Wind up (raise blade)
            t = progress / 0.25
            t = t * t * (3 - 2 * t)  # ease
            arm_angle = -1.5 + 0.3 * t
        elif progress < 0.55:
            # Swing forward (fast)
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3  # ease out
            arm_angle = -1.2 + 2.4 * t
        else:
            # Recovery
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 1.0 * t

        arm_len = 16
        fe_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * arm_len)
        fh_x = fe_x + int(math.cos(arm_angle) * 10) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 10)

        _NS_gorath._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_gorath._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_gorath._draw_hand(surface, fh_x, fh_y)

        # Big curved blade in swinging hand
        blade_angle = arm_angle + math.pi / 4 * facing
        _NS_gorath._draw_curved_blade_angled(surface, fh_x, fh_y, facing, blade_angle,
                                  phase, size=1.3)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Muscular arm segment."""
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 7)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_dark"], (x1, y1), (x2, y2), 5)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_mid"], (x1, y1), (x2, y2), 3)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_light"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_hand(surface, x, y):
        """Clenched fist."""
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["shadow_deep"], (x + 1, y + 1), 5)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_darkest"], (x, y), 4)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_dark"], (x, y), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_mid"], (x - 1, y - 1), 2)
        # Wrist wrap
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_dark"], (x - 4, y - 5, 8, 3),
              border_radius=1)
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_mid"], (x - 3, y - 5, 6, 1))


    def _draw_curved_blade(surface, hx, hy, side, tilt, phase):
        """Curved blade (idle pose)."""
        # Blade extends downward and curves outward
        tip_x = hx + int(side * 8)
        tip_y = hy + 18
        mid_x = hx + int(side * 12)
        mid_y = hy + 10

        # Shadow
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["shadow_deep"], [
            (hx + 1, hy + 3),
            (hx + int(side * 4) + 1, hy + 4),
            (mid_x + 1, mid_y + 1),
            (tip_x + 1, tip_y + 1),
            (hx + int(side * 2) + 1, hy + 8),
        ])

        # Blade curved shape
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_darkest"], [
            (hx, hy + 2),
            (hx + int(side * 5), hy + 3),
            (mid_x, mid_y),
            (tip_x, tip_y),
            (hx + int(side * 1), hy + 7),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_dark"], [
            (hx, hy + 3),
            (hx + int(side * 4), hy + 4),
            (mid_x - int(side), mid_y),
            (tip_x - int(side), tip_y - 1),
            (hx + int(side * 1), hy + 6),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_mid"], [
            (hx + int(side), hy + 4),
            (hx + int(side * 3), hy + 5),
            (mid_x - int(side * 2), mid_y),
            (tip_x - int(side * 2), tip_y - 2),
            (hx + int(side * 1), hy + 5),
        ])

        # Blade highlight (sharp edge)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["metal_light"],
                (hx + int(side * 4), hy + 4),
                (tip_x - int(side), tip_y - 1), 1)

        # Blood on blade edge
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_darkest"], (mid_x, mid_y + 2), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_mid"], (mid_x, mid_y + 2), 2)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_bright"], (mid_x - 1, mid_y + 1), 1)
        # Dripping blood
        _NS_gorath._draw_blood_droplet(surface, mid_x, mid_y + 6, 2, 220)


    def _draw_curved_blade_angled(surface, hx, hy, facing, angle, phase, size=1.0):
        """Larger curved blade for attack swing (angled)."""
        # Blade length varies with size
        blade_len = int(22 * size)
        curve = int(10 * size)

        # Compute blade points along angle
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        perp_x = -dy
        perp_y = dx * facing

        # Base near hand
        base1_x = hx + int(perp_x * 3)
        base1_y = hy + int(perp_y * 3)
        base2_x = hx - int(perp_x * 3)
        base2_y = hy - int(perp_y * 3)

        # Mid curve outward
        mid_x = hx + int(dx * blade_len * 0.55) + int(perp_x * curve)
        mid_y = hy + int(dy * blade_len * 0.55) + int(perp_y * curve)

        # Tip
        tip_x = hx + int(dx * blade_len)
        tip_y = hy + int(dy * blade_len)

        # Shadow
        shadow_pts = [
            (base1_x + 2, base1_y + 2),
            (mid_x + 2, mid_y + 2),
            (tip_x + 2, tip_y + 2),
            (base2_x + 2, base2_y + 2),
        ]
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["shadow_deep"], shadow_pts)

        # Blade
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_darkest"], [
            (base1_x, base1_y), (mid_x, mid_y),
            (tip_x, tip_y), (base2_x, base2_y),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_dark"], [
            (base1_x - int(perp_x), base1_y - int(perp_y)),
            (mid_x - int(perp_x * 0.7), mid_y - int(perp_y * 0.7)),
            (tip_x, tip_y),
            (base2_x, base2_y),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_mid"], [
            (base1_x - int(perp_x * 2), base1_y - int(perp_y * 2)),
            (mid_x - int(perp_x * 1.4), mid_y - int(perp_y * 1.4)),
            (tip_x, tip_y),
        ])

        # Sharp edge highlight
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["metal_shine"],
                (base1_x - int(perp_x * 2), base1_y - int(perp_y * 2)),
                (tip_x, tip_y), 1)

        # Blood covering blade
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_darkest"], (base1_x, base1_y),
                (tip_x, tip_y), 3)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_bright"], (mid_x, mid_y), (tip_x, tip_y), 2)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"], (mid_x, mid_y), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_glow"], (mid_x, mid_y), 1)


    def _draw_body_blood_drips(surface, cx, cy, phase):
        """Blood drips on body."""
        drips = [
            (cx - 8, cy + 5, 0),
            (cx + 6, cy + 8, 0.3),
            (cx - 3, cy - 5, 0.6),
            (cx + 10, cy - 2, 0.9),
        ]
        for dx, dy, offset in drips:
            t = (phase * 0.5 + offset) % 1.0
            drip_y = dy + int(t * 15)
            alpha = int(255 * (1 - t))
            if alpha > 20:
                _NS_gorath._draw_blood_droplet(surface, dx, drip_y, 2, alpha)


    # ===================================================================
    # FLOATING EFFECTS (replaces legs)
    # ===================================================================
    def _draw_blood_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Blood mist wisps rising from below."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = int((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_gorath.PALETTE["blood_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising blood wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_darkest"], alpha), (sx, sy), 5)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], alpha), (sx, sy - 2), 3)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha), (sx, sy - 3), 1)

        # Floating blood droplets
        for i in range(6):
            angle = phase * 0.7 + i * math.pi / 3
            r = 22 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 8)
            _NS_gorath._draw_blood_droplet(surface, sx, sy, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 140 - i * 25)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], alpha),
                          (sx, sy), max(2, 5 - i))
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha // 2),
                          (sx, sy), max(1, 3 - i))


    def _draw_blood_trail(surface, cx, cy, phase, facing):
        """Blood splashes on ground while walking."""
        for i in range(4):
            sx = cx - (i + 1) * 12 * facing
            sy = cy + int(math.cos(phase + i) * 2)
            alpha = max(0, 180 - i * 30)
            _NS_gorath._draw_blood_splatter(surface, sx, sy, max(2, 5 - i),
                                 seed=i, alpha=alpha)


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_gorath.PALETTE["blood_darkest"], 100), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_blood_aura(surface, x, y, phase, active_skill, rage=False):
        """Background aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.5 if active_skill == "q" else (1.3 if rage else 1.0)
        if rage:
            pulse = pulse * 1.15 + 0.05

        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.4 * pulse * strength)
            if alpha > 0:
                _NS_gorath._aacircle(aura, (*_NS_gorath.PALETTE["blood_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ground_blood_pool(surface, x, y, phase, active_skill):
        """Blood pool on ground beneath Gorath."""
        pulse = math.sin(phase * 0.8) * 0.15 + 0.85
        pool = pygame.Surface((130, 40), pygame.SRCALPHA)
        # Base pool
        pygame.draw.ellipse(pool, (*_NS_gorath.PALETTE["blood_darkest"], int(200 * pulse)),
                            (10, 12, 110, 20))
        pygame.draw.ellipse(pool, (*_NS_gorath.PALETTE["blood_dark"], int(180 * pulse)),
                            (20, 15, 90, 14))
        pygame.draw.ellipse(pool, (*_NS_gorath.PALETTE["blood_mid"], int(120 * pulse)),
                            (30, 17, 70, 10))

        # Irregular splashes around
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.1
            px = 65 + int(math.cos(angle) * 50)
            py = 22 + int(math.sin(angle) * 12)
            r = 3 + (i % 3)
            pygame.draw.ellipse(pool, (*_NS_gorath.PALETTE["blood_dark"], 180),
                                (px - r, py - r // 2, r * 2, r))

        surface.blit(pool, (x - 65, y - 20))


    def _draw_blade_swing_arc(surface, x, y, facing, progress):
        """Blade swing motion trail."""
        if progress < 0.28 or progress > 0.75:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.25
        visibility = max(0.0, min(1.0, visibility))

        arc = pygame.Surface((140, 110), pygame.SRCALPHA)
        for i in range(16):
            t = i / 15
            angle = -math.pi * 0.9 + t * math.pi * 1.1
            px = 70 + int(math.cos(angle) * 50) * facing
            py = 55 + int(math.sin(angle) * 38)
            alpha = int((200 - i * 10) * visibility)
            if alpha <= 0:
                continue
            _NS_gorath._aacircle(arc, (*_NS_gorath.PALETTE["blood_darkest"], alpha), (px, py), 8)
            _NS_gorath._aacircle(arc, (*_NS_gorath.PALETTE["blood_mid"], alpha), (px, py), 5)
            _NS_gorath._aacircle(arc, (*_NS_gorath.PALETTE["blood_bright"], alpha), (px, py), 3)
            _NS_gorath._aacircle(arc, (*_NS_gorath.PALETTE["blood_hot"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 70, y - 55))


    def _draw_swing_impact(surface, x, y, facing, progress):
        """Impact splash at end of swing."""
        if progress < 0.45 or progress > 0.85:
            return
        t = (progress - 0.45) / 0.40
        intensity = math.sin(t * math.pi)

        impact_x = x + 35 * facing
        impact_y = y + 3
        alpha = int(230 * intensity)
        radius = int(8 + intensity * 22)

        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], alpha // 2),
                  (impact_x, impact_y), radius + 4)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                  (impact_x, impact_y), radius, 3)

        # Splash droplets
        for i in range(8):
            angle = i * math.pi / 4 + progress * 3
            dx = impact_x + int(math.cos(angle) * radius * 1.2)
            dy = impact_y + int(math.sin(angle) * radius * 0.9)
            _NS_gorath._draw_blood_droplet(surface, dx, dy, 3, alpha)


    # ===================================================================
    # SKILL Q: BLOODRAGE
    # ===================================================================
    def _draw_bloodrage(surface, boss, x, y, timer, phase):
        """Self-buff — flame-like blood aura around Gorath."""
        duration = _NS_gorath.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # envelope: menyala cepat, meredup di 20% terakhir
        env = min(1.0, progress * 5, (1 - progress) * 5 + 0.35)
        pulse = (math.sin(phase * 3) * 0.3 + 0.7) * env

        # Flame tongues rising around body
        for i in range(10):
            angle = phase * 0.5 + i * math.pi * 2 / 10
            base_x = x + int(math.cos(angle) * 20)
            base_y = y + 20 + int(math.sin(angle) * 5)
            flame_h = int(20 + math.sin(phase * 2 + i) * 8)

            # Flame shape
            for h in range(flame_h):
                t = h / max(1, flame_h)
                w = int(4 * (1 - t * 0.7))
                fx = base_x + int(math.sin(phase * 3 + i + t * 5) * 2)
                fy = base_y - h
                alpha = int(200 * pulse * (1 - t * 0.5))
                if t < 0.3:
                    color = _NS_gorath.PALETTE["blood_darkest"]
                elif t < 0.6:
                    color = _NS_gorath.PALETTE["blood_mid"]
                else:
                    color = _NS_gorath.PALETTE["blood_hot"]
                _NS_gorath._aacircle(surface, (*color, alpha), (fx, fy), max(1, w))

        # Inner intense glow around body (SRCALPHA buffer, tidak
        # menutupi karakter seperti blob opaque sebelumnya)
        glow = pygame.Surface((80, 80), pygame.SRCALPHA)
        for radius in range(38, 5, -3):
            alpha = int((38 - radius) * 3.2 * pulse)
            _NS_gorath._aacircle(glow, (*_NS_gorath.PALETTE["blood_dark"], min(180, alpha)),
                      (40, 40), radius)
        surface.blit(glow, (x - 40, y - 40))

        # Rising blood particles
        for i in range(12):
            t = (phase * 0.6 + i * 0.08) % 1.0
            px = x + int(math.cos(i * 2.5 + phase) * 25)
            py = y + 20 - int(t * 40)
            alpha = int(255 * (1 - t) * env)
            if alpha > 0:
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha), (px, py), 2)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], alpha), (px, py), 1)


    # ===================================================================
    # SKILL W: BLOODRITE (ranged rain of blood spikes)
    # ===================================================================
    def _draw_bloodrite_ground(surface, boss, x, y, timer, phase):
        """Warning circle at target location."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / _NS_gorath.SKILL_DUR["w"]))
        fade = min(1.0, (1 - progress) * 4 + 0.15)
        pulse = (math.sin(phase * 3) * 0.3 + 0.7) * fade

        radius = int(30 + progress * 15)
        # Warning ring
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_darkest"], int(200 * pulse)),
                 (tx - radius, ty - radius // 2, radius * 2, radius), 3)
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_mid"], int(150 * pulse)),
                 (tx - radius + 4, ty - radius // 2 + 2,
                  radius * 2 - 8, radius - 4), 2)


    def _draw_bloodrite(surface, boss, x, y, timer, phase):
        """Blood spikes erupting at target."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / _NS_gorath.SKILL_DUR["w"]))

        # Spawn projectile at start
        if progress < 0.1 and not getattr(boss, "_gor_bloodrite_spawned", False):
            for i in range(3):
                offset_x = (i - 1) * 25
                _NS_gorath._spawn_projectile(boss, x, y - 10, tx + offset_x, ty)
            boss._gor_bloodrite_spawned = True
        if progress > 0.4:
            boss._gor_bloodrite_spawned = False

        # After 0.5 progress, spikes erupt
        if progress > 0.4:
            erupt_t = min(1.0, (progress - 0.4) / 0.3)
            radius = 45
            for i in range(12):
                angle = i * math.pi * 2 / 12
                spike_x = tx + int(math.cos(angle) * radius * 0.7)
                spike_y = ty + int(math.sin(angle) * radius * 0.4)
                spike_h = int(20 * erupt_t)

                # Blood spike
                _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_darkest"], [
                    (spike_x - 3, spike_y),
                    (spike_x + 3, spike_y),
                    (spike_x, spike_y - spike_h),
                ])
                _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_dark"], [
                    (spike_x - 2, spike_y),
                    (spike_x + 2, spike_y),
                    (spike_x, spike_y - spike_h + 2),
                ])
                _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_bright"], [
                    (spike_x - 1, spike_y),
                    (spike_x + 1, spike_y),
                    (spike_x, spike_y - spike_h + 4),
                ])
                # Tip highlight
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"],
                          (spike_x, spike_y - spike_h + 2), 1)

            # Central spike (bigger)
            big_h = int(30 * erupt_t)
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_darkest"], [
                (tx - 5, ty),
                (tx + 5, ty),
                (tx, ty - big_h),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_mid"], [
                (tx - 3, ty),
                (tx + 3, ty),
                (tx, ty - big_h + 3),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_bright"], [
                (tx - 1, ty),
                (tx + 1, ty),
                (tx, ty - big_h + 5),
            ])

            # Blood splash particles
            for i in range(8):
                angle = i * math.pi / 4 + phase
                px = tx + int(math.cos(angle) * 30 * erupt_t)
                py = ty + int(math.sin(angle) * 15 * erupt_t) - 5
                _NS_gorath._draw_blood_droplet(surface, px, py, 2, int(255 * erupt_t))


    # ===================================================================
    # SKILL E: THIRST (highlight enemy from distance)
    # ===================================================================
    def _draw_thirst(surface, boss, x, y, timer, phase):
        """Red highlighting beam / marker on target."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / _NS_gorath.SKILL_DUR["e"]))
        # marker memudar di 25% terakhir supaya tidak "klik-hilang"
        fade = min(1.0, (1 - progress) * 4 + 0.2)
        pulse = (math.sin(phase * 2.5) * 0.3 + 0.7) * fade

        # Line of sight beam (blood-red thin line)
        start_x = x + 5 * boss.direction
        start_y = y - 10
        for i in range(3):
            offset = (i - 1) * 2
            alpha = int(80 - i * 20)
            _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                    (start_x, start_y + offset), (tx, ty + offset), 2)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_hot"], 200), (start_x, start_y), (tx, ty), 1)

        # Target marker - crosshair
        marker_r = int(15 + math.sin(phase * 3) * 3)

        # Outer ring
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_darkest"], int(220 * fade)),
                  (tx, ty), marker_r + 2, 3)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], int(230 * pulse)),
                  (tx, ty), marker_r, 2)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], int(255 * pulse)),
                  (tx, ty), marker_r - 3, 1)

        # Cross lines
        for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
            x1 = tx + int(math.cos(angle) * (marker_r - 3))
            y1 = ty + int(math.sin(angle) * (marker_r - 3))
            x2 = tx + int(math.cos(angle) * (marker_r + 6))
            y2 = ty + int(math.sin(angle) * (marker_r + 6))
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_bright"], (x1, y1), (x2, y2), 2)
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_hot"], (x1, y1), (x2, y2), 1)

        # Central dot
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"], (tx, ty), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_light"], (tx, ty), 1)

        # Blood-tracking particles going from Gorath to target
        for i in range(5):
            t = (phase * 0.5 + i * 0.2) % 1.0
            px = int(start_x + (tx - start_x) * t)
            py = int(start_y + (ty - start_y) * t)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], 200), (px, py), 3)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], 240), (px, py), 1)


    # ===================================================================
    # SKILL R: RUPTURE (chained blood damage)
    # ===================================================================
    def _draw_rupture_ground(surface, boss, x, y, timer, phase):
        """Ground blood pool at target."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / _NS_gorath.SKILL_DUR["r"]))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        radius = int(20 + progress * 25)
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_darkest"], int(200 * pulse)),
                 (tx - radius, ty - radius // 3, radius * 2, radius // 1.5))
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_dark"], int(180 * pulse)),
                 (tx - radius + 4, ty - radius // 3 + 2,
                  radius * 2 - 8, radius // 1.5 - 4))


    def _draw_rupture(surface, boss, x, y, timer, phase):
        """Blood chain connecting to target, exploding at target."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / _NS_gorath.SKILL_DUR["r"]))

        start_x = x + 12 * boss.direction
        start_y = y - 10

        # Blood chain line
        segments = 12
        prev = (start_x, start_y)
        for i in range(1, segments + 1):
            t = i / segments
            mx = start_x + (tx - start_x) * t
            my = start_y + (ty - start_y) * t
            # Add wiggle
            wiggle = math.sin(phase * 3 + i) * 3
            mx += wiggle if i < segments else 0
            curr = (int(mx), int(my))

            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_darkest"], prev, curr, 5)
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_mid"], prev, curr, 3)
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_bright"], prev, curr, 1)

            # Blood droplets along chain
            if i % 3 == 0:
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_dark"], curr, 4)
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_bright"], curr, 2)
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"], curr, 1)
            prev = curr

        # Explosion at target
        if progress > 0.4:
            explosion_t = min(1.0, (progress - 0.4) / 0.5)
            radius = int(15 + explosion_t * 30)
            pulse = math.sin(phase * 4) * 0.3 + 0.7

            # Outer blast
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_darkest"], int(200 * pulse)),
                      (tx, ty), radius + 5)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_mid"], int(220 * pulse)),
                      (tx, ty), radius)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], int(240 * pulse)),
                      (tx, ty), max(1, radius - 8))
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], int(255 * pulse)),
                      (tx, ty), max(1, radius - 15))

            # Spikes bursting outward
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sp_len = int(radius * 1.3)
                sx1 = tx + int(math.cos(angle) * radius * 0.5)
                sy1 = ty + int(math.sin(angle) * radius * 0.5)
                sx2 = tx + int(math.cos(angle) * sp_len)
                sy2 = ty + int(math.sin(angle) * sp_len)
                _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_darkest"], (sx1, sy1), (sx2, sy2), 4)
                _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_bright"], (sx1, sy1), (sx2, sy2), 2)
                # Tip droplet
                _NS_gorath._draw_blood_droplet(surface, sx2, sy2, 2, 220)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_gorath.draw_gorath(surface, boss, x, y)


# ====================================================================
# ALCHEMIST
# ====================================================================
class _NS_alchemist:
    """Namespace alchemist - Level 2 Masterwork animation pass (TRUE BOSS).

    Yang diperbaiki di pass ini:
    * SKILL_DUR dikunci sama active_skill_timer AI -> cone Q tidak
      lagi terpotong, pile emas R tumbuh penuh lalu mengempis, bukan
      pop-in di tengah animasi.
    * Goblin rider digambar SEBELUM kepala ogre (dulu dia duduk di
      atas helm karena draw order terbalik) + pose mengangkat botol
      saat ultimate R.
    * Aura Chemical Rage tidak lagi menutupi seluruh karakter.
    * Idle/walk/attack amplitudo dinaikkan, root motion berfase
      (anticipation -> smash -> impact hold -> recovery).
    """

    # q: pose pistol + cone; w: lempar botol; e: buff; r: ultimate.
    SKILL_DUR = {"q": 60, "w": 60, "e": 80, "r": 120}
    SHADOW_DY = 55

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ---------------------------------------------------------------------------
    # HD Palette - Orange ogre / green acid / gold / purple goblin
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Ogre skin - orange/yellow
        "ogre_darkest":   (55,  30,  10),
        "ogre_dark":      (120, 65,  20),
        "ogre_mid":       (185, 115, 40),
        "ogre_light":     (225, 165, 65),
        "ogre_high":      (245, 205, 110),
        "ogre_shine":     (255, 235, 175),

        # Goblin (rider) - purple
        "gob_darkest":    (35,  20,  50),
        "gob_dark":       (75,  45, 105),
        "gob_mid":        (125, 80, 160),
        "gob_light":      (180, 130, 210),
        "gob_high":       (220, 175, 235),

        # Acid green
        "acid_darkest":   (18,  50,  10),
        "acid_dark":      (55, 115,  20),
        "acid_mid":       (110, 190, 30),
        "acid_bright":    (170, 240, 55),
        "acid_hot":       (215, 255, 100),
        "acid_glow":      (240, 255, 170),
        "acid_white":     (250, 255, 220),

        # Gold
        "gold_darkest":   (60,  38,  10),
        "gold_dark":      (135, 90,  15),
        "gold_mid":       (215, 170, 40),
        "gold_light":     (250, 220, 90),
        "gold_shine":     (255, 245, 175),

        # Leather / straps
        "leather_darkest": (22, 14,  8),
        "leather_dark":   (55,  35,  20),
        "leather_mid":    (100, 68,  35),
        "leather_light":  (155, 108, 62),

        # Metal (cleavers, armor)
        "metal_darkest":  (18,  18,  22),
        "metal_dark":     (48,  48,  55),
        "metal_mid":      (95,  95, 105),
        "metal_light":    (160, 158, 170),
        "metal_shine":    (215, 215, 225),
        "metal_edge":     (250, 250, 255),

        # Brass
        "brass_dark":     (85,  55,  15),
        "brass_mid":      (160, 115, 42),
        "brass_light":    (215, 175, 82),
        "brass_shine":    (250, 225, 145),

        # Bottle glass
        "glass_dark":     (25,  60,  20),
        "glass_mid":      (65, 130,  35),
        "glass_light":    (130, 200, 65),
        "glass_shine":    (200, 245, 145),

        # Teeth / tusks
        "bone_dark":      (110, 95,  70),
        "bone_mid":       (185, 170, 130),
        "bone_light":     (235, 225, 190),

        # Eyes
        "eye_dark":       (5,  35,   5),
        "eye_hot":        (255, 240, 100),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   3),
        "white":          (255, 255, 255),
        "red":            (200, 40,  30),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_alchemist._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_alchemist.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_alchemist._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 8
            h = abs(ey - sy) + width * 4 + 8
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_alchemist._clamp(color)
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
        color = _NS_alchemist._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])), width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_alchemist._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, int(rw), int(rh)),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3],
                         (rect[0], rect[1], int(rect[2]), int(rect[3])),
                         border_radius=border_radius)


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


    # ---------------------------------------------------------------------------
    # Acid particle helpers
    # ---------------------------------------------------------------------------
    def _draw_acid_splash(surface, cx, cy, size=8, phase=0, alpha=255):
        """Bubbly acid splash."""
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_darkest"], alpha), (cx, cy), size)
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_dark"], alpha), (cx, cy), max(1, size - 1))
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_mid"], alpha), (cx, cy), max(1, size - 3))
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha), (cx - 1, cy - 1), max(1, size - 4))
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_hot"], alpha), (cx - 1, cy - 2), max(1, size - 6))
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_glow"], min(255, alpha)),
                  (cx - 1, cy - 2), max(1, size - 7))

        # Bubbles
        for i in range(4):
            angle = phase * 0.5 + i * math.pi / 2
            bx = cx + int(math.cos(angle) * (size - 2))
            by = cy + int(math.sin(angle) * (size - 2))
            _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha), (bx, by), 1)


    def _draw_acid_droplet(surface, x, y, size=3, alpha=255):
        """Acid teardrop."""
        _NS_alchemist._poly(surface, (*_NS_alchemist.PALETTE["acid_darkest"], alpha), [
            (x, y - size),
            (x - size, y + size),
            (x + size, y + size),
        ])
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_dark"], alpha), (x, y + size // 2), size)
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha),
                  (x, y + size // 2), max(1, size - 1))
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_glow"], alpha),
                  (x - 1, y + size // 2 - 1), max(1, size - 2))


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class AcidBottle:
        """Arcing acid potion bottle."""
        def __init__(self, sx, sy, tx, ty, arc_height=50):
            self.start_x = float(sx)
            self.start_y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.arc_height = arc_height
            self.alive = True
            self.age = 0
            self.max_age = 40
            self.x = float(sx)
            self.y = float(sy)
            self.spin = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.35
            t = self.age / self.max_age
            if t >= 1.0:
                self.alive = False
                self.x, self.y = self.tx, self.ty
                return
            self.x = self.start_x + (self.tx - self.start_x) * t
            arc = -4 * self.arc_height * t * (1 - t)
            self.y = self.start_y + (self.ty - self.start_y) * t + arc
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 8:
                self.trail.pop(0)

        def draw(self, surface, phase):
            # Trail droplets
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(70 + i * 15)
                _NS_alchemist._draw_acid_droplet(surface, tx, ty, max(1, 3 - (len(self.trail) - i)), alpha)

            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_alchemist._draw_bottle_spinning(surface, px, py, self.spin)


    class AcidPatch:
        """Persistent acid puddle."""
        def __init__(self, x, y, radius=30, life=90):
            self.x = x
            self.y = y
            self.radius = radius
            self.age = 0
            self.life = life
            self.alive = True

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            t = self.age / self.life
            if t < 0.1:
                r = int(self.radius * (t / 0.1))
                alpha = int(255 * (t / 0.1))
            elif t < 0.7:
                r = self.radius
                alpha = 255
            else:
                r = self.radius
                alpha = int(255 * (1 - (t - 0.7) / 0.3))
            if r <= 0 or alpha <= 0:
                return

            # Ground puddle
            _NS_alchemist._ellipse(surface, (*_NS_alchemist.PALETTE["acid_darkest"], int(alpha * 0.9)),
                     (self.x - r, self.y - r // 3, r * 2, r // 1.5))
            _NS_alchemist._ellipse(surface, (*_NS_alchemist.PALETTE["acid_dark"], int(alpha * 0.85)),
                     (self.x - r + 3, self.y - r // 3 + 2,
                      r * 2 - 6, r // 1.5 - 4))
            _NS_alchemist._ellipse(surface, (*_NS_alchemist.PALETTE["acid_mid"], int(alpha * 0.7)),
                     (self.x - r + 6, self.y - r // 3 + 4,
                      r * 2 - 12, r // 1.5 - 8))
            # Bright puddle center
            _NS_alchemist._ellipse(surface, (*_NS_alchemist.PALETTE["acid_bright"], int(alpha * 0.5)),
                     (self.x - r + 10, self.y - r // 4 + 2,
                      r * 2 - 20, r // 3))

            # Bubbles
            for i in range(6):
                angle = phase * 0.5 + i * math.pi / 3
                bx = self.x + int(math.cos(angle) * (r - 5))
                by = self.y + int(math.sin(angle) * (r // 3 - 2))
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha), (bx, by), 2)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_glow"], alpha), (bx, by - 1), 1)

            # Rising vapor wisps
            for i in range(3):
                wt = (phase * 0.6 + i * 0.33) % 1.0
                wx = self.x - r // 2 + i * (r // 3) + int(math.sin(phase + i) * 3)
                wy = self.y - int(wt * 20)
                wa = int(alpha * (1 - wt) * 0.6)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_mid"], wa), (wx, wy), 3)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], wa), (wx, wy), 2)


    def _draw_bottle_spinning(surface, cx, cy, spin):
        """A potion bottle spinning through air."""
        # Rotate simple bottle shape around center
        # Bottle: cork on top, body below
        dx = math.cos(spin)
        dy = math.sin(spin)
        perp_x = -dy
        perp_y = dx

        # Body corners
        body_h = 8
        body_w = 5

        p1 = (cx + int(dx * body_h + perp_x * body_w),
              cy + int(dy * body_h + perp_y * body_w))
        p2 = (cx + int(dx * body_h - perp_x * body_w),
              cy + int(dy * body_h - perp_y * body_w))
        p3 = (cx + int(-dx * body_h - perp_x * body_w),
              cy + int(-dy * body_h - perp_y * body_w))
        p4 = (cx + int(-dx * body_h + perp_x * body_w),
              cy + int(-dy * body_h + perp_y * body_w))

        # Shadow
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in [p1, p2, p3, p4]])

        # Bottle body (green glass)
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["glass_dark"], [p1, p2, p3, p4])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["glass_mid"], [
            (cx + int(dx * (body_h - 1) + perp_x * (body_w - 1)),
             cy + int(dy * (body_h - 1) + perp_y * (body_w - 1))),
            (cx + int(dx * (body_h - 1) - perp_x * (body_w - 1)),
             cy + int(dy * (body_h - 1) - perp_y * (body_w - 1))),
            (cx + int(-dx * (body_h - 1) - perp_x * (body_w - 2)),
             cy + int(-dy * (body_h - 1) - perp_y * (body_w - 2))),
            (cx + int(-dx * (body_h - 1) + perp_x * (body_w - 2)),
             cy + int(-dy * (body_h - 1) + perp_y * (body_w - 2))),
        ])

        # Cork on top
        cork_x = cx + int(dx * (body_h + 3))
        cork_y = cy + int(dy * (body_h + 3))
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["leather_dark"], (cork_x, cork_y), 3)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["leather_mid"], (cork_x, cork_y), 2)

        # Bright acid glow inside
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_bright"], (cx, cy), 3)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_hot"], (cx, cy), 2)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_glow"], (cx, cy), 1)

        # Outer glow
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], 120), (cx, cy), 10)


    # ---------------------------------------------------------------------------
    # State
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_alch_last_x"):
            boss._alch_last_x = boss.x
            boss._alch_last_y = boss.y
            return False
        dx = abs(boss.x - boss._alch_last_x)
        dy = abs(boss.y - boss._alch_last_y)
        boss._alch_last_x = boss.x
        boss._alch_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_alch_prev_timer", 0))
        active = bool(getattr(boss, "_alch_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._alch_attack_active = True
            boss._alch_attack_frame = 0
            active = True
        elif active:
            boss._alch_attack_frame = int(getattr(boss, "_alch_attack_frame", 0)) + 1
            if boss._alch_attack_frame > cooldown:
                boss._alch_attack_active = False
                boss._alch_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._alch_attack_active = False
            boss._alch_attack_frame = 0
            active = False

        boss._alch_prev_timer = timer
        boss._alch_attack_progress = (
            min(1.0, getattr(boss, "_alch_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_alch_projectiles"):
            boss._alch_projectiles = []
        if not hasattr(boss, "_alch_patches"):
            boss._alch_patches = []
        if not hasattr(boss, "_alch_coins"):
            boss._alch_coins = []

        for proj in boss._alch_projectiles:
            proj.update()
            if not proj.alive and proj.age > 0:
                boss._alch_patches.append(
                    _NS_alchemist.AcidPatch(int(proj.tx), int(proj.ty), radius=32, life=100))
                proj.age = -1
            if proj.age >= 0:
                proj.draw(surface, phase)
        boss._alch_projectiles = [p for p in boss._alch_projectiles if p.alive]

        for patch in boss._alch_patches:
            patch.update()
        boss._alch_patches = [p for p in boss._alch_patches if p.alive]


    def _spawn_acid_bottle(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_alch_projectiles"):
            boss._alch_projectiles = []
        boss._alch_projectiles.append(_NS_alchemist.AcidBottle(sx, sy, tx, ty))


    def _spawn_coin(boss, x, y):
        if not hasattr(boss, "_alch_coins"):
            boss._alch_coins = []
        boss._alch_coins.append({
            "x": x, "y": y - 5,
            "vx": (hash((x, y, len(boss._alch_coins))) % 40 - 20) / 10.0,
            "vy": -3 - (hash((x, y, "vy")) % 20) / 10.0,
            "life": 60,
            "age": 0,
            "spin": 0.0,
            "spin_speed": 0.3 + (hash((x, y, "s")) % 30) / 100.0,
        })


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_alchemist(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_alchemist._detect_moving(boss)
        _NS_alchemist._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_alch_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # State buff persisten (Chemical Rage berjalan 360 frame,
        # FX cast hanya 80 -> uap + mata hijau tetap tampil)
        rage = bool(getattr(boss, "rage_active", False))

        # BG aura
        _NS_alchemist._draw_alch_aura(surface, x, y, pulse, active_skill, rage)

        # Ground effects
        if hasattr(boss, "_alch_patches"):
            for patch in boss._alch_patches:
                patch.draw(surface, pulse)

        _NS_alchemist._draw_ground_runes(surface, x, y + 45, pulse, active_skill)

        if active_skill == "r":
            _NS_alchemist._draw_greevil_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_alchemist._draw_chem_rage_ground(surface, boss, x, y, skill_timer, pulse)

        # Character
        if attacking:
            _NS_alchemist._draw_alch_attack(surface, boss, x, y)
        elif active_skill == "q":
            _NS_alchemist._draw_alch_qcast(surface, boss, x, y, skill_timer)
        elif active_skill == "w":
            _NS_alchemist._draw_alch_wcast(surface, boss, x, y, skill_timer)
        elif moving:
            _NS_alchemist._draw_alch_walk(surface, boss, x, y, rage)
        else:
            _NS_alchemist._draw_alch_idle(surface, boss, x, y, rage)

        if rage:
            # uap asam mengepul dari punggung selama rage
            _NS_alchemist._draw_rage_steam(surface, x, y, pulse)

        # Projectiles
        _NS_alchemist._manage_projectiles(boss, surface, pulse)

        # Foreground
        if active_skill == "q":
            _NS_alchemist._draw_acid_spray(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_alchemist._draw_chem_rage_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_alchemist._draw_greevil_foreground(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_alch_idle(surface, boss, x, y, rage=False):
        bob = int(math.sin(boss.pulse * 0.7) * 3.5)
        _NS_alchemist._draw_shadow(surface, x, y + _NS_alchemist.SHADOW_DY)
        _NS_alchemist._draw_alch_wisps(surface, x, y + 40, boss.pulse, intense=rage)
        _NS_alchemist._draw_alch_full(surface, x, y + bob, boss.direction, boss.pulse,
                                      "idle", rage=rage,
                                      cheer=getattr(boss, "active_skill", None) == "r")

    def _draw_alch_walk(surface, boss, x, y, rage=False):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 5)
        sway = int(math.sin(phase * 0.5) * 3)
        _NS_alchemist._draw_shadow(surface, x + sway, y + _NS_alchemist.SHADOW_DY)
        _NS_alchemist._draw_alch_wisps(surface, x + sway, y + 40, phase, trail=True,
                         facing=boss.direction, intense=rage)
        _NS_alchemist._draw_alch_full(surface, x + sway, y - bob, boss.direction, phase,
                                      "walk", rage=rage,
                                      cheer=getattr(boss, "active_skill", None) == "r")

    def _alch_root_motion(progress):
        """Ogre menumpu -> menghantam -> tanam -> angkat lagi."""
        if progress < 0.25:
            k = progress / 0.25
            return int(-5 * k), -int(3.5 * k)
        if progress < 0.55:
            k = (progress - 0.25) / 0.30
            e = 1 - (1 - k) ** 2
            return int(-5 + 17 * e), int(-3.5 + 6.5 * e)
        if progress < 0.70:
            return 12, 3 + int(math.sin(progress * 42) * 1.5)
        k = (progress - 0.70) / 0.30
        return int(12 * (1 - k)), int(3 * (1 - k))

    def _draw_alch_attack(surface, boss, x, y):
        progress = getattr(boss, "_alch_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        rage = bool(getattr(boss, "rage_active", False))
        lunge, lift = _NS_alchemist._alch_root_motion(progress)
        lunge = lunge * boss.direction

        _NS_alchemist._draw_shadow(surface, x + lunge, y + _NS_alchemist.SHADOW_DY)
        _NS_alchemist._draw_alch_wisps(surface, x + lunge, y + 40, boss.pulse, intense=True)
        _NS_alchemist._draw_alch_full(surface, x + lunge, y + lift, boss.direction, boss.pulse,
                        "attack", progress, rage=rage,
                        cheer=getattr(boss, "active_skill", None) == "r")
        _NS_alchemist._draw_cleaver_swing_arc(surface, x + lunge, y + lift, boss.direction, progress)
        _NS_alchemist._draw_swing_impact(surface, x + lunge, y + lift, boss.direction, progress)

    def _draw_alch_qcast(surface, boss, x, y, timer):
        duration = _NS_alchemist.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        rage = bool(getattr(boss, "rage_active", False))
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        # recoil mundur dua ketukan lalu settle
        recoil = int(math.sin(min(1.0, progress * 1.4) * math.pi * 2) * 3) * -boss.direction
        _NS_alchemist._draw_shadow(surface, x + recoil, y + _NS_alchemist.SHADOW_DY)
        _NS_alchemist._draw_alch_wisps(surface, x + recoil, y + 40, boss.pulse, intense=True)
        _NS_alchemist._draw_alch_full(surface, x + recoil, y + bob, boss.direction, boss.pulse,
                        "q_cast", progress, rage=rage)

    def _draw_alch_wcast(surface, boss, x, y, timer):
        duration = _NS_alchemist.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        rage = bool(getattr(boss, "rage_active", False))
        # wind-up botol: condong ke belakang (0-0.35), lempar (0.35-0.45), follow-through
        if progress < 0.35:
            k = progress / 0.35
            lean = int(-3 * k)
            lift = -int(2 * k)
        elif progress < 0.5:
            k = (progress - 0.35) / 0.15
            lean = int(-3 + 9 * k)
            lift = int(-2 + 3 * k)
        else:
            k = min(1.0, (progress - 0.5) / 0.4)
            lean = int(6 * (1 - k))
            lift = int(1 - k)
        d = boss.direction
        _NS_alchemist._draw_shadow(surface, x + lean * d, y + _NS_alchemist.SHADOW_DY)
        _NS_alchemist._draw_alch_wisps(surface, x + lean * d, y + 40, boss.pulse)
        _NS_alchemist._draw_alch_full(surface, x + lean * d, y + lift, d, boss.pulse,
                        "w_cast", progress, rage=rage)

        # Spawn bottle at right moment - keluar dari tangan goblin
        if 0.35 < progress < 0.45 and not getattr(boss, "_alch_wcast_spawned", False):
            tx, ty = _NS_alchemist._target_position(boss, x, y)
            sx = x - 14 * d + lean * d
            sy = y - 42 + lift
            _NS_alchemist._spawn_acid_bottle(boss, sx, sy, tx, ty)
            boss._alch_wcast_spawned = True
        if progress > 0.7:
            boss._alch_wcast_spawned = False

    def _draw_rage_steam(surface, x, y, phase):
        """Uap asam keluar dari backpack selama buff Chemical Rage."""
        for i in range(5):
            t = (phase * 0.45 + i * 0.2) % 1.0
            px = x - 12 * (1 - t * 0.4) + int(math.sin(phase + i * 1.9) * 4)
            py = y - 14 - int(t * 34)
            alpha = int(120 * (1 - t))
            if alpha > 8:
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_mid"], alpha),
                          (int(px), int(py)), 3)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha),
                          (int(px), int(py) - 1), 2)


    # ===================================================================
    # FULL COMPOSITE - Ogre + Goblin rider
    # ===================================================================
    def _draw_alch_full(surface, cx, cy, facing, phase, action,
                        attack_progress=0, rage=False, cheer=False):
        """Komposit Ogre + Goblin.

        Draw order DIPERBAIKI: dulu rider digambar paling akhir
        sehingga kepalanya menindih helm ogre (terlihat "duduk di
        atas kepala"). Sekarang: lower -> torso -> backpack ->
        goblin (di belakang kepala) -> kepala ogre -> lengan.
        """
        # Goblin menunggang sedikit menunduk mengikuti napas ogre
        ride_bob = int(math.sin(phase * 0.7) * 1.5)

        # Ogre body first
        _NS_alchemist._draw_ogre_lower(surface, cx, cy + 8, phase)
        _NS_alchemist._draw_ogre_torso(surface, cx, cy - 8, facing, phase, action, attack_progress)

        # Backpack potions on ogre's back
        _NS_alchemist._draw_backpack(surface, cx - 12 * facing, cy - 10, phase)

        # Goblin rider - DI BELAKANG kepala ogre, menempel di bahu
        _NS_alchemist._draw_goblin_rider(surface, cx - 9 * facing,
                                         cy - 24 + ride_bob, facing, phase,
                                         action, attack_progress,
                                         rage=rage, cheer=cheer)

        # Ogre head (menindih goblin => kedalaman benar)
        _NS_alchemist._draw_ogre_head(surface, cx + 3 * facing, cy - 20, facing, phase, action,
                                      rage)

        # Ogre arms + cleavers
        if action == "attack":
            _NS_alchemist._draw_ogre_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        elif action in ("q_cast", "w_cast"):
            _NS_alchemist._draw_ogre_cast_arms(surface, cx, cy - 8, facing, phase, action, attack_progress)
        else:
            _NS_alchemist._draw_ogre_idle_arms(surface, cx, cy - 8, facing, phase)


    def _draw_ogre_lower(surface, cx, cy, phase):
        """Floating lower body — belt + tattered leather skirt."""
        # Belt
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_darkest"], (cx - 22, cy - 4, 44, 8))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_dark"], (cx - 20, cy - 3, 40, 6))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_mid"], (cx - 18, cy - 2, 36, 3))

        # Big brass buckle
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_dark"], (cx - 6, cy - 4, 12, 8), border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_mid"], (cx - 5, cy - 3, 10, 6))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_light"], (cx - 4, cy - 3, 8, 2))
        # Alchemist symbol on buckle (small $ or R for Alchemist)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["gold_shine"], (cx, cy), 2)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["gold_light"], (cx, cy), 1)

        # Leather skirt strips
        for i, offset in enumerate([-16, -8, 0, 8, 16]):
            wave = math.sin(phase * 1.0 + i) * 2
            length = 22 + (i % 2) * 4
            _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["shadow_deep"], [
                (cx + offset - 4, cy + 3),
                (cx + offset + 4, cy + 3),
                (cx + offset + 3 + int(wave), cy + length),
                (cx + offset - 3 + int(wave), cy + length),
            ])
            _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["leather_darkest"], [
                (cx + offset - 4, cy + 2),
                (cx + offset + 4, cy + 2),
                (cx + offset + 3 + int(wave), cy + length - 1),
                (cx + offset - 3 + int(wave), cy + length - 1),
            ])
            _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["leather_dark"], [
                (cx + offset - 3, cy + 3),
                (cx + offset + 3, cy + 3),
                (cx + offset + 2 + int(wave), cy + length - 3),
                (cx + offset - 2 + int(wave), cy + length - 3),
            ])
            _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["leather_mid"], [
                (cx + offset - 2, cy + 4),
                (cx + offset + 2, cy + 4),
                (cx + offset + 1 + int(wave), cy + length - 5),
                (cx + offset - 1 + int(wave), cy + length - 5),
            ])


    def _draw_ogre_torso(surface, cx, cy, facing, phase, action, attack_progress):
        """Massive orange ogre torso."""
        # Body sway
        sway = int(math.sin(phase * 0.5) * 1)

        # Shadow
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["shadow_deep"], [
            (cx - 22 + 2, cy - 10 + 2), (cx + 22 + 2, cy - 10 + 2),
            (cx + 20 + 2, cy + 18 + 2), (cx - 20 + 2, cy + 18 + 2),
        ])

        # Main body (large trapezoid)
        body = [
            (cx - 22, cy - 10),
            (cx + 22, cy - 10),
            (cx + 20, cy + 18),
            (cx - 20, cy + 18),
        ]
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["ogre_darkest"], body)
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["ogre_dark"], [
            (cx - 20, cy - 8), (cx + 20, cy - 8),
            (cx + 18, cy + 16), (cx - 18, cy + 16),
        ])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["ogre_mid"], [
            (cx - 17, cy - 5), (cx + 17, cy - 5),
            (cx + 15, cy + 13), (cx - 15, cy + 13),
        ])

        # Belly bulge (round)
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["ogre_light"], (cx - 14, cy + 2, 28, 14))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["ogre_high"], (cx - 10, cy + 4, 20, 8))

        # Chest muscle highlights
        for side in (-1, 1):
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_light"],
                      (cx + side * 8, cy - 3), 5)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_high"],
                      (cx + side * 8 - 1, cy - 5), 2)

        # Belly button
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_darkest"], (cx, cy + 8), 2)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_dark"], (cx, cy + 8), 1)

        # Dark spots on skin
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_darkest"], (cx - 8, cy + 12), 2)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_darkest"], (cx + 10, cy - 2), 1)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_darkest"], (cx + 6, cy + 10), 1)

        # Metal shoulder armor
        for side in (-1, 1):
            sx = cx + side * 18
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (sx + 2, cy - 8 + 2), 10)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["metal_darkest"], (sx, cy - 8), 10)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["metal_dark"], (sx - side, cy - 9), 8)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["metal_mid"], (sx - side * 2, cy - 10), 6)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["metal_light"], (sx - side * 3, cy - 12), 3)
            # Rivets
            for i in range(3):
                angle = i * math.pi * 2 / 3
                rx = sx + int(math.cos(angle) * 5)
                ry = cy - 8 + int(math.sin(angle) * 5)
                _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["brass_mid"], (rx, ry), 1)


    def _draw_ogre_head(surface, cx, cy, facing, phase, action, rage=False):
        """Ogre head with tusks and helmet.

        `rage` (buff Chemical Rage) -> mata hijau menyala + asap
        hidung, indikator status yang bertahan sepanjang buff.
        """
        # Neck (thick)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["ogre_darkest"], (cx - 7, cy + 7, 14, 5))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["ogre_dark"], (cx - 6, cy + 7, 12, 4))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["ogre_mid"], (cx - 5, cy + 7, 10, 2))

        # Head base (large)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx + 2, cy + 2), 13)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_darkest"], (cx, cy), 12)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_dark"], (cx - 1, cy - 1), 10)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_mid"], (cx - 2, cy - 2), 8)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_light"], (cx - 3, cy - 3), 4)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_high"], (cx - 3, cy - 5), 2)

        # Small angry eyes
        is_rage = rage or action == "e"  # if E active glow more
        _epulse = math.sin(phase * 3) * 0.3 + 0.7 if is_rage else 1.0
        for side in (-1, 1):
            ex = cx + side * 4
            ey = cy - 1
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (ex, ey), 2)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["eye_dark"], (ex, ey), 2)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["eye_hot"], (ex, ey),
                    2 if is_rage else 1)
            if is_rage:
                # halo asam berdenyut + percik api hijau kecil
                _NS_alchemist._aacircle(surface,
                        (*_NS_alchemist.PALETTE["acid_bright"], int(150 * _epulse)),
                        (ex, ey), 3)
                _NS_alchemist._aacircle(surface,
                        (*_NS_alchemist.PALETTE["acid_hot"], int(200 * _epulse)),
                        (ex, ey), 1)
            # Angry brow
            _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["ogre_darkest"],
                    (ex - 2, ey - 3), (ex + 2, ey - 2), 2)
        if is_rage:
            # uap nostril saat rage
            for side in (-1, 1):
                t = (phase * 0.6 + side * 0.3) % 1.0
                _NS_alchemist._aacircle(surface,
                        (*_NS_alchemist.PALETTE["acid_mid"], int(110 * (1 - t))),
                        (cx + side * 2 + int(math.sin(phase + side) * 2),
                         int(cy + 4 - t * 10)), 2)

        # Nose (piggy snout)
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["ogre_dark"], (cx - 4, cy + 2, 8, 5))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["ogre_mid"], (cx - 3, cy + 2, 6, 4))
        # Nostrils
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx - 1, cy + 4), 1)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx + 1, cy + 4), 1)

        # Big lower lip
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["ogre_dark"], (cx - 6, cy + 6, 12, 4))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["ogre_mid"], (cx - 4, cy + 6, 8, 3))

        # Tusks (Alchemist signature - two big lower fangs)
        for side in (-1, 1):
            tusk_x = cx + side * 4
            tusk_y = cy + 6
            _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["shadow_deep"], [
                (tusk_x + 1, tusk_y + 1),
                (tusk_x - side * 2, tusk_y + 5),
                (tusk_x + side + 1, tusk_y + 7),
                (tusk_x + side * 2, tusk_y + 5),
            ])
            _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["bone_dark"], [
                (tusk_x, tusk_y),
                (tusk_x - side * 2, tusk_y + 5),
                (tusk_x + side, tusk_y + 6),
                (tusk_x + side * 2, tusk_y + 5),
            ])
            _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["bone_mid"], [
                (tusk_x, tusk_y + 1),
                (tusk_x - side, tusk_y + 4),
                (tusk_x + side, tusk_y + 5),
                (tusk_x + side * 2, tusk_y + 4),
            ])
            _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["bone_light"], [
                (tusk_x, tusk_y + 2),
                (tusk_x, tusk_y + 4),
                (tusk_x + side, tusk_y + 4),
            ])

        # Metal helmet cap on top
        helm = [
            (cx - 10, cy - 2),
            (cx - 8, cy - 10),
            (cx - 2, cy - 12),
            (cx + 4, cy - 12),
            (cx + 8, cy - 8),
            (cx + 10, cy - 2),
        ]
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in helm])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_darkest"], helm)
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_dark"], [
            (cx - 9, cy - 3),
            (cx - 7, cy - 9),
            (cx - 2, cy - 11),
            (cx + 4, cy - 11),
            (cx + 7, cy - 8),
            (cx + 9, cy - 3),
        ])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_mid"], [
            (cx - 7, cy - 4),
            (cx - 5, cy - 8),
            (cx + 4, cy - 10),
            (cx + 7, cy - 7),
        ])
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["metal_light"],
                (cx - 4, cy - 9), (cx + 3, cy - 10), 1)

        # Small horn spike on top
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_darkest"], [
            (cx - 1, cy - 12),
            (cx + 2, cy - 12),
            (cx, cy - 17),
        ])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_mid"], [
            (cx, cy - 12),
            (cx + 1, cy - 12),
            (cx, cy - 15),
        ])

        # Rivets on helmet
        for rx in (-5, 0, 5):
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["brass_mid"], (cx + rx, cy - 4), 1)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["brass_shine"], (cx + rx, cy - 4), 1)


    def _draw_backpack(surface, cx, cy, phase):
        """Wooden barrel + potion bottles on back."""
        # Barrel
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx - 6 + 1, cy - 8 + 1, 12, 18),
              border_radius=2)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_darkest"], (cx - 6, cy - 8, 12, 18),
              border_radius=2)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_dark"], (cx - 5, cy - 7, 10, 16),
              border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_mid"], (cx - 4, cy - 7, 8, 14))

        # Barrel hoops (metal bands)
        for hoop_y in (cy - 6, cy, cy + 6):
            _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["metal_darkest"], (cx - 6, hoop_y, 12, 2))
            _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["metal_mid"], (cx - 6, hoop_y, 12, 1))

        # Wood plank lines
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["leather_darkest"],
                (cx - 2, cy - 7), (cx - 2, cy + 9), 1)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["leather_darkest"],
                (cx + 1, cy - 7), (cx + 1, cy + 9), 1)


    def _draw_ogre_idle_arms(surface, cx, cy, facing, phase):
        """Both arms holding cleavers relaxed."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            sh_x = cx + side * 18
            sh_y = cy + 2
            elbow_x = sh_x + side * 12
            elbow_y = cy + 14 + int(sway)
            hand_x = elbow_x + side * 5
            hand_y = elbow_y + 12

            _NS_alchemist._draw_ogre_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_alchemist._draw_ogre_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_alchemist._draw_hand(surface, hand_x, hand_y)
            _NS_alchemist._draw_cleaver_held(surface, hand_x, hand_y, side, phase)


    def _draw_ogre_cast_arms(surface, cx, cy, facing, phase, action, progress):
        """Arms during Q or W cast — back arm holds cleaver, front arm holds tank hose or potion."""
        # Back arm holding cleaver
        back_side = -facing
        bs_x = cx + back_side * 18
        bs_y = cy + 2
        be_x = bs_x + back_side * 10
        be_y = cy + 14
        bh_x = be_x + back_side * 4
        bh_y = be_y + 12
        _NS_alchemist._draw_ogre_arm(surface, bs_x, bs_y, be_x, be_y)
        _NS_alchemist._draw_ogre_arm(surface, be_x, be_y, bh_x, bh_y)
        _NS_alchemist._draw_hand(surface, bh_x, bh_y)
        _NS_alchemist._draw_cleaver_held(surface, bh_x, bh_y, back_side, phase)

        # Front arm - extended forward
        fs_x = cx + facing * 18
        fs_y = cy + 2
        fe_x = fs_x + facing * 12
        fe_y = cy + 8
        fh_x = fe_x + facing * 8
        fh_y = fe_y + 2
        _NS_alchemist._draw_ogre_arm(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_alchemist._draw_ogre_arm(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_alchemist._draw_hand(surface, fh_x, fh_y)

        if action == "q_cast":
            # Acid gun / hose held forward
            _NS_alchemist._draw_acid_gun(surface, fh_x, fh_y, facing, phase, firing=progress > 0.2)


    def _draw_ogre_attack_arms(surface, cx, cy, facing, phase, progress):
        """Both arms swing cleavers overhead."""
        # Back arm — cleaver at side
        back_side = -facing
        bs_x = cx + back_side * 18
        bs_y = cy + 2
        be_x = bs_x + back_side * 8
        be_y = cy + 12
        bh_x = be_x + back_side * 4
        bh_y = be_y + 10
        _NS_alchemist._draw_ogre_arm(surface, bs_x, bs_y, be_x, be_y)
        _NS_alchemist._draw_ogre_arm(surface, be_x, be_y, bh_x, bh_y)
        _NS_alchemist._draw_hand(surface, bh_x, bh_y)
        _NS_alchemist._draw_cleaver_held(surface, bh_x, bh_y, back_side, phase)

        # Front arm swings cleaver
        fs_x = cx + facing * 18
        fs_y = cy + 2

        if progress < 0.25:
            t = progress / 0.25
            t = t * t * (3 - 2 * t)
            arm_angle = -1.4 + 0.3 * t
        elif progress < 0.55:
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3
            arm_angle = -1.1 + 2.3 * t
        else:
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 0.9 * t

        arm_len = 20
        fh_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fh_y = fs_y + int(math.sin(arm_angle) * arm_len)
        elbow_x = fs_x + int(math.cos(arm_angle) * arm_len * 0.55) * facing
        elbow_y = fs_y + int(math.sin(arm_angle) * arm_len * 0.55)

        _NS_alchemist._draw_ogre_arm(surface, fs_x, fs_y, elbow_x, elbow_y)
        _NS_alchemist._draw_ogre_arm(surface, elbow_x, elbow_y, fh_x, fh_y)
        _NS_alchemist._draw_hand(surface, fh_x, fh_y)

        # Big cleaver in motion
        blade_angle = arm_angle + math.pi / 4 * facing
        _NS_alchemist._draw_cleaver_swinging(surface, fh_x, fh_y, facing, blade_angle)


    def _draw_ogre_arm(surface, x1, y1, x2, y2):
        """Massive muscular ogre arm."""
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 11)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["ogre_darkest"], (x1, y1), (x2, y2), 10)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["ogre_dark"], (x1, y1), (x2, y2), 8)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["ogre_mid"], (x1, y1), (x2, y2), 5)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["ogre_light"], (x1 - 1, y1), (x2 - 1, y2), 2)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["ogre_high"], (x1 - 2, y1), (x2 - 2, y2), 1)


    def _draw_hand(surface, x, y):
        """Ogre fist."""
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (x + 1, y + 1), 6)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_darkest"], (x, y), 5)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_dark"], (x, y), 4)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_mid"], (x - 1, y - 1), 3)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_light"], (x - 1, y - 2), 1)
        # Leather wrist wrap
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_darkest"], (x - 5, y - 7, 10, 4),
              border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_dark"], (x - 4, y - 7, 8, 3))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_mid"], (x - 4, y - 6, 8, 1))


    def _draw_cleaver_held(surface, hx, hy, side, phase):
        """Cleaver held at rest — big rectangular blade with hook."""
        # Handle
        handle_len = 10
        handle_bot_x = hx + side * 2
        handle_bot_y = hy + handle_len

        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (handle_bot_x + 1, handle_bot_y + 1), 5)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["leather_darkest"],
                (hx, hy), (handle_bot_x, handle_bot_y), 4)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["leather_dark"],
                (hx, hy), (handle_bot_x, handle_bot_y), 3)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["leather_mid"],
                (hx, hy), (handle_bot_x, handle_bot_y), 1)

        # Cleaver blade (big rectangle)
        bx = hx - side * 1
        by = hy - 3
        bw = 14  # blade width
        bh = 12  # blade height

        # Shadow
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["shadow_deep"], [
            (bx + 1, by + 1),
            (bx + side * bw + 1, by + 1),
            (bx + side * (bw + 3) + 1, by + bh // 2 + 1),
            (bx + side * bw + 1, by + bh + 1),
            (bx - side * 2 + 1, by + bh + 1),
        ])

        # Blade shape
        blade_pts = [
            (bx, by),
            (bx + side * bw, by),
            (bx + side * (bw + 3), by + bh // 2),
            (bx + side * bw, by + bh),
            (bx - side * 2, by + bh),
        ]
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_darkest"], blade_pts)
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_dark"], [
            (bx + side, by + 1),
            (bx + side * (bw - 1), by + 1),
            (bx + side * (bw + 2), by + bh // 2),
            (bx + side * (bw - 1), by + bh - 1),
            (bx - side, by + bh - 1),
        ])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_mid"], [
            (bx + side * 2, by + 2),
            (bx + side * (bw - 2), by + 2),
            (bx + side * (bw + 1), by + bh // 2),
            (bx + side * (bw - 2), by + bh - 2),
            (bx, by + bh - 2),
        ])

        # Sharp edge highlight
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["metal_shine"],
                (bx + side * 2, by + 1),
                (bx + side * (bw + 2), by + bh // 2), 1)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["metal_edge"],
                (bx + side * (bw + 2), by + bh // 2),
                (bx + side * (bw - 1), by + bh - 1), 1)

        # Acid stain on blade
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_dark"],
                  (bx + side * bw // 2, by + bh // 2), 3)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_mid"],
                  (bx + side * bw // 2 - 1, by + bh // 2 - 1), 2)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_bright"],
                  (bx + side * bw // 2 - 1, by + bh // 2 - 1), 1)

        # Dripping acid
        _NS_alchemist._draw_acid_droplet(surface, bx + side * bw // 2,
                            by + bh + 4 + int(math.sin(phase + side) * 2), 2, 200)


    def _draw_cleaver_swinging(surface, hx, hy, facing, angle):
        """Large cleaver in motion."""
        handle_len = 12
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle) * facing

        # Handle
        end_x = hx + int(dx * handle_len)
        end_y = hy + int(dy * handle_len)

        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["shadow_deep"], (hx + 2, hy + 2),
                (end_x + 2, end_y + 2), 5)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["leather_darkest"], (hx, hy), (end_x, end_y), 4)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["leather_dark"], (hx, hy), (end_x, end_y), 3)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["leather_mid"], (hx, hy), (end_x, end_y), 1)

        # Blade
        blade_w = 14
        # Corners
        c1 = (end_x + int(dx * 2 + perp_x * blade_w),
              end_y + int(dy * 2 + perp_y * blade_w))
        c2 = (end_x + int(dx * (blade_w + 3) + perp_x * blade_w // 2),
              end_y + int(dy * (blade_w + 3) + perp_y * blade_w // 2))
        c3 = (end_x + int(dx * blade_w - perp_x * blade_w // 2),
              end_y + int(dy * blade_w - perp_y * blade_w // 2))
        c4 = (end_x + int(-dx * 2 - perp_x * 2),
              end_y + int(-dy * 2 - perp_y * 2))

        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["shadow_deep"], [
            (p[0] + 1, p[1] + 1) for p in [c1, c2, c3, c4]])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_darkest"], [c1, c2, c3, c4])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_dark"], [
            (c1[0] - int(perp_x), c1[1] - int(perp_y)),
            (c2[0] - int(perp_x), c2[1] - int(perp_y)),
            c3, c4,
        ])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["metal_mid"], [
            (c1[0] - int(perp_x * 2), c1[1] - int(perp_y * 2)),
            c2, c3,
        ])

        # Sharp edge
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["metal_shine"], c1, c2, 1)
        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["metal_edge"], c2, c3, 1)

        # Acid glow on blade
        mid_x = (c1[0] + c2[0] + c3[0]) // 3
        mid_y = (c1[1] + c2[1] + c3[1]) // 3
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], 180), (mid_x, mid_y), 4)
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_hot"], 220), (mid_x, mid_y), 2)


    def _draw_acid_gun(surface, hx, hy, facing, phase, firing=False):
        """Brass acid gun / hose held in ogre's hand."""
        # Handle
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_darkest"], (hx - 2, hy - 3, 4, 8),
              border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_dark"], (hx - 2, hy - 3, 4, 6))

        # Tank on top
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["shadow_deep"], (hx - 4 + 1, hy - 10 + 1, 8, 8),
              border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_dark"], (hx - 4, hy - 10, 8, 8),
              border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_mid"], (hx - 3, hy - 9, 6, 6))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_light"], (hx - 3, hy - 9, 3, 4))

        # Green fluid window
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["glass_dark"], (hx - 2, hy - 8, 4, 5))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["acid_mid"], (hx - 1, hy - 7, 3, 3))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["acid_bright"], (hx - 1, hy - 7, 2, 2))

        # Barrel/hose extending forward
        barrel_len = 16
        end_x = hx + facing * barrel_len

        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["shadow_deep"],
              (min(hx, end_x) + 1, hy - 2 + 1, barrel_len, 5), border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_dark"],
              (min(hx, end_x), hy - 2, barrel_len, 5), border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_mid"],
              (min(hx, end_x), hy - 1, barrel_len, 3))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_light"],
              (min(hx, end_x), hy - 1, barrel_len, 1))

        # Flared muzzle
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["brass_dark"], [
            (end_x, hy - 4),
            (end_x + facing * 5, hy - 5),
            (end_x + facing * 5, hy + 4),
            (end_x, hy + 3),
        ])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["brass_mid"], [
            (end_x, hy - 3),
            (end_x + facing * 4, hy - 4),
            (end_x + facing * 4, hy + 3),
            (end_x, hy + 2),
        ])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["brass_light"], [
            (end_x + facing * 1, hy - 2),
            (end_x + facing * 4, hy - 3),
            (end_x + facing * 4, hy + 1),
        ])

        if not firing:
            # Small drip
            _NS_alchemist._draw_acid_droplet(surface, end_x + facing * 6, hy + 4, 2, 200)


    def _draw_goblin_rider(surface, cx, cy, facing, phase, action,
                           attack_progress, rage=False, cheer=False):
        """Small purple goblin on ogre's shoulder holding potion.

        `cheer=True` (ultimate R) -> goblin mengangkat botol dan
        memompanya berdenyut + percik emas, perayaan klasik Greevil.
        """
        bob = int(math.sin(phase * 1.0) * (3 if cheer else 1.5))

        # Legs (little dangling)
        for side in (-1, 1):
            lx = cx + side * 3
            ly = cy + 6 + bob
            _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_darkest"], (lx - 1, ly, 3, 5),
                  border_radius=1)
            _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_dark"], (lx - 1, ly, 3, 4))
            # Boot
            _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_darkest"], (lx - 2, ly + 5, 5, 3))
            _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_dark"], (lx - 2, ly + 5, 5, 1))

        # Torso (small purple robe)
        torso = [
            (cx - 5, cy - 4 + bob),
            (cx + 5, cy - 4 + bob),
            (cx + 4, cy + 6 + bob),
            (cx - 4, cy + 6 + bob),
        ]
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in torso])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["gob_darkest"], torso)
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["gob_dark"], [
            (cx - 4, cy - 3 + bob),
            (cx + 4, cy - 3 + bob),
            (cx + 3, cy + 5 + bob),
            (cx - 3, cy + 5 + bob),
        ])
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["gob_mid"], [
            (cx - 3, cy - 2 + bob),
            (cx + 3, cy - 2 + bob),
            (cx + 2, cy + 4 + bob),
            (cx - 2, cy + 4 + bob),
        ])

        # Belt
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_dark"], (cx - 5, cy + 2 + bob, 10, 2))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["brass_mid"], (cx - 1, cy + 2 + bob, 2, 2))

        # Head (green skin, small)
        hy = cy - 8 + bob
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx + 1, hy + 1), 6)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["ogre_dark"], (cx, hy), 5)  # greenish tint
        # Actually let's use goblin-ish green
        _NS_alchemist._aacircle(surface, (50, 90, 30), (cx, hy), 5)
        _NS_alchemist._aacircle(surface, (85, 130, 45), (cx - 1, hy - 1), 4)
        _NS_alchemist._aacircle(surface, (130, 175, 65), (cx - 1, hy - 2), 2)

        # Long pointed ears
        for side in (-1, 1):
            _NS_alchemist._poly(surface, (35, 70, 25), [
                (cx + side * 4, hy - 1),
                (cx + side * 8, hy - 4),
                (cx + side * 5, hy + 2),
            ])
            _NS_alchemist._poly(surface, (75, 110, 40), [
                (cx + side * 4, hy),
                (cx + side * 7, hy - 3),
                (cx + side * 5, hy + 1),
            ])

        # Big nose
        _NS_alchemist._poly(surface, (65, 100, 35), [
            (cx + facing * 1, hy + 1),
            (cx + facing * 4, hy + 2),
            (cx + facing * 4, hy + 4),
            (cx + facing * 1, hy + 4),
        ])
        _NS_alchemist._poly(surface, (95, 140, 50), [
            (cx + facing * 1, hy + 2),
            (cx + facing * 3, hy + 3),
            (cx + facing * 1, hy + 3),
        ])

        # Grinning mouth
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx - 2, hy + 4, 4, 1))
        # Small fang
        _NS_alchemist._poly(surface, _NS_alchemist.PALETTE["bone_light"], [
            (cx - 1, hy + 4),
            (cx, hy + 6),
            (cx + 1, hy + 4),
        ])

        # Beady eyes
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx - 2, hy - 1), 1)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx + 2, hy - 1), 1)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["eye_hot"], (cx - 2, hy - 1), 1)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["eye_hot"], (cx + 2, hy - 1), 1)

        # Explorer hat (Alchemist style safari helmet)
        _NS_alchemist._draw_goblin_hat(surface, cx, hy - 4, phase)

        # Goblin arms holding potion
        _NS_alchemist._draw_goblin_arms(surface, cx, cy + bob, facing, phase, action,
                                         attack_progress, cheer=cheer)


    def _draw_goblin_hat(surface, cx, cy, phase):
        """Explorer/pith helmet."""
        # Brim
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx - 8 + 1, cy + 1 + 1, 16, 4))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["leather_darkest"], (cx - 8, cy + 1, 16, 4))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["leather_dark"], (cx - 7, cy + 1, 14, 3))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["leather_mid"], (cx - 6, cy + 1, 12, 2))

        # Dome
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["leather_darkest"], (cx - 5, cy - 4, 10, 8))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["leather_dark"], (cx - 4, cy - 4, 8, 7))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["leather_mid"], (cx - 3, cy - 4, 6, 5))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["leather_light"], (cx - 3, cy - 4, 4, 3))

        # Hat band
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["red"], (cx - 5, cy, 10, 2))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["gold_mid"], (cx - 4, cy + 1, 8, 1))


    def _draw_goblin_arms(surface, cx, cy, facing, phase, action,
                          attack_progress, cheer=False):
        """Goblin arms — one holds potion up, one hangs down.

        Saat cheer (R) lengan botol diangkat lebih tinggi + dipompa
        seirama denyut, tangan kanan mengepal ke atas.
        """
        sway = math.sin(phase * 1.0 + 1) * 1
        pump = int(math.sin(phase * 4.2) * 3) if cheer else 0
        raise_ = 9 if cheer else 0

        # Left arm - holding potion up (celebratory)
        la_x = cx - 5
        la_y = cy - 2
        lh_x = cx - 9 + int(sway)
        lh_y = cy - 8 - raise_ + pump

        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["shadow_deep"], (la_x + 1, la_y + 1),
                (lh_x + 1, lh_y + 1), 3)
        _NS_alchemist._aaline(surface, (35, 70, 25), (la_x, la_y), (lh_x, lh_y), 3)
        _NS_alchemist._aaline(surface, (75, 110, 40), (la_x, la_y), (lh_x, lh_y), 2)
        _NS_alchemist._aaline(surface, (115, 155, 55), (la_x, la_y), (lh_x, lh_y), 1)

        # Potion in hand
        _NS_alchemist._draw_small_potion(surface, lh_x, lh_y - 4, phase)
        if cheer:
            # percik emas dari botol saat perayaan
            for i in range(3):
                t = (phase * 0.9 + i * 0.33) % 1.0
                gx = lh_x + int(math.cos(phase * 3 + i * 2.1) * (3 + 5 * t))
                gy = lh_y - 8 - int(t * 9)
                _NS_alchemist._aacircle(surface,
                        (*_NS_alchemist.PALETTE["gold_shine"], int(220 * (1 - t))),
                        (gx, gy), 1)

        # Right arm - normal: menggantung; cheer: mengepal ke atas
        ra_x = cx + 5
        ra_y = cy - 2
        if cheer:
            rh_x = cx + 9 + int(-sway)
            rh_y = cy - 6 + pump
        else:
            rh_x = cx + 8 + int(-sway)
            rh_y = cy + 4

        _NS_alchemist._aaline(surface, _NS_alchemist.PALETTE["shadow_deep"], (ra_x + 1, ra_y + 1),
                (rh_x + 1, rh_y + 1), 3)
        _NS_alchemist._aaline(surface, (35, 70, 25), (ra_x, ra_y), (rh_x, rh_y), 3)
        _NS_alchemist._aaline(surface, (75, 110, 40), (ra_x, ra_y), (rh_x, rh_y), 2)

        # Small hand
        _NS_alchemist._aacircle(surface, (35, 70, 25), (rh_x, rh_y), 2)
        _NS_alchemist._aacircle(surface, (85, 130, 45), (rh_x - 1, rh_y - 1), 1)


    def _draw_small_potion(surface, cx, cy, phase):
        """Small acid potion held by goblin."""
        # Bottle body
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["shadow_deep"], (cx - 2 + 1, cy - 1 + 1, 4, 6),
              border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["glass_dark"], (cx - 2, cy - 1, 4, 6), border_radius=1)
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["glass_mid"], (cx - 2, cy, 4, 4))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["glass_light"], (cx - 2, cy, 1, 4))

        # Cork
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_dark"], (cx - 1, cy - 3, 3, 2))
        _NS_alchemist._rect(surface, _NS_alchemist.PALETTE["leather_mid"], (cx - 1, cy - 3, 2, 1))

        # Pink ribbon (decorative like reference)
        _NS_alchemist._rect(surface, (220, 130, 180), (cx - 2, cy - 2, 4, 1))
        _NS_alchemist._rect(surface, (255, 180, 220), (cx - 2, cy - 2, 2, 1))

        # Bright glow
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], int(150 * pulse)), (cx, cy + 2), 4)
        _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_hot"], (cx, cy + 2), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_alch_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Acid green wisps under Alchemist."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -4):
            alpha = int((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_alchemist.PALETTE["acid_darkest"], min(255, alpha)),
                    (75 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 75, cy - 11))

        # Rising acid vapors
        for i, offset in enumerate((-25, -10, 8, 24)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(210 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_darkest"], alpha), (sx, sy), 5)
            _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_mid"], alpha), (sx, sy - 2), 3)
            _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha), (sx, sy - 3), 2)
            _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_hot"], alpha), (sx, sy - 3), 1)

        # Bubbles orbiting
        for i in range(7):
            angle = phase * 0.7 + i * math.pi * 2 / 7
            r = 25 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_mid"], (sx, sy), 2)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["acid_bright"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 13 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 140 - i * 25)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha),
                          (sx, sy), max(1, 3 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 22), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (11 - radius, 11 - radius, 98 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_alchemist.PALETTE["acid_dark"], 60), (10, 5, 100, 12))
        surface.blit(shadow, (x - 60, y - 11))


    def _draw_alch_aura(surface, x, y, phase, active_skill, rage=False):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("e", "r") else (1.35 if rage else 1.0)
        if rage and active_skill not in ("e", "r"):
            pulse = pulse * 1.1 + 0.06
        aura = pygame.Surface((220, 190), pygame.SRCALPHA)
        color = _NS_alchemist.PALETTE["acid_darkest"] if active_skill != "r" else _NS_alchemist.PALETTE["gold_darkest"]
        for radius in range(88, 5, -4):
            alpha = int((88 - radius) * 1.2 * pulse * strength)
            if alpha > 0:
                _NS_alchemist._aacircle(aura, (*color, min(255, alpha)), (110, 95), radius)
        surface.blit(aura, (x - 110, y - 95))


    def _draw_ground_runes(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((140, 46), pygame.SRCALPHA)
        color1 = (*_NS_alchemist.PALETTE["acid_dark"], 140)
        color2 = (*_NS_alchemist.PALETTE["acid_mid"], 170)
        color3 = (*_NS_alchemist.PALETTE["acid_bright"], 160)
        if active_skill == "r":
            color1 = (*_NS_alchemist.PALETTE["gold_dark"], 160)
            color2 = (*_NS_alchemist.PALETTE["gold_mid"], 190)
            color3 = (*_NS_alchemist.PALETTE["gold_light"], 180)

        pygame.draw.ellipse(ring, color1, (5, 10, 130, 26), 3)
        pygame.draw.ellipse(ring, color2, (20, 14, 100, 18), 2)

        for i in range(10):
            angle = phase * 0.15 + i * math.pi / 5
            x1 = 70 + int(math.cos(angle) * 32)
            y1 = 23 + int(math.sin(angle) * 7)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 23 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, color3, (x1, y1), (x2, y2), 1)

        if active_skill:
            pygame.draw.ellipse(ring, (color3[0], color3[1], color3[2], int(80 * pulse)),
                                (15, 8, 110, 30), 1)

        surface.blit(ring, (x - 70, y - 23))


    def _draw_cleaver_swing_arc(surface, x, y, facing, progress):
        if progress < 0.28 or progress > 0.75:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.25
        visibility = max(0.0, min(1.0, visibility))

        arc = pygame.Surface((160, 120), pygame.SRCALPHA)
        for i in range(18):
            t = i / 17
            angle = -math.pi * 0.9 + t * math.pi * 1.1
            px = 80 + int(math.cos(angle) * 60) * facing
            py = 60 + int(math.sin(angle) * 44)
            alpha = int((210 - i * 10) * visibility)
            if alpha <= 0:
                continue
            _NS_alchemist._aacircle(arc, (*_NS_alchemist.PALETTE["acid_darkest"], alpha), (px, py), 10)
            _NS_alchemist._aacircle(arc, (*_NS_alchemist.PALETTE["acid_mid"], alpha), (px, py), 6)
            _NS_alchemist._aacircle(arc, (*_NS_alchemist.PALETTE["acid_bright"], alpha), (px, py), 4)
            _NS_alchemist._aacircle(arc, (*_NS_alchemist.PALETTE["acid_hot"], alpha), (px, py), 2)
            _NS_alchemist._aacircle(arc, (*_NS_alchemist.PALETTE["acid_glow"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 80, y - 60))


    def _draw_swing_impact(surface, x, y, facing, progress):
        if progress < 0.5 or progress > 0.85:
            return
        t = (progress - 0.5) / 0.35
        intensity = math.sin(t * math.pi)

        impact_x = x + 42 * facing
        impact_y = y + 5
        alpha = int(230 * intensity)
        radius = int(10 + intensity * 22)

        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_dark"], alpha // 2),
                  (impact_x, impact_y), radius + 4)
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha),
                  (impact_x, impact_y), radius, 3)
        _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_hot"], alpha),
                  (impact_x, impact_y), max(1, radius - 6), 2)

        for i in range(10):
            angle = i * math.pi / 5 + progress * 3
            dx = impact_x + int(math.cos(angle) * radius * 1.3)
            dy = impact_y + int(math.sin(angle) * radius * 0.9)
            _NS_alchemist._draw_acid_droplet(surface, dx, dy, 3, alpha)


    # ===================================================================
    # SKILL Q: ACID SPRAY (green cone)
    # ===================================================================
    def _draw_acid_spray(surface, boss, x, y, timer, phase):
        duration = _NS_alchemist.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_alchemist._target_position(boss, x, y)

        if progress > 0.96:
            return
        # percik memudar di 10% terakhir, tidak "klik-hilang"
        fade = min(1.0, (1.0 - progress) / 0.10)

        # From the acid gun muzzle (tangan depan ogre yang terentang)
        start_x = x + 46 * boss.direction
        start_y = y - 4

        dx = tx - start_x
        dy = ty - start_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            dist = 1
        dir_x = dx / dist
        dir_y = dy / dist
        perp_x = -dir_y
        perp_y = dir_x

        if progress < 0.2:
            cone_len = int(160 * (progress / 0.2))
        else:
            cone_len = 160

        # Cone of acid particles
        for i in range(28):
            t = i / 28
            base_x = start_x + dir_x * cone_len * t
            base_y = start_y + dir_y * cone_len * t
            spread = t * 22
            offset = math.sin(phase * 5 + i * 1.7) * spread
            fx = int(base_x + perp_x * offset)
            fy = int(base_y + perp_y * offset)

            size = int(5 + t * 5)
            alpha_t = (1 - t * 0.3) * fade
            alpha = int(230 * alpha_t)
            if alpha <= 0:
                continue

            if t < 0.2:
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_white"], alpha), (fx, fy), size)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_glow"], alpha), (fx, fy), max(1, size - 2))
            elif t < 0.5:
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_hot"], alpha), (fx, fy), size)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha), (fx, fy), max(1, size - 2))
            elif t < 0.8:
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha), (fx, fy), size)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_mid"], alpha), (fx, fy), max(1, size - 2))
            else:
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_mid"], alpha), (fx, fy), size)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_dark"], alpha), (fx, fy), max(1, size - 2))

        # Bright muzzle
        _mz = int(255 * fade)
        if _mz > 0:
            _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_white"], _mz),
                      (int(start_x), int(start_y)), 6)
            _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_hot"], _mz),
                      (int(start_x + dir_x * 6), int(start_y + dir_y * 6)), 4)

        # Small droplet particles falling from cone
        for i in range(8):
            t = (phase * 0.5 + i * 0.12) % 1.0
            drop_t = 0.3 + t * 0.6
            base_x = start_x + dir_x * cone_len * drop_t
            base_y = start_y + dir_y * cone_len * drop_t + int(t * 10)
            _NS_alchemist._draw_acid_droplet(surface, int(base_x), int(base_y), 2, 200)


    # ===================================================================
    # SKILL E: CHEMICAL RAGE (self buff)
    # ===================================================================
    def _draw_chem_rage_ground(surface, boss, x, y, timer, phase):
        """Ground pulse rings under boss."""
        duration = _NS_alchemist.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        env = min(1.0, progress * 5, (1 - progress) * 4 + 0.3)
        pulse = (math.sin(phase * 3) * 0.3 + 0.7) * env

        for i in range(3):
            r = int(30 + i * 15 + math.sin(phase * 2 + i) * 5)
            _NS_alchemist._ellipse(surface, (*_NS_alchemist.PALETTE["acid_bright"], int(120 * pulse)),
                     (x - r, y + _NS_alchemist.SHADOW_DY - 8 - r // 3,
                      r * 2, r // 1.5), 2)


    def _draw_chem_rage_foreground(surface, boss, x, y, timer, phase):
        """Green aura + steam rising from Alchemist.

        Dulu blobnya opaque besar (x4 per lapis) sampai karakter
        tenggelam total; sekarang jadi cincin aura transparan +
        envelope masuk/keluar."""
        duration = _NS_alchemist.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        env = min(1.0, progress * 5, (1 - progress) * 4 + 0.3)
        pulse = (math.sin(phase * 3) * 0.3 + 0.7) * env

        # Ring aura (SRCALPHA buffer agar alpha menumpuk natural,
        # bukan menutupi badan seperti blob sebelumnya)
        glow = pygame.Surface((120, 110), pygame.SRCALPHA)
        for radius in range(56, 16, -4):
            alpha = int((56 - radius) * 1.8 * pulse)
            _NS_alchemist._aacircle(glow, (*_NS_alchemist.PALETTE["acid_dark"],
                              min(90, alpha)), (60, 55), radius)
        surface.blit(glow, (x - 60, y - 60))

        # Rising steam wisps
        for i in range(12):
            t = (phase * 0.8 + i * 0.08) % 1.0
            angle = i * math.pi * 2 / 12
            px = x + int(math.cos(angle) * 25)
            py = y + 15 - int(t * 50)
            alpha = int(255 * (1 - t))
            if alpha > 0:
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_mid"], alpha), (px, py), 4)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_bright"], alpha), (px, py), 2)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_hot"], alpha), (px - 1, py - 1), 1)

        # Sparkles/electric arcs
        _sa = int(255 * env)
        if _sa > 20:
            for i in range(6):
                angle = phase * 2 + i * math.pi / 3
                r = 30 + int(math.sin(phase * 3 + i) * 8)
                sx = x + int(math.cos(angle) * r)
                sy = y - 10 + int(math.sin(angle) * r * 0.5)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_white"], _sa),
                          (sx, sy), 2)
                _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["acid_glow"], _sa),
                          (sx, sy), 1)


    # ===================================================================
    # SKILL R: GREEVIL'S GREED (gold rain)
    # ===================================================================
    def _draw_greevil_ground(surface, boss, x, y, timer, phase):
        """Golden aura on ground + pile of coins yang tumbuh dari tanah."""
        duration = _NS_alchemist.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        env = min(1.0, progress * 5)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        fade = 1.0 if progress < 0.85 else max(0.0, (1.0 - progress) / 0.15)

        # Golden circle
        for i in range(3):
            r = int(50 + i * 20 + math.sin(phase + i) * 4)
            _NS_alchemist._ellipse(surface, (*_NS_alchemist.PALETTE["gold_mid"], int(120 * pulse * env * fade)),
                     (x - r, y + _NS_alchemist.SHADOW_DY - 10 - r // 3, r * 2, r // 1.5), 2)

        # Gold pile at feet - tumbuh 0.15..0.55 lalu ditenggelamkan lagi
        if progress > 0.15:
            pile_grow = min(1.0, (progress - 0.15) / 0.40)
            pile_grow *= fade  # t 0.85-1.0: emas "disedot" balik
            if pile_grow > 0.02:
                _NS_alchemist._draw_gold_pile(surface, x, y + _NS_alchemist.SHADOW_DY - 5,
                                  pile_grow, phase)


    def _draw_gold_pile(surface, cx, cy, grow, phase):
        """Pile of gold coins on ground."""
        pile_w = int(60 * grow)
        pile_h = int(12 * grow)

        # Base pile
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["shadow_deep"],
                 (cx - pile_w // 2 + 1, cy - pile_h // 2 + 1, pile_w, pile_h))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["gold_dark"],
                 (cx - pile_w // 2, cy - pile_h // 2, pile_w, pile_h))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["gold_mid"],
                 (cx - pile_w // 2 + 3, cy - pile_h // 2 + 2,
                  pile_w - 6, pile_h - 4))
        _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["gold_light"],
                 (cx - pile_w // 2 + 6, cy - pile_h // 2 + 3,
                  pile_w - 15, pile_h - 8))

        # Individual coins scattered
        coin_count = int(15 * grow)
        for i in range(coin_count):
            seed = i * 1234567 % 100
            angle = (seed / 100) * math.pi
            r = (seed % 30)
            cx_offset = int(math.cos(angle) * r - pile_w // 2 + r)
            cx_offset = max(-pile_w // 2, min(pile_w // 2, cx_offset))
            cy_offset = int(-abs(math.sin(angle) * 5) + seed % 4)
            px = cx + cx_offset
            py = cy + cy_offset

            # Coin
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["gold_dark"], (px, py), 3)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["gold_mid"], (px, py), 2)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["gold_light"], (px - 1, py - 1), 1)
            _NS_alchemist._aacircle(surface, _NS_alchemist.PALETTE["gold_shine"], (px - 1, py - 1), 1)


    def _draw_greevil_foreground(surface, boss, x, y, timer, phase):
        """Gold coins raining down + goblin celebrating."""
        duration = _NS_alchemist.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Spawn coins periodically
        if not hasattr(boss, "_alch_coins"):
            boss._alch_coins = []
        if not hasattr(boss, "_alch_last_coin_frame"):
            boss._alch_last_coin_frame = 0
        boss._alch_last_coin_frame += 1
        if boss._alch_last_coin_frame % 3 == 0 and progress < 0.8:
            # coin hujan dari atas, bukan cuma 2 baris
            seed = boss._alch_last_coin_frame
            cx_off = (seed * 137 % 110) - 55
            _NS_alchemist._spawn_coin(boss, x + cx_off, y - 52)

        # Update and draw coins
        for coin in boss._alch_coins:
            coin["age"] += 1
            coin["vy"] += 0.25  # gravity
            coin["x"] += coin["vx"]
            coin["y"] += coin["vy"]
            coin["spin"] += coin["spin_speed"]

            # Draw spinning coin
            px, py = int(coin["x"]), int(coin["y"])
            spin_w = abs(math.cos(coin["spin"]))
            w = max(1, int(4 * spin_w))
            # Coin as ellipse for spinning effect
            _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["shadow_deep"],
                     (px - w + 1, py - 3 + 1, w * 2, 6))
            _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["gold_dark"],
                     (px - w, py - 3, w * 2, 6))
            _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["gold_mid"],
                     (px - w + 1, py - 2, max(1, w * 2 - 2), 4))
            _NS_alchemist._ellipse(surface, _NS_alchemist.PALETTE["gold_light"],
                     (px - w + 1, py - 2, max(1, w * 2 - 2), 2))

            # Sparkle trail
            _NS_alchemist._aacircle(surface, (*_NS_alchemist.PALETTE["gold_shine"], 200), (px, py - 4), 1)

        # Clean up old coins
        boss._alch_coins = [c for c in boss._alch_coins
                             if c["age"] < c["life"] and c["y"] < y + 80]

        # Sparkles around boss - memudar bersama akhir ultimate
        _sp = 1.0 if progress < 0.8 else max(0.0, (1 - progress) / 0.2)
        if _sp > 0.02:
            for i in range(8):
                angle = phase * 1.5 + i * math.pi / 4
                r = 40 + int(math.sin(phase * 2 + i) * 8)
                sx = x + int(math.cos(angle) * r)
                sy = y + int(math.sin(angle) * r * 0.6)
                _NS_alchemist._aacircle(surface,
                        (*_NS_alchemist.PALETTE["gold_shine"], int(255 * _sp)), (sx, sy), 2)
                _NS_alchemist._aacircle(surface,
                        (*_NS_alchemist.PALETTE["gold_light"], int(255 * _sp)), (sx, sy), 1)
                # Sparkle cross
                _NS_alchemist._aaline(surface,
                        (*_NS_alchemist.PALETTE["gold_shine"], int(200 * _sp)),
                        (sx - 3, sy), (sx + 3, sy), 1)
                _NS_alchemist._aaline(surface,
                        (*_NS_alchemist.PALETTE["gold_shine"], int(200 * _sp)),
                        (sx, sy - 3), (sx, sy + 3), 1)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_alchemist.draw_alchemist(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_razak(surface, boss, x, y):
    """Entry point razak."""
    return _NS_razak.draw_razak(surface, boss, x, y)

def draw_khalros(surface, boss, x, y):
    """Entry point khalros."""
    return _NS_khalros.draw_khalros(surface, boss, x, y)

def draw_gorath(surface, boss, x, y):
    """Entry point gorath."""
    return _NS_gorath.draw_gorath(surface, boss, x, y)

def draw_alchemist(surface, boss, x, y):
    """Entry point alchemist."""
    return _NS_alchemist.draw_alchemist(surface, boss, x, y)
