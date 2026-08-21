"""
_system.py - performa & sistem (digabung dari 5 file)

  performance.py        (versi kanonik FrustumCuller, SpatialGrid)
  fps_counter.py
  fps_limiter.py
  sound_manager.py
  save_manager.py
"""
import pygame
import math
import random
from _core import *
import os as _os

# Folder asset absolut (robust walau game dijalankan dari folder lain)
_SOUND_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                           "assets", "sounds")


def _sound_path(filename):
    """Resolve path sound: coba absolut dulu, fallback relatif."""
    p = _os.path.join(_SOUND_DIR, filename)
    if _os.path.exists(p):
        return p
    return _os.path.join("assets", "sounds", filename)


# ====================================================================
# performance.py
# ====================================================================

# performance.py
# Screen culling & spatial grid
# ================================

import math


class FrustumCuller:
    """Skip draw kalau entity di luar layar"""

    MARGIN = 80

    @staticmethod
    def is_visible(x, y, radius=30):
        m = FrustumCuller.MARGIN + radius
        return (-m <= x <= SCREEN_WIDTH + m and
                -m <= y <= SCREEN_HEIGHT + m)


class SpatialGrid:
    """Grid untuk percepat enemy lookup dari O(n²) ke O(n)"""

    def __init__(self, cell_size=100):
        self.cell_size = cell_size
        self.grid = {}

    def clear(self):
        self.grid.clear()

    def insert(self, entity):
        cx = int(entity.x // self.cell_size)
        cy = int(entity.y // self.cell_size)
        key = (cx, cy)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(entity)

    def query_range(self, x, y, radius):
        results = []
        min_cx = int((x - radius) // self.cell_size)
        max_cx = int((x + radius) // self.cell_size)
        min_cy = int((y - radius) // self.cell_size)
        max_cy = int((y + radius) // self.cell_size)

        seen = set()
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                key = (cx, cy)
                if key in self.grid:
                    for entity in self.grid[key]:
                        eid = id(entity)
                        if eid not in seen:
                            seen.add(eid)
                            dist = math.hypot(entity.x - x,
                                              entity.y - y)
                            if dist <= radius:
                                results.append(entity)
        return results


# Global grid instance
_grid = SpatialGrid(cell_size=100)


def update_spatial_grid(minions, heroes, towers):
    """Panggil sekali per frame di game.update()"""
    _grid.clear()
    for m in minions:
        if m.alive:
            _grid.insert(m)
    for h in heroes:
        if h.alive:
            _grid.insert(h)


def query_enemies_in_range(x, y, radius, team):
    """Query musuh dalam range - CEPAT"""
    candidates = _grid.query_range(x, y, radius)
    return [e for e in candidates
            if hasattr(e, 'team') and e.team != team and e.alive]




# ================================


# ====================================================================
# fps_counter.py
# ====================================================================

# ================================
# fps_counter.py
# FPS Counter - Toggle ON/OFF dengan F8
# ================================

import pygame
import math


class FPSCounter:
    """FPS Counter - Singleton"""

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

        self.enabled = False
        self.fps_history = []
        self.history_size = 120
        self.frame_count = 0
        self.display_fps = 0.0
        self.display_avg = 0.0
        self.display_min = 0.0
        self.display_max = 0.0
        self._fonts = {}

    def _get_font(self, size):
        if size not in self._fonts:
            self._fonts[size] = get_font(size)
        return self._fonts[size]

    def toggle(self):
        self.enabled = not self.enabled
        print(f"[FPS COUNTER] {'ON' if self.enabled else 'OFF'}")

    def update(self, clock):
        """
        Panggil setiap frame dengan clock yang sudah ada.
        TIDAK memanggil clock.tick() sendiri.
        """
        current_fps = clock.get_fps()

        self.fps_history.append(current_fps)
        if len(self.fps_history) > self.history_size:
            self.fps_history.pop(0)

        self.frame_count += 1
        if self.frame_count >= 10:
            self.frame_count = 0
            if self.fps_history:
                recent = self.fps_history[-30:]
                self.display_fps = recent[-1]
                self.display_avg = sum(recent) / len(recent)
                self.display_min = min(recent)
                self.display_max = max(recent)

    def draw(self, surface):
        """Draw FPS counter - hanya kalau enabled"""
        if not self.enabled:
            return

        # ═══ POSISI ═══
        base_x = 10
        base_y = 45

        # ═══ PANEL ═══
        panel_w = 200
        panel_h = 95
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (0, 0, 0, 200),
                         (0, 0, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(panel_surf, (60, 70, 90, 255),
                         (0, 0, panel_w, panel_h), 1, border_radius=8)

        # ═══ FPS COLOR ═══
        fps = self.display_fps
        if fps >= 55:
            fps_color = (100, 255, 100)
            status = "SMOOTH"
        elif fps >= 40:
            fps_color = (255, 255, 100)
            status = "OK"
        elif fps >= 25:
            fps_color = (255, 150, 50)
            status = "SLOW"
        else:
            fps_color = (255, 60, 60)
            status = "LAG!"

        # ═══ FPS NUMBER ═══
        fps_font = self._get_font(40)
        fps_surf = fps_font.render(f"{int(fps)}", True, fps_color)
        panel_surf.blit(fps_surf, (12, 6))

        # ═══ "FPS" LABEL ═══
        lbl_font = self._get_font(16)
        lbl = lbl_font.render("FPS", True, (160, 170, 190))
        panel_surf.blit(lbl, (12 + fps_surf.get_width() + 5, 22))

        # ═══ STATUS ═══
        st_font = self._get_font(15)
        st_surf = st_font.render(status, True, fps_color)
        panel_surf.blit(st_surf,
                        (panel_w - st_surf.get_width() - 10, 10))

        # ═══ TOMBOL INFO ═══
        key_font = self._get_font(12)
        key_surf = key_font.render("[F8] toggle", True, (120, 130, 150))
        panel_surf.blit(key_surf,
                        (panel_w - key_surf.get_width() - 8,
                         panel_h - 15))

        # ═══ STATS ROW ═══
        stat_font = self._get_font(14)
        avg_s = stat_font.render(f"AVG {int(self.display_avg)}",
                                  True, (180, 200, 220))
        min_s = stat_font.render(
            f"MIN {int(self.display_min)}",
            True, (255, 130, 130) if self.display_min < 30
            else (180, 200, 220))
        max_s = stat_font.render(f"MAX {int(self.display_max)}",
                                  True, (180, 200, 220))

        panel_surf.blit(avg_s, (10, 48))
        panel_surf.blit(min_s, (80, 48))
        panel_surf.blit(max_s, (145, 48))

        # ═══ MINI GRAPH ═══
        graph_x = 10
        graph_y = 65
        graph_w = panel_w - 20
        graph_h = 22

        # Background graph
        pygame.draw.rect(panel_surf, (15, 20, 35),
                         (graph_x, graph_y, graph_w, graph_h),
                         border_radius=3)
        pygame.draw.rect(panel_surf, (50, 60, 80),
                         (graph_x, graph_y, graph_w, graph_h),
                         1, border_radius=3)

        # Garis 60 FPS (target)
        line_60_y = graph_y + graph_h - int(graph_h * min(60, 80) / 80)
        pygame.draw.line(panel_surf, (60, 80, 60),
                         (graph_x, line_60_y),
                         (graph_x + graph_w, line_60_y), 1)

        # Garis 30 FPS (warning)
        line_30_y = graph_y + graph_h - int(graph_h * min(30, 80) / 80)
        pygame.draw.line(panel_surf, (80, 40, 40),
                         (graph_x, line_30_y),
                         (graph_x + graph_w, line_30_y), 1)

        # Bar chart
        if len(self.fps_history) > 1:
            num_bars = min(len(self.fps_history), graph_w)
            bar_w = max(1, graph_w // num_bars)
            start_idx = max(0, len(self.fps_history) - num_bars)

            for i in range(num_bars):
                idx = start_idx + i
                if idx >= len(self.fps_history):
                    break

                f = self.fps_history[idx]
                bh = int(graph_h * min(f, 80) / 80)
                bx = graph_x + i * bar_w
                by = graph_y + graph_h - bh

                if f >= 55:
                    bc = (50, 160, 50)
                elif f >= 40:
                    bc = (160, 160, 50)
                elif f >= 25:
                    bc = (160, 90, 40)
                else:
                    bc = (160, 40, 40)

                pygame.draw.rect(panel_surf, bc,
                                 (bx, by,
                                  max(1, bar_w - 1), bh))

        # Blit panel ke screen
        surface.blit(panel_surf, (base_x, base_y))


# ====================================================================
# fps_limiter.py
# ====================================================================

# ================================
# fps_limiter.py
# Adaptive quality berdasarkan FPS
# ================================

import pygame


class AdaptiveQuality:
    """
    Monitor FPS dan turunkan quality kalau drop.
    Tanpa menghilangkan fitur - hanya skip beberapa efek.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.clock = pygame.time.Clock()
        self.fps_history = []
        self.history_size = 30
        self.quality = 'high'  # 'high', 'medium', 'low'

        # Threshold
        self.HIGH_THRESHOLD = 50
        self.MEDIUM_THRESHOLD = 35

    def tick(self, target_fps=60):
        """Call setiap frame, return current quality level"""
        self.clock.tick(target_fps)
        fps = self.clock.get_fps()

        self.fps_history.append(fps)
        if len(self.fps_history) > self.history_size:
            self.fps_history.pop(0)

        # Update quality berdasarkan rata-rata FPS
        if len(self.fps_history) >= 10:
            avg_fps = sum(self.fps_history) / len(self.fps_history)

            if avg_fps >= self.HIGH_THRESHOLD:
                self.quality = 'high'
            elif avg_fps >= self.MEDIUM_THRESHOLD:
                self.quality = 'medium'
            else:
                self.quality = 'low'

        return self.quality

    def get_fps(self):
        return self.clock.get_fps()

    @property
    def skip_glow_effects(self):
        """Skip glow/particle effects saat FPS rendah"""
        return self.quality == 'low'

    @property
    def skip_shadow_effects(self):
        """Skip shadow saat FPS medium/low"""
        return self.quality in ('medium', 'low')

    @property
    def reduce_particles(self):
        """Kurangi jumlah particles"""
        return self.quality != 'high'


# ====================================================================
# sound_manager.py
# ====================================================================

# ================================
# SOUND_MANAGER.PY - Full Featured
# ================================

import pygame
import os
import random


class SoundManager:
    """Global sound manager: BGM + SFX + Voice + Ambient"""

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

        try:
            pygame.mixer.pre_init(frequency=44100, size=-16,
                                   channels=2, buffer=512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(32)
            self.enabled = True
        except pygame.error as e:
            print(f"[WARNING] Sound init failed: {e}")
            self.enabled = False

        self.sounds = {}
        self.throttle = {}

        # Volume settings
        self.master_volume = 0.7
        self.sfx_volume = 0.6
        self.voice_volume = 0.5
        self.bgm_volume = 0.35    # BGM lebih pelan biar ga overpower
        self.ambient_volume = 0.25

        # BGM state
        self.current_bgm = None
        self.bgm_paused = False

        # Ambient loop channel
        self.ambient_channel = None

        # Throttle
        self.throttle_ms = {
            'slash': 80,
            'goblin_attack': 400,
            'goblin_spawn': 200,
            'goblin_death': 150,
            'tower_shoot': 60,
            'bullet_hit': 40,
            'nexus_hit': 300,
            'ui_click': 50,
        }

    def load(self, name, filename, category='sfx'):
        """Load sound file"""
        if not self.enabled:
            return

        path = _sound_path(filename)
        if not os.path.exists(path):
            # Dikumpulkan lalu dilaporkan SEKALI di akhir load_all().
            # Sebelumnya tiap berkas hilang mencetak satu baris; karena
            # assets/sounds pernah kosong total, log startup dipenuhi
            # puluhan peringatan yang mengubur pesan penting.
            self._hilang = getattr(self, "_hilang", [])
            self._hilang.append(filename)
            return

        try:
            sound = pygame.mixer.Sound(path)
            self.sounds[name] = {
                'sound': sound,
                'category': category,
                'path': path,
            }
        except pygame.error as e:
            print(f"[ERROR] Gagal load sound '{path}': {e}")

    def load_all(self):
        """Load semua sounds"""
        if not self.enabled:
            return
        self._hilang = []

        # Goblin
        self.load('goblin_spawn', 'goblin_spawn.wav', 'voice')
        self.load('goblin_attack', 'goblin_attack.wav', 'voice')
        self.load('goblin_death', 'goblin_death.wav', 'voice')

        # Ambient
        self.load('ambient_forest', 'ambient_forest.wav', 'ambient')

        # Combat
        self.load('slash', 'slash.wav', 'sfx')
        self.load('tower_shoot', 'tower_shoot.wav', 'sfx')
        self.load('bullet_hit', 'bullet_hit.wav', 'sfx')
        self.load('explosion', 'explosion.wav', 'sfx')
        self.load('nexus_hit', 'nexus_hit.wav', 'sfx')

        # UI
        self.load('ui_click', 'ui_click.wav', 'sfx')
        self.load('ui_buy', 'ui_buy.wav', 'sfx')
        self.load('ui_upgrade', 'ui_upgrade.wav', 'sfx')
        self.load('ui_error', 'ui_error.wav', 'sfx')
        self.load('ui_sell', 'ui_sell.wav', 'sfx')

        # Events
        self.load('wave_start', 'wave_start.wav', 'sfx')
        self.load('victory', 'victory.wav', 'sfx')
        self.load('defeat', 'defeat.wav', 'sfx')

        # Hero
        self.load('hero_skill', 'hero_skill.wav', 'sfx')
        self.load('hero_spawn', 'hero_spawn.wav', 'sfx')

        hilang = getattr(self, "_hilang", [])
        if hilang:
            print("[AUDIO] %d berkas SoundManager belum ada (BGM/UI): %s%s"
                  % (len(hilang), ", ".join(hilang[:4]),
                     " ..." if len(hilang) > 4 else ""))
        print("[AUDIO] SoundManager memuat %d berkas" % len(self.sounds))

    def play(self, name, volume_mult=1.0):
        """Play sound dengan throttle"""
        if not self.enabled or name not in self.sounds:
            return

        # Throttle
        now = pygame.time.get_ticks()
        throttle_time = self.throttle_ms.get(name, 50)
        last_time = self.throttle.get(name, 0)
        if now - last_time < throttle_time:
            return
        self.throttle[name] = now

        sound_data = self.sounds[name]
        sound = sound_data['sound']

        # Volume
        if sound_data['category'] == 'voice':
            base_vol = self.voice_volume
        elif sound_data['category'] == 'ambient':
            base_vol = self.ambient_volume
        else:
            base_vol = self.sfx_volume

        final_vol = self.master_volume * base_vol * volume_mult
        final_vol = max(0.0, min(1.0, final_vol))

        channel = pygame.mixer.find_channel(True)
        if channel:
            channel.set_volume(final_vol)
            channel.play(sound)

    def play_positional(self, name, x, y, player_x, player_y,
                         max_distance=800, volume_mult=1.0):
        """Sound dengan volume berdasar jarak"""
        if not self.enabled:
            return

        import math
        dist = math.hypot(x - player_x, y - player_y)
        if dist > max_distance:
            return

        distance_vol = 1.0 - (dist / max_distance)
        distance_vol = max(0.15, distance_vol)

        self.play(name, volume_mult=volume_mult * distance_vol)

    # ═══════════════════════════════════════
    # BGM (Background Music)
    # ═══════════════════════════════════════

    def play_bgm(self, filename, loop=True, fade_ms=2000):
        """
        Play background music (loop by default).
        Menggunakan pygame.mixer.music untuk streaming (lebih hemat memory).
        """
        if not self.enabled:
            return

        path = _sound_path(filename)
        if not os.path.exists(path):
            print(f"[WARNING] BGM '{path}' tidak ditemukan!")
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(
                self.master_volume * self.bgm_volume)
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            self.current_bgm = filename
            self.bgm_paused = False
        except pygame.error as e:
            print(f"[ERROR] Gagal play BGM: {e}")

    def stop_bgm(self, fade_ms=1000):
        """Stop BGM dengan fade out"""
        if not self.enabled:
            return
        pygame.mixer.music.fadeout(fade_ms)
        self.current_bgm = None

    def pause_bgm(self):
        """Pause BGM"""
        if self.enabled and self.current_bgm:
            pygame.mixer.music.pause()
            self.bgm_paused = True

    def resume_bgm(self):
        """Resume BGM"""
        if self.enabled and self.bgm_paused:
            pygame.mixer.music.unpause()
            self.bgm_paused = False

    def update_bgm_volume(self):
        """Update BGM volume (dipanggil saat master volume berubah)"""
        if self.enabled:
            pygame.mixer.music.set_volume(
                self.master_volume * self.bgm_volume)

    # ═══════════════════════════════════════
    # AMBIENT LOOP
    # ═══════════════════════════════════════

    def play_ambient(self, name, volume_mult=1.0):
        """Play ambient loop (looping sound seperti hutan/angin)"""
        if not self.enabled or name not in self.sounds:
            return

        sound = self.sounds[name]['sound']
        vol = self.master_volume * self.ambient_volume * volume_mult
        vol = max(0.0, min(1.0, vol))

        # Stop existing ambient
        if self.ambient_channel and self.ambient_channel.get_busy():
            self.ambient_channel.stop()

        self.ambient_channel = pygame.mixer.find_channel(True)
        if self.ambient_channel:
            self.ambient_channel.set_volume(vol)
            self.ambient_channel.play(sound, loops=-1, fade_ms=2000)

    def stop_ambient(self, fade_ms=1500):
        """Stop ambient"""
        if self.ambient_channel:
            self.ambient_channel.fadeout(fade_ms)
            self.ambient_channel = None

    # ═══════════════════════════════════════
    # VOLUME CONTROL
    # ═══════════════════════════════════════

    def set_master_volume(self, vol):
        """Set master volume"""
        self.master_volume = max(0.0, min(1.0, vol))
        self.update_bgm_volume()
        # Update ambient volume
        if self.ambient_channel and self.ambient_channel.get_busy():
            self.ambient_channel.set_volume(
                self.master_volume * self.ambient_volume)

    def stop_all(self):
        """Stop semua"""
        if self.enabled:
            pygame.mixer.stop()
            pygame.mixer.music.stop()


# ====================================================================
# save_manager.py
# ====================================================================

# ================================
# SAVE_MANAGER.PY - Save/Load Progress (Multi-Slot)
# ================================

import json
import os
import time


SAVE_DIR = "saves"
NUM_SLOTS = 3
LEGACY_SAVE_FILE = os.path.join(SAVE_DIR, "progress.json")


class SaveManager:
    """
    Multi-slot save system:
    - 3 slots (slot_1.json, slot_2.json, slot_3.json)
    - Auto-migrate save lama ke Slot 1
    - Metadata per slot (level, gold, playtime, dll)
    """

    _current_slot = 1  # Default active slot

    # ═══════════════════════════════════════
    # SLOT MANAGEMENT
    # ═══════════════════════════════════════

    @staticmethod
    def get_slot_file(slot_num):
        """Get path untuk slot tertentu"""
        return os.path.join(SAVE_DIR, f"slot_{slot_num}.json")

    @staticmethod
    def get_current_slot():
        """Get slot yang sedang aktif"""
        return SaveManager._current_slot

    @staticmethod
    def set_current_slot(slot_num):
        """Set slot aktif untuk save/load"""
        if 1 <= slot_num <= NUM_SLOTS:
            SaveManager._current_slot = slot_num
            print(f"[SAVE] Active slot: {slot_num}")

    @staticmethod
    def ensure_save_dir():
        """Buat save dir kalau belum ada"""
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

    @staticmethod
    def slot_exists(slot_num):
        """Cek apakah slot punya save file"""
        return os.path.exists(SaveManager.get_slot_file(slot_num))

    # ═══════════════════════════════════════
    # AUTO-MIGRATION (legacy → slot 1)
    # ═══════════════════════════════════════

    @staticmethod
    def migrate_legacy_save():
        """
        Migrate save lama (progress.json) ke slot_1.json.
        Cuma jalan kalau progress.json ada DAN slot_1.json belum ada.
        """
        SaveManager.ensure_save_dir()

        if not os.path.exists(LEGACY_SAVE_FILE):
            return False

        slot_1_file = SaveManager.get_slot_file(1)
        if os.path.exists(slot_1_file):
            # Slot 1 sudah ada, jangan overwrite
            return False

        try:
            # Read legacy
            with open(LEGACY_SAVE_FILE, 'r') as f:
                data = json.load(f)

            # Add metadata
            data['slot_created'] = time.time()
            data['slot_last_played'] = time.time()
            data['slot_playtime_seconds'] = 0

            # Write ke slot_1
            with open(slot_1_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"[SAVE] Legacy save migrated to Slot 1")

            # Rename legacy file (backup)
            backup_file = os.path.join(
                SAVE_DIR, "progress_backup.json.old")
            try:
                os.rename(LEGACY_SAVE_FILE, backup_file)
                print(f"[SAVE] Legacy backed up: {backup_file}")
            except Exception:
                pass

            return True
        except Exception as e:
            print(f"[SAVE] Migration failed: {e}")
            return False

    # ═══════════════════════════════════════
    # SAVE / LOAD
    # ═══════════════════════════════════════

    @staticmethod
    def save(data, slot_num=None):
        """Save data ke slot tertentu (default = current slot)"""
        if slot_num is None:
            slot_num = SaveManager._current_slot

        try:
            SaveManager.ensure_save_dir()

            # Update metadata
            data['slot_last_played'] = time.time()
            if 'slot_created' not in data:
                data['slot_created'] = time.time()

            slot_file = SaveManager.get_slot_file(slot_num)
            with open(slot_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[SAVE] Slot {slot_num} saved!")
        except Exception as e:
            print(f"[SAVE] Failed: {e}")

    @staticmethod
    def load(slot_num=None):
        """Load data dari slot tertentu (default = current slot)"""
        if slot_num is None:
            slot_num = SaveManager._current_slot

        # Auto-migrate legacy sekali (kalau perlu)
        SaveManager.migrate_legacy_save()

        try:
            slot_file = SaveManager.get_slot_file(slot_num)
            if os.path.exists(slot_file):
                with open(slot_file, 'r') as f:
                    data = json.load(f)
                print(f"[SAVE] Slot {slot_num} loaded!")

                # Backfill default fields (untuk save lama)
                data.setdefault('unlocked_bosses', [])
                data.setdefault('purchased_heroes', [])
                data.setdefault('meta_gold', 0)
                data.setdefault('completed_levels', [])
                data.setdefault('last_played_level', 1)
                data.setdefault('slot_created', time.time())
                data.setdefault('slot_last_played', time.time())
                data.setdefault('slot_playtime_seconds', 0)
                data.setdefault('level_stats', {})  # ← BARU

                return data
        except Exception as e:
            print(f"[SAVE] Load failed: {e}")

        # Default data (empty slot)
        return SaveManager.get_empty_save()

    @staticmethod
    def get_empty_save():
        """Default empty save data"""
        return {
            'unlocked_bosses': [],
            'purchased_heroes': [],
            'meta_gold': 0,
            'completed_levels': [],
            'last_played_level': 1,
            'slot_created': time.time(),
            'slot_last_played': time.time(),
            'slot_playtime_seconds': 0,
            'level_stats': {},  # ← BARU: dict per level number
        }

    @staticmethod
    def delete_slot(slot_num):
        """Delete save slot"""
        try:
            slot_file = SaveManager.get_slot_file(slot_num)
            if os.path.exists(slot_file):
                os.remove(slot_file)
                print(f"[SAVE] Slot {slot_num} deleted!")
                return True
        except Exception as e:
            print(f"[SAVE] Delete failed: {e}")
        return False

    # ═══════════════════════════════════════
    # SLOT METADATA (untuk display di UI)
    # ═══════════════════════════════════════

    @staticmethod
    def get_slot_info(slot_num):
        """
        Get metadata slot untuk display di UI.
        Return dict dengan info, atau None kalau slot kosong.
        """
        if not SaveManager.slot_exists(slot_num):
            return None

        try:
            slot_file = SaveManager.get_slot_file(slot_num)
            with open(slot_file, 'r') as f:
                data = json.load(f)

            # Calculate info
            completed = data.get('completed_levels', [])
            highest_level = max(completed) if completed else 0
            last_played = data.get('last_played_level', 1)

            return {
                'slot_num': slot_num,
                'meta_gold': data.get('meta_gold', 0),
                'completed_levels': completed,
                'highest_level': highest_level,
                'last_played_level': last_played,
                'purchased_heroes': data.get('purchased_heroes', []),
                'unlocked_bosses': data.get('unlocked_bosses', []),
                'slot_created': data.get('slot_created', 0),
                'slot_last_played': data.get('slot_last_played', 0),
                'playtime_seconds': data.get(
                    'slot_playtime_seconds', 0),
            }
        except Exception as e:
            print(f"[SAVE] Get slot info failed: {e}")
            return None

    @staticmethod
    def get_all_slot_info():
        """Get info semua slot (list of dict/None)"""
        return [SaveManager.get_slot_info(i)
                for i in range(1, NUM_SLOTS + 1)]

    @staticmethod
    def format_playtime(seconds):
        """Format playtime seconds → 'Xh Ym'"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @staticmethod
    def format_last_played(timestamp):
        """Format last played timestamp → readable"""
        if timestamp == 0:
            return "Never"

        try:
            elapsed = time.time() - timestamp

            if elapsed < 60:
                return "Just now"
            elif elapsed < 3600:
                return f"{int(elapsed // 60)}m ago"
            elif elapsed < 86400:
                return f"{int(elapsed // 3600)}h ago"
            elif elapsed < 604800:
                return f"{int(elapsed // 86400)}d ago"
            else:
                return time.strftime(
                    "%d %b %Y", time.localtime(timestamp))
        except Exception:
            return "Unknown"

    # ═══════════════════════════════════════
    # LEVEL STATS TRACKING
    # ═══════════════════════════════════════

    @staticmethod
    def get_level_stats(data, level_num):
        """
        Get stats untuk level tertentu.
        Return dict dengan default kalau belum ada.
        """
        stats_dict = data.get('level_stats', {})
        level_key = str(level_num)

        if level_key not in stats_dict:
            return {
                'best_score': 0,
                'best_time_seconds': 0,   # 0 = belum pernah
                'total_attempts': 0,
                'wins': 0,
                'total_kills': 0,
                'max_combo': 0,
                'total_playtime_seconds': 0,
            }

        return stats_dict[level_key]

    @staticmethod
    def update_level_stats(data, level_num, match_stats):
        """
        Update stats level dengan hasil match.

        Args:
            data: save data dict
            level_num: int
            match_stats: dict dengan keys:
                - 'won': bool
                - 'score': int
                - 'time_seconds': int (durasi match)
                - 'kills': int
                - 'combo': int
                - 'playtime_seconds': int (waktu match ini)

        Returns:
            dict {
                'is_new_best_score': bool,
                'is_new_best_time': bool,
                'new_stats': stats after update
            }
        """
        if 'level_stats' not in data:
            data['level_stats'] = {}

        level_key = str(level_num)
        current = SaveManager.get_level_stats(data, level_num)

        is_new_best_score = False
        is_new_best_time = False

        # Update total attempts
        current['total_attempts'] += 1

        # Update total playtime
        current['total_playtime_seconds'] += \
            match_stats.get('playtime_seconds', 0)

        # Update total kills (cumulative)
        current['total_kills'] += match_stats.get('kills', 0)

        # Update max combo (all-time)
        if match_stats.get('combo', 0) > current['max_combo']:
            current['max_combo'] = match_stats.get('combo', 0)

        # HANYA update best score/time kalau WIN
        if match_stats.get('won', False):
            current['wins'] += 1

            # Best score (higher is better)
            if match_stats.get('score', 0) > current['best_score']:
                current['best_score'] = match_stats.get('score', 0)
                is_new_best_score = True

            # Best time (lower is better, 0 = belum pernah)
            match_time = match_stats.get('time_seconds', 0)
            if match_time > 0:
                if current['best_time_seconds'] == 0 or \
                        match_time < current['best_time_seconds']:
                    current['best_time_seconds'] = match_time
                    is_new_best_time = True

        # Save back
        data['level_stats'][level_key] = current

        return {
            'is_new_best_score': is_new_best_score,
            'is_new_best_time': is_new_best_time,
            'new_stats': current,
        }

    @staticmethod
    def format_time(seconds):
        """Format seconds → 'M:SS'"""
        if seconds == 0:
            return "--:--"

        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
