#!/usr/bin/env python3
"""test_system_perf_parity.py — oracle blok `performance.py` + `fps_counter.py`
di `_system.py` (sumber kebenaran pygame) untuk port Godot.

Kenapa tool sendiri (bukan seksi baru `test_godot_match_parity.py`): blok ini
tidak punya state pertandingan sama sekali — grid spasial, culling layar, dan
overlay FPS bisa dievaluasi sendiri, deterministik, dan murah. Fixture yang
dihasilkan (`godot/tests/fixtures/system_perf.json`) diputar ulang oleh
`godot/tests/SystemPerfParityTest.tscn` lewat KELAS PRODUKSINYA
(`SpatialGrid.gd`, `FrustumCuller.gd`, `FpsCounter.gd`, `CombatSystem.gd`).

Yang dijalankan adalah kode pygame SUNGGUHAN, bukan rumus yang disalin:
  * `SpatialGrid.query_range` + `update_spatial_grid` + `query_enemies_in_range`
    (`_system.py:52-200`) → keanggotaan DAN urutan entitas (urutan bucket:
    sel dijajak cx lalu cy, isi bucket = urutan insert) — urutan inilah yang
    dipakai `Minion._get_enemies`/`_find_target_smart` memilih `in_range[0]`;
  * `FrustumCuller.is_visible` (`_system.py:40-50`) → tabel batas layar;
  * `FPSCounter.update` (`_system.py:237-256`) → aturan riwayat (trim 120,
    jendela tampil 30, refresh tiap 10 frame);
  * `FPSCounter.draw` (`_system.py:258-398`) → jejak `pygame.draw.rect/line`
    dan `font.render` SUNGGUHAN (warna panel, garis panduan 60/30 fps, bar
    grafik, teks + ukuran + warnanya);
  * konstanta LETAK teks (`base_x`, `panel_surf.blit(fps_surf, (12, 6))`, ...)
    di-PIN dari TEKS SUMBER `_system.py` lewat regex; pola yang hilang bikin
    tool GAGAL, tidak diam-diam meloloskan perubahan.

CATATAN SHIM (temuan audit pada kode pygame, bukan kreasi Godot):
`_system.FPSCounter.draw()` memanggil `get_font(size)`, dan nama itu TIDAK PERNAH
masuk ke namespace `_system` (`from _core import *` dieksekusi saat `_core` masih
parsial karena import melingkar; `get_font` tinggal di `_render.py`). Jadi
menekan F8 di `main_desktop_legacy.py` = `NameError: name 'get_font' is not
defined`. Tool ini menambal `_system.get_font = _render.get_font` SEBELUM
memanggil `draw()` supaya jalur render-nya tetap bisa di-oracle; fakta
"tanpa shim = crash" disimpan ke fixture (`fps.py_draw_needs_shim`) supaya port
Godot tahu sisi pygame-nya tidak pernah benar-benar menampilkan panel ini.
`main.py` (entry HIDUP) memang tidak memakai kelas ini — overlay debug di sana
adalah `mobile/debug.py` dengan 4 mode + tombol FPS TouchHUD.

Jalankan:
  python3 tools/test_system_perf_parity.py                  # gate drift + kunci statis Godot
  python3 tools/test_system_perf_parity.py --write-fixture  # regenerasi fixture
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, ROOT)

FIXTURE = os.path.join(ROOT, "godot", "tests", "fixtures", "system_perf.json")
SYSTEM_PY = os.path.join(ROOT, "_system.py")
GODOT = os.path.join(ROOT, "godot")

PASS = []


def check(cond, msg):
    if not cond:
        raise AssertionError("GAGAL: %s" % msg)
    PASS.append(msg)


# ══════════════════════════════════════════════════════════
#  1. SpatialGrid + FrustumCuller (jalur HIDUP: _core.py/_entity.py)
# ══════════════════════════════════════════════════════════

class U(object):
    """Entitas palsu sewajar `Minion`/`Hero` sebatas yang dibaca `_system`."""

    def __init__(self, uid, x, y, team="red", alive=True):
        self.id = uid
        self.x = float(x)
        self.y = float(y)
        self.team = team
        self.alive = alive

    def __repr__(self):
        return self.id


def _rows(units):
    return [{"id": u.id, "x": u.x, "y": u.y, "team": u.team,
             "alive": bool(u.alive)} for u in units]


def _run_production(_system, minions, heroes, x, y, radius, team):
    """Jalur produksi pygame: grid modul + `update_spatial_grid` +
    `query_enemies_in_range` — persis `_core.py:2013` + `_entity.py:5639`."""
    _system.update_spatial_grid(minions, heroes)
    return _system.query_enemies_in_range(x, y, radius, team)


def _run_raw(grid_builder, units, x, y, radius, team=None):
    """Jalur struktur data: insert manual + `query_range` (team=None = tanpa
    filter, padanan `SpatialGrid.query_range(x, y, radius)`)."""
    grid = grid_builder()
    for e in units:
        grid.insert(e)
    if team is None:
        return grid.query_range(x, y, radius)
    return grid.query_range(x, y, radius, team)


def build_grid_scenarios(_system):
    scenarios = []

    def scenario(name, minions, heroes, queries):
        rows = []
        for q in queries:
            if q.get("raw"):
                found = _run_raw(
                    lambda: _system.SpatialGrid(cell_size=60),
                    q["raw"], q["x"], q["y"], q["radius"], q.get("team"))
            else:
                found = _run_production(_system, minions, heroes, q["x"],
                                        q["y"], q["radius"], q["team"])
            rows.append({"x": q["x"], "y": q["y"], "radius": q["radius"],
                         "team": q.get("team"),
                         "ids": [e.id for e in found], "count": len(found)})
        scenarios.append({"name": name,
                          "insert": {"minions": _rows(minions),
                                     "heroes": _rows(heroes)},
                          "queries": rows})

    # ── urutan bucket: sel dijajak cx lalu cy; isi sel = urutan insert ──
    mob = [U("m_0_0", 0, 0), U("m_0_1", 5, 65), U("m_1_0", 65, 5),
           U("m_2_2", 125, 125), U("m_1_1", 70, 70)]
    hero = [U("h_0_0", 10, 10, "blue"), U("h_1_0", 61, 12, "blue"),
            U("h_2_2", 130, 131, "blue")]
    scenario("bucket_order", mob, hero, [
        {"x": 60, "y": 60, "radius": 200, "team": "blue"},
        {"x": 60, "y": 60, "radius": 40, "team": "blue"},
        {"x": 0, "y": 0, "radius": 10, "team": "blue"},
    ])

    # ── minion didahulukan di atas hero + boss dalam sel yang sama
    #    (`update_spatial_grid(self.minions, spatial_heroes)`, boss di-append
    #    paling akhir: `_core.py:2010-2013`) ──
    scenario("insert_order_minion_lalu_hero",
             [U("m_a", 200, 200), U("m_b", 205, 210)],
             [U("h_a", 210, 205, "blue"), U("boss", 215, 215, "blue")],
             [{"x": 205, "y": 208, "radius": 500, "team": "red"}])

    # ── radius dibandingkan dengan jarak kuadrat `<= r2`: TEPAT di batas
    #    (3,4 dgn r=5; 60,0 dgn r=60) tetap masuk; 61,0 keluar ──
    scenario("radius_boundary_inclusive",
             [U("tepat_60", 60, 0), U("tepat_61", 61, 0), U("diagonal", 3, 4)],
             [], [{"x": 0, "y": 0, "radius": 60, "team": "blue"},
                  {"x": 0, "y": 0, "radius": 5, "team": "blue"}])

    # ── pra-saring kotak (bbox) tidak boleh mengubah hasil: titik di sudut
    #    bbox yang jatuh di luar lingkaran harus tetap tidak kembali ──
    scenario("bbox_vs_circle", [U("di_sudut", 59, 59), U("tengah", 0, 0)],
             [], [{"x": 0, "y": 0, "radius": 60, "team": "blue"}])

    # ── koordinat NEGATIF: `x // cell` = floor, BUKAN truncation ke nol.
    #    Ini jebakan yang bikin port naif (`int(x / cell)`) salah sel ──
    scenario("keys_negatif",
             [U("neg_1", -5, -5), U("neg_2", -61, -5), U("neg_3", -120, -120),
              U("neg_4", -0.5, 59.5, "blue")],
             [U("pos_1", 5, 5, "blue"), U("pos_2", -1, 1, "blue")],
             [{"x": -60, "y": -60, "radius": 120, "team": "blue"},
              {"x": 0, "y": 0, "radius": 10, "team": "blue"},
              {"x": 0, "y": 0, "radius": 1000, "team": "blue"}])

    # ── sekutu dibuang; tim KOSONG pun difilter (hero netral pygame punya
    #    `team == ""` dan satu sama lain dianggap sekutu) ──
    teams = [U("r0", 10, 10), U("b0", 20, 20, "blue"), U("n0", 30, 30, ""),
             U("n1", 40, 40, "")]
    scenario("sekutu_dibuang", teams, [],
             [{"x": 25, "y": 25, "radius": 100, "team": "blue"},
              {"x": 25, "y": 25, "radius": 100, "team": ""},
              {"x": 25, "y": 25, "radius": 100, "team": "red"}])

    # ── `.alive` dibaca SAAT KUERI (live), bukan saat insert ──
    live = [U("mati_setelah_insert", 10, 10), U("hidup", 30, 10)]
    before = [e.id for e in _run_production(_system, live, [], 20, 10, 60,
                                           "blue")]
    live[0].alive = False
    after = [e.id for e in _run_production(_system, live, [], 20, 10, 60,
                                           "blue")]
    check("mati_setelah_insert" in before and "mati_setelah_insert" not in after,
          "pygame membaca .alive saat kueri: %s -> %s" % (before, after))
    scenarios.append({"name": "alive_dibaca_live",
                      "insert": {"minions": _rows(live), "heroes": []},
                      "queries": [{"x": 20, "y": 10, "radius": 60,
                                   "team": "blue", "ids": after,
                                   "count": len(after)}]})

    # ── cabang `team=None`: TIDAK menyaring tim DAN tidak menyaring alive
    #    (unit mati hasil insert tetap kembali) ──
    allies = [U("a0", 10, 10), U("a1", 20, 10)]
    allies[1].alive = False
    none_filtered = _run_raw(lambda: _system.SpatialGrid(cell_size=60), allies,
                             15, 10, 60)
    team_filtered = _run_raw(lambda: _system.SpatialGrid(cell_size=60), allies,
                             15, 10, 60, "blue")
    check([e.id for e in none_filtered] == ["a0", "a1"]
          and [e.id for e in team_filtered] == ["a0"],
          "cabang team=None = TANPA filter apa pun (unit mati hasil insert "
          "tetap kembali); cabang team=... membuang sekutu DAN yang mati "
          "(`entity.team == team or not entity.alive`): none=%s team=%s"
          % ([e.id for e in none_filtered], [e.id for e in team_filtered]))
    scenarios.append({"name": "team_none_tanpa_filter",
                      "insert": {"minions": _rows(allies), "heroes": []},
                      "queries": [
                          {"x": 15, "y": 10, "radius": 60, "team": None,
                           "raw": _rows(allies),
                           "ids": [e.id for e in none_filtered],
                           "count": len(none_filtered)},
                          {"x": 15, "y": 10, "radius": 60, "team": "blue",
                           "raw": _rows(allies),
                           "ids": [e.id for e in team_filtered],
                           "count": len(team_filtered)}]})

    # ── kerumunan: kisi 20x20 = 400 unit (skenario yang bikin pygame turun ke
    #    cell 60); fixture menyimpan id pertama + jumlah, bukan 400 baris ──
    crowd = []
    for i in range(20):
        for j in range(20):
            team = "red" if (i + j) % 2 == 0 else "blue"
            crowd.append(U("c%02d_%02d" % (i, j), i * 17.0, j * 13.0, team))
    scenario("kerumunan_400", crowd[:200], crowd[200:], [
        {"x": 200, "y": 150, "radius": 90, "team": "red"},
        {"x": 200, "y": 150, "radius": 90, "team": "blue"},
    ])
    big = _run_production(_system, crowd[:200], crowd[200:], 0, 0, 100000,
                          "red")
    check(len(big) == 200, "kerumunan: hanya tim red yang kembali (dapat %d)"
          % len(big))
    scenarios[-1]["queries"].append({"x": 0, "y": 0, "radius": 100000,
                                     "team": "red", "ids": [e.id for e in big],
                                     "count": len(big)})
    return scenarios


def build_culler_cases(_system):
    margin = _system.FrustumCuller.MARGIN
    w = _system.SCREEN_WIDTH
    h = _system.SCREEN_HEIGHT
    raw = [(0, 0, 30), (-margin, 0, 0), (-margin - 1, 0, 0), (w, h, 0),
           (w + margin, h + margin, 0), (w + margin + 1, h, 0),
           (w, h + margin + 1, 0), (-110, 0, 30), (100, 100, 30),
           (w + margin + 29, h, 30), (-1, -1, 0.5), (0, 0, 0)]
    cases = []
    for x, y, r in raw:
        # kasus r=30 sengaja TIDAK mengirim radius -> `radius=30` default
        found = (_system.FrustumCuller.is_visible(x, y) if r == 30
                 else _system.FrustumCuller.is_visible(x, y, r))
        cases.append({"x": x, "y": y, "radius": r, "expect": bool(found)})
    for r in (10, 12, 22, 26, 40):
        x = -margin - r
        cases.append({"x": x, "y": 100, "radius": r,
                      "expect": bool(_system.FrustumCuller.is_visible(
                          x, 100, r))})
    return {"margin": margin, "screen": [w, h], "default_radius": 30,
            "cases": cases}


# ══════════════════════════════════════════════════════════
#  2. FPSCounter — aturan riwayat + jejak render sungguhan
# ══════════════════════════════════════════════════════════

class _Clock(object):
    def __init__(self, fps):
        self._fps = float(fps)

    def get_fps(self):
        return self._fps


class _ScreenProxy(object):
    """Duck-type surface: `FPSCounter.draw` hanya memanggil `blit` di argumen
    permukaan ini — cukup untuk merekam titik asal panel."""

    def __init__(self):
        self.blit_calls = []

    def blit(self, src, dest=(0, 0), *a):
        self.blit_calls.append({"dest": [int(dest[0]), int(dest[1])],
                                "src_size": [int(src.get_width()),
                                             int(src.get_height())]})


def _fresh_counter(_system):
    """`FPSCounter` singleton lewat `__new__`; beri instance bersih per run."""
    _system.FPSCounter._instance = None
    c = _system.FPSCounter()
    c._fonts = {}
    return c


def build_fps_data(_system, samples):
    c = _fresh_counter(_system)
    trace = []
    # `prev` = nilai TAMPIL awal (0 semua) supaya kondisi kosong tidak tercatat;
    # yang dibandingkan HANYA 4 angka yang dibaca panel — `history`/
    # `frame_count` berubah tiap frame dan bukan bagian dari quirk "tiap 10
    # frame".
    prev = (0.0, 0.0, 0.0, 0.0)
    for i, fps in enumerate(samples, 1):
        c.update(_Clock(fps))
        disp = (c.display_fps, c.display_avg, c.display_min, c.display_max)
        if disp != prev:
            trace.append({"frame": i, "display_fps": c.display_fps,
                          "display_avg": c.display_avg,
                          "display_min": c.display_min,
                          "display_max": c.display_max,
                          "frame_count": c.frame_count,
                          "history": len(c.fps_history)})
            prev = disp
    return {"history_size": int(c.history_size),
            "samples": [float(s) for s in samples], "trace": trace,
            "history": [float(v) for v in c.fps_history],
            "state": {"display_fps": c.display_fps,
                      "display_avg": c.display_avg,
                      "display_min": c.display_min,
                      "display_max": c.display_max,
                      "frame_count": int(c.frame_count)}}


def build_fps_render_trace(_system, samples):
    import pygame
    import _render

    real_get_font = _render.get_font
    captured = {"ops": [], "render": [], "panel_blit": []}
    real_rect = pygame.draw.rect
    real_line = pygame.draw.line

    def rect(surf, color, r, width=0, border_radius=0, **kw):
        captured["ops"].append(
            {"op": "rect", "color": [int(v) for v in color],
             "rect": [int(r[0]), int(r[1]), int(r[2]), int(r[3])],
             "width": int(width), "border_radius": int(border_radius),
             "target": [int(surf.get_width()), int(surf.get_height())]})
        return real_rect(surf, color, r, width, border_radius, **kw)

    def line(surf, color, start, end, width=1):
        captured["ops"].append(
            {"op": "line", "color": [int(v) for v in color],
             "s": [int(start[0]), int(start[1])],
             "e": [int(end[0]), int(end[1])], "width": int(width)})
        return real_line(surf, color, start, end, width)

    class _FontWrap(object):
        def __init__(self, font, size):
            self._font = font
            self._size = size

        def render(self, text, aa=True, color=(255, 255, 255)):
            surf = self._font.render(text, aa, color)
            captured["render"].append(
                {"text": text, "size": int(self._size),
                 "color": [int(v) for v in color][:3],
                 "w": int(surf.get_width())})
            return surf

        def __getattr__(self, name):
            return getattr(self._font, name)

    pygame.draw.rect = rect
    pygame.draw.line = line
    _system.get_font = lambda size, *a, **k: _FontWrap(real_get_font(size), size)
    try:
        c = _fresh_counter(_system)
        for fps in samples:
            c.update(_Clock(fps))
        c.enabled = True
        screen = _ScreenProxy()
        c.draw(screen)
        captured["panel_blit"] = list(screen.blit_calls)
    finally:
        pygame.draw.rect = real_rect
        pygame.draw.line = real_line
        _system.get_font = real_get_font
    return captured


def build_fps_ops(_system, samples, layout, render):
    """Jejak draw+render pygame -> skema op yang dipakai `build_ops` Godot.

    `panel_blit` tidak bisa direkam (Surface.blit milik C dan tidak bisa
    di-patch), jadi titik asal panel diambil dari `base_x/base_y` yang sudah
    di-PIN dari sumber — dan dibuktikan lewat rect panel yang benar-benar
    digambar pygame di (0,0,panel_w,panel_h)."""
    rects = [o for o in render["ops"] if o["op"] == "rect"]
    lines = [o for o in render["ops"] if o["op"] == "line"]
    texts = render["render"]
    bx, by = layout["base"]
    panel_fill, panel_border = rects[0], rects[1]
    check(panel_fill["rect"][:2] == [0, 0] and panel_fill["border_radius"] == 8
          and panel_border["width"] == 1,
          "panel overlay pygame harus rect(0,0,w,h) radius 8 + tepi 1px, "
          "dapat %s / %s" % (panel_fill["rect"], panel_border["width"]))
    ops = [{"op": "panel", "x": bx, "y": by, "w": panel_fill["rect"][2],
            "h": panel_fill["rect"][3], "radius": panel_fill["border_radius"],
            "bg": panel_fill["color"], "border": panel_border["color"]}]
    num, lbl, status, hint, avg, mn, mx = texts[:7]
    gx, gy, gw_sub, gh = layout["graph"]
    graph_w = layout["panel"][0] - gw_sub
    pos = [layout["fps_at"],
           [layout["label"][0] + num["w"] + layout["label"][1],
            layout["label"][2]],
           [layout["panel"][0] - status["w"] - layout["status"][0],
            layout["status"][1]],
           [layout["panel"][0] - hint["w"] - layout["hint"][0],
            layout["panel"][1] - layout["hint"][1]],
           layout["stats_avg"], layout["stats_min"], layout["stats_max"]]
    for item, xy in zip([num, lbl, status, hint, avg, mn, mx], pos):
        ops.append({"op": "text", "text": item["text"], "size": item["size"],
                    "x": xy[0], "y": xy[1], "color": item["color"],
                    "w": item["w"]})
    graph_fill, graph_border = rects[2], rects[3]
    check(graph_fill["rect"] == [gx, gy, graph_w, gh],
          "grafik harus rect(%s, panel_w-%d, %d) — dapat %s"
          % ([gx, gy], gw_sub, gh, graph_fill["rect"]))
    ops.append({"op": "graph", "x": gx, "y": gy, "w": graph_w, "h": gh,
                "radius": graph_fill["border_radius"],
                "bg": graph_fill["color"], "border": graph_border["color"]})
    for ln in lines[:2]:
        ops.append({"op": "line", "x1": ln["s"][0], "y1": ln["s"][1],
                    "x2": ln["e"][0], "color": ln["color"]})
    for r in rects[4:]:
        ops.append({"op": "bar", "x": r["rect"][0], "y": r["rect"][1],
                    "w": r["rect"][2], "h": r["rect"][3],
                    "color": r["color"]})
    return ops


# ── PIN konstanta letak overlay dari TEKS SUMBER `_system.py` ─────────────
LAYOUT_PATTERNS = [
    ("base", r"base_x = (\d+)\n\s*base_y = (\d+)"),
    ("panel", r"panel_w = (\d+)\n\s*panel_h = (\d+)"),
    ("fps_at", r"blit\(fps_surf, \((\d+), (\d+)\)\)"),
    ("label", r"blit\(lbl, \((\d+) \+ fps_surf\.get_width\(\) \+ (\d+), (\d+)\)\)"),
    ("status", r"\(panel_w - st_surf\.get_width\(\) - (\d+), (\d+)\)"),
    ("hint", r"\(panel_w - key_surf\.get_width\(\) - (\d+),\s*\n\s*panel_h - (\d+)\)"),
    ("stats_avg", r"blit\(avg_s, \((\d+), (\d+)\)\)"),
    ("stats_min", r"blit\(min_s, \((\d+), (\d+)\)\)"),
    ("stats_max", r"blit\(max_s, \((\d+), (\d+)\)\)"),
    ("graph", r"graph_x = (\d+)\n\s*graph_y = (\d+)\n\s*graph_w = panel_w - (\d+)\n\s*graph_h = (\d+)"),
]


def pin_layout():
    src = open(SYSTEM_PY, encoding="utf-8").read()
    body = src.split("def draw(self, surface):", 1)[1].split(
        "class AdaptiveQuality", 1)[0]
    out = {}
    for key, pat in LAYOUT_PATTERNS:
        m = re.search(pat, body)
        check(m is not None,
              "pola letak overlay FPS `%s` tidak ditemukan di _system.py — "
              "pygame berubah: sesuaikan port Godot lalu regenerasi fixture"
              % key)
        out[key] = [int(v) for v in m.groups()]
    return out


# ══════════════════════════════════════════════════════════
#  3. Klaim "tidak diport karena dead code" — dijaga supaya tetap benar
# ══════════════════════════════════════════════════════════

TOOL = os.path.relpath(os.path.abspath(__file__), ROOT)


def find_call_sites(pattern, skip=()):
    """Cari pemanggil di SEMUA .py repo (relatif); `skip` = awalan path."""
    hits = []
    rx = re.compile(pattern)
    skip = tuple(skip) + (TOOL,)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in
                       (".git", "__pycache__", ".godot", "node_modules")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
            if rel.startswith(skip):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        if rx.search(line):
                            hits.append("%s:%d" % (rel, i))
            except (UnicodeDecodeError, OSError):
                continue
    return hits


def build_dead_claims():
    out = {}
    adaptive = [h for h in find_call_sites(r"\bAdaptiveQuality\b",
                                           skip=("_system.py", "mobile/"))]
    out["adaptive_quality"] = {"sites": adaptive}
    check(len(adaptive) == 0,
          "`_system.AdaptiveQuality` (blok `fps_limiter.py`, _system.py:400-456) "
          "harus TIDAK punya pemanggil; itulah alasan port Godot tidak "
          "menyalinnya. Pemanggil baru: %s" % adaptive[:6])
    positional = find_call_sites(r"\bplay_positional\b",
                                 skip=("_system.py", "docs/"))
    out["sound_manager_play_positional"] = {"sites": positional}
    check(len(positional) == 0,
          "`SoundManager.play_positional` harus tetap dead code (alasan "
          "AudioManager.gd tidak memportnya): %s" % positional[:6])
    fps_user = find_call_sites(r"\bFPSCounter\b",
                               skip=("_system.py", "main.py"))
    out["fps_counter_users"] = {"sites": fps_user}
    check(len(fps_user) >= 1,
          "FPSCounter harus tetap punya konsumen (kalau tidak, overlay Godot "
          "tidak lagi memindahkan perilaku apa pun)")
    return out


# ══════════════════════════════════════════════════════════
#  4. Kunci statis sisi Godot (tanpa engine: baca sumber .gd)
# ══════════════════════════════════════════════════════════

def gd_read(rel):
    with open(os.path.join(GODOT, rel), encoding="utf-8") as fh:
        return fh.read()


def gd_const(src, name):
    """Teks di kanan `const NAME := ...` pada SATU baris (komentar buang).

    Capture dibatasi satu baris: tanpa itu regex bisa melahap baris berikutnya
    dan mengembalikan nama variabel lain — `const CELL_SIZE := 60.0` lalu
    `var cell_size: float = CELL_SIZE` pernah terbaca sebagai "CELL_SIZE".
    """
    m = re.search(r"^const[ \t]+%s[ \t]*(?:=|:=)[ \t]*([^\n#]+)"
                  % re.escape(name), src, re.M)
    return m.group(1).strip() if m else None


def gd_color(src, name):
    """`const X := array([r, g, b])` -> [r, g, b]; None kalau bukan array int."""
    m = re.search(r"^const[ \t]+%s[ \t]*(?::[ \t]*Array)?[ \t]*(?:=|:)[ \t]*"
                  r"\[([^\]]*)\]" % re.escape(name), src, re.M)
    if not m:
        return None
    try:
        return [int(float(x)) for x in m.group(1).split(",") if x.strip()]
    except ValueError:
        return None


def gd_vec2(src, name):
    """`const X := Vector2(a, b)` -> (a, b); None kalau tidak literal."""
    m = re.search(r"^const[ \t]+%s[ \t]*(?:=|:=)[ \t]*Vector2\(([^)]*)\)"
                  % re.escape(name), src, re.M)
    if not m:
        return None
    try:
        return tuple(float(x) for x in m.group(1).split(",") if x.strip())
    except ValueError:
        return None


def same_num(got, want):
    if got is None:
        return False
    try:
        return abs(float(got) - float(want)) < 1e-9
    except (TypeError, ValueError):
        return False


_GD_FAILS = []


def gd_check(cond, msg):
    if cond:
        PASS.append("godot-source")
    else:
        _GD_FAILS.append(msg)


def check_godot_source(layout, culler, fps):
    grid = gd_read("scripts/systems/SpatialGrid.gd")
    gd_check(same_num(gd_const(grid, "CELL_SIZE"), 60),
             "SpatialGrid.CELL_SIZE harus 60 (paritas `cell_size=60`), dapat %s"
             % gd_const(grid, "CELL_SIZE"))
    for needle, why in (
            ("floor(v / cell_size)",
             "sel harus floor(x/cell) — `int()` Godot memotong ke nol sehingga "
             "koordinat negatif masuk sel yang salah"),
            ("dx * dx + dy * dy <= r2",
             "jarak dibandingkan sebagai KUADRAT (paritas `dx*dx + dy*dy <= radius ** 2`)"),
            ("for cy in range(min_cy, max_cy + 1)",
             "cy loop DALAM (paritas `_system.py:103-104`: cx di luar, jadi "
             "urutan hasil = per kolom sel, baru per baris)"),
            ("for cx in range(min_cx, max_cx + 1)",
             "cx loop LUAR"),
            ("p.x < x0 or p.x > x1",
             "pra-saring bbox wajib ada sebelum uji jarak kuadrat"),
            ('_query(x, y, radius, "", false)',
             "query_range harus TANPA filter apa pun (cabang `team=None` pygame "
             "tidak membuang sekutu maupun bangkai)"),
            ('_query(x, y, radius, team, true)',
             "query_enemies harus menyaring sekutu DAN bangkai, sama seperti "
             "cabang `team` di `_system.py:113-119`"),
            ("func query_range(x: float, y: float, radius: float) -> Array:",
             "query_range publik harus tetap 3 argumen (dipakai harness & "
             "fallback), filter tim lewat query_enemies"),
            ("func update_from(minions: Array, heroes: Array) -> void:",
             "badan `update_spatial_grid` (clear + insert minion lalu hero) "
             "harus tinggal SATU tempat: SpatialGrid.update_from, dipakai "
             "produksi dan direplay tes"),
            ("_is_dead(entity)",
             "unit mati harus dicek saat insert MAUPUN dibaca ulang saat kueri "
             "(`.alive` pygame begitu)")):
        gd_check(needle in grid, "SpatialGrid.gd: %s" % why)

    cull = gd_read("scripts/systems/FrustumCuller.gd")
    gd_check(same_num(gd_const(cull, "MARGIN"), culler["margin"]),
             "FrustumCuller.MARGIN harus %s" % culler["margin"])
    gd_check(same_num(gd_const(cull, "SCREEN_WIDTH"), culler["screen"][0])
             and same_num(gd_const(cull, "SCREEN_HEIGHT"), culler["screen"][1]),
             "FrustumCuller.SCREEN_{WIDTH,HEIGHT} harus %dx%d (`SCREEN_*` _core.py)"
             % tuple(culler["screen"]))
    gd_check(same_num(gd_const(cull, "DEFAULT_RADIUS"), culler["default_radius"]),
             "radius default is_visible harus %s" % culler["default_radius"])
    gd_check("-m <= x and x <= screen.x + m" in cull,
             "batas culling harus inklusif di kedua sisi (`<=` di pygame)")

    fc = gd_read("scenes/ui/FpsCounter.gd")
    ops_by_op = {}
    for op in fps["ops"]:
        ops_by_op.setdefault(op["op"], op)
    lines = [op for op in fps["ops"] if op["op"] == "line"]
    for key, want in (("HISTORY_SIZE", fps["history_size"]),
                      ("DISPLAY_WINDOW", fps["display_window"]),
                      ("DISPLAY_EVERY", fps["display_every"]),
                      ("PANEL_W", layout["panel"][0]),
                      ("PANEL_H", layout["panel"][1]),
                      ("GRAPH_X", layout["graph"][0]),
                      ("GRAPH_Y", layout["graph"][1]),
                      ("GRAPH_H", layout["graph"][3]),
                      ("GRAPH_PAD", layout["graph"][2]),
                      ("PANEL_BG_ALPHA", ops_by_op["panel"]["bg"][3]),
                      ("PANEL_RADIUS", ops_by_op["panel"]["radius"]),
                      ("GRAPH_RADIUS", ops_by_op["graph"]["radius"]),
                      ("NUM_SIZE", 40), ("LABEL_SIZE", 16),
                      ("STATUS_SIZE", 15), ("STATS_SIZE", 14),
                      ("HINT_SIZE", 12), ("GRAPH_SCALE_MAX", 80.0),
                      ("LABEL_GAP", layout["label"][1]),
                      ("LABEL_Y", layout["label"][2]),
                      ("STATUS_PAD", layout["status"][0]),
                      ("STATUS_Y", layout["status"][1]),
                      ("HINT_PAD", layout["hint"][0]),
                      ("HINT_BOTTOM", layout["hint"][1]),
                      ("STATS_Y", layout["stats_avg"][1]),
                      ("AVG_X", layout["stats_avg"][0]),
                      ("MIN_X", layout["stats_min"][0]),
                      ("MAX_X", layout["stats_max"][0])):
        gd_check(same_num(gd_const(fc, key), want),
                 "FpsCounter.%s harus %s (paritas `_system.py:259-398`), "
                 "dapat %s" % (key, want, gd_const(fc, key)))
    gd_check(gd_vec2(fc, "PANEL_POS") == tuple(layout["base"]),
             "FpsCounter.PANEL_POS harus %s, dapat %s"
             % (tuple(layout["base"]), gd_vec2(fc, "PANEL_POS")))
    gd_check(gd_vec2(fc, "FPS_AT") == tuple(layout["fps_at"]),
             "FpsCounter.FPS_AT harus %s (blit angka FPS), dapat %s"
             % (tuple(layout["fps_at"]), gd_vec2(fc, "FPS_AT")))
    by_text = {}
    for op in fps["ops"]:
        if op["op"] == "text":
            by_text[op["text"]] = op

    def stat_color(prefix):
        for text in by_text:
            if text.startswith(prefix):
                return by_text[text]["color"]
        raise AssertionError("teks %s tidak ada di jejak ops" % prefix)

    for key, want in (("PANEL_BG", ops_by_op["panel"]["bg"][:3]),
                      ("PANEL_BORDER", ops_by_op["panel"]["border"]),
                      ("GRAPH_BG", ops_by_op["graph"]["bg"]),
                      ("GRAPH_BORDER", ops_by_op["graph"]["border"]),
                      ("GUIDE_60", lines[0]["color"]),
                      ("GUIDE_30", lines[1]["color"]),
                      ("LABEL_COLOR", by_text["FPS"]["color"]),
                      ("HINT_COLOR", by_text["[F8] toggle"]["color"]),
                      ("STAT_COLOR", stat_color("AVG ")),
                      ("COLOR_EXCELLENT", [100, 255, 100]),
                      ("COLOR_GOOD", [255, 255, 100]),
                      ("COLOR_FAIR", [255, 150, 50]),
                      ("COLOR_POOR", [255, 60, 60]),
                      ("BAR_EXCELLENT", [50, 160, 50]),
                      ("BAR_GOOD", [160, 160, 50]),
                      ("BAR_FAIR", [160, 90, 40]),
                      ("BAR_POOR", [160, 40, 40])):
        got = gd_color(fc, key)
        gd_check(got is not None,
                 "FpsCounter.%s harus array 0..255 literal (bukan Color) "
                 "supaya bisa dibandingkan dengan jejak pygame" % key)
        gd_check(got == list(want),
                 "FpsCounter.%s harus %s (jejak pygame), dapat %s"
                 % (key, list(want), got))
    # MIN di bawah 30 fps -> merah; di atasnya -> abu-abu biasa. Fixture ini
    # berada di cabang merah, jadi yang lain ikut dikunci lewat stat_color.
    if float(fps["state_short"]["display_min"]) < 30.0:
        gd_check(gd_color(fc, "STAT_MIN_COLOR") == stat_color("MIN "),
                 "FpsCounter.STAT_MIN_COLOR harus sama dengan warna teks MIN "
                 "saat display_min < 30 (jejak pygame)")
    gd_check("minf(fps, GRAPH_SCALE_MAX)" in fc,
             "skala bar harus dibatasi `min(fps, 80)` (`bar_scale = min(80.0, "
             "max_fps)`, `_system.py:376`)")
    gd_check("if frame_count >= DISPLAY_EVERY:" in fc,
             "angka panel hanya diperbarui setiap 10 frame, dan `frame_count` "
             "di-reset ke 0 (paritas `if self.frame_count >= 10` `_system.py:243`)")
    gd_check("if not fps_history.is_empty():" in fc
             and "begin: int = maxi(0, fps_history.size() - DISPLAY_WINDOW)" in fc,
             "jendela statistik = 30 sampel terakhir dari riwayat yang "
             "di-trim 120 (`_system.py:245-250`)")
    gd_check("fps_history.pop_front()" in fc,
             "riwayat dipotong dari depan (deque maxlen=120 di pygame)")
    gd_check("update(Engine.get_frames_per_second())" in fc,
             "produksi memberi fps dari Engine (satu sampel per frame) — bukan "
             "clock.tick() seperti `main_desktop_legacy.py:455`")

    combat = gd_read("scripts/systems/CombatSystem.gd")
    gd_check("_spatial_grid.update_from(_alive_only(minions), _alive_only(heroes))"
             in combat,
             "CombatSystem.update_spatial_grid harus memakai SpatialGrid.update_from "
             "plus penjaga `_alive_only` (is_instance_valid) — bukan salinan loop")
    for needle, why in (
            ("GRID_REBUILD_EVERY := 2",
             "rebuild terjadwal 2 frame sekali (`animation_time % 2 == 0`, "
             "_core.py:2009) — angka 100 yang pernah dipakai bukan paritas"),
            ("const SpatialGridScript := preload",
             "CombatSystem harus memakai kelas SpatialGrid bersama (identik "
             "dengan satu `_grid` global pygame)"),
            ("query_enemies(center.x, center.y, radius, team)",
             "satu-satunya jalur baca grid = query_enemies_in_range (targeting "
             "minion); sihir/panah/AoE sengaja TIDAK dialihkan ke grid supaya "
             "urutan kunci (index grup) tidak berubah"),
            ('for group in ["towers", "nexus"]',
             "tower/nexus tidak diindeks grid pygame (`_system.py:155-158`) -> "
             "tetap scan grup dan appended di belakang"),
            ('return enemies_in_radius(team, center, radius)',
             "fallback = fungsi scan yang sudah dikunci tes lain, bukan salinan "
             "rumus baru"),
            ("func reset_spatial_grid() -> void:",
             "harness harus bisa membuang grid supaya jalur fallback teruji")):
        gd_check(needle in combat, "CombatSystem.gd: %s" % why)

    minion = gd_read("scenes/minion/Minion.gd")
    gd_check("CombatSystem.query_enemies_in_range(" in minion
             and "team, global_position, attack_range + 30.0)" in minion,
             "Minion._find_target_smart harus mengambil kandidat lewat grid, "
             "bukan scan grup (padanan `Minion._get_enemies` _entity.py:5635)")

    main = gd_read("scenes/main/Main.gd")
    gd_check("if _grid_tick % CombatSystem.GRID_REBUILD_EVERY == 0:" in main
             and "CombatSystem.update_spatial_grid_from_tree()" in main,
             "Main menjadwalkan rebuild 2 frame sekali, meniru `animation_time "
             "% 2 == 0` (_core.py:2009) — jangan rebuild tiap frame")
    gd_check("keycode == KEY_F8:" in main and "toggle_fps_counter()" in main,
             "F8 harus memicu toggle lewat `_on_key` SEBELUM dispatch state "
             "(persis `main_desktop_legacy.py:98-100`)")
    popups = gd_read("scenes/fx/WorldPopups.gd")
    gd_check("FrustumCuller.is_visible_world(" in popups,
             "WorldPopups harus memakai FrustumCuller (konsumen draw-side satu-"
             "satunya yang masuk akal di Godot)")
    if _GD_FAILS:
        print("[system_perf] %d kunci statis Godot gagal:" % len(_GD_FAILS))
        for f in _GD_FAILS:
            print("  - " + f)
        return False
    return True
# ══════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════

def build_fixture():
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    pygame.font.init()
    import _core                                   # noqa: F401 (anti-circular)
    import _system

    layout = pin_layout()
    # 150 sampel = mengunci trim 120 DAN jendela tampil 30 + refresh tiap 10
    long_run = [float(20 + (i * 7) % 45) for i in range(150)]
    fps_data = build_fps_data(_system, long_run)
    check(fps_data["history_size"] == 120,
          "FPSCounter.history_size harus 120, dapat %s"
          % fps_data["history_size"])
    check(len(fps_data["history"]) == 120,
          "riwayat di-trim ke 120 (Godot memotong dengan pop_front)")
    recent = long_run[-30:]
    check(abs(fps_data["state"]["display_avg"] - sum(recent) / 30.0) < 1e-9,
          "display_avg = rata-rata 30 sampel TERAKHIR")
    check(fps_data["state"]["display_fps"] == float(recent[-1]),
          "display_fps = sampel terakhir jendela 30")
    check(fps_data["state"]["display_min"] == float(min(recent))
          and fps_data["state"]["display_max"] == float(max(recent)),
          "display_min/max = min/max jendela 30")
    updates = [t for t in fps_data["trace"]]
    check(all(u["frame"] % 10 == 0 for u in updates),
          "angka panel hanya diperbarui setiap 10 frame (quirk pygame) — "
          "dapat %s" % [u["frame"] for u in updates][:6])

    short = [60.0, 58.0, 61.0, 55.0, 57.0, 59.0, 60.0, 44.0, 38.0, 30.0,
             25.0, 22.0, 19.0, 60.0, 60.0, 59.5, 55.25, 41.0, 33.0, 24.5,
             21.0]
    render = build_fps_render_trace(_system, short)
    # State yang dibaca panel SAAT digambar: setelah 21 sampel, angka tampil
    # masih hasil update frame ke-20 (refresh tiap 10 frame) — jadi state
    # `short` inilah yang harus dipakai Godot untuk mereplay ops, BUKAN state
    # long-run di atas.
    state_short = build_fps_data(_system, short)["state"]
    check(len(render["render"]) == 7,
          "overlay harus me-render 7 teks (angka, FPS, status, petunjuk, "
          "AVG, MIN, MAX) — dapat %d" % len(render["render"]))
    ops = build_fps_ops(_system, short, layout, render)
    for band, want_status, want_color in ((60.0, "SMOOTH", [100, 255, 100]),
                                          (45.0, "OK", [255, 255, 100]),
                                          (30.0, "SLOW", [255, 150, 50]),
                                          (10.0, "LAG!", [255, 60, 60])):
        # 10 sampel identik: panel baru menghitung angka setelah 10 frame
        # (`if self.frame_count >= 10`), jadi satu sampel saja tetap 0 fps.
        r = build_fps_render_trace(_system, [band] * 10)
        st = [x for x in r["render"] if x["text"] == want_status]
        check(st and st[0]["color"] == want_color,
              "band %s harus status %s warna %s (render sungguhan), dapat %s"
              % (band, want_status, want_color, st[:1]))
    bars = [o for o in ops if o["op"] == "bar"]
    check(len(bars) == len(short),
          "satu bar per sampel riwayat (`num_bars = min(len(history), graph_w)`), "
          "dapat %d dari %d sampel" % (len(bars), len(short)))

    fixture = {
        "_generated_by": "tools/test_system_perf_parity.py --write-fixture",
        "grid": {"cell_size": _system.SpatialGrid(cell_size=60).cell_size,
                 "scenarios": build_grid_scenarios(_system)},
        "culler": build_culler_cases(_system),
        "fps": {
            "history_size": fps_data["history_size"],
            "display_window": 30, "display_every": 10,
            "samples": fps_data["samples"], "trace": fps_data["trace"],
            "state": fps_data["state"],
            "samples_short": short, "state_short": state_short,
            "render": render["render"],
            "raw_ops": render["ops"], "ops": ops, "layout": layout,
            "py_draw_needs_shim": True,
            "py_bug": ("_system.FPSCounter.draw() memakai get_font yang tidak "
                       "ada di namespace _system -> NameError tanpa shim "
                       "(lihat docstring tool)"),
        },
        "dead": build_dead_claims(),
    }
    return fixture


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-fixture", action="store_true")
    args = ap.parse_args()
    fixture = build_fixture()
    text = json.dumps(fixture, indent=1, sort_keys=True) + "\n"
    if args.write_fixture:
        with open(FIXTURE, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("[system_perf] fixture ditulis: %s (%d byte, %d pemeriksaan)"
              % (os.path.relpath(FIXTURE, ROOT), len(text), len(PASS)))
        return
    if not os.path.exists(FIXTURE):
        raise AssertionError("fixture belum ada — jalankan "
                             "tools/test_system_perf_parity.py --write-fixture")
    with open(FIXTURE, encoding="utf-8") as fh:
        old = fh.read()
    check(old.strip() == text.strip(),
          "fixture system_perf.json basi: perilaku pygame berubah — sesuaikan "
          "Godot lalu regenerasi dengan --write-fixture")
    again = json.dumps(build_fixture(), indent=1, sort_keys=True) + "\n"
    check(again == text, "fixture harus deterministik antar run")
    ok = check_godot_source(fixture["fps"]["layout"], fixture["culler"],
        fixture["fps"])
    if not ok:
        raise SystemExit(1)
    print("[system_perf] %d pemeriksaan oracle + kunci statis Godot lulus"
          % len(PASS))


if __name__ == "__main__":
    main()
