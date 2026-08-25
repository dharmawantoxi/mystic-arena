"""
_render.py - rendering & efek (digabung dari 7 file)

  map_renderer.py
  effects.py
  effects_death.py
  effects_intro.py       (_skip_button_label duplikat DIHAPUS)
  effects_level_intro.py
  sprite_cache.py
  render_cache.py        (versi kanonik get_font, clear_cache, dll.)
"""
import pygame
import math
import random
from _core import *
import os as _os


# ═══════════════════════════════════════════════════════════════
# FONT SYSTEM PROFESIONAL (tertanam di bundle ini - tanpa file baru)
#   - TITLE : Cinzel  (epic serif untuk judul/level/boss)
#   - BODY  : Barlow  (clean sans untuk HUD/UI, 4 weight)
# File font dibundle di assets/fonts/ (bukan .py, aman).
# Fallback otomatis: SysFont -> font bawaan pygame.
# ═══════════════════════════════════════════════════════════════
_FONT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                          "assets", "fonts")
_TITLE_FONT_FILE = "Cinzel.ttf"
_BODY_FONT_FILES = {
    "body": "Barlow-Regular.ttf",
    "body_medium": "Barlow-Medium.ttf",
    "body_semibold": "Barlow-SemiBold.ttf",
    "body_bold": "Barlow-Bold.ttf",
}
_SYS_FALLBACKS = ["Verdana", "DejaVu Sans", "Arial", "Helvetica"]
_STYLE_FONT_MAP = {
    "title": "Cinzel.ttf",
    "body": "Barlow-Regular.ttf",
    "body_medium": "Barlow-Medium.ttf",
    "body_semibold": "Barlow-SemiBold.ttf",
    "body_bold": "Barlow-Bold.ttf",
}


def _font_path(style):
    fname = _STYLE_FONT_MAP.get(style, "Barlow-Regular.ttf")
    return _os.path.join(_FONT_DIR, fname)


def _make_font(size, style="body", bold=False):
    """Buat font: TTF bundle -> SysFont -> default pygame."""
    path = _font_path(style)
    if _os.path.exists(path):
        try:
            f = pygame.font.Font(path, size)
            f.set_bold(bold)
            return f
        except Exception:
            pass
    for name in _SYS_FALLBACKS:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f is not None:
                return f
        except Exception:
            continue
    return pygame.font.Font(None, size)


def title_font(size, bold=True):
    """Font judul (Cinzel) - nama game, level, boss."""
    size = max(8, min(int(size), 220))
    return get_font(size, "title", bold)



# ====================================================================
# map_renderer.py
# ====================================================================

# MAP_RENDERER.PY - Dark Fantasy Edition
# Coordinator - delegates ke map_components/
# ================================

import pygame
import math
from map_components.palettes import *


class MapRenderer:
    """
    Dark Fantasy Map Renderer - Coordinator.
    Delegates rendering ke map_components/.
    """

    def __init__(self, screen, theme_name="forest"):
        self.screen = screen
        self.map_width = SCREEN_WIDTH
        self.map_height = SCREEN_HEIGHT

        # Load theme
        from map_components.themes import get_theme
        self.theme = get_theme(theme_name)
        self.theme_name = theme_name

        # Shop positions
        self.radiant_shop_pos = (340, 540)
        self.dire_shop_pos = (940, 180)
        self.shop_size = 60

        # ═══ GENERATE DATA ═══
        from map_components.generators import (
            PathGenerator, DecorationGenerator)

        # Lane paths
        self.top_lane_points, self.mid_lane_points, \
            self.bot_lane_points = PathGenerator.generate_lanes(
                self.map_width, self.map_height)

        # River path
        self.river_points = PathGenerator.generate_river(
            self.map_width, self.map_height)

        # Decoration positions
        all_lane_pts = (self.top_lane_points +
                        self.bot_lane_points +
                        self.mid_lane_points)

        decor_gen = DecorationGenerator(
            self.map_width, self.map_height,
            all_lane_pts, self.river_points,
            [self.radiant_shop_pos, self.dire_shop_pos])

        decor_data = decor_gen.generate_all()

        # Assign decoration data
        for key, value in decor_data.items():
            setattr(self, key, value)

        # ═══ RENDER STATIC MAP (cached) ═══
        self.static_map = self._render_static_map()

        # ═══ INIT DYNAMIC ELEMENTS ═══
        from map_components.dynamic_renderer import DynamicRenderer
        self.dynamic = DynamicRenderer(self)

    def _render_static_map(self):
        """Pre-render static map ke cached surface"""
        from map_components.static_renderer import StaticRenderer
        from map_components.decoration_renderer import DecorationRenderer
        from map_components.shop_renderer import ShopRenderer

        surf = pygame.Surface((self.map_width, self.map_height))

        # Layer 1: Terrain (with theme)
        StaticRenderer.draw_terrain(surf, self.map_width,
                                    self.map_height, self.theme)
        StaticRenderer.draw_terrain_details(surf, self.map_width,
                                            self.map_height, self.theme)

        # Layer 2: River (with theme)
        StaticRenderer.draw_river(surf, self.river_points,
                                  self.map_width, self.map_height,
                                  self.theme)

        # Layer 3: Lanes (with theme)
        StaticRenderer.draw_lane(surf, self.top_lane_points,
                                 self.map_width, self.map_height,
                                 self.theme)
        StaticRenderer.draw_lane(surf, self.mid_lane_points,
                                 self.map_width, self.map_height,
                                 self.theme)
        StaticRenderer.draw_lane(surf, self.bot_lane_points,
                                 self.map_width, self.map_height,
                                 self.theme)

        # Layer 4: Decorations (with theme filter)
        DecorationRenderer.draw_all(surf, self)

        # Layer 5: Shops
        ShopRenderer.draw(surf, self.radiant_shop_pos,
                          self.dire_shop_pos)

        # Layer 6: Border wall
        StaticRenderer.draw_border_wall(surf, self.map_width,
                                        self.map_height, self.theme)

        return surf

    # ═══════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════

    def draw(self, surface, animation_time=0):
        """Main draw (called every frame)"""
        surface.blit(self.static_map, (0, 0))
        self.dynamic.draw(surface, animation_time)

        # Ambient tint overlay (kalau ada)
        # Surface tint dibuat SEKALI lalu dipakai ulang. Dulu
        # dialokasi + di-fill tiap frame (~0.5 ms terbuang).
        tint = self.theme.get("ambient_tint")
        if tint:
            # BOM WAKTU: ini blit SRCALPHA SEUKURAN LAYAR setiap frame.
            # Di HP = 204 ms/frame (3 FPS) untuk semua tema yang punya
            # ambient_tint. Diganti fill BLEND_RGB_MULT (~2 ms) yang
            # memberi efek pewarnaan setara.
            from mobile.perf import Quality as _Qt
            if _Qt.cheap_alpha:
                if getattr(self, '_tint_surface', None) is None:
                    self._tint_surface = pygame.Surface(
                        (self.map_width, self.map_height),
                        pygame.SRCALPHA)
                    self._tint_surface.fill(tint)
                surface.blit(self._tint_surface, (0, 0))
            else:
                _a = (tint[3] if len(tint) > 3 else 255) / 255.0
                surface.fill((int(255 - (255 - tint[0]) * _a),
                              int(255 - (255 - tint[1]) * _a),
                              int(255 - (255 - tint[2]) * _a)),
                             special_flags=pygame.BLEND_RGB_MULT)

    def get_lane_path(self, lane_name):
        """Get lane path points"""
        if lane_name == "top":
            return self.top_lane_points
        elif lane_name == "mid":
            return self.mid_lane_points
        elif lane_name == "bot":
            return self.bot_lane_points
        return []

    def get_shop_positions(self):
        """Get shop positions.
        radiant (dekat base biru) = ITEM FORGE
        dire (dekat base merah)   = HERO SHOP
        """
        return {
            'radiant': self.radiant_shop_pos,
            'dire': self.dire_shop_pos,
            'size': self.shop_size,
        }

    def is_click_on_shop(self, mx, my):
        """True kalau klik mengenai salah satu dari dua bangunan toko."""
        for pos in [self.radiant_shop_pos, self.dire_shop_pos]:
            if math.hypot(mx - pos[0], my - pos[1]) <= self.shop_size:
                return True
        return False

    def get_clicked_shop(self, mx, my):
        """Kembalikan 'item' (Radiant/ITEM FORGE), 'hero' (Dire/HERO
        SHOP), atau None. Radiant dekat base biru dipakai pemain,
        jadi kami jadikan ITEM FORGE; Dire tetap HERO SHOP."""
        for label, pos in (
            ('item', self.radiant_shop_pos),
            ('hero', self.dire_shop_pos),
        ):
            if math.hypot(mx - pos[0], my - pos[1]) <= self.shop_size:
                return label
        return None





# ================================


# ====================================================================
# effects.py
# ====================================================================

# ================================
# EFFECTS.PY - Visual Effects System
# ================================

import pygame
import math
import random


class FloatingText:
    """Text yang mengambang naik + fade out"""

    def __init__(self, x, y, text, color=(255, 255, 255),
                 size='medium', velocity=(0, -2), lifetime=45,
                 critical=False):
        self.x = float(x)
        self.y = float(y)
        self.text = str(text)
        self.color = color
        self.velocity_x = velocity[0]
        self.velocity_y = velocity[1]
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
        self.critical = critical

        # Font size
        if size == 'small':
            self.font_size = 14
        elif size == 'medium':
            self.font_size = 18
        elif size == 'large':
            self.font_size = 24
        elif size == 'huge':
            self.font_size = 32
        else:
            self.font_size = 18

        # Random horizontal drift
        self.x_drift = random.uniform(-0.3, 0.3)

        # Scale animation (pop in effect)
        self.scale = 0.3
        self.target_scale = 1.2 if critical else 1.0

    def update(self):
        if not self.alive:
            return

        # Move
        self.x += self.velocity_x + self.x_drift
        self.y += self.velocity_y

        # Slow down over time
        self.velocity_y *= 0.95

        # Scale animation (spring effect)
        if self.scale < self.target_scale:
            self.scale += (self.target_scale - self.scale) * 0.3
        else:
            self.scale *= 0.99  # gently shrink

        # Lifetime
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    # ================================
    # PATCH untuk FloatingText.draw()
    # Gunakan cached font
    # ================================

    def draw(self, surface):
        if not self.alive:
            return

        alpha_ratio = min(1.0, self.lifetime / (self.max_lifetime * 0.5))
        alpha = int(255 * alpha_ratio)
        if alpha <= 0:
            return

        # ← GUNAKAN CACHED FONT (bukan buat baru tiap frame!)
        font_size = int(self.font_size * self.scale)
        font_size = max(8, min(font_size, 64))  # clamp
        font = get_font(font_size)

        # Shadow
        shadow_color = (0, 0, 0)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                shadow_surf = font.render(self.text, True, shadow_color)
                shadow_surf.set_alpha(alpha)
                shadow_rect = shadow_surf.get_rect(
                    center=(int(self.x) + dx, int(self.y) + dy))
                surface.blit(shadow_surf, shadow_rect)

        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text_surf, text_rect)


class HitParticle:
    """Small spark particle saat hit"""

    def __init__(self, x, y, color=(255, 200, 100),
                 velocity=None, lifetime=15, size=2):
        self.x = float(x)
        self.y = float(y)
        self.color = color

        if velocity:
            self.vx = velocity[0]
            self.vy = velocity[1]
        else:
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed

        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.alive = True
        self.gravity = 0.15

    def update(self):
        if not self.alive:
            return

        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.95  # friction

        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return

        alpha_ratio = self.lifetime / self.max_lifetime
        alpha = int(255 * alpha_ratio)
        current_size = max(1, int(self.size * alpha_ratio))

        if alpha > 0 and current_size > 0:
            particle_surf = pygame.Surface(
                (current_size * 3, current_size * 3), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf,
                               (*self.color, alpha),
                               (current_size * 3 // 2,
                                current_size * 3 // 2),
                               current_size)
            # Bright core
            pygame.draw.circle(particle_surf,
                               (255, 255, 255, alpha),
                               (current_size * 3 // 2,
                                current_size * 3 // 2),
                               max(1, current_size // 2))
            surface.blit(particle_surf,
                         (int(self.x) - current_size * 3 // 2,
                          int(self.y) - current_size * 3 // 2))


class DeathExplosion:
    """Explosion effect saat musuh mati"""

    def __init__(self, x, y, team="red", size='medium'):
        self.x = x
        self.y = y
        self.particles = []

        if team == "blue":
            colors = [(100, 200, 255), (150, 220, 255), (200, 240, 255)]
        else:
            colors = [(255, 100, 100), (255, 150, 100), (255, 200, 100)]

        # Sizes based on target
        if size == 'small':
            particle_count = 8
            spark_range = (2, 4)
        elif size == 'medium':
            particle_count = 15
            spark_range = (3, 5)
        else:  # large (boss)
            particle_count = 25
            spark_range = (4, 6)

        # Radial burst
        for _ in range(particle_count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 4)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(colors)
            spark_size = random.randint(*spark_range)

            self.particles.append(
                HitParticle(x, y, color, (vx, vy),
                            lifetime=random.randint(20, 35),
                            size=spark_size))

        # Central flash
        self.flash_timer = 8
        self.flash_max = 8

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surface):
        # Central flash
        if self.flash_timer > 0:
            intensity = self.flash_timer / self.flash_max
            size = int(20 * intensity)
            if size > 0:
                flash_surf = pygame.Surface((size * 3, size * 3),
                                            pygame.SRCALPHA)
                pygame.draw.circle(flash_surf,
                                   (255, 255, 200, int(200 * intensity)),
                                   (size * 3 // 2, size * 3 // 2),
                                   size)
                pygame.draw.circle(flash_surf,
                                   (255, 255, 255, int(255 * intensity)),
                                   (size * 3 // 2, size * 3 // 2),
                                   size // 2)
                surface.blit(flash_surf,
                             (int(self.x) - size * 3 // 2,
                              int(self.y) - size * 3 // 2))

        for p in self.particles:
            p.draw(surface)

    @property
    def alive(self):
        return len(self.particles) > 0 or self.flash_timer > 0


class ScreenShake:
    """Screen shake effect"""

    def __init__(self):
        self.intensity = 0
        self.decay = 0.85
        self.enabled = True   # di-sync dari GameSettings

    def add_shake(self, intensity):
        """Add shake, higher intensity = more shake"""
        if not self.enabled:
            return
        self.intensity = max(self.intensity, intensity)

    def update(self):
        self.intensity *= self.decay
        if self.intensity < 0.5:
            self.intensity = 0

    def get_offset(self):
        """Return (x, y) offset for shake"""
        if self.intensity <= 0:
            return (0, 0)
        return (
            random.randint(-int(self.intensity), int(self.intensity)),
            random.randint(-int(self.intensity), int(self.intensity))
        )


class EffectManager:
    """Central manager untuk semua effects"""

    def __init__(self):
        self.floating_texts = []
        self.particles = []
        self.explosions = []
        self.screen_shake = ScreenShake()
        # ═══ TIER 2 ADDITIONS ═══
        self.combo_counter = ComboCounter()
        self.wave_announcer = WaveAnnouncer()
        self.kill_feed = KillFeed()
        self.path_preview = PathPreview()
        self.achievement = AchievementPopup()
        # Ambil status screen shake dari settings sekali di awal
        self.sync_settings()

    def add_damage_number(self, x, y, damage, is_critical=False,
                          damage_type='normal'):
        """Add floating damage number (respect settings)"""
        from _core import GameSettings
        if not GameSettings().damage_numbers_enabled:
            return
        # Color berdasarkan type
        if damage_type == 'heal':
            color = (100, 255, 100)
            text = f"+{damage}"
        elif is_critical:
            color = (255, 220, 50)  # gold
            text = f"{damage}!"
        elif damage_type == 'fire':
            color = (255, 150, 50)
            text = str(damage)
        elif damage_type == 'ice':
            color = (150, 220, 255)
            text = str(damage)
        elif damage_type == 'magic':
            color = (200, 150, 255)
            text = str(damage)
        else:  # normal
            color = (255, 255, 255)
            text = str(damage)

        size = 'large' if is_critical else 'medium'

        # Slight random offset biar text tidak overlap
        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-3, 3)

        text = FloatingText(
            x + offset_x, y + offset_y,
            text, color=color, size=size,
            velocity=(0, -2), lifetime=45,
            critical=is_critical
        )
        self.floating_texts.append(text)

    def add_gold_popup(self, x, y, amount):
        """Add gold gained popup"""
        text = FloatingText(
            x, y - 10,
            f"+{amount}G", color=(255, 220, 50),
            size='medium',
            velocity=(0, -1.5), lifetime=50
        )
        self.floating_texts.append(text)

    def add_hit_particles(self, x, y, team="red", count=5):
        """Add hit spark particles"""
        if team == "blue":
            colors = [(100, 200, 255), (200, 240, 255)]
        else:
            colors = [(255, 150, 100), (255, 200, 150)]

        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 2.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(colors)

            self.particles.append(
                HitParticle(x, y, color, (vx, vy),
                            lifetime=random.randint(12, 20),
                            size=random.randint(2, 3)))

    def add_death_explosion(self, x, y, team="red", size='medium'):
        """Add death explosion"""
        self.explosions.append(DeathExplosion(x, y, team, size))

    def shake_screen(self, intensity=5):
        """
        Add screen shake (respect settings).

        Status setting di-cache di ScreenShake.enabled supaya tidak
        import + baca singleton tiap kali skill dipakai (fungsi ini
        dipanggil puluhan kali per detik saat combat ramai).
        """
        self.screen_shake.add_shake(intensity)

    def sync_settings(self):
        """Sync flag dari GameSettings. Panggil saat setting berubah."""
        try:
            from _core import GameSettings
            self.screen_shake.enabled = \
                GameSettings().screen_shake_enabled
        except Exception:
            pass

    def update(self):
        """Update all effects"""
        for t in self.floating_texts:
            t.update()
        self.floating_texts = [t for t in self.floating_texts if t.alive]

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for e in self.explosions:
            e.update()
        self.explosions = [e for e in self.explosions if e.alive]

        self.screen_shake.update()

        # ═══ TIER 2 UPDATES ═══
        self.combo_counter.update()
        self.wave_announcer.update()
        self.kill_feed.update()
        self.path_preview.update()
        self.achievement.update()

    def draw(self, surface, animation_time=0):
        """Draw world-space effects (ikut screen shake)"""
        self.path_preview.draw(surface, animation_time)
        for e in self.explosions:
            e.draw(surface)
        for p in self.particles:
            p.draw(surface)
        for t in self.floating_texts:
            t.draw(surface)

    def show_path_preview(self, lane_paths):
        """Trigger path preview"""
        self.path_preview.show(lane_paths)

    def draw_ui(self, surface, screen_w, screen_h):
        """Draw UI-space effects (tidak ikut shake)"""
        # ═══ NOTIFIKASI DIHAPUS (request user) ═══
        # Panel kanan kini berisi COMMAND saja - kill feed & kotak
        # notifikasi tidak lagi digambar di sana. Combo counter dan
        # popup ACHIEVEMENT tetap tampil DI MAP (layar arena), sama
        # seperti feedback command taktis.
        self.combo_counter.draw(surface, screen_w, screen_h)
        self.wave_announcer.draw(surface, screen_w, screen_h)
        self.achievement.draw(surface, screen_w, screen_h)

    # ═══ TIER 2 HELPER METHODS ═══
    def unlock_achievement(self, title, description, icon="star"):
        """Unlock an achievement - popup tampil DI MAP (bukan panel)."""
        self.achievement.unlock(title, description, icon)

    def register_kill(self, killer_name="Tower", victim_name="Enemy",
                      killer_team="blue"):
        """Register a kill (combo counter di map).

        Kill feed DIHAPUS (request user: notifikasi dihapus, panel
        diisi command saja) - method tetap ada untuk combo counter.
        """
        self.combo_counter.add_kill()

    def announce_wave(self, wave_num):
        """Trigger wave announcement"""
        self.wave_announcer.announce(wave_num)

    def get_shake_offset(self):
        return self.screen_shake.get_offset()


# ================================
# Tambahkan di effects.py (paling bawah)
# ================================


class ComboCounter:
    """Kill combo tracker dengan visual"""

    def __init__(self):
        self.count = 0
        self.timer = 0
        self.max_timer = 120  # 2 detik reset
        self.display_scale = 0.0
        self.target_scale = 1.0
        self.color_flash = 0
        self.last_combo = 0

    def add_kill(self):
        """Register a kill"""
        self.count += 1
        self.timer = self.max_timer
        self.target_scale = 1.3
        self.color_flash = 20

        # ═══ LABEL TIER KE PANEL KANAN ═══
        # Hanya saat MELEWATI ambang, bukan tiap kill - kalau tidak,
        # panel akan dibanjiri baris yang sama.
        _tier = None
        if self.count == 5:
            _tier = ("KILLING SPREE!", (100, 255, 100))
        elif self.count == 10:
            _tier = ("RAMPAGE!", (255, 200, 50))
        elif self.count == 15:
            _tier = ("UNSTOPPABLE!", (255, 100, 50))
        elif self.count == 20:
            _tier = ("GODLIKE!", (255, 50, 50))
        elif self.count == 3:
            _tier = ("COMBO x3", (255, 255, 255))
        if _tier:
            try:
                from mobile import sidepanel as _sp
                _sp.beri_tahu_global(_tier[0], _tier[1], 3000)
            except Exception:
                pass

    def update(self):
        # Timer countdown
        if self.timer > 0:
            self.timer -= 1
            if self.timer <= 0:
                # Combo expired
                self.last_combo = self.count
                self.count = 0

        # Scale animation
        if self.count > 0:
            if self.display_scale < self.target_scale:
                self.display_scale += (self.target_scale - self.display_scale) * 0.3
            else:
                self.target_scale = 1.0
                self.display_scale += (1.0 - self.display_scale) * 0.15
        else:
            self.display_scale *= 0.85
            if self.display_scale < 0.05:
                self.display_scale = 0.0

        # Color flash
        if self.color_flash > 0:
            self.color_flash -= 1

    def draw(self, surface, screen_w, screen_h):
        """Draw combo counter di sisi kanan atas"""
        if self.count < 2 and self.display_scale < 0.1:
            return

        # Position (kanan atas)
        cx = screen_w - 100
        cy = 100

        # Combo threshold colors
        if self.count >= 20:
            color = (255, 50, 50)
            label = "GODLIKE!"
        elif self.count >= 15:
            color = (255, 100, 50)
            label = "UNSTOPPABLE!"
        elif self.count >= 10:
            color = (255, 200, 50)
            label = "RAMPAGE!"
        elif self.count >= 5:
            color = (100, 255, 100)
            label = "KILLING SPREE!"
        else:
            color = (255, 255, 255)
            label = "COMBO"

        # Color flash effect (white pulse)
        if self.color_flash > 0:
            flash_ratio = self.color_flash / 20
            r = int(color[0] + (255 - color[0]) * flash_ratio)
            g = int(color[1] + (255 - color[1]) * flash_ratio)
            b = int(color[2] + (255 - color[2]) * flash_ratio)
            display_color = (r, g, b)
        else:
            display_color = color

        # Timer bar (jam pasir progress)
        timer_ratio = self.timer / self.max_timer
        timer_w = 80
        timer_x = cx - timer_w // 2
        timer_y = cy + 40

        if self.count >= 2:
            pygame.draw.rect(surface, (40, 40, 40),
                             (timer_x, timer_y, timer_w, 4))
            fill_w = int(timer_w * timer_ratio)
            pygame.draw.rect(surface, color,
                             (timer_x, timer_y, fill_w, 4))

        # Combo count (big text)
        count_size = int(48 * self.display_scale)
        if count_size < 8:
            return

        count_font = get_font(count_size, 'body_bold')
        label_font = get_font(24)  # 18->24

        count_text = count_font.render(f"x{self.count}", True,
                                       display_color)
        count_rect = count_text.get_rect(center=(cx, cy))

        # Shadow (8 arah -> 1 arah saja kalau alpha blit mahal)
        from mobile.perf import Quality as _Q
        _offsets = ([(dx, dy) for dx in (-2, 0, 2) for dy in (-2, 0, 2)
                     if (dx, dy) != (0, 0)] if _Q.cheap_alpha
                    else [(2, 2)])
        for dx, dy in _offsets:
            shadow = count_font.render(f"x{self.count}", True,
                                       (0, 0, 0))
            surface.blit(shadow,
                         (count_rect.x + dx, count_rect.y + dy))

        surface.blit(count_text, count_rect)

        # Label
        if self.count >= 5:
            label_text = label_font.render(label, True, display_color)
            label_rect = label_text.get_rect(center=(cx, cy - 30))

            # Shadow
            shadow = label_font.render(label, True, (0, 0, 0))
            surface.blit(shadow, (label_rect.x + 1, label_rect.y + 1))
            surface.blit(label_text, label_rect)


class WaveAnnouncer:
    """Big animated banner untuk wave announcement"""

    def __init__(self):
        self.active = False
        self.wave_num = 0
        self.timer = 0
        self.duration = 120  # 2 detik

    def announce(self, wave_num):
        """Trigger wave announcement"""
        self.active = True
        self.wave_num = wave_num
        self.timer = self.duration

    def update(self):
        if not self.active:
            return

        self.timer -= 1
        if self.timer <= 0:
            self.active = False

    def draw(self, surface, screen_w, screen_h):
        if not self.active:
            return

        progress = 1 - (self.timer / self.duration)

        # 3 phases: slide in (0-0.2), hold (0.2-0.7), slide out (0.7-1.0)
        if progress < 0.2:
            # Slide in from left
            slide_progress = progress / 0.2
            eased = _ease_out_back(slide_progress)
            x_offset = -screen_w + int(screen_w * eased)
            alpha = int(255 * min(1.0, slide_progress * 2))
        elif progress < 0.7:
            # Hold
            x_offset = 0
            alpha = 255
        else:
            # Slide out to right
            slide_progress = (progress - 0.7) / 0.3
            eased = _ease_in_back(slide_progress)
            x_offset = int(screen_w * eased)
            alpha = int(255 * (1 - slide_progress))

        cx = screen_w // 2 + x_offset
        cy = screen_h // 3

        # Background banner
        banner_w = 400
        banner_h = 80

        banner_surf = pygame.Surface((banner_w, banner_h),
                                     pygame.SRCALPHA)

        # Gradient background
        for i in range(banner_h):
            grad_alpha = int(alpha * (1 - abs(i - banner_h / 2) / (banner_h / 2) * 0.3))
            color = (20, 20, 40, grad_alpha)
            pygame.draw.rect(banner_surf, color,
                             (0, i, banner_w, 1))

        # Gold border
        pygame.draw.rect(banner_surf, (255, 220, 50, alpha),
                         (0, 0, banner_w, banner_h), 3)
        pygame.draw.rect(banner_surf, (255, 250, 180, alpha),
                         (2, 2, banner_w - 4, banner_h - 4), 1)

        # Diagonal lines decoration
        for i in range(0, banner_w, 10):
            line_alpha = alpha // 4
            pygame.draw.line(banner_surf,
                             (255, 220, 50, line_alpha),
                             (i, 0), (i + 10, banner_h), 1)

        surface.blit(banner_surf, (cx - banner_w // 2, cy - banner_h // 2))

        # Text
        wave_font = title_font(46)
        sub_font = get_font(22)

        # "WAVE X" text
        wave_text = wave_font.render(f"WAVE {self.wave_num}", True,
                                     (255, 220, 50))
        wave_rect = wave_text.get_rect(center=(cx, cy - 8))

        # Text shadow
        shadow = wave_font.render(f"WAVE {self.wave_num}", True,
                                  (0, 0, 0))
        for dx, dy in [(-2, -2), (2, 2), (-2, 2), (2, -2)]:
            surface.blit(shadow, (wave_rect.x + dx, wave_rect.y + dy))

        # Set alpha
        alpha_surf = pygame.Surface(wave_text.get_size(),
                                    pygame.SRCALPHA)
        alpha_surf.fill((255, 255, 255, alpha))
        wave_text.blit(alpha_surf, (0, 0),
                       special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(wave_text, wave_rect)

        # Subtitle
        sub_text = sub_font.render("ENEMIES INCOMING!", True,
                                   (200, 200, 220))
        sub_rect = sub_text.get_rect(center=(cx, cy + 22))
        surface.blit(sub_text, sub_rect)


class KillFeed:
    """Kill feed di pojok kanan atas"""

    def __init__(self):
        self.entries = []  # list of (text, color, lifetime, y_offset)

    def add_kill(self, killer_name, victim_name, killer_team="blue"):
        """Add kill entry"""
        # Icon berdasarkan team
        if killer_team == "blue":
            arrow = ">>"
            color = (100, 200, 255)
        else:
            arrow = "<<"
            color = (255, 100, 100)

        text = f"{killer_name} {arrow} {victim_name}"

        entry = {
            'text': text,
            'color': color,
            'lifetime': 180,  # 3 detik
            'max_lifetime': 180,
            'y_offset': 0,
            'target_y': 0,
        }

        # Push existing entries down
        for e in self.entries:
            e['target_y'] += 20

        self.entries.append(entry)

        # Keep only last 5
        if len(self.entries) > 5:
            self.entries.pop(0)

    def update(self):
        for e in self.entries:
            e['lifetime'] -= 1
            # Smooth Y transition
            e['y_offset'] += (e['target_y'] - e['y_offset']) * 0.2

        self.entries = [e for e in self.entries if e['lifetime'] > 0]

    def draw(self, surface, screen_w, screen_h):
        base_x = screen_w - 20
        base_y = 250  # di bawah combo counter

        font = get_font(22, 'body_medium')  # 16->22

        for i, entry in enumerate(self.entries):
            # Alpha (fade in first 15 frames, fade out last 45)
            if entry['lifetime'] > 45:
                if entry['lifetime'] > entry['max_lifetime'] - 15:
                    # Fade in
                    fade_progress = (entry['max_lifetime'] - entry['lifetime']) / 15
                    alpha = int(255 * fade_progress)
                else:
                    alpha = 255
            else:
                # Fade out
                alpha = int(255 * (entry['lifetime'] / 45))

            if alpha <= 0:
                continue

            y = base_y + int(entry['y_offset'])

            # Slide-in animation
            if entry['lifetime'] > entry['max_lifetime'] - 15:
                slide_progress = (entry['max_lifetime'] - entry['lifetime']) / 15
                slide_x = int((1 - slide_progress) * 100)
            else:
                slide_x = 0

            # Render text
            text_surf = font.render(entry['text'], True, entry['color'])
            text_rect = text_surf.get_rect(topright=(base_x + slide_x, y))

            # Background box
            bg_rect = text_rect.inflate(12, 4)
            bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, alpha // 2))
            surface.blit(bg_surf, bg_rect)

            # Border (team color)
            border_color = (*entry['color'], alpha // 2)
            border_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(border_surf, border_color,
                             (0, 0, bg_rect.width, bg_rect.height),
                             1, border_radius=3)
            surface.blit(border_surf, bg_rect)

            # Text
            text_surf.set_alpha(alpha)
            surface.blit(text_surf, text_rect)


class PopupAnimation:
    """Wrapper untuk animate popup slide-in"""

    def __init__(self):
        self.progress = 0.0
        self.target = 1.0
        self.speed = 0.15

    def show(self):
        """Trigger show animation"""
        self.progress = 0.0
        self.target = 1.0

    def hide(self):
        """Trigger hide animation"""
        self.target = 0.0

    def update(self):
        diff = self.target - self.progress
        self.progress += diff * self.speed

        # Clamp
        if abs(diff) < 0.01:
            self.progress = self.target

    def get_scale(self):
        """Return scale (0-1) for pop animation"""
        return _ease_out_back(self.progress)

    def get_offset_y(self):
        """Return Y offset for slide animation"""
        return int((1 - self.progress) * 30)


# ═══════════════════════════════════════════════════════
# EASING FUNCTIONS
# ═══════════════════════════════════════════════════════

def _ease_out_back(t):
    """Ease out with bounce"""
    c1 = 1.70158
    c3 = c1 + 1
    t1 = t - 1
    return 1 + c3 * (t1 * t1 * t1) + c1 * (t1 * t1)


def _ease_in_back(t):
    """Ease in with acceleration"""
    c1 = 1.70158
    c3 = c1 + 1
    return c3 * t * t * t - c1 * t * t


def _ease_out_cubic(t):
    """Smooth ease out"""
    return 1 - pow(1 - t, 3)


def _ease_out_elastic(t):
    """Elastic bounce effect"""
    c4 = (2 * math.pi) / 3
    if t == 0:
        return 0
    if t == 1:
        return 1
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


# ================================
# Tambahkan di effects.py
# ================================


class PathPreview:
    """Preview lane path saat wave dimulai"""

    def __init__(self):
        self.active = False
        self.paths = []  # list of lane paths
        self.timer = 0
        self.duration = 120  # 2 detik

    def show(self, lane_paths):
        """Show path preview untuk lanes tertentu"""
        self.active = True
        self.paths = lane_paths
        self.timer = self.duration

    def update(self):
        if not self.active:
            return
        self.timer -= 1
        if self.timer <= 0:
            self.active = False
            self.paths = []

    def draw(self, surface, animation_time):
        if not self.active:
            return

        # Alpha fade
        if self.timer > self.duration - 20:
            # Fade in
            alpha_ratio = (self.duration - self.timer) / 20
        elif self.timer < 40:
            # Fade out
            alpha_ratio = self.timer / 40
        else:
            alpha_ratio = 1.0

        alpha = int(200 * alpha_ratio)
        if alpha <= 0:
            return

        # Animated moving dashes
        offset = int(animation_time * 2) % 20

        for lane_path in self.paths:
            if len(lane_path) < 2:
                continue

            # Draw arrows sepanjang path
            for i in range(0, len(lane_path) - 1, 8):
                x, y = lane_path[i]

                # Get direction to next point
                if i + 4 < len(lane_path):
                    nx, ny = lane_path[i + 4]
                    dx = nx - x
                    dy = ny - y
                    dist = math.hypot(dx, dy) or 1
                    dx /= dist
                    dy /= dist
                else:
                    dx, dy = 1, 0

                # Draw arrow with pulse
                pulse_i = (i // 8 + offset // 5) % 4

                if pulse_i == 0:
                    arrow_color = (255, 100, 100, alpha)
                    arrow_size = 8
                else:
                    arrow_color = (255, 100, 100, alpha // 2)
                    arrow_size = 5

                # Arrow triangle
                angle = math.atan2(dy, dx)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)

                arrow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                pts = [
                    (10 + int(cos_a * arrow_size),
                     10 + int(sin_a * arrow_size)),
                    (10 + int(-cos_a * arrow_size // 2 - sin_a * arrow_size // 2),
                     10 + int(-sin_a * arrow_size // 2 + cos_a * arrow_size // 2)),
                    (10 + int(-cos_a * arrow_size // 2 + sin_a * arrow_size // 2),
                     10 + int(-sin_a * arrow_size // 2 - cos_a * arrow_size // 2)),
                ]
                pygame.draw.polygon(arrow_surf, arrow_color, pts)
                surface.blit(arrow_surf, (int(x) - 10, int(y) - 10))


# ================================
# Tambahkan di effects.py
# ================================


class AchievementPopup:
    """Achievement notification popup"""

    def __init__(self):
        self.queue = []
        self.current = None
        self.timer = 0
        self.duration = 180  # 3 detik

    def unlock(self, title, description, icon_type="star"):
        """Unlock achievement"""
        self.queue.append({
            'title': title,
            'description': description,
            'icon_type': icon_type,
        })

    def update(self):
        # Countdown current
        if self.current:
            self.timer -= 1
            if self.timer <= 0:
                self.current = None

        # Show next in queue
        if not self.current and self.queue:
            self.current = self.queue.pop(0)
            self.timer = self.duration

    def draw(self, surface, screen_w, screen_h):
        if not self.current:
            return

        progress = 1 - (self.timer / self.duration)

        # Slide-in/out animation
        if progress < 0.15:
            # Slide in from right
            slide_ratio = progress / 0.15
            eased = _ease_out_back(slide_ratio)
            x_offset = int((1 - eased) * 300)
            alpha = int(255 * slide_ratio)
        elif progress < 0.85:
            # Hold
            x_offset = 0
            alpha = 255
        else:
            # Slide out to right
            slide_ratio = (progress - 0.85) / 0.15
            x_offset = int(slide_ratio * 300)
            alpha = int(255 * (1 - slide_ratio))

        # Position (kanan atas, di bawah combo counter)
        panel_w = 280
        panel_h = 60
        panel_x = screen_w - panel_w - 20 + x_offset
        panel_y = 180

        # Background
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)

        # Gradient BG (dark gold)
        for i in range(panel_h):
            grad = int(20 + i * 0.3)
            pygame.draw.line(panel_surf,
                             (grad, grad, grad // 2, alpha),
                             (0, i), (panel_w, i))

        # Gold border
        pygame.draw.rect(panel_surf, (255, 220, 50, alpha),
                         (0, 0, panel_w, panel_h), 3,
                         border_radius=6)
        pygame.draw.rect(panel_surf, (255, 250, 180, alpha),
                         (2, 2, panel_w - 4, panel_h - 4), 1,
                         border_radius=5)

        # Draw icon (di kiri)
        icon_x = 15
        icon_y = panel_h // 2
        self._draw_icon(panel_surf, icon_x, icon_y,
                        self.current['icon_type'], alpha)

        # "ACHIEVEMENT UNLOCKED" text (kecil, atas) - DIPERBESAR
        small_font = get_font(24)  # 18->24  # 12->18
        title_font = get_font(24, 'body_semibold')  # 18->24
        desc_font = get_font(20)  # 14->20

        header = small_font.render("ACHIEVEMENT UNLOCKED",
                                   True, (255, 220, 50))
        header_alpha = pygame.Surface(header.get_size(),
                                      pygame.SRCALPHA)
        header_alpha.fill((255, 255, 255, alpha))
        header.blit(header_alpha, (0, 0),
                    special_flags=pygame.BLEND_RGBA_MULT)
        panel_surf.blit(header, (55, 8))

        # Title (bold, tengah)
        title = title_font.render(self.current['title'], True,
                                  (255, 255, 255))
        title_alpha = pygame.Surface(title.get_size(),
                                     pygame.SRCALPHA)
        title_alpha.fill((255, 255, 255, alpha))
        title.blit(title_alpha, (0, 0),
                   special_flags=pygame.BLEND_RGBA_MULT)
        panel_surf.blit(title, (55, 22))

        # Description (kecil, bawah)
        desc = desc_font.render(self.current['description'],
                                True, (200, 200, 200))
        desc_alpha = pygame.Surface(desc.get_size(), pygame.SRCALPHA)
        desc_alpha.fill((255, 255, 255, alpha))
        desc.blit(desc_alpha, (0, 0),
                  special_flags=pygame.BLEND_RGBA_MULT)
        panel_surf.blit(desc, (55, 42))

        # Blit panel
        surface.blit(panel_surf, (panel_x, panel_y))

        # Glow effect di sekitar (kalau baru muncul)
        if progress < 0.3:
            glow_alpha = int(150 * (1 - progress / 0.3))
            glow_surf = pygame.Surface((panel_w + 20, panel_h + 20),
                                       pygame.SRCALPHA)
            pygame.draw.rect(glow_surf,
                             (255, 220, 50, glow_alpha),
                             (0, 0, panel_w + 20, panel_h + 20),
                             border_radius=10)
            surface.blit(glow_surf, (panel_x - 10, panel_y - 10))

    def _draw_icon(self, surface, cx, cy, icon_type, alpha):
        """Draw achievement icon"""
        # Circle background
        circle_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.circle(circle_surf, (60, 40, 10, alpha),
                           (18, 18), 16)
        pygame.draw.circle(circle_surf, (255, 220, 50, alpha),
                           (18, 18), 16, 2)
        surface.blit(circle_surf, (cx - 18, cy - 18))

        # Icon drawing berdasarkan type
        if icon_type == "star":
            # Star shape
            pts = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r = 8 if i % 2 == 0 else 4
                pts.append((cx + math.cos(angle) * r,
                            cy + math.sin(angle) * r))
            pygame.draw.polygon(surface, (255, 220, 50), pts)
            pygame.draw.polygon(surface, (255, 250, 180), pts, 1)

        elif icon_type == "sword":
            # Sword icon
            pygame.draw.polygon(surface, (200, 200, 220), [
                (cx, cy - 10), (cx + 3, cy - 7),
                (cx + 3, cy + 5), (cx - 3, cy + 5),
                (cx - 3, cy - 7),
            ])
            pygame.draw.rect(surface, (100, 60, 30),
                             (cx - 5, cy + 5, 10, 3))
            pygame.draw.rect(surface, (60, 40, 20),
                             (cx - 2, cy + 8, 4, 4))

        elif icon_type == "skull":
            # Skull icon
            pygame.draw.circle(surface, (240, 240, 220),
                               (cx, cy - 2), 8)
            pygame.draw.rect(surface, (0, 0, 0), (cx - 3, cy - 4, 2, 2))
            pygame.draw.rect(surface, (0, 0, 0), (cx + 1, cy - 4, 2, 2))
            pygame.draw.rect(surface, (240, 240, 220),
                             (cx - 4, cy + 4, 8, 4))
            pygame.draw.rect(surface, (0, 0, 0), (cx - 2, cy + 5, 1, 3))
            pygame.draw.rect(surface, (0, 0, 0), (cx + 1, cy + 5, 1, 3))

        elif icon_type == "shield":
            # Shield icon
            pygame.draw.polygon(surface, (100, 200, 255), [
                (cx, cy - 8), (cx + 7, cy - 5),
                (cx + 7, cy + 3), (cx, cy + 8),
                (cx - 7, cy + 3), (cx - 7, cy - 5),
            ])
            pygame.draw.polygon(surface, (255, 255, 255), [
                (cx, cy - 8), (cx + 7, cy - 5),
                (cx + 7, cy + 3), (cx, cy + 8),
                (cx - 7, cy + 3), (cx - 7, cy - 5),
            ], 2)

        elif icon_type == "gold":
            # Gold coin
            pygame.draw.circle(surface, (200, 150, 20),
                               (cx, cy), 10)
            pygame.draw.circle(surface, (255, 220, 50),
                               (cx, cy), 9)
            pygame.draw.circle(surface, (255, 250, 180),
                               (cx - 2, cy - 2), 4)
            # $ symbol - DIPERBESAR 14->20
            small_font = get_font(20)
            dollar = small_font.render("$", True, (100, 60, 10))
            dollar_rect = dollar.get_rect(center=(cx, cy))
            surface.blit(dollar, dollar_rect)


# ====================================================================
# effects_death.py
# ====================================================================

# ================================
# effects_death.py
# Boss Death Animation Dramatic
# ================================

import pygame
import math
import random




# ---------------------------------------------------------------
# Teks prompt mulai - ikut mode input (sentuh / keyboard)
# ---------------------------------------------------------------
def _begin_prompt_text():
    try:
        from mobile import platform_utils as _plat
        if _plat.TOUCH_MODE:
            return "TAP TO BEGIN"
    except Exception:
        pass
    return "PRESS SPACE TO BEGIN"


# ---------------------------------------------------------------
# Label tombol skip, otomatis ikut input mode (keyboard/controller)
# ---------------------------------------------------------------
def _skip_button_label():
    """Label aksi skip: 'TAP' (sentuh), 'SPACE' (keyboard)."""
    try:
        from mobile import platform_utils as _plat
        if _plat.TOUCH_MODE:
            return 'TAP'
    except Exception:
        pass
    try:
        import __main__
        game = getattr(__main__, 'game_instance', None)
        mgr = getattr(game, 'controller_mgr', None)
        if mgr is not None and mgr.is_controller_mode():
            return mgr.get_action_label('skip')
    except Exception:
        pass
    return 'SPACE'

class BossDeathAnimation:
    """
    Dramatic boss death sequence:
    - Multiple explosion waves
    - Body dissolve + shatter fragments
    - Screen white flash
    - Camera shake intense
    - Post-death celebration (true boss only)
    """

    def __init__(self, boss, screen_w, screen_h):
        self.boss = boss
        self.screen_w = screen_w
        self.screen_h = screen_h

        # Boss info (cache karena boss akan di-destroy)
        self.boss_x = boss.x
        self.boss_y = boss.y
        self.boss_name = boss.name
        self.boss_title = boss.title
        self.boss_class = boss.boss_class
        self.boss_color = boss.color
        self.boss_color_dark = boss.color_dark
        self.entrance_color = boss.entrance_color
        self.boss_gold_reward = boss.gold_reward
        self.boss_radius = boss.radius

        # Animation state
        self.active = True

        # Duration berdasarkan tier
        if self.boss_class == "true":
            self.duration = 90  # 1.5 detik full dramatic
            self.show_celebration = True
        else:
            self.duration = 60  # 1.0 detik medium
            self.show_celebration = False

        self.timer = self.duration

        # Explosion waves (3 bertahap)
        # Each wave: (start_frame, max_radius, color)
        if self.boss_class == "true":
            self.explosion_waves = [
                (0, 60, self.entrance_color),
                (15, 120, (255, 200, 100)),
                (30, 200, (255, 255, 200)),
            ]
        else:
            self.explosion_waves = [
                (0, 50, self.entrance_color),
                (15, 100, (255, 220, 150)),
            ]

        # Fragments (shatter effect)
        self.fragments = self._init_fragments()

        # Rising particles
        self.rising_particles = self._init_rising_particles()

        # Sound
        self._sound_played = False

        # Celebration state (untuk true boss)
        self.celebration_timer = 0
        self.celebration_duration = 120  # 2 detik after death
        self.celebration_active = False

        # Fonts (profesional: Cinzel judul, Barlow body) - DIPERBESAR
        try:
            self.font_huge = title_font(66)
            self.font_big = title_font(46)  # 44->46
            self.font_medium = get_font(32, "body_semibold")  # 28->32
            self.font_small = get_font(24, "body_medium")     # 20->24
        except:
            self.font_huge = title_font(66)
            self.font_big = title_font(46)
            self.font_medium = get_font(32, "body_semibold")
            self.font_small = get_font(24, "body_medium")

    def _init_fragments(self):
        """Init shatter fragments dari boss body"""
        fragments = []
        num_fragments = 25 if self.boss_class == "true" else 15

        for _ in range(num_fragments):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            fragments.append({
                'x': self.boss_x + random.uniform(-15, 15),
                'y': self.boss_y + random.uniform(-15, 15),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 2,  # slight up
                'size': random.randint(3, 8),
                'color': random.choice([
                    self.boss_color,
                    self.boss_color_dark,
                    self.entrance_color,
                ]),
                'rotation': random.uniform(0, math.pi * 2),
                'rot_speed': random.uniform(-0.3, 0.3),
                'gravity': 0.2,
                'life': 60,
                'max_life': 60,
            })
        return fragments

    def _init_rising_particles(self):
        """Init rising particles (soul-like effect)"""
        particles = []
        num = 30 if self.boss_class == "true" else 15

        for _ in range(num):
            particles.append({
                'x': self.boss_x + random.uniform(-30, 30),
                'y': self.boss_y + random.uniform(-10, 10),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-3, -1),
                'size': random.randint(2, 5),
                'color': self.entrance_color,
                'life': random.randint(60, 100),
                'max_life': 100,
                'phase': random.uniform(0, math.pi * 2),
            })
        return particles

    def update(self):
        """Update animation timer"""
        if not self.active:
            # Update celebration if active
            if self.celebration_active:
                self.celebration_timer -= 1
                if self.celebration_timer <= 0:
                    self.celebration_active = False
            return

        self.timer -= 1

        # Play sound at start
        if not self._sound_played:
            self._sound_played = True
            try:
                from _system import SoundManager
                if self.boss_class == "true":
                    SoundManager().play('explosion', volume_mult=1.5)
                    SoundManager().play('victory', volume_mult=0.7)
                else:
                    SoundManager().play('explosion', volume_mult=1.0)
            except Exception:
                pass

        # Update fragments
        for frag in self.fragments:
            frag['x'] += frag['vx']
            frag['y'] += frag['vy']
            frag['vy'] += frag['gravity']
            frag['rotation'] += frag['rot_speed']
            frag['life'] -= 1

        # Update rising particles
        for p in self.rising_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['phase'] += 0.1
            # Wave motion
            p['x'] += math.sin(p['phase']) * 0.5
            p['life'] -= 1

        # End of death animation
        if self.timer <= 0:
            self.active = False
            # Trigger celebration for true boss
            if self.show_celebration:
                self.celebration_active = True
                self.celebration_timer = self.celebration_duration

                # Play fanfare
                try:
                    from _system import SoundManager
                    SoundManager().play('victory', volume_mult=1.0)
                except Exception:
                    pass

    def handle_skip(self, key=None, click=False):
        """Skip celebration only (death animation tetap play)"""
        if self.celebration_active:
            if key == pygame.K_SPACE or key == pygame.K_ESCAPE or click:
                self.celebration_active = False
                return True
        return False

    def is_active(self):
        """True kalau death animation OR celebration masih running"""
        return self.active or self.celebration_active

    def is_death_active(self):
        """Cuma death phase (untuk pause gameplay)"""
        return self.active

    def draw(self, surface):
        """Draw death animation + celebration"""
        if self.active:
            self._draw_death_sequence(surface)

        if self.celebration_active:
            self._draw_celebration(surface)

    def _draw_death_sequence(self, surface):
        """Draw main death animation"""
        elapsed = self.duration - self.timer
        progress = elapsed / self.duration

        # ═══ 1. WHITE FLASH (di awal) ═══
        if elapsed < 15:
            flash_alpha = int(200 * (1 - elapsed / 15))
            from mobile.perf import flash as _flash
            _flash(surface, flash_alpha)

        # ═══ 2. EXPLOSION WAVES ═══
        for start_frame, max_radius, color in self.explosion_waves:
            wave_elapsed = elapsed - start_frame
            if wave_elapsed < 0:
                continue

            # Wave duration 40 frames
            wave_duration = 40
            if wave_elapsed >= wave_duration:
                continue

            wave_progress = wave_elapsed / wave_duration
            radius = int(max_radius * wave_progress)
            alpha = int(220 * (1 - wave_progress))

            if alpha <= 0 or radius <= 0:
                continue

            # Outer ring
            ring_surf = pygame.Surface(
                (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)

            # Multiple concentric rings
            for r in range(radius, max(0, radius - 20), -3):
                a = int(alpha * (r / radius))
                pygame.draw.circle(ring_surf, (*color, a),
                                   (radius + 2, radius + 2),
                                   r, 3)

            # Solid inner (fading)
            inner_alpha = alpha // 2
            pygame.draw.circle(ring_surf,
                               (*color, inner_alpha),
                               (radius + 2, radius + 2),
                               max(1, radius - 15))

            surface.blit(ring_surf,
                         (int(self.boss_x) - radius,
                          int(self.boss_y) - radius))

        # ═══ 3. BODY DISSOLVE (fading circle) ═══
        if progress < 0.5:
            dissolve_alpha = int(255 * (1 - progress * 2))
            dissolve_size = int(self.boss_radius * (1 - progress * 0.5))

            body_surf = pygame.Surface(
                (dissolve_size * 3, dissolve_size * 3),
                pygame.SRCALPHA)

            # Fading boss body silhouette
            pygame.draw.circle(body_surf,
                               (*self.boss_color, dissolve_alpha),
                               (dissolve_size * 3 // 2,
                                dissolve_size * 3 // 2),
                               dissolve_size)
            pygame.draw.circle(body_surf,
                               (*self.entrance_color,
                                dissolve_alpha // 2),
                               (dissolve_size * 3 // 2,
                                dissolve_size * 3 // 2),
                               dissolve_size // 2)

            surface.blit(body_surf,
                         (int(self.boss_x) - dissolve_size * 3 // 2,
                          int(self.boss_y) - dissolve_size * 3 // 2))

        # ═══ 4. FRAGMENTS (shatter) ═══
        for frag in self.fragments:
            if frag['life'] <= 0:
                continue

            life_ratio = frag['life'] / frag['max_life']
            alpha = int(255 * life_ratio)

            if alpha < 10:
                continue

            # Rotate fragment (simple square shape)
            size = frag['size']
            frag_surf = pygame.Surface(
                (size * 3, size * 3), pygame.SRCALPHA)

            # Draw rotated square (simple)
            cos_r = math.cos(frag['rotation'])
            sin_r = math.sin(frag['rotation'])

            # 4 corners
            pts = []
            for corner_x, corner_y in [(-size, -size), (size, -size),
                                         (size, size), (-size, size)]:
                rx = corner_x * cos_r - corner_y * sin_r
                ry = corner_x * sin_r + corner_y * cos_r
                pts.append((size * 3 // 2 + rx,
                             size * 3 // 2 + ry))

            pygame.draw.polygon(frag_surf,
                                (*frag['color'], alpha), pts)

            # Bright edge
            pygame.draw.polygon(frag_surf,
                                (*self.entrance_color, alpha),
                                pts, 1)

            surface.blit(frag_surf,
                         (int(frag['x']) - size * 3 // 2,
                          int(frag['y']) - size * 3 // 2))

        # ═══ 5. RISING PARTICLES (soul effect) ═══
        for p in self.rising_particles:
            if p['life'] <= 0:
                continue

            life_ratio = p['life'] / p['max_life']
            alpha = int(200 * life_ratio)

            if alpha < 10:
                continue

            # Rising particle with glow
            size = p['size']
            p_surf = pygame.Surface(
                (size * 4, size * 4), pygame.SRCALPHA)

            # Glow
            for r in range(size + 2, 0, -1):
                a = int(alpha * (1 - r / (size + 2)))
                pygame.draw.circle(p_surf,
                                   (*p['color'], a),
                                   (size * 2, size * 2), r)

            # Core
            pygame.draw.circle(p_surf,
                               (255, 255, 255, alpha),
                               (size * 2, size * 2), 1)

            surface.blit(p_surf,
                         (int(p['x']) - size * 2,
                          int(p['y']) - size * 2))

    def _draw_celebration(self, surface):
        """Draw post-death celebration (true boss only)"""
        elapsed = self.celebration_duration - self.celebration_timer
        progress = elapsed / self.celebration_duration

        # ═══ DARK OVERLAY ═══
        if progress < 0.15:
            overlay_alpha = int(180 * (progress / 0.15))
        elif progress > 0.85:
            overlay_alpha = int(180 * (1 - (progress - 0.85) / 0.15))
        else:
            overlay_alpha = 180

        from mobile.perf import darken
        darken(surface, overlay_alpha)

        # ═══ TINT OVERLAY (victory gold) ═══
        if progress < 0.85:
            tint = pygame.Surface(
                (self.screen_w, self.screen_h), pygame.SRCALPHA)
            tint.fill((80, 60, 20, 40))
            surface.blit(tint, (0, 0))

        # ═══ CELEBRATION TEXT ═══
        cx = self.screen_w // 2
        cy = self.screen_h // 2 - 50

        # Text bounce animation
        if progress < 0.3:
            bounce_prog = progress / 0.3
            eased = 1 - (1 - bounce_prog) ** 3
            text_alpha = int(255 * eased)
            text_offset_y = int((1 - eased) * 60)
        elif progress > 0.85:
            text_alpha = int(255 * (1 - (progress - 0.85) / 0.15))
            text_offset_y = 0
        else:
            text_alpha = 255
            text_offset_y = 0

        # ═══ "BOSS DEFEATED!" ═══
        # Big shadow
        from mobile.perf import Quality as _Qz
        for offset in (range(6, 0, -1) if _Qz.cheap_alpha else (3,)):
            shadow = self.font_huge.render(
                "BOSS DEFEATED!", True, (0, 0, 0))
            shadow.set_alpha(min(text_alpha, 80))
            shadow_rect = shadow.get_rect(
                center=(cx + offset,
                        cy - 40 + text_offset_y + offset))
            surface.blit(shadow, shadow_rect)

        # Main text (gold)
        title = self.font_huge.render(
            "BOSS DEFEATED!", True, (255, 220, 100))
        title.set_alpha(text_alpha)
        title_rect = title.get_rect(
            center=(cx, cy - 40 + text_offset_y))
        surface.blit(title, title_rect)

        # ═══ BOSS NAME ═══
        name_surf = self.font_big.render(
            self.boss_name, True, self.entrance_color)
        name_surf.set_alpha(text_alpha)
        name_rect = name_surf.get_rect(
            center=(cx, cy + 30 + text_offset_y))

        # Shadow
        name_shadow = self.font_big.render(
            self.boss_name, True, (0, 0, 0))
        name_shadow.set_alpha(text_alpha // 2)
        surface.blit(name_shadow,
                     (name_rect.x + 2, name_rect.y + 2))
        surface.blit(name_surf, name_rect)

        # ═══ TITLE ═══
        title_text = f'"{self.boss_title}"'
        title_surf = self.font_medium.render(
            title_text, True, (200, 200, 220))
        title_surf.set_alpha(text_alpha)
        title_rect = title_surf.get_rect(
            center=(cx, cy + 75 + text_offset_y))
        surface.blit(title_surf, title_rect)

        # ═══ REWARD INFO ═══
        if progress > 0.3:
            reward_alpha = min(255,
                               int(255 * (progress - 0.3) / 0.3))

            # Gold reward
            reward_text = self.font_medium.render(
                f"+ {self.boss_gold_reward} GOLD",
                True, (255, 220, 100))
            reward_text.set_alpha(reward_alpha)
            reward_rect = reward_text.get_rect(
                center=(cx, cy + 130))

            # Gold coin icon (simple circle)
            pygame.draw.circle(surface, (255, 200, 50),
                               (reward_rect.left - 30, reward_rect.centery),
                               10)
            pygame.draw.circle(surface, (200, 150, 30),
                               (reward_rect.left - 30, reward_rect.centery),
                               10, 2)
            coin_font = get_font(22, 'body_bold')  # 16->22
            dollar = coin_font.render("$", True, (100, 60, 10))
            dollar_rect = dollar.get_rect(
                center=(reward_rect.left - 30, reward_rect.centery))
            surface.blit(dollar, dollar_rect)

            surface.blit(reward_text, reward_rect)

            # Hero unlock hint
            unlock_text = self.font_small.render(
                "★ Hero Unlocked! ★",
                True, (255, 180, 220))
            unlock_text.set_alpha(reward_alpha)
            unlock_rect = unlock_text.get_rect(
                center=(cx, cy + 170))
            surface.blit(unlock_text, unlock_rect)

        # ═══ DECORATIVE STARS ═══
        if progress > 0.4:
            # Rotating stars around text
            for i in range(6):
                angle = pygame.time.get_ticks() * 0.001 + \
                    i * math.pi / 3
                radius = 220
                sx = cx + int(math.cos(angle) * radius)
                sy = cy + int(math.sin(angle) * 60)

                # Star sparkle
                pulse = math.sin(pygame.time.get_ticks() * 0.005 +
                                 i) * 0.3 + 0.7

                pygame.draw.circle(surface, (255, 220, 100),
                                   (sx, sy), int(4 * pulse))
                pygame.draw.circle(surface, (255, 255, 255),
                                   (sx, sy), int(2 * pulse))

        # ═══ SKIP HINT ═══
        if progress > 0.5:
            hint_pulse = math.sin(pygame.time.get_ticks() *
                                   0.005) * 0.3 + 0.7
            hint_alpha = int(180 * hint_pulse)

            hint_text = self.font_small.render(
                f"[{_skip_button_label()}] to continue",
                True, (200, 200, 200))
            hint_text.set_alpha(hint_alpha)
            hint_rect = hint_text.get_rect(
                center=(cx, self.screen_h - 40))
            surface.blit(hint_text, hint_rect)


# ====================================================================
# effects_intro.py
# ====================================================================

# ================================
# effects_intro.py
# Boss Intro Cinematic
# ================================

import pygame
import math
import random

class BossIntroCinematic:
    """
    Dramatic boss intro screen:
    - Pause gameplay
    - Boss silhouette slide-in
    - Name + title with glow animation
    - HP bar preview
    - Skip-able dengan click/space
    """

    def __init__(self, boss, screen_w, screen_h):
        self.boss = boss
        self.screen_w = screen_w
        self.screen_h = screen_h

        # Timing
        self.duration = 100  # 1.7 detik @ 60fps
        self.timer = self.duration
        self.active = True

        # Animation phases
        # 0-15: overlay fade in
        # 15-45: boss slide in from left
        # 45-90: name + title bounce
        # 90-120: HP bar reveal + wait
        self.PHASE_FADE_IN = 15
        self.PHASE_SLIDE = 45
        self.PHASE_TEXT = 90
        self.PHASE_HP = 120

        # Cache boss info
        self.boss_name = boss.name
        self.boss_title = boss.title
        self.boss_class = boss.boss_class  # "mini" or "true"
        self.boss_color = boss.color
        self.boss_color_dark = boss.color_dark
        self.entrance_color = boss.entrance_color

        # Fonts (lazy init)
        self._init_fonts()

        # Sound (play once)
        self._sound_played = False

    def _init_fonts(self):
        """Init fonts (profesional) - DIPERBESAR"""
        try:
            self.font_huge = title_font(66)
            self.font_big = title_font(46)  # 44->46
            self.font_medium = get_font(32, "body_semibold")  # 28->32
            self.font_small = get_font(24, "body_medium")     # 20->24
        except:
            self.font_huge = title_font(66)
            self.font_big = title_font(46)
            self.font_medium = get_font(32, "body_semibold")
            self.font_small = get_font(24, "body_medium")

    def update(self):
        """Update timer & check skip input"""
        if not self.active:
            return

        self.timer -= 1
        if self.timer <= 0:
            self.active = False

        # Play sound at start
        if not self._sound_played:
            self._sound_played = True
            try:
                from _system import SoundManager
                # Use nexus_hit as dramatic boss appear sound
                SoundManager().play('nexus_hit', volume_mult=1.0)
            except Exception:
                pass

    def handle_skip(self, key=None, click=False):
        """Skip cinematic dengan spacebar/click"""
        if not self.active:
            return False

        if key == pygame.K_SPACE or key == pygame.K_ESCAPE or click:
            self.active = False
            return True
        return False

    def is_active(self):
        return self.active

    def draw(self, surface):
        """Banner nama boss KOMPAK di atas layar.

        Bukan overlay fullscreen lagi - hanya strip di bagian atas,
        jadi tidak menghalangi area pertarungan. Gameplay tetap jalan
        (tidak pause) selama banner tampil.
        """
        if not self.active:
            return

        elapsed = self.duration - self.timer

        # Fade in/out di ujung animasi
        if elapsed < 12:
            alpha = int(255 * elapsed / 12)
        elif self.timer < 20:
            alpha = int(255 * self.timer / 20)
        else:
            alpha = 255

        # Slide dari kiri (ease-out)
        slide_progress = min(1.0, elapsed / 18)
        eased = 1 - (1 - slide_progress) ** 3
        x_offset = int((1 - eased) * -640)

        # ── Banner background (hanya area banner) ──
        banner_w = min(600, self.screen_w - 40)
        banner_h = 92
        banner_x = (self.screen_w - banner_w) // 2 + x_offset
        banner_y = 12

        bg = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 10, 18, int(210 * alpha / 255)),
                         (0, 0, banner_w, banner_h), border_radius=10)
        pygame.draw.rect(bg, (*self.entrance_color, alpha),
                         (0, 0, banner_w, banner_h), 2, border_radius=10)
        surface.blit(bg, (banner_x, banner_y))

        # ── Class tag ──
        if self.boss_class == "true":
            tag_text = "TRUE BOSS"
            tag_color = (255, 90, 90)
        else:
            tag_text = "MINI BOSS"
            tag_color = (255, 200, 100)
        tag = self.font_small.render(tag_text, True, tag_color)
        tag.set_alpha(alpha)
        surface.blit(tag, (banner_x + 14, banner_y + 8))

        # ── Nama boss ──
        name = self.font_big.render(self.boss_name, True,
                                    self.entrance_color)
        name.set_alpha(alpha)
        surface.blit(name, (banner_x + 14, banner_y + 26))

        # ── Title ──
        title = self.font_small.render(
            f'"{self.boss_title}"', True, (215, 215, 235))
        title.set_alpha(alpha)
        surface.blit(title, (banner_x + 14, banner_y + 64))

        # ── HP bar preview (kanan banner) ──
        hp_progress = min(1.0, elapsed / (self.duration * 0.85))
        bar_w = 150
        bar_h = 12
        bx = banner_x + banner_w - bar_w - 16
        by = banner_y + banner_h // 2 - bar_h // 2
        pygame.draw.rect(surface, (40, 8, 12),
                         (bx, by, bar_w, bar_h), border_radius=5)
        fill = int(bar_w * hp_progress)
        if fill > 0:
            pygame.draw.rect(surface, (*self.entrance_color, 255),
                             (bx, by, fill, bar_h), border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255),
                         (bx, by, bar_w, bar_h), 1, border_radius=5)

    def _draw_boss_silhouette(self, surface, offset_x):
        """Draw boss silhouette di kanan tengah"""
        # Position: kanan tengah screen
        cx = self.screen_w // 2 + 100 + offset_x
        cy = self.screen_h // 2

        # ═══ ENERGY AURA di belakang silhouette ═══
        aura_pulse = math.sin(pygame.time.get_ticks() * 0.005) * 0.3 + 0.7
        aura_r = int(180 * aura_pulse)

        aura_surf = pygame.Surface(
            (aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        for r in range(aura_r, 20, -8):
            alpha = int((aura_r - r) * 1.2)
            if alpha > 0:
                pygame.draw.circle(
                    aura_surf,
                    (*self.entrance_color, alpha),
                    (aura_r, aura_r), r)
        from mobile.perf import Quality as _Q0
        if _Q0.cheap_alpha:
            surface.blit(aura_surf, (cx - aura_r, cy - aura_r))
        else:
            # aura 280x280 ber-alpha = 17 ms di HP; ganti 2 lingkaran
            pygame.draw.circle(surface, self.boss_entrance_color,
                               (cx, cy), int(aura_r * 0.7), 2)

        # ═══ BOSS SILHOUETTE (simplified body) ═══
        # Draw big silhouette shape based on boss class
        silhouette_alpha = 255

        if self.boss_class == "true":
            # True boss = bigger, more imposing
            self._draw_true_boss_silhouette(surface, cx, cy,
                                             silhouette_alpha)
        else:
            # Mini boss
            self._draw_mini_boss_silhouette(surface, cx, cy,
                                             silhouette_alpha)

        # ═══ RADIATING RAYS from boss ═══
        # OPTIMASI: dulu 8 Surface layar penuh + 8 blit per frame.
        from mobile.perf import POOL as _POOL
        num_rays = 8
        ray_overlay = _POOL.get(self.screen_w, self.screen_h)
        ticks = pygame.time.get_ticks()
        for i in range(num_rays):
            angle = i * math.pi * 2 / num_rays + ticks * 0.001
            sx = cx + int(math.cos(angle) * 80)
            sy = cy + int(math.sin(angle) * 80)
            ex = cx + int(math.cos(angle) * 200)
            ey = cy + int(math.sin(angle) * 200)
            pygame.draw.line(ray_overlay, (*self.entrance_color, 60),
                             (sx, sy), (ex, ey), 3)
        from mobile.perf import blit_overlay
        blit_overlay(surface, ray_overlay,
                     pygame.Rect(cx - 210, cy - 210, 420, 420))
        _POOL.release(ray_overlay)

    def _draw_true_boss_silhouette(self, surface, cx, cy, alpha):
        """Silhouette bigger dark shape untuk true boss"""
        # Body (large)
        body_pts = [
            (cx - 60, cy - 20),
            (cx - 40, cy - 80),
            (cx, cy - 100),
            (cx + 40, cy - 80),
            (cx + 60, cy - 20),
            (cx + 70, cy + 40),
            (cx + 50, cy + 90),
            (cx - 50, cy + 90),
            (cx - 70, cy + 40),
        ]

        # Shadow layer
        shadow_pts = [(p[0] + 3, p[1] + 3) for p in body_pts]
        pygame.draw.polygon(surface, (0, 0, 0, alpha // 2), shadow_pts)

        # Dark silhouette
        pygame.draw.polygon(surface, (0, 0, 0, alpha), body_pts)

        # Inner glow (boss color hint)
        inner_pts = [
            (cx - 55, cy - 15),
            (cx - 35, cy - 75),
            (cx, cy - 95),
            (cx + 35, cy - 75),
            (cx + 55, cy - 15),
            (cx + 65, cy + 35),
            (cx + 45, cy + 85),
            (cx - 45, cy + 85),
            (cx - 65, cy + 35),
        ]
        pygame.draw.polygon(
            surface,
            (*self.boss_color_dark, alpha // 3),
            inner_pts)

        # Crown spikes (true boss)
        for i in range(5):
            spike_x = cx - 40 + i * 20
            spike_y = cy - 100
            pygame.draw.polygon(surface, (0, 0, 0, alpha), [
                (spike_x - 5, spike_y),
                (spike_x, spike_y - 20 - (i % 2) * 8),
                (spike_x + 5, spike_y),
            ])

        # Glowing eyes
        pulse = math.sin(pygame.time.get_ticks() * 0.008) * 0.3 + 0.7
        eye_alpha = int(255 * pulse)

        for eye_x in [cx - 20, cx + 20]:
            # Eye glow
            glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            for r in range(12, 0, -2):
                a = int(200 * pulse - r * 10)
                if a > 0:
                    pygame.draw.circle(
                        glow_surf,
                        (*self.entrance_color, a),
                        (15, 15), r)
            surface.blit(glow_surf, (eye_x - 15, cy - 55))

            pygame.draw.circle(surface, self.entrance_color,
                               (eye_x, cy - 50), 5)
            pygame.draw.circle(surface, (255, 255, 255),
                               (eye_x, cy - 50), 2)

    def _draw_mini_boss_silhouette(self, surface, cx, cy, alpha):
        """Silhouette smaller untuk mini boss"""
        # Body (medium)
        body_pts = [
            (cx - 45, cy - 20),
            (cx - 30, cy - 65),
            (cx, cy - 80),
            (cx + 30, cy - 65),
            (cx + 45, cy - 20),
            (cx + 55, cy + 30),
            (cx + 40, cy + 75),
            (cx - 40, cy + 75),
            (cx - 55, cy + 30),
        ]

        # Shadow
        shadow_pts = [(p[0] + 2, p[1] + 2) for p in body_pts]
        pygame.draw.polygon(surface, (0, 0, 0, alpha // 2), shadow_pts)

        # Dark silhouette
        pygame.draw.polygon(surface, (0, 0, 0, alpha), body_pts)

        # Inner tint
        inner_pts = [
            (cx - 40, cy - 15),
            (cx - 25, cy - 60),
            (cx, cy - 75),
            (cx + 25, cy - 60),
            (cx + 40, cy - 15),
            (cx + 50, cy + 25),
            (cx + 35, cy + 70),
            (cx - 35, cy + 70),
            (cx - 50, cy + 25),
        ]
        pygame.draw.polygon(
            surface,
            (*self.boss_color_dark, alpha // 3),
            inner_pts)

        # Simple crown (3 spikes)
        for i in range(3):
            spike_x = cx - 20 + i * 20
            spike_y = cy - 80
            pygame.draw.polygon(surface, (0, 0, 0, alpha), [
                (spike_x - 4, spike_y),
                (spike_x, spike_y - 15),
                (spike_x + 4, spike_y),
            ])

        # Glowing eyes
        pulse = math.sin(pygame.time.get_ticks() * 0.008) * 0.3 + 0.7

        for eye_x in [cx - 15, cx + 15]:
            glow_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            for r in range(10, 0, -2):
                a = int(180 * pulse - r * 10)
                if a > 0:
                    pygame.draw.circle(
                        glow_surf,
                        (*self.entrance_color, a),
                        (12, 12), r)
            surface.blit(glow_surf, (eye_x - 12, cy - 47))

            pygame.draw.circle(surface, self.entrance_color,
                               (eye_x, cy - 40), 4)
            pygame.draw.circle(surface, (255, 255, 255),
                               (eye_x, cy - 40), 2)

    def _draw_boss_text(self, surface, alpha, offset_y):
        """Draw name + title dengan animasi"""
        # Text di kiri tengah
        text_x = self.screen_w // 4
        text_y = self.screen_h // 2 - 20 + offset_y

        # ═══ CLASS TAG (BOSS / TRUE BOSS) ═══
        if self.boss_class == "true":
            tag_text = "TRUE BOSS"
            tag_color = (255, 80, 80)
        else:
            tag_text = "BOSS"
            tag_color = (255, 200, 100)

        tag_surf = self.font_medium.render(tag_text, True, tag_color)
        tag_surf.set_alpha(alpha)
        tag_rect = tag_surf.get_rect(center=(text_x, text_y - 80))

        # Tag glow background
        tag_bg = tag_rect.inflate(30, 10)
        tag_bg_surf = pygame.Surface(tag_bg.size, pygame.SRCALPHA)
        pygame.draw.rect(tag_bg_surf,
                         (*tag_color, alpha // 3),
                         (0, 0, tag_bg.width, tag_bg.height),
                         border_radius=6)
        pygame.draw.rect(tag_bg_surf,
                         (*tag_color, alpha),
                         (0, 0, tag_bg.width, tag_bg.height),
                         2, border_radius=6)
        surface.blit(tag_bg_surf, tag_bg)
        surface.blit(tag_surf, tag_rect)

        # ═══ BOSS NAME (huge) ═══
        # Multiple shadow layers untuk dramatic effect
        from mobile.perf import Quality as _Qz
        for offset in (range(5, 0, -1) if _Qz.cheap_alpha else (3,)):
            shadow = self.font_huge.render(
                self.boss_name, True, (0, 0, 0))
            shadow.set_alpha(min(alpha, 100))
            shadow_rect = shadow.get_rect(
                center=(text_x + offset, text_y + offset))
            surface.blit(shadow, shadow_rect)

        # Main name text
        name_surf = self.font_huge.render(
            self.boss_name, True, self.entrance_color)
        name_surf.set_alpha(alpha)
        name_rect = name_surf.get_rect(center=(text_x, text_y))
        surface.blit(name_surf, name_rect)

        # ═══ TITLE (smaller, italic feel) ═══
        title_text = f'"{self.boss_title}"'
        title_surf = self.font_medium.render(
            title_text, True, (220, 220, 240))
        title_surf.set_alpha(alpha)
        title_rect = title_surf.get_rect(
            center=(text_x, text_y + 60))

        # Title shadow
        title_shadow = self.font_medium.render(
            title_text, True, (0, 0, 0))
        title_shadow.set_alpha(alpha // 2)
        surface.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        surface.blit(title_surf, title_rect)

        # ═══ DECORATIVE LINES ═══
        line_alpha = alpha
        line_color = (*self.entrance_color, line_alpha)

        line_surf = pygame.Surface(
            (self.screen_w, 4), pygame.SRCALPHA)
        # Top line
        pygame.draw.line(line_surf, line_color,
                         (text_x - 200, 2),
                         (text_x + 200, 2), 2)
        surface.blit(line_surf, (0, text_y - 55))

        # Bottom line
        surface.blit(line_surf, (0, text_y + 95))

    def _draw_hp_preview(self, surface, fill_ratio):
        """Draw HP bar preview di bawah name"""
        text_x = self.screen_w // 4
        text_y = self.screen_h // 2 + 130

        # HP bar
        bar_w = 300
        bar_h = 16
        bx = text_x - bar_w // 2
        by = text_y

        # Border
        pygame.draw.rect(surface, (0, 0, 0),
                         (bx - 2, by - 2, bar_w + 4, bar_h + 4),
                         border_radius=3)

        # BG
        pygame.draw.rect(surface, (40, 10, 10),
                         (bx, by, bar_w, bar_h),
                         border_radius=3)

        # Fill (animated)
        fill_w = int(bar_w * fill_ratio)
        if fill_w > 0:
            # Gradient effect
            for i in range(fill_w):
                t = i / bar_w
                r = int(220 - t * 40)
                g = int(60 + t * 30)
                b = int(60 - t * 30)
                pygame.draw.line(surface, (r, g, b),
                                 (bx + i, by),
                                 (bx + i, by + bar_h))

        # White border
        pygame.draw.rect(surface, (255, 255, 255),
                         (bx, by, bar_w, bar_h),
                         2, border_radius=3)

        # HP text (kalau sudah full)
        if fill_ratio >= 1.0:
            hp_text = self.font_small.render(
                f"HP: {self.boss.max_hp:,}", True, (255, 255, 255))
            hp_rect = hp_text.get_rect(center=(text_x, by + bar_h + 15))

            # Shadow
            hp_shadow = self.font_small.render(
                f"HP: {self.boss.max_hp:,}", True, (0, 0, 0))
            surface.blit(hp_shadow, (hp_rect.x + 1, hp_rect.y + 1))
            surface.blit(hp_text, hp_rect)

    def _draw_skip_hint(self, surface):
        """Draw skip hint di bottom"""
        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 0.3 + 0.7
        alpha = int(180 * pulse)

        hint_text = self.font_small.render(
            f"[{_skip_button_label()}] to skip",
            True, (200, 200, 200))
        hint_text.set_alpha(alpha)
        hint_rect = hint_text.get_rect(
            center=(self.screen_w // 2, self.screen_h - 40))
        surface.blit(hint_text, hint_rect)


# ====================================================================
# effects_level_intro.py
# ====================================================================

# ================================
# effects_level_intro.py
# Level Intro Cinematic Screen
# ================================

import pygame
import math


class LevelIntroScreen:
    """
    Split screen level intro:
    - Left: Level info (number, name, description, difficulty, reward)
    - Right: Boss preview (silhouette + name + title)
    - Bottom: "PRESS SPACE TO BEGIN"
    """

    def __init__(self, level_config, screen_w, screen_h):
        self.level_config = level_config
        self.screen_w = screen_w
        self.screen_h = screen_h

        # State
        self.active = True
        self.timer = 0  # elapsed frames (for fade in animation)
        self.fade_in_duration = 30  # 0.5 detik fade in

        # Cache level info
        self.level_num = level_config["level_number"]
        self.level_name = level_config["name"]
        self.level_desc = level_config["description"]
        self.hp_mult = level_config.get("enemy_hp_mult", 1.0)
        self.dmg_mult = level_config.get("enemy_damage_mult", 1.0)
        self.reward = level_config.get("meta_gold_reward_win", 500)
        self.map_theme = level_config.get("map_theme", "forest")

        # Cache boss info (dari boss_data)
        boss_type = level_config.get("true_boss", "abaddon")
        from bosses.boss_data import get_all_boss_types
        all_bosses = get_all_boss_types()
        boss_data = all_bosses.get(boss_type, {})

        self.boss_type = boss_type
        self.boss_name = boss_data.get("name", "Unknown")
        self.boss_title = boss_data.get("title", "The Boss")
        self.boss_color = boss_data.get("color", (150, 100, 200))
        self.boss_color_dark = boss_data.get(
            "color_dark", (75, 50, 100))
        self.boss_entrance_color = boss_data.get(
            "entrance_color", (150, 100, 200))
        self.boss_class = boss_data.get("boss_class", "true")

        # Fonts (profesional) - DIPERBESAR
        self.font_huge = title_font(66)
        self.font_big = title_font(46)  # 44->46
        self.font_medium = get_font(32, "body_semibold")  # 28->32
        self.font_small = get_font(24, "body_medium")     # 20->24
        self.font_tiny = get_font(20, "body")             # 16->20

        # Sound
        self._sound_played = False

    def update(self):
        """Update timer"""
        if not self.active:
            return

        self.timer += 1

        # Play sound at start
        if not self._sound_played:
            self._sound_played = True
            try:
                from _system import SoundManager
                SoundManager().play('wave_start', volume_mult=1.0)
            except Exception:
                pass

    def handle_skip(self, key=None, click=False):
        """Skip intro dengan spacebar / click"""
        if not self.active:
            return False

        if key == pygame.K_SPACE or key == pygame.K_RETURN or click:
            self.active = False
            return True
        return False

    def is_active(self):
        return self.active

    def draw(self, surface):
        """Draw level intro"""
        if not self.active:
            return

        # ═══ FADE IN alpha ═══
        if self.timer < self.fade_in_duration:
            fade_alpha = int(255 * (self.timer / self.fade_in_duration))
        else:
            fade_alpha = 255

        # ═══ FULL DARK BACKGROUND ═══
        from mobile.perf import darken
        darken(surface, min(255, fade_alpha + 30))

        # ═══ THEME TINT (biar mood match dengan map theme) ═══
        theme_tint_alpha = int(30 * (fade_alpha / 255))
        tint = pygame.Surface(
            (self.screen_w, self.screen_h), pygame.SRCALPHA)

        if self.map_theme == "desert":
            tint.fill((100, 60, 20, theme_tint_alpha))
        elif self.map_theme == "ice":
            tint.fill((40, 80, 130, theme_tint_alpha))
        elif self.map_theme == "ocean":
            tint.fill((30, 70, 120, theme_tint_alpha))
        elif self.map_theme == "abyss":
            tint.fill((40, 10, 10, theme_tint_alpha))
        elif self.map_theme == "nethervenom":
            tint.fill((25, 55, 15, theme_tint_alpha))
        elif self.map_theme == "spectral":
            tint.fill((15, 50, 55, theme_tint_alpha))
        elif self.map_theme == "sundered":
            tint.fill((70, 30, 8, theme_tint_alpha))
        elif self.map_theme == "empyrean":
            tint.fill((70, 55, 15, theme_tint_alpha))
        elif self.map_theme == "solaris":
            tint.fill((85, 50, 10, theme_tint_alpha))
        elif self.map_theme == "abysstide":
            tint.fill((10, 50, 50, theme_tint_alpha))
        elif self.map_theme == "crimsonmatriarch":
            tint.fill((60, 10, 15, theme_tint_alpha))
        elif self.map_theme == "astral":
            tint.fill((15, 25, 60, theme_tint_alpha))
        elif self.map_theme == "shadowchain":
            tint.fill((45, 12, 60, theme_tint_alpha))
        elif self.map_theme == "frostveil":
            tint.fill((25, 45, 85, theme_tint_alpha))
        elif self.map_theme == "warshade":
            tint.fill((10, 40, 48, theme_tint_alpha))
        elif self.map_theme == "outlaw":
            tint.fill((80, 45, 35, theme_tint_alpha))
        elif self.map_theme == "hexbound":
            tint.fill((55, 25, 75, theme_tint_alpha))
        elif self.map_theme == "voidbound":
            tint.fill((45, 18, 70, theme_tint_alpha))
        elif self.map_theme == "earthborn":
            tint.fill((45, 55, 25, theme_tint_alpha))
        elif self.map_theme == "heartbane":
            tint.fill((60, 18, 55, theme_tint_alpha))
        elif self.map_theme == "sunfist":
            tint.fill((80, 55, 12, theme_tint_alpha))
        elif self.map_theme == "voidwing":
            tint.fill((45, 15, 65, theme_tint_alpha))
        elif self.map_theme == "crimsondevourer":
            tint.fill((60, 10, 15, theme_tint_alpha))
        elif self.map_theme == "elementweave":
            tint.fill((55, 30, 75, theme_tint_alpha))
        elif self.map_theme == "tempest":
            tint.fill((20, 40, 90, theme_tint_alpha))
        elif self.map_theme == "sawmill":
            tint.fill((70, 45, 18, theme_tint_alpha))
        elif self.map_theme == "croweye":
            tint.fill((55, 12, 18, theme_tint_alpha))
        elif self.map_theme == "crystalstorm":
            tint.fill((30, 45, 85, theme_tint_alpha))
        elif self.map_theme == "eternalwarlord":
            tint.fill((70, 15, 20, theme_tint_alpha))
        elif self.map_theme == "explosiveart":
            tint.fill((70, 18, 18, theme_tint_alpha))
        elif self.map_theme == "sandshadow":
            tint.fill((85, 35, 22, theme_tint_alpha))
        elif self.map_theme == "emberweaver":
            tint.fill((95, 28, 22, theme_tint_alpha))
        elif self.map_theme == "skyfury":
            tint.fill((70, 45, 20, theme_tint_alpha))
        else:  # forest
            tint.fill((20, 40, 20, theme_tint_alpha))

        # OPTIMASI HP: blit surface ber-alpha seukuran layar = 204 ms
        # di Cortex-A53. fill() dengan BLEND_RGB_MULT memberi efek
        # pewarnaan yang mirip dengan biaya ~2 ms.
        from mobile.perf import Quality as _Q
        if _Q.cheap_alpha:
            surface.blit(tint, (0, 0))
        else:
            _c = tint.get_at((0, 0))
            _a = max(0, min(255, _c[3])) / 255.0
            surface.fill((int(255 - (255 - _c[0]) * _a),
                          int(255 - (255 - _c[1]) * _a),
                          int(255 - (255 - _c[2]) * _a)),
                         special_flags=pygame.BLEND_RGB_MULT)

        # ═══ VIGNETTE (darker corners) ═══
        # OPTIMASI: bentuk vignette selalu sama, hanya alpha global
        # yang berubah -> gambar sekali, simpan, lalu set_alpha.
        from mobile.perf import cached_render

        def _paint_vignette(surf):
            for i in range(60):
                pygame.draw.rect(surf, (0, 0, 0, i * 3),
                                 (i, i,
                                  self.screen_w - i * 2,
                                  self.screen_h - i * 2), 1)

        from mobile.perf import Quality as _Q
        if _Q.cheap_alpha:
            vignette = cached_render(("vignette", self.screen_w,
                                      self.screen_h),
                                     self.screen_w, self.screen_h,
                                     _paint_vignette)
            vignette.set_alpha(fade_alpha)
            surface.blit(vignette, (0, 0))

        # ═══ SPLIT DIVIDER (vertical line di tengah) ═══
        divider_x = self.screen_w // 2
        pygame.draw.line(surface, (100, 100, 130, fade_alpha),
                         (divider_x, 100),
                         (divider_x, self.screen_h - 100), 2)

        # Decorative diamonds on divider
        for i in range(3):
            y = 250 + i * 200
            pygame.draw.polygon(
                surface, (255, 220, 100), [
                    (divider_x, y - 8),
                    (divider_x + 8, y),
                    (divider_x, y + 8),
                    (divider_x - 8, y),
                ])

        # ═══ LEFT SIDE: LEVEL INFO ═══
        self._draw_level_info(surface, fade_alpha)

        # ═══ RIGHT SIDE: BOSS PREVIEW ═══
        self._draw_boss_preview(surface, fade_alpha)

        # ═══ BOTTOM: "PRESS SPACE" PROMPT ═══
        if self.timer > self.fade_in_duration:
            self._draw_space_prompt(surface)

    def _draw_level_info(self, surface, alpha):
        """Draw left side: level info"""
        cx = self.screen_w // 4  # kiri tengah
        cy_start = 130

        # ═══ "LEVEL" LABEL ═══
        label = self.font_medium.render("LEVEL", True, (180, 200, 220))
        label.set_alpha(alpha)
        label_rect = label.get_rect(center=(cx, cy_start))
        surface.blit(label, label_rect)

        # ═══ BIG LEVEL NUMBER ═══
        lvl_num_font = title_font(200)

        # Multi-layer shadow (di HP cukup 1 lapis: tiap lapis =
        # satu alpha blit besar, 6 lapis bisa 43 ms sendiri)
        from mobile.perf import Quality as _Q
        _layers = range(6, 0, -1) if _Q.cheap_alpha else (3,)
        for offset in _layers:
            shadow = lvl_num_font.render(
                str(self.level_num), True, (0, 0, 0))
            shadow.set_alpha(min(alpha, 60))
            shadow_rect = shadow.get_rect(
                center=(cx + offset, cy_start + 100 + offset))
            surface.blit(shadow, shadow_rect)

        # Main level number
        lvl_num = lvl_num_font.render(
            str(self.level_num), True, (255, 220, 100))
        lvl_num.set_alpha(alpha)
        lvl_num_rect = lvl_num.get_rect(center=(cx, cy_start + 100))
        surface.blit(lvl_num, lvl_num_rect)

        # ═══ DECORATIVE LINE ═══
        line_y = cy_start + 220
        pygame.draw.line(surface, (255, 220, 100, alpha),
                         (cx - 150, line_y), (cx + 150, line_y), 2)
        pygame.draw.line(surface, (255, 255, 200, alpha),
                         (cx - 100, line_y + 3),
                         (cx + 100, line_y + 3), 1)

        # ═══ LEVEL NAME ═══
        name_shadow = self.font_big.render(
            self.level_name, True, (0, 0, 0))
        name_shadow.set_alpha(alpha // 2)
        name_rect = name_shadow.get_rect(
            center=(cx + 2, cy_start + 260 + 2))
        surface.blit(name_shadow, name_rect)

        name_surf = self.font_big.render(
            self.level_name, True, (240, 240, 250))
        name_surf.set_alpha(alpha)
        name_rect = name_surf.get_rect(
            center=(cx, cy_start + 260))
        surface.blit(name_surf, name_rect)

        # ═══ DESCRIPTION ═══
        desc_surf = self.font_small.render(
            self.level_desc, True, (180, 200, 220))
        desc_surf.set_alpha(alpha)
        desc_rect = desc_surf.get_rect(
            center=(cx, cy_start + 310))
        surface.blit(desc_surf, desc_rect)

        # ═══ DIFFICULTY BARS ═══
        diff_y = cy_start + 370
        try:
            from _core import GameSettings
            is_hard = GameSettings().is_hard_mode()
        except Exception:
            is_hard = False

        if is_hard:
            diff_title = f"DIFFICULTY: HARD (SCALING ON)"
            diff_level = min(5, max(1, int(self.hp_mult * 2.5)))
            diff_color = (255, 120, 100)
        else:
            diff_title = "DIFFICULTY: NORMAL (SCALING OFF)"
            diff_level = 1
            diff_color = (100, 220, 150)

        diff_label = self.font_tiny.render(
            diff_title, True, diff_color)
        diff_label.set_alpha(alpha)
        diff_label_rect = diff_label.get_rect(center=(cx, diff_y))
        surface.blit(diff_label, diff_label_rect)

        bar_start_x = cx - (5 * 22) // 2
        for i in range(5):
            bar_x = bar_start_x + i * 22
            bar_y = diff_y + 20
            if i < diff_level:
                if i >= 3:
                    bar_col = (255, 100, 80)
                elif i >= 1:
                    bar_col = (255, 200, 80)
                else:
                    bar_col = (100, 220, 100)
            else:
                bar_col = (60, 60, 70)

            bar_surf = pygame.Surface((18, 10), pygame.SRCALPHA)
            pygame.draw.rect(bar_surf, (*bar_col, alpha),
                             (0, 0, 18, 10), border_radius=2)
            surface.blit(bar_surf, (bar_x, bar_y))

        # ═══ REWARD INFO ═══
        reward_y = cy_start + 430

        reward_label = self.font_tiny.render(
            "VICTORY REWARD", True, (150, 170, 190))
        reward_label.set_alpha(alpha)
        reward_label_rect = reward_label.get_rect(
            center=(cx, reward_y))
        surface.blit(reward_label, reward_label_rect)

        # Gold coin icon + reward
        coin_x = cx - 60
        coin_y = reward_y + 30
        pygame.draw.circle(surface, (255, 200, 50),
                           (coin_x, coin_y), 12)
        pygame.draw.circle(surface, (200, 150, 30),
                           (coin_x, coin_y), 12, 2)

        coin_font = get_font(24, 'body_bold')  # 18->24
        dollar = coin_font.render("$", True, (100, 60, 10))
        dollar_rect = dollar.get_rect(center=(coin_x, coin_y))
        surface.blit(dollar, dollar_rect)

        reward_text = self.font_medium.render(
            f"+{self.reward} HERO GOLD", True, (255, 220, 100))
        reward_text.set_alpha(alpha)
        surface.blit(reward_text, (coin_x + 18, coin_y - 12))

    def _draw_boss_preview(self, surface, alpha):
        """Draw right side: boss preview"""
        cx = self.screen_w * 3 // 4  # kanan tengah
        cy = self.screen_h // 2

        # ═══ "FINAL BOSS" LABEL ═══
        label = self.font_medium.render(
            "FINAL BOSS", True, (255, 100, 100))
        label.set_alpha(alpha)
        label_rect = label.get_rect(center=(cx, 130))
        surface.blit(label, label_rect)

        # ═══ CLASS TAG ═══
        if self.boss_class == "true":
            tag_text = "TRUE BOSS"
            tag_color = (255, 80, 80)
        else:
            tag_text = "MINI BOSS"
            tag_color = (255, 200, 100)

        tag_surf = self.font_small.render(
            tag_text, True, tag_color)
        tag_surf.set_alpha(alpha)
        tag_rect = tag_surf.get_rect(center=(cx, 165))

        # Tag bg
        tag_bg = tag_rect.inflate(30, 8)
        tag_bg_surf = pygame.Surface(tag_bg.size, pygame.SRCALPHA)
        pygame.draw.rect(tag_bg_surf,
                         (*tag_color, alpha // 4),
                         (0, 0, tag_bg.width, tag_bg.height),
                         border_radius=6)
        pygame.draw.rect(tag_bg_surf,
                         (*tag_color, alpha),
                         (0, 0, tag_bg.width, tag_bg.height),
                         2, border_radius=6)
        surface.blit(tag_bg_surf, tag_bg)
        surface.blit(tag_surf, tag_rect)

        # ═══ BOSS SILHOUETTE ═══
        silhouette_cy = cy - 20
        self._draw_boss_silhouette(surface, cx, silhouette_cy, alpha)

        # ═══ BOSS NAME (huge, glowing) ═══
        name_y = cy + 180

        # Multi-layer shadow
        from mobile.perf import Quality as _Q1
        for offset in (range(5, 0, -1) if _Q1.cheap_alpha else (3,)):
            shadow = self.font_big.render(
                self.boss_name, True, (0, 0, 0))
            shadow.set_alpha(min(alpha, 80))
            shadow_rect = shadow.get_rect(
                center=(cx + offset, name_y + offset))
            surface.blit(shadow, shadow_rect)

        # Main name
        name_surf = self.font_big.render(
            self.boss_name, True, self.boss_entrance_color)
        name_surf.set_alpha(alpha)
        name_rect = name_surf.get_rect(center=(cx, name_y))
        surface.blit(name_surf, name_rect)

        # ═══ BOSS TITLE ═══
        title_text = f'"{self.boss_title}"'
        title_surf = self.font_medium.render(
            title_text, True, (200, 200, 220))
        title_surf.set_alpha(alpha)
        title_rect = title_surf.get_rect(
            center=(cx, name_y + 45))

        # Shadow
        title_shadow = self.font_medium.render(
            title_text, True, (0, 0, 0))
        title_shadow.set_alpha(alpha // 2)
        surface.blit(title_shadow,
                     (title_rect.x + 2, title_rect.y + 2))
        surface.blit(title_surf, title_rect)

        # ═══ WARNING TEXT ═══
        warning_pulse = math.sin(
            pygame.time.get_ticks() * 0.005) * 0.3 + 0.7

        warning_text = self.font_small.render(
            "⚠  PREPARE FOR BATTLE  ⚠",
            True, (255, 100, 100))
        warning_alpha = int(alpha * warning_pulse)
        warning_text.set_alpha(warning_alpha)
        warning_rect = warning_text.get_rect(
            center=(cx, name_y + 95))
        surface.blit(warning_text, warning_rect)

    def _draw_boss_silhouette(self, surface, cx, cy, alpha):
        """Draw big boss silhouette"""
        # ═══ ENERGY AURA di belakang silhouette ═══
        aura_pulse = math.sin(
            pygame.time.get_ticks() * 0.003) * 0.3 + 0.7
        aura_r = int(140 * aura_pulse)

        aura_surf = pygame.Surface(
            (aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        for r in range(aura_r, 20, -6):
            aura_alpha = int((aura_r - r) * 1.5 * (alpha / 255))
            if aura_alpha > 0:
                pygame.draw.circle(
                    aura_surf,
                    (*self.boss_entrance_color, aura_alpha),
                    (aura_r, aura_r), r)
        surface.blit(aura_surf, (cx - aura_r, cy - aura_r))

        # ═══════════════════════════════════════════════════
        # OPTIMASI ANDROID:
        # Versi lama membuat SATU Surface SEUKURAN LAYAR untuk
        # tiap sinar, bayangan, badan, dan tiap duri mahkota
        # (14+ surface 1280x720 per frame, 14+ blit layar penuh).
        # Di HP ini saja bisa 40-60 ms/frame.
        # Sekarang: 1 overlay dari pool, digambar sekali.
        # ═══════════════════════════════════════════════════
        from mobile.perf import POOL as _POOL, Quality as _QS
        overlay = _POOL.get(self.screen_w, self.screen_h)

        # ═══ RADIATING RAYS ═══
        # Sinar menjangkau r=180 sehingga kotak blit ikut membesar.
        # Di HP dengan alpha mahal, sinarnya dilewati saja supaya
        # kotaknya cukup sebesar badan boss.
        num_rays = 12 if _QS.cheap_alpha else 0
        ray_alpha = int(50 * (alpha / 255))
        ticks = pygame.time.get_ticks()
        for i in range(num_rays):
            ray_angle = i * math.pi * 2 / num_rays + ticks * 0.0005
            sx = cx + int(math.cos(ray_angle) * 90)
            sy = cy + int(math.sin(ray_angle) * 90)
            ex = cx + int(math.cos(ray_angle) * 180)
            ey = cy + int(math.sin(ray_angle) * 180)
            pygame.draw.line(overlay,
                             (*self.boss_entrance_color, ray_alpha),
                             (sx, sy), (ex, ey), 3)

        # ═══ BOSS SILHOUETTE (dark shape) ═══
        body_pts = [
            (cx - 55, cy - 20), (cx - 35, cy - 75), (cx, cy - 95),
            (cx + 35, cy - 75), (cx + 55, cy - 20), (cx + 65, cy + 35),
            (cx + 45, cy + 85), (cx - 45, cy + 85), (cx - 65, cy + 35),
        ]
        shadow_pts = [(p[0] + 3, p[1] + 3) for p in body_pts]
        pygame.draw.polygon(overlay, (0, 0, 0, alpha // 2), shadow_pts)
        pygame.draw.polygon(overlay, (0, 0, 0, alpha), body_pts)

        inner_pts = [
            (cx - 50, cy - 15), (cx - 30, cy - 70), (cx, cy - 90),
            (cx + 30, cy - 70), (cx + 50, cy - 15), (cx + 60, cy + 30),
            (cx + 40, cy + 80), (cx - 40, cy + 80), (cx - 60, cy + 30),
        ]
        pygame.draw.polygon(overlay,
                            (*self.boss_color_dark, alpha // 3), inner_pts)

        # ═══ CROWN SPIKES ═══
        num_spikes = 5 if self.boss_class == "true" else 3
        for i in range(num_spikes):
            spike_x = (cx - 40 + i * 20) if num_spikes == 5 else (
                cx - 20 + i * 20)
            spike_y = cy - 95
            spike_height = 25 + (i % 2) * 10
            pygame.draw.polygon(overlay, (0, 0, 0, alpha), [
                (spike_x - 6, spike_y),
                (spike_x, spike_y - spike_height),
                (spike_x + 6, spike_y),
            ])

        # Blit HANYA kotak yang benar-benar tergambar. Di HP,
        # alpha blit dihitung per piksel (~222 ns/px di Cortex-A53),
        # jadi 1280x720 = 204 ms sedangkan 460x300 = 30 ms.
        from mobile.perf import blit_overlay
        _box = (pygame.Rect(cx - 230, cy - 160, 460, 300) if _QS.cheap_alpha
                else pygame.Rect(cx - 90, cy - 130, 180, 230))
        blit_overlay(surface, overlay, _box)
        _POOL.release(overlay)

        # ═══ GLOWING EYES ═══
        eye_pulse = math.sin(
            pygame.time.get_ticks() * 0.008) * 0.3 + 0.7

        for eye_x in [cx - 20, cx + 20]:
            # Eye glow
            glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            for r in range(12, 0, -2):
                a = int(200 * eye_pulse * (alpha / 255) - r * 12)
                if a > 0:
                    pygame.draw.circle(
                        glow_surf,
                        (*self.boss_entrance_color, a),
                        (15, 15), r)
            surface.blit(glow_surf, (eye_x - 15, cy - 55))

            # Bright eye center
            eye_alpha = int(255 * (alpha / 255))
            eye_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(
                eye_surf,
                (*self.boss_entrance_color, eye_alpha),
                (5, 5), 5)
            pygame.draw.circle(
                eye_surf,
                (255, 255, 255, eye_alpha),
                (5, 5), 2)
            surface.blit(eye_surf, (eye_x - 5, cy - 55))

    def _draw_space_prompt(self, surface):
        """Draw 'PRESS SPACE' prompt di bawah"""
        # Pulse animation
        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 0.3 + 0.7

        prompt_y = self.screen_h - 60
        cx = self.screen_w // 2

        # Background bar
        bar_w = 400
        bar_h = 45
        bar_x = cx - bar_w // 2
        bar_y = prompt_y - bar_h // 2

        bar_alpha = int(150 * pulse)
        bar_surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(bar_surf, (0, 0, 0, bar_alpha),
                         (0, 0, bar_w, bar_h), border_radius=10)
        pygame.draw.rect(bar_surf, (255, 220, 100, int(220 * pulse)),
                         (0, 0, bar_w, bar_h), 2, border_radius=10)
        surface.blit(bar_surf, (bar_x, bar_y))

        # Text
        _prompt_str = _begin_prompt_text()
        prompt_text = self.font_medium.render(
            _prompt_str,
            True, (255, 220, 100))
        prompt_text.set_alpha(int(255 * pulse))
        prompt_rect = prompt_text.get_rect(
            center=(cx, prompt_y))

        # Text shadow
        shadow = self.font_medium.render(
            _prompt_str, True, (0, 0, 0))
        shadow.set_alpha(int(150 * pulse))
        surface.blit(shadow, (prompt_rect.x + 2, prompt_rect.y + 2))

        surface.blit(prompt_text, prompt_rect)

        # Small arrows kiri kanan (decorative)
        arrow_offset = int(math.sin(
            pygame.time.get_ticks() * 0.005) * 5)

        # Left arrow
        arrow_x_left = bar_x - 30 - arrow_offset
        pygame.draw.polygon(surface, (255, 220, 100), [
            (arrow_x_left, prompt_y),
            (arrow_x_left + 15, prompt_y - 10),
            (arrow_x_left + 15, prompt_y + 10),
        ])

        # Right arrow
        arrow_x_right = bar_x + bar_w + 15 + arrow_offset
        pygame.draw.polygon(surface, (255, 220, 100), [
            (arrow_x_right, prompt_y),
            (arrow_x_right - 15, prompt_y - 10),
            (arrow_x_right - 15, prompt_y + 10),
        ])


# ====================================================================
# sprite_cache.py
# ====================================================================

# ================================
# sprite_cache.py
# Pre-render minion/hero sprites ke cached surface
# PALING BERDAMPAK untuk FPS!
# ================================

import pygame


class SpriteCache:
    """
    Cache rendered sprite per (type, team, level, state).
    Minion yang sama type+team+level+state pakai Surface yang sama.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache = {}
        self._cropped = {}   # cache versi ter-crop (hemat blit)
        # Kapasitas dinaikkan dari 500. Dengan 5 tipe minion x 2 tim
        # x 5 level x banyak state animasi, 500 cepat penuh lalu
        # thrashing (evict entri yang masih dipakai -> render ulang).
        self._max_cache = 2000
        self._hits = 0
        self._misses = 0

    def get_or_render(self, cache_key, width, height, render_func):
        """
        Get cached surface atau render baru.

        Returns:
            pygame.Surface (cached, ukuran penuh)
        """
        if cache_key in self._cache:
            self._hits += 1
            return self._cache[cache_key]

        # Cache miss - render baru
        self._misses += 1
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        render_func(surf)
        self._cache[cache_key] = surf

        # Evict oldest kalau terlalu banyak
        if len(self._cache) > self._max_cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._cropped.pop(oldest_key, None)

        return surf

    def get_or_render_cropped(self, cache_key, width, height,
                              render_func, anchor=None):
        """
        Sama seperti get_or_render, tapi hasilnya DI-CROP ke area
        yang benar-benar berisi piksel.

        Kenapa penting: canvas cache biasanya 120x120 tapi sprite
        minion cuma mengisi ~35% area. Blit canvas penuh berarti
        ~65% piksel terbuang -> dengan 80 minion di layar itu
        beberapa milidetik hilang percuma tiap frame.

        Args:
            anchor: (ax, ay) titik jangkar DI DALAM canvas. Default
                    titik tengah. Untuk menara, jangkarnya di kaki
                    (mis. (w//2, h-30)), bukan tengah.

        Returns:
            (surface_terpotong, anchor_x, anchor_y)
            anchor_x/y = posisi titik jangkar di dalam surface hasil,
            jadi pemanggil cukup blit di (x - anchor_x, y - anchor_y).
        """
        if anchor is None:
            anchor = (width // 2, height // 2)
        anc_x, anc_y = anchor
        entry = self._cropped.get(cache_key)
        if entry is not None:
            self._hits += 1
            return entry

        self._misses += 1
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        render_func(surf)

        rect = surf.get_bounding_rect(min_alpha=8)
        if rect.width <= 0 or rect.height <= 0:
            entry = (surf, anc_x, anc_y)
        else:
            cropped = surf.subsurface(rect).copy()
            entry = (cropped,
                     anc_x - rect.x,
                     anc_y - rect.y)

        self._cropped[cache_key] = entry

        if len(self._cropped) > self._max_cache:
            oldest = next(iter(self._cropped))
            del self._cropped[oldest]

        return entry

    def invalidate(self, prefix=None):
        """
        Hapus cache.
        prefix: string - hapus semua key yang mulai dengan prefix
        """
        if prefix is None:
            self._cache.clear()
            self._cropped.clear()
        else:
            keys_to_del = [k for k in self._cache
                           if isinstance(k, tuple) and
                           len(k) > 0 and k[0] == prefix]
            for k in keys_to_del:
                del self._cache[k]
                self._cropped.pop(k, None)

    def clear(self):
        self._cache.clear()
        self._cropped.clear()

    def get_stats(self):
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            'cached': len(self._cache) + len(self._cropped),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.1f}%",
        }


_sprite_cache = SpriteCache()


def get_cached_sprite(cache_key, width, height, render_func):
    """Global shortcut (canvas penuh)"""
    return _sprite_cache.get_or_render(
        cache_key, width, height, render_func)


def get_cached_sprite_cropped(cache_key, width, height, render_func,
                              anchor=None):
    """
    Global shortcut versi hemat: return (surface, anchor_x, anchor_y).
    Blit dengan: surface.blit(spr, (x - ax, y - ay))
    """
    return _sprite_cache.get_or_render_cropped(
        cache_key, width, height, render_func, anchor)


def clear_sprite_cache():
    _sprite_cache.clear()


# ====================================================================
# render_cache.py
# ====================================================================

# ================================
# render_cache.py
# Global surface & font cache
# ================================

import pygame


class RenderCache:
    """Cache Surface dan Font agar tidak buat baru tiap frame"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._fonts = {}
        self._circles = {}
        self._surfaces = {}

    def get_font(self, size, style="body", bold=False):
        """Cached font - BESAR impact karena Font() mahal.
        style: 'title'|'body'|'body_medium'|'body_semibold'|'body_bold'"""
        size = max(8, min(size, 220))
        key = (size, style, bold)
        if key not in self._fonts:
            self._fonts[key] = _make_font(size, style, bold)
        return self._fonts[key]

    def get_circle_surface(self, radius, color, width=0):
        """
        Cached circle surface.
        Key: (radius, color, width)
        """
        # Clamp alpha
        if len(color) == 4:
            color = (max(0, min(255, color[0])),
                     max(0, min(255, color[1])),
                     max(0, min(255, color[2])),
                     max(0, min(255, color[3])))
        else:
            color = (max(0, min(255, color[0])),
                     max(0, min(255, color[1])),
                     max(0, min(255, color[2])))

        key = (radius, color, width)
        if key not in self._circles:
            size = radius * 2 + 4
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, color,
                               (size // 2, size // 2),
                               radius, width)
            self._circles[key] = surf

        return self._circles[key]

    def get_glow_surface(self, radius, color, layers=5):
        """
        Cached multi-layer glow surface.
        Ini yang PALING BOROS di kode lama (tiap minion buat 5+ Surface).
        """
        key = ('glow', radius, color[:3], layers)
        if key not in self._surfaces:
            size = radius * 2 + 4
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cx, cy = size // 2, size // 2
            for i in range(layers):
                r = radius - i * (radius // layers)
                if r <= 0:
                    continue
                alpha = int((layers - i) * (200 // layers))
                alpha = max(0, min(255, alpha))
                pygame.draw.circle(surf,
                                   (*color[:3], alpha),
                                   (cx, cy), r)
            self._surfaces[key] = surf

        return self._surfaces[key]

    def clear(self):
        """Clear saat level change"""
        self._circles.clear()
        self._surfaces.clear()
        # Jangan clear fonts

    def get_stats(self):
        return {
            'fonts': len(self._fonts),
            'circles': len(self._circles),
            'surfaces': len(self._surfaces),
        }


# ═══ Global shortcuts ═══
_cache = RenderCache()


def get_font(size, style="body", bold=False):
    """Font profesional ter-cache. style: title/body/body_medium/
    body_semibold/body_bold. Aman dipakai di seluruh game."""
    return _cache.get_font(size, style, bold)


def get_circle(radius, color, width=0):
    return _cache.get_circle_surface(radius, color, width)


def get_glow(radius, color, layers=5):
    return _cache.get_glow_surface(radius, color, layers)


def clear_cache():
    _cache.clear()
