#!/usr/bin/env python3
"""test_godot_mobile_touch_parity.py — oracle `mobile/touch.py` +
`mobile/debug.py` + `mobile/platform_utils.get_safe_area()` untuk port Godot
(`TouchGestures.gd`, `DebugOverlay.gd`, `MobileLayout.safe_area()`).

Ini tool gap #3/#4/#5/#6/#8 di docs/AUDIT_ULANG_DARI_AWAL.md: rantai
"tahan >= 450 ms = klik kanan, overlay debug 4 mode, getar, safe-area".

Tiga lapis, sama seperti tool paritas lain di repo ini:

  1. ORACLE — kode SUNGGUHAN pygame dijalankan, tidak ada rumus yang
     disalin ke tool ini:
     * `TouchManager.process_event/update/cancel/collect` dengan jam palsu
       (`time.perf_counter` di-monkeypatch -> ambang 450/280 ms dan held_ms
       deterministik). Yang direkam: urutan aksi lengkap (tap vs long_press
       vs double_tap, notch scroll, fling + inersia per frame), nilai
       `consumed`, kecepatan fling akhir, dan state `points`.
     * `DebugOverlay.update/toggle/set_mode/_build_lines/_log_line` dengan
       clock + game palsu -> riwayat 180, peak, frame lambat, warna tangga
       fps, teks baris LENGKAP + warnanya, baris `[PERF]` (dibajak dari
       stdout), dan GEOMETRI panel yang benar-benar digambar (jejak
       `pygame.draw.*` + `surface.blit` direkam lewat permukaan dan proxy
       pencatat).
     * `platform_utils.get_safe_area()` dengan MYSTIC_FORCE_TOUCH=1 -> rect
       (28, 10, 1280-56, 720-20) yang sama dipakai layout sentuh Godot.
     Font pygame TIDAK identik dengan font Godot, jadi oracle menginjeksi
     font palsu dengan RUMUS UKURAN `len(text) * size * 3 // 8` dan tes
     Godot memakai measurer dengan rumus yang sama -> yang dibandingkan
     adalah aritmetika tata letak, bukan hasil raster.

  2. PIN STATIK — konstanta + literal format + geometri di-PIN dari TEKS
     SUMBER `mobile/touch.py`, `mobile/debug.py`, `mobile/platform_utils.py`
     dan `main.py`, lalu padanannya dicari di `godot/scenes/ui/
     DebugOverlay.gd`, `godot/scripts/systems/TouchGestures.gd`,
     `godot/scripts/autoload/MobileLayout.gd`, `godot/scenes/main/Main.gd`,
     `godot/scenes/ui/SidePanel.gd`, `godot/scenes/ui/TouchHUD.gd`,
     `godot/scenes/ui/HUD.gd`. Pola yang hilang = tool GAGAL, supaya
     perubahan diam-diam di salah satu sisi tidak bisa lolos.

  3. FIXTURE — `godot/tests/fixtures/mobile_touch.json`, diputar ulang oleh
     `godot/tests/MobileTouchParityTest.tscn` lewat KELAS PRODUKSINYA.

Jalankan:
  python3 tools/test_godot_mobile_touch_parity.py                  # cek
  python3 tools/test_godot_mobile_touch_parity.py --write-fixture  # regenerasi
"""
import argparse
import contextlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
# safe area hanya aktif di mode sentuh (platform_utils:621) - paksa supaya
# rumus (28, 10, W-56, H-20) yang di-oracle, bukan rect arena penuh.
os.environ["MYSTIC_FORCE_TOUCH"] = "1"
sys.path.insert(0, ROOT)

FIXTURE = os.path.join(ROOT, "godot", "tests", "fixtures", "mobile_touch.json")
GODOT = os.path.join(ROOT, "godot")
SRC = {
    "touch.py": os.path.join(ROOT, "mobile", "touch.py"),
    "debug.py": os.path.join(ROOT, "mobile", "debug.py"),
    "platform_utils.py": os.path.join(ROOT, "mobile", "platform_utils.py"),
    "main.py": os.path.join(ROOT, "main.py"),
    "TouchGestures.gd": os.path.join(GODOT, "scripts", "systems",
                                      "TouchGestures.gd"),
    "DebugOverlay.gd": os.path.join(GODOT, "scenes", "ui", "DebugOverlay.gd"),
    "MobileLayout.gd": os.path.join(GODOT, "scripts", "autoload",
                                    "MobileLayout.gd"),
    "Main.gd": os.path.join(GODOT, "scenes", "main", "Main.gd"),
    "SidePanel.gd": os.path.join(GODOT, "scenes", "ui", "SidePanel.gd"),
    "TouchHUD.gd": os.path.join(GODOT, "scenes", "ui", "TouchHUD.gd"),
    "HUD.gd": os.path.join(GODOT, "scenes", "ui", "HUD.gd"),
    "MobileTouchParityTest.gd": os.path.join(GODOT, "tests",
                                             "MobileTouchParityTest.gd"),
    "combat_audio.py": os.path.join(ROOT, "mobile", "combat_audio.py"),
    "hud.py": os.path.join(ROOT, "mobile", "hud.py"),
}

# Skenario replay overlay. Nilai sengaja TIDAK jatuh di .5 supaya
# pembulatan "%.1f"/"%3.0f" identik di libc mana pun (tie-break bisa beda).
FEED = [[41.5, 26.25, 40], [59.25, 17.125, 139]]
FINAL = [58.62, 18.25]
SLOW_FEED = [24.25, 41.375]
LOG_FRAME = [31.26, 27.53]
ENTITIES = [3, 1, 2, 4]
QUALITY = ("high", True, True)
TOUCH_POINTS = [[100, 200], [640, 360], [1279, 719]]

PASS = []


def check(cond, msg):
    if not cond:
        raise AssertionError("GAGAL: %s" % msg)
    PASS.append(msg)


def read(name):
    with open(SRC[name], "r", encoding="utf-8") as fh:
        return fh.read()


def pin(pattern, name, what, flags=0):
    m = re.search(pattern, read(name), flags)
    check(m is not None, "%s: pola %r hilang dari %s"
          % (what, pattern, SRC[name]))
    return m


def _jsonable(value):
    """Jejak menggambar pygame -> bentuk yang bisa di-JSON (Surface/Rect ->
    angka). Yang dibandingkan koordinat + ukuran, bukan objeknya."""
    import pygame
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pygame.Rect):
        return [value.left, value.top, value.width, value.height]
    if isinstance(value, pygame.Surface):
        return ["surface", value.get_width(), value.get_height()]
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return round(float(value), 6)
    return str(value)


def no_tie(value, digits, what):
    """`%.1f` untuk angka yang berakhir tepat di .5 dibulatkan berbeda oleh
    pembulats yang tidak sama (banker's vs half-up). Godot dan CPython sama-
    sama memakai libc, jadi TIDAK ada yang boleh jatuh di tie -> skenario
    dijamin bebas tie supaya fixture bisa direproduksi GDScript bit-per-bit."""
    scaled = float(value) * (10.0 ** digits)
    check(abs(scaled - floor_nearest(scaled)) > 1e-6,
          "%s: %.10f jatuh di tie pembulatan digit ke-%d"
          % (what, float(value), digits))


def floor_nearest(x):
    return float(int(x + 0.5)) if x >= 0 else -float(int(-x + 0.5))


def fake_font_metrics(text, size):
    """Rumus ukuran font yang DIPAKAI KEDUA SISI (oracle lewat OracleFont,
    tes Godot lewat measurer palsunya) - lihat docstring."""
    return (len(text) * size * 3 // 8, size)


# ══════════════════════════════════════════════════════════
#  1. ORACLE GESTURE
# ══════════════════════════════════════════════════════════

class FakeTime(object):
    """`time.perf_counter()` dengan jam yang bisa diputar. touch.py mengali
    1000.0 sendiri, jadi langkah skenario ditulis dalam ms."""

    def __init__(self):
        self.now_ms = 0.0

    def perf_counter(self):
        return self.now_ms / 1000.0


class FakeEvent(object):
    """Event tetikus sintetis: `process_event` hanya membaca
    .type/.button/.pos/.buttons, jadi objek biasa cukup."""

    def __init__(self, kind, pos):
        import pygame
        self.type = {"down": pygame.MOUSEBUTTONDOWN,
                     "up": pygame.MOUSEBUTTONUP,
                     "motion": pygame.MOUSEMOTION,
                     "wheel_up": pygame.MOUSEBUTTONDOWN,
                     "wheel_down": pygame.MOUSEBUTTONDOWN,
                     "right": pygame.MOUSEBUTTONDOWN}[kind]
        self.pos = pos
        self.button = {"down": 1, "up": 1, "wheel_up": 4,
                       "wheel_down": 5, "right": 3}.get(kind, 0)
        self.buttons = (1, 0, 0) if kind == "motion" else (0, 0, 0)


TOUCH_SCENARIOS = [
    ("tap_dilepas_sebelum_450ms", [
        {"kind": "down", "pos": [300, 400], "t": 0.0},
        {"kind": "up", "pos": [300, 400], "t": 120.0},
    ]),
    ("tahan_jadi_klik_kanan", [
        {"kind": "down", "pos": [300, 400], "t": 0.0},
        {"kind": "update", "t": 300.0},
        {"kind": "update", "t": 449.9},
        {"kind": "update", "t": 450.0},
        {"kind": "up", "pos": [300, 400], "t": 700.0},
    ]),
    ("lepas_di_449ms_bukan_long_press", [
        {"kind": "down", "pos": [100, 100], "t": 0.0},
        {"kind": "update", "t": 440.0},
        {"kind": "up", "pos": [100, 100], "t": 449.0},
    ]),
    ("double_tap_dalam_280ms", [
        {"kind": "down", "pos": [640, 360], "t": 0.0},
        {"kind": "up", "pos": [640, 360], "t": 80.0},
        {"kind": "down", "pos": [645, 355], "t": 200.0},
        {"kind": "up", "pos": [645, 355], "t": 260.0},
    ]),
    ("tap_kedua_41px_bukan_double", [
        {"kind": "down", "pos": [640, 360], "t": 0.0},
        {"kind": "up", "pos": [640, 360], "t": 80.0},
        {"kind": "down", "pos": [681, 360], "t": 200.0},
        {"kind": "up", "pos": [681, 360], "t": 260.0},
    ]),
    ("tap_kedua_281ms_bukan_double", [
        {"kind": "down", "pos": [640, 360], "t": 0.0},
        {"kind": "up", "pos": [640, 360], "t": 80.0},
        {"kind": "down", "pos": [640, 360], "t": 361.0},
        {"kind": "up", "pos": [640, 360], "t": 420.0},
    ]),
    ("seret_turun_dua_notch_scroll", [
        {"kind": "down", "pos": [500, 200], "t": 0.0},
        {"kind": "motion", "pos": [500, 225]},
        {"kind": "motion", "pos": [500, 270]},
        {"kind": "motion", "pos": [500, 245]},
        {"kind": "up", "pos": [500, 245], "t": 200.0},
    ]),
    ("geser_8px_masih_tap", [
        {"kind": "down", "pos": [500, 200], "t": 0.0},
        {"kind": "motion", "pos": [498, 206]},
        {"kind": "up", "pos": [498, 206], "t": 120.0},
    ]),
    ("fling_dan_inersia", [
        {"kind": "down", "pos": [500, 300], "t": 0.0},
        {"kind": "motion", "pos": [500, 330]},
        {"kind": "motion", "pos": [500, 368]},
        {"kind": "up", "pos": [500, 368], "t": 90.0},
        {"kind": "update", "t": 100.0},
        {"kind": "update", "t": 116.0},
        {"kind": "update", "t": 132.0},
        {"kind": "update", "t": 148.0},
        {"kind": "update", "t": 164.0},
    ]),
    ("tahan_lalu_seret_jauh_tidak_ada_tap", [
        {"kind": "down", "pos": [400, 400], "t": 0.0},
        {"kind": "update", "t": 500.0},
        {"kind": "motion", "pos": [430, 460]},
        {"kind": "up", "pos": [430, 460], "t": 700.0},
    ]),
    ("klik_kanan_langsung_long_press", [
        {"kind": "right", "pos": [222, 333], "t": 0.0},
    ]),
    ("mouse_wheel_naik_turun", [
        {"kind": "wheel_up", "pos": [640, 360], "t": 0.0},
        {"kind": "wheel_down", "pos": [640, 360], "t": 16.0},
    ]),
    ("cancel_membuang_tekanan", [
        {"kind": "down", "pos": [700, 500], "t": 0.0},
        {"kind": "cancel", "t": 10.0},
        {"kind": "update", "t": 900.0},
        {"kind": "up", "pos": [700, 500], "t": 910.0},
    ]),
    ("dua_jari_mandiri", [
        {"kind": "down", "pos": [200, 300], "t": 0.0},
        {"kind": "down", "pos": [900, 300], "t": 40.0},
        {"kind": "update", "t": 460.0},
        {"kind": "up", "pos": [200, 300], "t": 500.0},
        {"kind": "up", "pos": [900, 300], "t": 520.0},
    ]),
]


def run_touch_scenario(touch_mod, name, steps):
    """Satu skenario pada TouchManager ASLI -> jejak aksi + state akhir."""
    clock = FakeTime()
    real_time = touch_mod.time
    touch_mod.time = clock
    try:
        mgr = touch_mod.TouchManager(use_finger_events=False)
        trace = []
        for ev in steps:
            if "t" in ev:
                clock.now_ms = float(ev["t"])
            kind = ev["kind"]
            if kind == "update":
                mgr.update()
            elif kind == "cancel":
                mgr.cancel()
            else:
                consumed = mgr.process_event(FakeEvent(
                    kind, (int(ev["pos"][0]), int(ev["pos"][1]))))
                trace.append({"step": kind, "consumed": bool(consumed)})
            for a in mgr.collect():
                trace.append({"action": a.kind,
                              "pos": [round(float(a.pos[0]), 4),
                                      round(float(a.pos[1]), 4)],
                              "delta": [round(float(a.delta[0]), 4),
                                        round(float(a.delta[1]), 4)],
                              "value": round(float(a.value), 6),
                              "touch_id": int(a.touch_id)})
        return {"name": name, "steps": steps, "trace": trace,
                "fling_velocity": round(float(mgr.fling_velocity), 6),
                "open_points": len(mgr.points),
                "counts": {k: int(v) for k, v in mgr.counts.items()},
                "active_pos": None if mgr.active_pos is None
                else [round(float(mgr.active_pos[0]), 4),
                      round(float(mgr.active_pos[1]), 4)]}
    finally:
        touch_mod.time = real_time


# ══════════════════════════════════════════════════════════
#  2. ORACLE OVERLAY
# ══════════════════════════════════════════════════════════

class FakeClock(object):
    def __init__(self, fps, frame_ms):
        self._fps = float(fps)
        self._ms = float(frame_ms)

    def get_fps(self):
        return self._fps

    def get_time(self):
        return self._ms


class FakeGame(object):
    def __init__(self, minions, towers, heroes, projectiles):
        self.minions = minions
        self.towers = towers
        self.heroes = heroes
        self.projectiles = projectiles


class FakeTouch(object):
    def __init__(self, points):
        import collections
        self.points = collections.OrderedDict()
        for i, p in enumerate(points):
            # TouchPoint sungguhan punya 10 slot; `_draw_touch` hanya
            # membaca .pos -> itu yang dipalsukan di sini.
            self.points[i] = type("TP", (), {
                "pos": (float(p[0]), float(p[1])),
            })()


class OracleFont(object):
    """Font palsu dengan rumus ukuran bersama (lihat fake_font_metrics)."""

    def __init__(self, size):
        self._size = size

    def size(self, text):
        return fake_font_metrics(text, self._size)

    def render(self, text, antialias, color):
        import pygame
        w, h = self.size(text)
        return pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)


class _DrawRecorder(object):
    """Proxy `pygame.draw`: CATAT setiap panggilan, tidak menggambar."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def proxy(*a, **k):
            self.calls.append([name, _jsonable(a)])
        return proxy


def _rec_surface(w, h):
    """pygame.Surface sungguhan (blit teks sungguhan terjadi di atasnya),
    dengan .blit dicatat lewat subclass."""
    import pygame

    class RecSurface(pygame.Surface):
        def __init__(self):
            super().__init__((w, h), pygame.SRCALPHA)
            self.blit_ops = []

        def blit(self, src, dest, *a, **k):
            self.blit_ops.append([[int(dest[0]), int(dest[1])],
                                  int(src.get_width()),
                                  int(src.get_height())])
            return super().blit(src, dest, *a, **k)

    return RecSurface()


def geom_summary(draw_calls, blit_ops):
    """Ringkasan geometri dari jejak menggambar - bentuknya sama dengan yang
    dibangun MobileTouchParityTest.gd dari ops CanvasItem produksinya."""
    out = {"panels": [], "border_rects": [], "blits": blit_ops,
           "guides": [], "poly": {"color": None, "closed": None,
                                  "width": None, "count": 0, "head": []},
           "segments": [], "dots": []}
    for (name, args) in draw_calls:
        a = list(args)
        if name == "rect":
            out["border_rects"].append({"rect": a[2], "color": a[1],
                                        "width": a[3] if len(a) > 3 else 0})
        elif name == "line":
            seg = {"a": a[2][:2], "b": a[3][:2], "color": a[1],
                   "width": a[4] if len(a) > 4 else 1}
            out["segments"].append(seg)
            out["guides"].append(seg)
        elif name == "lines":
            pts = a[3]
            out["poly"] = {"color": a[1], "closed": a[2],
                           "width": a[4] if len(a) > 4 else 1,
                           "count": len(pts),
                           "head": [[round(float(p[0]), 4),
                                     float(p[1])] for p in pts[:3]]}
        elif name == "circle":
            out["dots"].append({"center": [a[2][0], a[2][1]], "radius": a[3],
                                "color": a[1],
                                "width": a[4] if len(a) > 4 else 0})
    return out


def _trace_mode(ov, debug_mod, key, mode, clock, game):
    import pygame
    real_draw = pygame.draw
    surf = _rec_surface(1280, 720)
    rec = _DrawRecorder()
    pygame.draw = rec
    try:
        ov.mode = mode
        if key == "mini":
            ov._draw_mini(surf, clock)
        elif key == "full":
            ov._draw_full(surf, clock, game)
        elif key == "graph":
            ov._draw_graph(surf)
        else:
            ov._draw_touch(surf, FakeTouch(TOUCH_POINTS))
    finally:
        pygame.draw = real_draw
    t = geom_summary(rec.calls, list(surf.blit_ops))
    # [x, y, w, h] pipih -> dibanding langsung dengan Rect2 sisi Godot
    t["panels"] = [[b[0][0], b[0][1], b[1], b[2]] for b in surf.blit_ops[:1]]
    return t


def build_debug_oracle(debug_mod, perf_mod, plat_mod, touch_mod):
    out = {}
    quality = perf_mod.Quality
    saved = (quality.level, quality.cheap_alpha, quality.sprite_cache)
    quality.level, quality.cheap_alpha, quality.sprite_cache = QUALITY
    try:
        # ── kontrol mode ──
        ov = debug_mod.DebugOverlay(
            lambda size, weight=None: OracleFont(size))
        ov.log_to_console = False
        cycle = []
        for _ in range(5):
            m = ov.toggle()
            cycle.append({"mode": int(m),
                          "name": str(debug_mod._MODE_NAMES[int(m)])})
        out["toggle_cycle"] = cycle
        wrap = []
        for m in (-1, 0, 1, 2, 3, 4, 5, 7):
            ov.set_mode(m)
            wrap.append({"in": m, "mode": int(ov.mode),
                         "enabled": bool(ov.enabled)})
        out["set_mode_wrap"] = wrap

        # ── SATU overlay untuk riwayat + baris + geometri (sumber angka
        #    yang sama, jadi replay Godot membandingkan apel dengan apel) ──
        game = FakeGame(*[[0] * n for n in ENTITIES])
        hist = debug_mod.DebugOverlay(
            lambda size, weight=None: OracleFont(size))
        hist.log_to_console = False
        for (fps, ms, n) in FEED:
            for _ in range(n):
                hist.update(FakeClock(fps, ms), game)
        check(len(hist.frame_ms_history) < 180,
              "oracle: feed awal belum menyentuh pemangkasan")
        out["history"] = {"fed": sum(n for (_, _, n) in FEED),
                          "frames": int(hist._frames),
                          "fps_len": len(hist.fps_history),
                          "ms_len": len(hist.frame_ms_history)}
        for _ in range(3):
            hist.update(FakeClock(*SLOW_FEED), game)
        check(len(hist.frame_ms_history) == 180,
              "oracle: riwayat terpotong ke maxlen 180")
        out["history_after_slow"] = {
            "frames": int(hist._frames),
            "fps_len": len(hist.fps_history),
            "ms_len": len(hist.frame_ms_history),
            "peak": round(float(hist._peak_ms), 6),
            "slow": int(hist._slow_frames),
            "fps_avg": round(float(hist._avg(hist.fps_history)), 6),
            "ms_avg": round(float(hist._avg(hist.frame_ms_history)), 6)}

        ms_avg = float(hist._avg(hist.frame_ms_history))
        no_tie(SLOW_FEED[0], 0, "fps panel (baris 1)")
        no_tie(ms_avg, 1, "rata-rata frame-ms (baris 1)")
        no_tie(float(hist._peak_ms), 1, "peak ms")
        no_tie(SLOW_FEED[1], 1, "frame_ms log")
        lines = hist._build_lines(FakeClock(*SLOW_FEED), game)
        # CATATAN: TIDAK semua baris stabil antar-proses — `konversi sprite`,
        # `font new/reuse`, `mem …`, `jalur cepat alpha` membaca counter modul
        # pygame yang ikut berubah oleh import. Yang disimpan ke fixture
        # hanyalah subset yang direproduksi Godot (lihat `godot_lines`) +
        # JUMLAH barisnya, jadi fixture tetap byte-deterministik.
        out["line_count"] = len(lines)
        out["line_tags"] = [str(t).split(" ")[0] for (t, _c) in lines]
        out["lines_state"] = {
            "fps": float(SLOW_FEED[0]),
            "frame_avg": round(ms_avg, 6),
            "peak": round(float(hist._peak_ms), 6),
            "phases": {"event": 0.0, "update": 0.0, "draw": 0.0,
                       "flip": 0.0},
            "entities": debug_mod.DebugOverlay._entity_counts(game),
            "quality": quality.level,
            "cheap_alpha": bool(quality.cheap_alpha),
            "sprite_cache": bool(quality.sprite_cache),
            "slow_frames": int(hist._slow_frames),
            "frames": int(hist._frames),
        }
        out["color_for_fps"] = [[v, [int(c) for c in debug_mod
                                     ._color_for_fps(v)]]
                                for v in (60.0, 50.0, 49.9, 30.0, 29.9, 0.0)]
        hist.extra = {"sim": "4x/frame  mentok 0"}
        extra_lines = hist._build_lines(FakeClock(*SLOW_FEED), game)
        hist.extra = {}
        out["extra_line"] = [[str(t), [int(c) for c in col]]
                             for (t, col) in extra_lines[len(lines):]]

        # ── baris [PERF] dibajak dari stdout ──
        log = debug_mod.DebugOverlay(
            lambda size, weight=None: OracleFont(size))
        log.log_interval = 0.0
        no_tie(LOG_FRAME[0], 1, "fps baris [PERF]")
        no_tie(LOG_FRAME[1], 1, "frame baris [PERF]")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            log.update(FakeClock(*LOG_FRAME), game)
        got = [l for l in buf.getvalue().splitlines()
               if l.startswith("[PERF]")]
        check(len(got) == 1, "oracle: tepat satu baris [PERF] per update "
                             "dengan interval 0 - dapat %d" % len(got))
        out["perf_log"] = {"text": re.sub(r"mem=\S+", "mem=MEM", got[0]),
                           "fps": LOG_FRAME[0],
                           "frame_avg": round(float(log._avg(
                               log.frame_ms_history)), 6),
                           "quality": quality.level,
                           "entities": debug_mod.DebugOverlay
                           ._entity_counts(game),
                           "memory": "MEM"}
        log.log_interval = 10.0 ** 9
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            for _ in range(5):
                log.update(FakeClock(*LOG_FRAME), game)
        out["perf_log_throttled"] = not any(
            l.startswith("[PERF]") for l in buf2.getvalue().splitlines())
        check(out["perf_log_throttled"], "oracle: throttle log bekerja")

        # ── GEOMETRI: jejak menggambar SUNGGUHAN pada overlay yang sama ──
        safe = plat_mod.get_safe_area()
        out["safe_area"] = [safe.left, safe.top, safe.width, safe.height]
        shared = select_godot_lines(lines)
        out["godot_lines"] = shared
        shared_pairs = [(entry["text"], tuple(entry["color"]))
                        for entry in shared if "text" in entry]
        clk = FakeClock(SLOW_FEED[0], SLOW_FEED[1])
        hist._lines_cache = shared_pairs
        hist._lines_at = 10.0 ** 15      # cache jangan disegar ulang
        traces = {}
        for (key, mode) in (("mini", debug_mod.MODE_MINI),
                            ("full", debug_mod.MODE_FULL),
                            ("graph", debug_mod.MODE_GRAPH),
                            ("touch", debug_mod.MODE_FULL)):
            traces[key] = _trace_mode(hist, debug_mod, key, mode, clk, game)
        out["geometry"] = traces
        out["replay"] = {
            "feed": FEED, "final": FINAL, "slow_feed": SLOW_FEED,
            "log_feed": LOG_FRAME, "entities": ENTITIES,
            "safe": out["safe_area"],
            "fps": float(SLOW_FEED[0]),
            "ms_avg": round(ms_avg, 6),
            "fps_avg": round(float(hist._avg(hist.fps_history)), 6),
            "peak": round(float(hist._peak_ms), 6),
            "mini_text": "%3.0f FPS  %4.1fms" % (SLOW_FEED[0], ms_avg),
            "lines_state": dict(out["lines_state"]),
            "graph_history": [round(float(v), 6)
                              for v in list(hist.frame_ms_history)[-240:]],
            "touch_points": TOUCH_POINTS,
            "shared_line_indices": [e["i"] for e in shared],
            "full_text_at": [traces["full"]["panels"][0][0] + 8,
                             traces["full"]["panels"][0][1] + 6],
            "full_line_pitch": 19,
            "font_sizes": {"mini": 20, "full": 16},
        }
        out["throttle_ms"] = float(debug_mod.DebugOverlay.JEDA_SEGAR_MS)
        # `__init__(self, get_font, frame_timer=None, log_interval=5.0)`
        out["log_interval"] = float(
            debug_mod.DebugOverlay.__init__.__defaults__[-1])
        out["history_max"] = int(hist.fps_history.maxlen)
        out["entity_counts"] = debug_mod.DebugOverlay._entity_counts(game)
        out["touch_manager_points"] = _gesture_points_oracle(touch_mod)
    finally:
        (quality.level, quality.cheap_alpha,
         quality.sprite_cache) = saved
    return out


def _gesture_points_oracle(touch_mod):
    """Titik aktif yang dilihat `_draw_touch` setelah 2 jari menekan lalu
    `update()` pada 460 ms (long-press sudah menyala, `moved` masih palsu)."""
    clock = FakeTime()
    real_time = touch_mod.time
    touch_mod.time = clock
    try:
        m = touch_mod.TouchManager(use_finger_events=False)
        m._down(0, (200, 300))
        clock.now_ms = 40.0
        m._down(1, (900, 300))
        clock.now_ms = 460.0
        m.update()
        return {"n": len(m.points),
                "items": [[int(k), [round(float(v.pos[0]), 4),
                                    round(float(v.pos[1]), 4)],
                           int(v.moved), int(v.long_fired),
                           round(float(v.velocity), 6),
                           round(float(v.scroll_accum), 6)]
                          for k, v in m.points.items()]}
    finally:
        touch_mod.time = real_time


# baris yang TIDAK direproduksi Godot (sumber datanya milik pygame)
SKIP_PREFIX = ("konversi sprite:", "jalur cepat alpha",
               "memori: cache", "font new ", "ALPHA BLIT", "DRAW(", "  ...:")


def select_godot_lines(lines):
    """Sub集 baris pygame yang dipunyai Godot + indeks aslinya. Baris nilai
    mesin (mem/BUILD/perangkat) hanya dikunci FORMATnya lewat regex."""
    keep = []
    for i, (text, color) in enumerate(lines):
        if text.startswith(SKIP_PREFIX):
            continue
        if text.endswith("ms") and "FPS" in text and " | " not in text:
            tag = "perf"
        elif text.startswith("event "):
            tag = "phases"
        elif text.startswith("entity "):
            tag = "entity"
        elif text.startswith("suara: "):
            tag = "audio"
        elif text.startswith("mem "):
            tag = "memory"
        elif text.startswith("BUILD "):
            tag = "build"
        elif " | Android " in text:
            tag = "device"
        elif "mentok " in text:
            tag = "extra"
        else:
            continue
        entry = {"i": i, "tag": tag, "color": color}
        if tag in ("memory", "build", "device"):
            entry["format"] = True
            entry["regex"] = {"memory": r"^mem (\d+MB|n/a)$",
                              "build": r"^BUILD \S+",
                              "device": r"^.+ \| Android .+ \(API .+\) \| "
                                         r"Godot .+ / .+$"}[tag]
        else:
            entry["text"] = text
        keep.append(entry)
    return keep


# ══════════════════════════════════════════════════════════
#  3. PIN STATIK
# ══════════════════════════════════════════════════════════

TOUCH_THRESHOLDS = ["TAP_SLOP", "LONG_PRESS_MS", "DOUBLE_TAP_MS",
                    "SCROLL_STEP", "FLING_FRICTION", "FLING_MIN_SPEED"]


def static_checks():
    want = {}
    # ── ambang gesture: satu sumber nama di pygame, nama sama di Godot ──
    for name in TOUCH_THRESHOLDS:
        m = pin(r"^%s = ([0-9.]+)" % name, "touch.py", "ambang %s" % name,
                re.M)
        val = float(m.group(1))
        want[name] = int(val) if val == int(val) else val
        gd = re.search(r"^const %s := ([0-9.]+)" % name.upper(),
                       read("TouchGestures.gd"), re.M)
        check(gd is not None, "TouchGestures.gd tidak punya const %s"
              % name.upper())
        got = float(gd.group(1))
        check(abs(got - val) < 1e-12,
              "%s: pygame %r != Godot %r" % (name, val, got))
    check((want["TAP_SLOP"], want["LONG_PRESS_MS"], want["DOUBLE_TAP_MS"],
           want["SCROLL_STEP"]) == (14, 450, 280, 42),
          "ambang gesture = 14/450/280/42 (bank angka yang sama dengan "
          "gdext/mystic_mobile)")

    # ── literal tanpa nama di pygame -> konstanta bernama di Godot ──
    for (py, gd, what) in (
        (r"\* 0\.6 \+ dy \* 0\.4", r"VELOCITY_KEEP := 0\.6",
         "pelumatan kecepatan 0,6 + 0,4"),
        (r"self\.fling_velocity \*= FLING_FRICTION",
         r"return velocity \* FLING_FRICTION",
         "gesekan inersia memakai FLING_FRICTION"),
        (r"abs\(pos\[0\] - self\._last_tap_pos\[0\]\) < 40",
         r"DOUBLE_TAP_RADIUS_PX := 40", "radius double-tap 40 px"),
        (r"abs\(tp\.velocity\) > 4", r"FLING_ARM_SPEED := 4",
         "ambang lengan fling 4 px/frame"),
        (r"SCROLL_STEP \* 0\.35", r"FLING_DIVISOR := 0\.35",
         "pembagi langkah fling 0,35"),
        (r"min\(steps, 3\)", r"FLING_MAX_STEPS := 3",
         "batas 3 notch per fling"),
        (r"\* 1000\.0 >= LONG_PRESS_MS",
         r"return held_ms >= float\(LONG_PRESS_MS\)",
         "long-press >= ambang (bukan >)"),
        (r"while abs\(tp\.scroll_accum\) >= SCROLL_STEP:",
         r"while absf\(accum\) >= float\(SCROLL_STEP\):",
         "notch scroll setiap 42 px akumulator"),
        (r"tp\.scroll_accum -= SCROLL_STEP \* \(1 if tp\.scroll_accum > 0",
         r"var sub := float\(SCROLL_STEP\) \* \(1\.0 if accum > 0\.0 "
         r"else -1\.0\)",
         "sisa akumulator notch dikurangi 42, bukan dinolkan"),
        (r"\(now - self\._last_tap_time\) \* 1000\.0 < DOUBLE_TAP_MS",
         r"return dt_ms < float\(DOUBLE_TAP_MS\)",
         "double-tap < 280 ms (detik vs ms)"),
    ):
        pin(py, "touch.py", what, 0)
        pin(gd, "TouchGestures.gd", what, 0)

    # ── pemetaan aksi -> tombol klik (dispatch_to_game) ──
    pin(r"if k == \"tap\":\n\s*game\.handle_click\(action\.pos, 1\)\n\s*"
        r"return True\n\s*if k == \"long_press\":\n\s*"
        r"game\.handle_click\(action\.pos, 3\)\n\s*return True",
        "touch.py", "tap->klik kiri, long_press->klik kanan", 0)
    pin(r"if k == \"scroll\":\n\s*game\.handle_click\(action\.pos, "
        r"4 if action\.value < 0 else 5\)",
        "touch.py", "scroll -> tombol 4/5", 0)
    gd = read("TouchGestures.gd")
    for frag in (r"if kind == KIND_TAP:\n\s*return 1",
                 r"if kind == KIND_LONG_PRESS:\n\s*return 3",
                 r"return 4 if value < 0 else 5"):
        check(re.search(frag, gd), "TouchGestures.dispatch_button: %s "
              "tidak ada" % frag[:40])

    # ── debug.py: palet, mode, geometri, format ──
    pins = [
        (r"^BG = \(0, 0, 0, 170\)", r"const BG: Array = \[0, 0, 0, 170\]",
         "BG overlay"),
        (r"^OK = \(120, 235, 140\)", r"const OK: Array = \[120, 235, 140\]",
         "warna OK"),
        (r"^WARN = \(255, 205, 90\)", r"const WARN: Array = \[255, 205, 90\]",
         "warna WARN"),
        (r"^BAD = \(255, 110, 110\)", r"const BAD: Array = \[255, 110, 110\]",
         "warna BAD"),
        (r"^TXT = \(225, 228, 240\)", r"const TXT: Array = \[225, 228, 240\]",
         "warna TXT"),
        (r"MODE_OFF, MODE_MINI, MODE_FULL, MODE_GRAPH = 0, 1, 2, 3",
         r"const MODE_GRAPH := 3", "nomor mode 0..3"),
        (r"_MODE_NAMES = \[\"off\", \"mini\", \"full\", \"graph\"\]",
         r'const MODE_NAMES := \["off", "mini", "full", "graph"\]',
         "nama mode"),
        (r"print\(\"\[DEBUG\] overlay = %s\" % _MODE_NAMES\[self\.mode\]\)",
         r"print\(\"\[DEBUG\] overlay = %s\" % str\(MODE_NAMES\[mode\]\)\)",
         "pesan toggle [DEBUG]"),
        (r"self\.mode = \(self\.mode \+ 1\) % 4", r"return \(m \+ 1\) % 4",
         "siklus toggle (mode+1)%4"),
        (r"self\.mode = mode % 4", r"return posmod\(m, 4\)",
         "wrap set_mode %4"),
        (r"return self\.mode != MODE_OFF", r"return m != MODE_OFF",
         "enabled = mode != OFF"),
        (r"self\.fps_history = deque\(maxlen=180\)",
         r"const HISTORY_MAX := 180", "riwayat 180 sampel"),
        (r"if frame_ms > 33:\n\s*self\._slow_frames \+= 1",
         r"const SLOW_MS := 33\.0", "ambang frame lambat 33 ms"),
        (r"if frame_ms > self\._peak_ms:", r"if frame_ms > _peak_ms:",
         "peak = max(frame_ms)"),
        (r"if fps >= 50:\n\s*return OK\n\s*if fps >= 30:\n\s*return WARN\n"
         r"\s*return BAD",
         r"if fps >= 50\.0:\n\s*return OK\n\s*if fps >= 30\.0:\n\s*"
         r"return WARN\n\s*return BAD", "tangga warna fps 50/30"),
        (r"\"%3\.0f FPS  %4\.1fms\" % \(fps, self\._avg\(self\.frame_ms_"
         r"history\)\)",
         r"\"%3\.0f FPS  %4\.1fms\" % \[fps, avg_frame_ms\]",
         "teks mini = fps SEKETIKA + rata-rata ms"),
        (r"surf = font\.render\(text, True, _color_for_fps\(fps\)\)",
         r"\"color\": color_for_fps\(fps\)",
         "teks mini diwarnai tangga fps"),
        (r"self\._panel\(surface, x - 4, y - 3, surf\.get_width\(\) \+ 12,\s*"
         r"surf\.get_height\(\) \+ 8\)\n\s*surface\.blit\(surf, \(x \+ 2, "
         r"y \+ 1\)\)",
         r"const MINI_TEXT_INNER_OFF := Vector2\(2, 1\)",
         "geometri panel mini (-4,-3 / +12,+8 / teks +2,+1)"),
        (r"w = max\(font\.size\(t\)\[0\] for t, _ in lines\) \+ 18\n\s*"
         r"h = len\(lines\) \* 19 \+ 12\n\s*x, y = safe\.left \+ 4, "
         r"safe\.top \+ 4",
         r"const FULL_PAD_W := 18\.0",
         "geometri panel lengkap (+18 / 19 per baris / +12)"),
        (r"buf\.fill\(\(8, 8, 14\)\)\n\s*pygame\.draw\.rect\(buf, "
         r"\(90, 90, 120\), buf\.get_rect\(\), 1\)\n\s*for idx, "
         r"\(text, color\) in enumerate\(lines\):\n\s*buf\.blit\(font\.render"
         r"\(text, True, color\), \(8, 6 \+ idx \* 19\)\)",
         r"const FULL_TEXT_AT := Vector2\(8, 6\)",
         "buffer opaque (8,8,14) + tepi (90,90,120) + teks (8, 6+19i)"),
        (r"font = self\._get_font\(16, \"body\"\)",
         r"const FULL_FONT := 16", "ukuran font panel lengkap 16"),
        (r"font = self\._get_font\(20, \"body_bold\"\)",
         r"const MINI_FONT := 20", "ukuran font mini 20 body_bold"),
        (r"w, h = 240, 70\n\s*x = safe\.left \+ 4\n\s*y = safe\.top \+ 145",
         r"const GRAPH_SIZE := Vector2\(240, 70\)",
         "grafik 240x70 di (safe.left+4, safe.top+145)"),
        (r"y = safe\.top \+ 145", r"const GRAPH_AT := Vector2\(4, 145\)",
         "anchor grafik"),
        (r"for ms, col in \(\(16\.7, \(70, 120, 70\)\), \(33\.3, "
         r"\(120, 80, 60\)\)\):\n\s*gy = y \+ h - int\(min\(ms, 50\) / 50\.0 "
         r"\* h\)\n\s*pygame\.draw\.line\(surface, col, \(x, gy\), "
         r"\(x \+ w, gy\), 1\)",
         r"const GRAPH_MS_MAX := 50\.0",
         "garis panduan 16,7/33,3 ms pada skala tetap 50 ms"),
        (r"for i, ms in enumerate\(data\):\n\s*gy = y \+ h - int\(min\(ms, "
         r"50\) / 50\.0 \* h\)",
         r"return int\(at_y\) \+ int\(h\) - int\(minf\(ms, GRAPH_MS_MAX\) / "
         r"GRAPH_MS_MAX \* h\)",
         "rumus y titik data grafik (int, bukan bulat)"),
        (r"data = list\(self\.frame_ms_history\)\[-w:\]",
         r"const GRAPH_WINDOW := 240", "jendela grafik 240 sampel"),
        (r"step = w / max\(1, len\(data\) - 1\)",
         r"var step := size\.x / float\(maxi\(1, data\.size\(\) - 1\)\)",
         "jarak antar titik grafik"),
        (r"pygame\.draw\.lines\(surface, \(150, 220, 255\), False, pts, 1\)",
         r"const GRAPH_LINE: Array = \[150, 220, 255\]",
         "poly-line grafik (150,220,255) lebar 1"),
        (r"if len\(data\) > 1:", r"if pts\.size\(\) > 1:",
         "grafik butuh >= 2 sampel"),
        (r"pygame\.draw\.circle\(surface, \(90, 220, 255\),\s*"
         r"\(int\(tp\.pos\[0\]\), int\(tp\.pos\[1\]\)\), 26, 2\)\n\s*"
         r"pygame\.draw\.circle\(surface, \(255, 255, 255\),\s*"
         r"\(int\(tp\.pos\[0\]\), int\(tp\.pos\[1\]\)\), 3\)",
         r"const TOUCH_RING_R := 26\.0",
         "cincin jari r=26 tebal 2 + titik putih r=3"),
        (r"for tp in getattr\(touch, \"points\", \{\}\)\.values\(\):",
         r"for tid in \(pts as Dictionary\):",
         "titik jari dibaca dari TouchManager.points (dict aktif)"),
        (r"self\._panel\(surface, x, y, w, h\)",
         r"const PANEL_BORDER: Array = \[90, 90, 120\]",
         "pinggiran panel _panel"),
        (r"panel = pygame\.Surface\(\(w, h\), pygame\.SRCALPHA\)\n\s*"
         r"panel\.fill\(BG\)\n\s*pygame\.draw\.rect\(panel, "
         r"\(90, 90, 120\), panel\.get_rect\(\), 1\)\n\s*"
         r"surface\.blit\(panel, \(x, y\)\)",
         r"\"bg\": BG\.duplicate\(\)",
         "cabang murah _panel: Surface SRCALPHA + BG + tepi + blit"),
        (r"else:\n\s*pygame\.draw\.rect\(surface, \(8, 8, 14\), "
         r"\(x, y, w, h\)\)",
         r"const PANEL_FILL: Array = \[8, 8, 14\]",
         "cabang mahal _panel = panel opaque (8,8,14)"),
        (r"def draw\(self, surface, clock, game=None, touch=None\):",
         None, "signature draw(surface, clock, game, touch)"),
        (r"else:\n\s*self\._draw_full\(surface, clock, game\)\n\s*"
         r"self\._draw_graph\(surface\)",
         r"if m == MODE_GRAPH:\n\s*ops\.append_all\(graph_ops\(safe, s\)\)",
         "mode GRAFIK = LENGKAP + grafik"),
        (r"def draw\(self, surface, clock, game=None, touch=None\):\n\s*"
         r"if self\.mode == MODE_OFF:\n\s*return",
         r"if not is_enabled\(m\):\n\s*return ops",
         "mode OFF = tidak menggambar apa pun"),
        (r"if touch is not None:\n\s*self\._draw_touch\(surface, touch\)",
         r"ops\.append_all\(touch_ops\(s\.get\(\"points\", \[\]\) as "
         r"Array\)\)",
         "titik jari digambar SETELAH panel, di semua mode non-OFF"),
        (r"self\._lines_cache = self\._build_lines\(clock, game\)\n\s*"
         r"self\._lines_at = sekarang",
         r"_lines_cache = build_lines\(s\)", "cache teks 250 ms"),
        (r"JEDA_SEGAR_MS = 250", r"const JEDA_SEGAR_MS := 250\.0",
         "seegar teks 250 ms"),
        (r"log_interval=5\.0", r"const LOG_INTERVAL_SEC := 5\.0",
         "jeda log 5 dtk"),
        (r"if self\.log_to_console and now - self\._last_log >= "
         r"self\.log_interval:",
         r"if log_to_console and now - _last_log_ms >= log_interval \* 1000\.0",
         "log console dithrottle log_interval"),
        (r"\"%\3\.0f FPS   frame %4\.1f ms   peak %4\.1f ms\"", None,
         "placeholder"),
    ]
    for (py, gd, what) in pins[:-1]:
        pin(py, "debug.py", what, re.M)
        if gd:
            pin(gd, "DebugOverlay.gd", what, re.M)

    # format baris: literal pygame harus ada VERBATIM di Godot
    body = read("debug.py")
    start = body.index("def _build_lines")
    body = body[start:body.index("def _render_lines")]
    q = chr(34)          # tanda kutip, tanpa perlu kabur
    fmt = re.findall(q + r'[^' + q + r']*%[0-9.]*[sdf][^' + q + r']*' + q,
                     body)
    joined = read("DebugOverlay.gd")
    shared_fmt = [f for f in fmt if ("FPS" in f or "entity" in f
                                     or "event " in f or "suara" in f
                                     or "PERF" in f)]
    check(len(shared_fmt) >= 3, "oracle: format baris debug.py tidak ketemu "
                                "(dapat %d)" % len(shared_fmt))
    for f in shared_fmt:
        check(f in joined or _unquote(f) in joined,
              "format baris %s tidak ada di DebugOverlay.gd" % f[:48])
    out = {"perf": want}
    out["formats"] = [_unquote(f) for f in shared_fmt]

    # ── baris audio: format berasal dari mobile/combat_audio.py ──
    ring = read("combat_audio.py")
    if ring:
        m = re.search(r"\(\"(suara: [^\"]+)\"", ring)
        check(m, "combat_audio.ringkas() mengembalikan satu string")
        check(m.group(1) in joined,
              "format baris suara %r harus sama persis di Godot" % m.group(1))
        out["audio_format"] = m.group(1)

    # ── safe area + getar ──
    m = pin(r"^_SAFE_MARGIN_LOGICAL = ([0-9]+)", "platform_utils.py",
            "margin safe area", re.M)
    check(int(m.group(1)) == 28, "margin safe area pygame = 28 px")
    pin(r"const SAFE_MARGIN_LOGICAL := 28\.0", "MobileLayout.gd",
        "margin 28 px ikut dipindah ke Godot", re.M)
    lay = read("MobileLayout.gd")
    pin(r"return pygame\.Rect\(m, 10, LOGICAL_WIDTH - 2 \* m, "
        r"LOGICAL_HEIGHT - 20\)", "platform_utils.py",
        "rumus rect aman mode sentuh", 0)
    pin(r"SAFE_TOP := 10\.0", "MobileLayout.gd", "safe top 10", 0)
    pin(r"SAFE_BOTTOM := 10\.0", "MobileLayout.gd", "safe bottom 10", 0)
    pin(r"DESIGN_SIZE\.x - SAFE_MARGIN_LOGICAL \* 2\.0", "MobileLayout.gd",
        "lebar aman = 1280 - 2*28", 0)
    pin(r"DESIGN_SIZE\.y - SAFE_TOP - SAFE_BOTTOM", "MobileLayout.gd",
        "tinggi aman = 720 - 10 - 10", 0)
    pin(r"if not TOUCH_MODE:\n\s*return pygame\.Rect\(0, 0, LOGICAL_WIDTH, "
        r"LOGICAL_HEIGHT\)", "platform_utils.py",
        "di luar mode sentuh: rect penuh", 0)
    pin(r"if not touch_mode\(\):\n\s*return Rect2\(Vector2\.ZERO, "
        r"DESIGN_SIZE\)", "MobileLayout.gd",
        "Godot: di luar mode sentuh juga rect penuh", 0)
    pin(r"def vibrate\(ms=25\)", "platform_utils.py", "vibrate(ms=25)", 0)
    check("func vibrate(ms: int) -> bool:" in lay
          and "Input.vibrate_handheld" in lay,
          "MobileLayout.vibrate memakai Input.vibrate_handheld (Godot 4)")

    # ── rantai long-press: hud.py -> main.py -> SidePanel/TouchHUD ──
    pin(r"^TAP_SLOP = 14 .*\n^LONG_PRESS_MS = 450", "touch.py",
        "tabel ambang di kepala modul (14 px / 450 ms)", re.M)
    for (frag, name, what) in (
        (r"^MIN_TAP = 80", "hud.py", "tap minimum 80 px"),
        (r"self\.hit_rect = self\.rect\.inflate\(24, 24\)", "hud.py",
         "hit_rect = rect.inflate(24)"),
        (r"def contains\(self, pos\):\n\s*return self\.visible and self\."
         r"hit_rect\.collidepoint\(pos\)", "hud.py",
         "contains = visible + hit_rect.collidepoint"),
        (r"for btn in reversed\(list\(self\.buttons\.values\(\)\)\):",
         "hud.py", "hit_test menelusuri tombol terbalik (paling atas dulu)"),
    ):
        pin(frag, name, what, re.M)
    hud_gd = read("TouchHUD.gd")
    check("func contains_button(action: String, pos: Vector2) -> bool:"
          in hud_gd
          and re.search(r"return bool\(d\[\"visible\"\]\) and "
                        r"\(d\[\"hit\"\] as Rect2\)\.has_point\(pos\)",
                        hud_gd),
          "TouchHUD.contains_button = visible + hit_rect (padanan "
          "TouchButton.contains)")
    sp = read("SidePanel.gd")
    for (frag, what) in (
        (r"func rail_active\(\) -> bool:", "SidePanel.rail_active()"),
        (r"func rail_pause_contains\(pos: Vector2\) -> bool:",
         "SidePanel.rail_pause_contains(pos)"),
        (r"MobileLayout\.vibrate\(15\)", "getar 15 ms saat rail menangkap"),
    ):
        check(re.search(frag, sp, re.M), "%s tidak ada di SidePanel.gd" % what)
    main_py = read("main.py")
    for (frag, what) in (
        (r"_pb = side\.buttons\.get\(\"pause\"\) if side\.aktif else None",
         "tahan-jeda hanya dicek kalau rail aktif"),
        (r"if \(\(_pb is not None and _pb\.contains\(action\.pos\)\)\n"
         r"\s*or hud\.buttons\[\"pause\"\]\.contains\(action\.pos\)\):",
         "targets tahan-jeda = rail ATAU tombol HUD"),
        (r"if action\.kind == \"long_press\" and current_state == "
         r"STATE_GAME:", "long-press debug hanya di dalam match"),
        (r"debug\.toggle\(\)\n\s*plat\.vibrate\(30\)\n\s*continue",
         "rantai: toggle overlay -> getar -> aksi tidak diteruskan"),
        (r"plat\.vibrate\(30\)", "getar 30 ms pada tahan-jeda"),
        (r"if hit:\n\s*plat\.vibrate\(15\)",
         "getar 15 ms saat sentuhan ditangkap panel"),
        (r"if event\.key == pygame\.K_F8:\n\s*debug\.toggle\(\)",
         "F8 = DebugOverlay.toggle"),
    ):
        pin(frag, "main.py", what, re.M)

    # ── integrasi Godot: mesin gesture benar-benar dipakai Main ──
    for (frag, what) in (
        (r"TouchGestures\.gd", "Main memuat mesin gesture"),
        (r"_gestures\.feed_event\(event\)",
         "Main meneruskan SETIAP event ke mesin gesture lewat _input"),
        (r"_gestures\.update\(\)",
         "Main memanggil update() tiap frame (long-press + fling)"),
        (r"_dispatch_gesture\(action as Dictionary\)",
         "Main mendispatch antrean collect()"),
        (r"_press_claim\[TouchGestures\.touch_id_of\(event\)\] = true",
         "Main mencatat klaim press per jari"),
        (r"if kind == TouchGestures\.KIND_RELEASE:",
         "release melepas klaim sebelum dispatch"),
        (r"var claimed := bool\(_press_claim\.get\(tid, false\)\)",
         "gerbang klaim dibaca sebelum tap/long_press"),
        (r"if _pause_button_holds\(pos\):\n\s*toggle_debug_overlay\(\)",
         "tahan-jeda MENGALAHKAN gerbang klaim (paritas main.py:404-413)"),
        (r"MobileLayout\.vibrate\(30\)",
         "tahan tombol jeda = getar 30 ms (padanan main.py:412)"),
        (r"toggle_debug_overlay\(\)",
         "tahan tombol jeda mengsiklus overlay debug"),
        (r"keycode == KEY_F8", "F8 ditangani Main"),
        (r"_debug_overlay\.bind_gestures\(_gestures\)",
         "overlay debug membaca titik jari dari mesin gesture"),
        (r"_debug_overlay\.note_event\(",
         "biaya fase 'event' diumpan ke baris fase overlay"),
    ):
        pin(frag, "Main.gd", what, re.M)
    main_gd = read("Main.gd")
    check("_unhandled_input" in main_gd, "Main tetap punya _unhandled_input")
    check(main_gd.count("set_input_as_handled") <= 2,
          "lapisan gesture TIDAK memakan event (hanya cabang yang sudah ada "
          "sebelumnya yang boleh menandai tertangani)")

    # ── HUD: tidak ada overlay tempelan lagi ──
    hud = read("HUD.gd")
    for gone in ("var _debug_overlay", "func _build_debug_overlay",
                 "func _refresh_debug_overlay", "add_to_group(\"debug\""):
        check(gone not in hud, "HUD.gd masih punya `%s` (overlay tempelan)"
              % gone)
    check("func toggle_debug_overlay() -> int:" in hud
          and "func debug_mode() -> int:" in hud,
          "HUD.toggle_debug_overlay/debug_mode mengembalikan mode (0..3)")

    # ── tes Godot harus memutar ulang fixture (anti 'tes kosong') ──
    test = read("MobileTouchParityTest.gd")
    for key in ("mobile_touch.json", "TouchGestures", "DebugOverlay",
                "scenarios", "toggle_cycle", "set_mode_wrap", "history",
                "geometry", "perf_log", "lines_state", "safe_area",
                "color_for_fps", "touch_manager_points", "dispatch_button"):
        check(key in test, "MobileTouchParityTest.gd tidak memakai %s" % key)
    return out


def _unquote(s):
    return s[1:-1].replace('\\"', '"').replace("\\n", "\n")


# ══════════════════════════════════════════════════════════
#  4. MAIN
# ══════════════════════════════════════════════════════════

def build_payload():
    from mobile import debug as debug_mod
    from mobile import perf as perf_mod
    from mobile import platform_utils as plat_mod
    from mobile import touch as touch_mod
    return {
        "_generated_by": "tools/test_godot_mobile_touch_parity.py",
        "_sumber": ["mobile/touch.py", "mobile/debug.py",
                    "mobile/platform_utils.py::get_safe_area", "main.py"],
        "font_metric_formula": "len(text) * size * 3 // 8",
        "touch": {"constants": {
            "tap_slop": touch_mod.TAP_SLOP,
            "long_press_ms": touch_mod.LONG_PRESS_MS,
            "double_tap_ms": touch_mod.DOUBLE_TAP_MS,
            "scroll_step": touch_mod.SCROLL_STEP,
            "fling_friction": touch_mod.FLING_FRICTION,
            "fling_min_speed": touch_mod.FLING_MIN_SPEED},
            "scenarios": [run_touch_scenario(touch_mod, n, st)
                          for (n, st) in TOUCH_SCENARIOS]},
        "debug": build_debug_oracle(debug_mod, perf_mod, plat_mod,
                                    touch_mod),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-fixture", action="store_true")
    args = ap.parse_args(argv)

    import pygame  # driver dummy; dipakai helper di atas
    pygame.display.init()
    try:
        pygame.display.set_mode((4, 4))   # Surface.convert() butuh display
    except Exception:
        pass
    payload = build_payload()
    pins = static_checks()
    payload["_pins"] = pins
    check(len(payload["debug"]["godot_lines"]) >= 7,
          "subset baris yang dipunyahi Godot bukan kosong (%d baris)"
          % len(payload["debug"]["godot_lines"]))

    text = json.dumps(payload, indent=1, sort_keys=True)
    if args.write_fixture:
        with open(FIXTURE, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("[mobile-touch] fixture ditulis: %s (%d byte, %d skenario "
              "gesture)" % (os.path.relpath(FIXTURE, ROOT), len(text),
                            len(payload["touch"]["scenarios"])))
    else:
        check(os.path.exists(FIXTURE),
              "fixture belum ada - jalankan --write-fixture dulu")
        with open(FIXTURE, "r", encoding="utf-8") as fh:
            old = json.load(fh)
        check(json.dumps(old, indent=1, sort_keys=True) == text,
              "fixture cocok dengan oracle terbaru (tidak ada drift)")
    print("[mobile-touch] %d cek oracle + pin lulus" % len(PASS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
