# ================================
# mobile/debug.py
# Overlay debug on-device + logging ke logcat
#
# Cara pakai di HP:
#   - Tekan tombol "FPS" di kanan atas untuk siklus mode:
#       OFF -> RINGKAS -> LENGKAP -> GRAFIK -> OFF
#   - Semua yang tampil juga dicetak ke stdout, dan di Android
#     stdout masuk ke logcat, jadi bisa dipantau lewat:
#       adb logcat -s python:*
# ================================

import gc
import os
import time
from collections import deque

import pygame

from mobile import platform_utils as plat
from mobile import perf

MODE_OFF, MODE_MINI, MODE_FULL, MODE_GRAPH = 0, 1, 2, 3
_MODE_NAMES = ["off", "mini", "full", "graph"]

BG = (0, 0, 0, 170)
OK = (120, 235, 140)
WARN = (255, 205, 90)
BAD = (255, 110, 110)
TXT = (225, 228, 240)


def _color_for_fps(fps):
    if fps >= 50:
        return OK
    if fps >= 30:
        return WARN
    return BAD


class DebugOverlay:
    def __init__(self, get_font, frame_timer=None, log_interval=5.0):
        self._get_font = get_font
        self.mode = MODE_OFF
        self.timer = frame_timer or perf.FrameTimer()
        self.fps_history = deque(maxlen=180)
        self.frame_ms_history = deque(maxlen=180)
        self._last_log = 0.0
        self.log_interval = log_interval
        self.log_to_console = True
        self.device = plat.get_device_info()
        self.extra = {}
        self._peak_ms = 0.0
        self._slow_frames = 0
        self._frames = 0

    # ── kontrol ───────────────────────────────────────
    def toggle(self):
        self.mode = (self.mode + 1) % 4
        print("[DEBUG] overlay = %s" % _MODE_NAMES[self.mode])
        return self.mode

    def set_mode(self, mode):
        self.mode = mode % 4

    @property
    def enabled(self):
        return self.mode != MODE_OFF

    # ── pengumpulan data ──────────────────────────────
    def update(self, clock, game=None):
        fps = clock.get_fps()
        frame_ms = clock.get_time()
        self.fps_history.append(fps)
        self.frame_ms_history.append(frame_ms)
        self._frames += 1
        if frame_ms > self._peak_ms:
            self._peak_ms = frame_ms
        if frame_ms > 33:
            self._slow_frames += 1

        now = time.perf_counter()
        if self.log_to_console and now - self._last_log >= self.log_interval:
            self._last_log = now
            self._log_line(fps, game)

    def _log_line(self, fps, game):
        t = self.timer.report()
        counts = self._entity_counts(game)
        print("[PERF] fps=%.1f frame=%.1fms upd=%.1f draw=%.1f "
              "q=%s ent=%s mem=%s" % (
                  fps, self._avg(self.frame_ms_history),
                  t.get("update", 0.0), t.get("draw", 0.0),
                  perf.Quality.level, counts, self._memory_str()))

    @staticmethod
    def _avg(seq):
        return sum(seq) / len(seq) if seq else 0.0

    @staticmethod
    def _entity_counts(game):
        if game is None:
            return "-"
        try:
            return "m%d/t%d/h%d/p%d" % (
                len(getattr(game, "minions", [])),
                len(getattr(game, "towers", [])),
                len(getattr(game, "heroes", [])),
                len(getattr(game, "projectiles", []))
                if hasattr(game, "projectiles") else 0)
        except Exception:
            return "-"

    @staticmethod
    def _memory_str():
        # Tanpa dependensi tambahan: baca /proc (ada di Android & Linux)
        try:
            with open("/proc/self/statm", "r") as fh:
                pages = int(fh.read().split()[1])
            mb = pages * os.sysconf("SC_PAGE_SIZE") / (1024 * 1024)
            return "%.0fMB" % mb
        except Exception:
            return "n/a"

    # ── gambar ────────────────────────────────────────
    def draw(self, surface, clock, game=None, touch=None):
        if self.mode == MODE_OFF:
            return
        if self.mode == MODE_MINI:
            self._draw_mini(surface, clock)
        elif self.mode == MODE_FULL:
            self._draw_full(surface, clock, game)
        else:
            self._draw_full(surface, clock, game)
            self._draw_graph(surface)
        if touch is not None:
            self._draw_touch(surface, touch)

    def _panel(self, surface, x, y, w, h):
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill(BG)
        pygame.draw.rect(panel, (90, 90, 120), panel.get_rect(), 1)
        surface.blit(panel, (x, y))

    def _draw_mini(self, surface, clock):
        fps = clock.get_fps()
        font = self._get_font(20, "body_bold")
        text = "%3.0f FPS  %4.1fms" % (fps, self._avg(self.frame_ms_history))
        safe = plat.get_safe_area()
        surf = font.render(text, True, _color_for_fps(fps))
        x = safe.left + 6
        y = safe.top + 6
        self._panel(surface, x - 4, y - 3, surf.get_width() + 12,
                    surf.get_height() + 8)
        surface.blit(surf, (x + 2, y + 1))

    def _draw_full(self, surface, clock, game):
        fps = clock.get_fps()
        t = self.timer.report()
        fstats = perf.font_cache_stats()
        safe = plat.get_safe_area()

        lines = [
            ("%3.0f FPS   frame %4.1f ms   peak %4.1f ms"
             % (fps, self._avg(self.frame_ms_history), self._peak_ms),
             _color_for_fps(fps)),
            ("event %4.1f | update %4.1f | draw %4.1f | flip %4.1f ms"
             % (t.get("event", 0), t.get("update", 0),
                t.get("draw", 0), t.get("flip", 0)), TXT),
            ("entity %s   quality %s   slowframe %d/%d"
             % (self._entity_counts(game), perf.Quality.level,
                self._slow_frames, self._frames), TXT),
            ("font new %d / reuse %d   text render %d / cache %d"
             % (fstats["font_created"], fstats["font_reused"],
                fstats["text_rendered"], fstats["text_cached"]), TXT),
            ("mem %s   gc %s   surfpool hit %d/new %d"
             % (self._memory_str(), gc.get_count(),
                fstats["surf_pool_hit"], fstats["surf_pool_new"]), TXT),
            ("%s | Android %s (API %s) | pygame %s / SDL %s"
             % (self.device["model"], self.device["android_release"],
                self.device["api_level"], self.device["pygame"],
                self.device["sdl"]), (150, 170, 210)),
        ]
        try:
            from mobile import blitwatch
            if blitwatch.enabled() and blitwatch.FRAMES[0] > 5:
                lines.append(("ALPHA BLIT ~%.0f ms/frame:"
                              % blitwatch.total_ms(), (255, 140, 140)))
                for key, px, ms in blitwatch.top(3):
                    lines.append(("   %-42s %6.0fpx %5.1fms"
                                  % (key[:42], px, ms), (255, 170, 150)))
        except Exception:
            pass

        try:
            from mobile.perf import PHASES
            top = PHASES.top(6)
            if top:
                lines.append(("DRAW: " + "  ".join(
                    "%s %.0f" % (k, v) for k, v in top), (255, 190, 120)))
        except Exception:
            pass

        for key, val in self.extra.items():
            lines.append(("%s: %s" % (key, val), (200, 190, 140)))

        font = self._get_font(16, "body")
        w = max(font.size(s)[0] for s, _ in lines) + 18
        h = len(lines) * 19 + 12
        x, y = safe.left + 4, safe.top + 4
        self._panel(surface, x, y, w, h)
        for i, (text, color) in enumerate(lines):
            surface.blit(font.render(text, True, color),
                         (x + 8, y + 6 + i * 19))

    def _draw_graph(self, surface):
        safe = plat.get_safe_area()
        w, h = 240, 70
        x = safe.left + 4
        y = safe.top + 145
        self._panel(surface, x, y, w, h)

        # garis 60 fps (16.7ms) dan 30 fps (33.3ms)
        for ms, col in ((16.7, (70, 120, 70)), (33.3, (120, 80, 60))):
            gy = y + h - int(min(ms, 50) / 50.0 * h)
            pygame.draw.line(surface, col, (x, gy), (x + w, gy), 1)

        pts = []
        data = list(self.frame_ms_history)[-w:]
        if len(data) > 1:
            step = w / max(1, len(data) - 1)
            for i, ms in enumerate(data):
                gy = y + h - int(min(ms, 50) / 50.0 * h)
                pts.append((x + i * step, gy))
            pygame.draw.lines(surface, (150, 220, 255), False, pts, 1)

    def _draw_touch(self, surface, touch):
        """Lingkaran di titik jari - membantu debug area tekan."""
        if self.mode == MODE_OFF:
            return
        for tp in getattr(touch, "points", {}).values():
            pygame.draw.circle(surface, (90, 220, 255),
                               (int(tp.pos[0]), int(tp.pos[1])), 26, 2)
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(tp.pos[0]), int(tp.pos[1])), 3)


# ═══════════════════════════════════════════════════════
# PENANGKAP CRASH -> tulis ke file + logcat
# ═══════════════════════════════════════════════════════
def install_crash_handler(log_dir=None):
    """
    Simpan traceback ke <writable>/crash_log.txt supaya bug di HP
    tetap bisa dibaca walau tidak sedang tersambung ke adb.
    """
    import sys
    import traceback

    log_dir = log_dir or plat.get_writable_dir()
    path = os.path.join(log_dir, "crash_log.txt")

    def _hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        print("[CRASH]\n" + text)
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\n===== %s =====\n%s"
                         % (time.strftime("%Y-%m-%d %H:%M:%S"), text))
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook
    return path
