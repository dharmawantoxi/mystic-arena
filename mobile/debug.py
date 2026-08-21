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


def _build_label():
    try:
        from mobile.buildinfo import label
        return label()
    except Exception:
        return "BUILD ?"


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
    def _fastblit_line():
        """
        Status jalur cepat alpha + cache sprite dalam satu baris.

        Ini yang membedakan "perbaikannya tidak berhasil" dari
        "perbaikannya tidak pernah menyala" - dua hal yang sudah
        berkali-kali tertukar dalam proyek ini.
        """
        try:
            from mobile import fastblit
            bagian = ("jalur cepat alpha(SDL): %s"
                      % ("ON" if fastblit.AKTIF else "off"))
            st = fastblit.stats()
            if st["sdl2"] or st["lewat"]:
                bagian += " %d/%d" % (st["sdl2"], st["sdl2"] + st["lewat"])
        except Exception:
            bagian = "jalur cepat alpha: ?"
        try:
            from mobile import spritecache
            c = spritecache.stats()
            total = c["hit"] + c["miss"]
            if total:
                bagian += ("   minion %d%%" % (100 * c["hit"] // total))
        except Exception:
            pass
        # Cache HERO adalah penentu terbesar: satu miss = render penuh
        # + get_bounding_rect + smoothscale (~98 ms/hero saat v22).
        try:
            import heroes
            h = heroes.hero_cache_stats()
            tot = h.get("hits", 0) + h.get("misses", 0)
            if tot:
                bagian += ("   cache HERO hit %d%% (%d miss, %d entri)"
                           % (100 * h["hits"] // tot, h["misses"],
                              h.get("entries", 0)))
        except Exception:
            pass
        return bagian

    @staticmethod
    def _memori_line():
        """Rincian pemakaian memori - 491 MB terukur di HP uji."""
        bagian = []
        try:
            import heroes
            bagian.append("cache hero %.0fMB" % heroes.hero_cache_bytes())
        except Exception:
            pass
        try:
            from mobile import spritecache
            bagian.append("cache unit %d entri"
                          % spritecache.stats().get("entries", 0))
        except Exception:
            pass
        return "memori: " + "  ".join(bagian) if bagian else "memori: -"

    @staticmethod
    def _fastblit_color():
        try:
            from mobile import fastblit
            return (120, 235, 140) if fastblit.AKTIF else (255, 205, 90)
        except Exception:
            return (200, 190, 140)

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
        # Panel ber-alpha seukuran ini = ~33 ms di HP (244 ns/piksel).
        # Alat ukur tidak boleh lebih mahal dari yang diukur.
        try:
            from mobile.perf import Quality
            cheap = Quality.cheap_alpha
        except Exception:
            cheap = True
        if cheap:
            panel = pygame.Surface((w, h), pygame.SRCALPHA)
            panel.fill(BG)
            pygame.draw.rect(panel, (90, 90, 120), panel.get_rect(), 1)
            surface.blit(panel, (x, y))
        else:
            pygame.draw.rect(surface, (8, 8, 14), (x, y, w, h))
            pygame.draw.rect(surface, (90, 90, 120), (x, y, w, h), 1)

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

    # ═══ ALAT UKUR TIDAK BOLEH MENGGANGGU YANG DIUKUR ═══
    # Terukur di HP: overlay ini sendiri memakan 14 ms dari 38 ms
    # total draw - 36% dari yang sedang diukur.
    #
    # Penyebabnya bukan panel atau blit, melainkan TEKSNYA. Setiap
    # baris memuat angka yang berubah tiap frame, jadi string-nya
    # selalu baru dan cache teks selalu meleset -> 14 render font
    # per frame.
    #
    # Isi baris cukup diperbarui 4x per detik. Selain jauh lebih
    # murah, angkanya juga jadi terbaca (sebelumnya berkedip 23x
    # per detik).
    JEDA_SEGAR_MS = 250
    _lines_cache = None
    _lines_at = 0.0
    _panel_buf = None
    _panel_lines = None

    def _draw_full(self, surface, clock, game):
        import time as _t
        sekarang = _t.perf_counter() * 1000.0
        if (self._lines_cache is None
                or sekarang - self._lines_at >= self.JEDA_SEGAR_MS):
            self._lines_cache = self._build_lines(clock, game)
            self._lines_at = sekarang
        lines = self._lines_cache
        safe = plat.get_safe_area()
        self._render_lines(surface, lines, safe)

    def _build_lines(self, clock, game):
        fps = clock.get_fps()
        t = self.timer.report()
        fstats = perf.font_cache_stats()

        lines = [
            ("%3.0f FPS   frame %4.1f ms   peak %4.1f ms"
             % (fps, self._avg(self.frame_ms_history), self._peak_ms),
             _color_for_fps(fps)),
            ("event %4.1f | update %4.1f | draw %4.1f | flip %4.1f ms"
             % (t.get("event", 0), t.get("update", 0),
                t.get("draw", 0), t.get("flip", 0)), TXT),
            ("entity %s  quality %s  hemat:%s  sprite:%s  slow %d/%d"
             % (self._entity_counts(game), perf.Quality.level,
                "ON" if not perf.Quality.cheap_alpha else "off",
                "ON" if perf.Quality.sprite_cache else "off",
                self._slow_frames, self._frames),
             OK if not perf.Quality.cheap_alpha else WARN),
            ("konversi sprite: %s   |   %s"
             % (perf.convert_stats(), perf.Quality.colorkey_gain and
                "gain %.0fx" % perf.Quality.colorkey_gain or "-"),
             (200, 190, 140)),
            (self._fastblit_line(), self._fastblit_color()),
            (self._memori_line(), (190, 190, 220)),
            ("font new %d / reuse %d   text render %d / cache %d"
             % (fstats["font_created"], fstats["font_reused"],
                fstats["text_rendered"], fstats["text_cached"]), TXT),
            ("mem %s   gc %s   surfpool hit %d/new %d"
             % (self._memory_str(), gc.get_count(),
                fstats["surf_pool_hit"], fstats["surf_pool_new"]), TXT),
            (_build_label(), (140, 230, 160)),
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
            top = PHASES.top(20)
            if top:
                tot = sum(v for _, v in top)
                shown = top[:6]
                txt = "  ".join("%s %.0f" % (k, v) for k, v in shown)
                lines.append(("DRAW(%0.f ms): %s" % (tot, txt),
                              (255, 190, 120)))
                rest = top[6:]
                if rest:
                    lines.append(("  ...: " + "  ".join(
                        "%s %.0f" % (k, v) for k, v in rest[:6]),
                        (230, 170, 110)))
        except Exception:
            pass

        for key, val in self.extra.items():
            lines.append(("%s: %s" % (key, val), (200, 190, 140)))

        return lines

    def _render_lines(self, surface, lines, safe):
        """
        SELALU lewat buffer opaque yang di-cache.

        Versi lama hanya memakai buffer ini di perangkat lambat
        (cheap_alpha False). Setelah NEON hidup, cheap_alpha jadi True
        dan overlay kembali ke jalur naif: panel ber-alpha + 14 render
        font setiap frame = 14 ms. Buffer ini murah di kedua kondisi,
        jadi tidak ada alasan memisahkan jalurnya.
        """
        font = self._get_font(16, "body")
        w = max(font.size(t)[0] for t, _ in lines) + 18
        h = len(lines) * 19 + 12
        x, y = safe.left + 4, safe.top + 4

        buf = getattr(self, "_panel_buf", None)
        perlu = (buf is None or buf.get_size() != (w, h)
                 or getattr(self, "_panel_lines", None) is not lines)
        if perlu:
            if buf is None or buf.get_size() != (w, h):
                buf = pygame.Surface((w, h)).convert()
                self._panel_buf = buf
            buf.fill((8, 8, 14))
            pygame.draw.rect(buf, (90, 90, 120), buf.get_rect(), 1)
            for idx, (text, color) in enumerate(lines):
                buf.blit(font.render(text, True, color), (8, 6 + idx * 19))
            self._panel_lines = lines
        surface.blit(buf, (x, y))

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
