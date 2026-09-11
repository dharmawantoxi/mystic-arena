#!/usr/bin/env python3
"""Oracle paritas ui_theme.py -> godot/scripts/utils/UiTheme.gd + widgets.

    python3 tools/test_godot_ui_theme_parity.py                  # verifikasi
    python3 tools/test_godot_ui_theme_parity.py --write-fixture  # sengaja perbarui

Sumber kebenaran = `ui_theme.py` (pygame). Alat ini TIDAK menyalin rumus ke
sisi Godot; ia MENJALANKAN modul pygame asli (SDL dummy) dan merekam hasilnya:

  1. PALET       — 32 konstanta warna dibaca dari atribut modul pygame lalu
                   dibandingkan dengan `const` di UiTheme.gd (dua arah: nilai
                   harus sama dan TIDAK boleh ada nama pygame yang hilang).
  2. COVERAGE    — closed-world: setiap `def` di ui_theme.py harus punya
                   padanan di Godot (tabel PEMETAAN di bawah). def baru di
                   pygame yang belum diport = GAGAL, bukan "nanti saja".
  3. IKON        — nama ikon diparse dari cabang `if name == ...` di
                   `ui_theme.draw_icon` lalu dibandingkan dengan
                   `UiTheme.ICON_NAMES` (dua arah).
  4. WARNA TABEL — warna komponen diambil dari KUNCI CACHE pygame
                   (`_GRAD_CACHE`/`_GLOW_CACHE`): kunci `_vgrad` memuat tuple
                   (w, h, top, bottom, radius) PERSIS seperti yang digambar,
                   jadi tidak ada tebakan piksel. Tabel `pill` dibaca dari
                   literal dict di sumber `pill()` (ast.literal_eval).
  5. GEOMETRI    — rect yang DIKEMBALIKAN fungsi pygame + isi dict `btns`
                   (hit-test) untuk button/pill/tab/toggle/back_button/
                   option_cycler/chip/scroll_indicator, termasuk quirk
                   `inflate(18, 8)` saat hover dan "tombol mati tidak
                   terdaftar di btns".
  6. MATEMATIKA  — `_vgrad` per baris (dibaca dari piksel permukaan cache),
                   `_radial` (kunci alpha // 8 * 8 + alpha per blok dari
                   piksel), `_shadow` (ukuran permukaan + sel 1/8),
                   `_dim`, `letter`, `math_hyp`, `tab_width`, lebar isi bar.
  7. FONT PALSU  — pengukuran teks memakai FakeFont deterministik
                   (lebar = 7 × karakter) supaya oracle GEOMETRI tidak
                   bergantung metrik font engine mana pun: sisi Godot
                   membandingkan fungsi murni dengan lebar masukan yang sama.

Butuh pygame-ce (SDL dummy). Tanpa pygame, alat ini tetap menjalankan cek
statistik 1-3 (palet/coverage/ikon) lalu melapor bahwa seksi oracle dilewati —
jadi bisa dipasang di langkah linter CI yang belum memasang pygame.

Regenerasi fixture HANYA bila ui_theme.py berubah (aturan docs/MIGRASI_1_1.md:
pygame tidak pernah disetel mengikuti Godot).
"""
import argparse
import ast
import inspect
import json
import os
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GD_THEME = ROOT / "godot" / "scripts" / "utils" / "UiTheme.gd"
GD_WIDGETS = ROOT / "godot" / "scenes" / "ui" / "widgets"
GD_TEST = ROOT / "godot" / "tests" / "UiThemeParityTest.gd"
FIXTURE = ROOT / "godot" / "tests" / "fixtures" / "ui_theme.json"

# ══════════════════════════════════════════════════════════
#  Tabel pemetaan closed-world: def ui_theme.py -> simbol Godot
#  (simbol harus benar-benar ada di berkas .gd; def pygame baru yang
#   tidak ada di tabel ini = kegagalan, supaya port tidak pernah "lupa")
# ══════════════════════════════════════════════════════════

PEMETAAN = {
    "cheap_alpha": ["UiTheme.cheap_alpha"],
    "clear_caches": ["UiTheme.clear_caches"],
    "_vgrad": ["UiTheme.draw_vgrad", "UiTheme.vgrad_row_color"],
    "_shadow": ["UiTheme.draw_shadow", "UiTheme.shadow_texture",
                "UiTheme.shadow_surface_size", "UiTheme.shadow_small_size"],
    "_radial": ["UiTheme.draw_glow", "UiTheme.radial_texture",
                "UiTheme.radial_alpha_key", "UiTheme.glow_alpha_at"],
    "math_hyp": ["UiTheme.hyp"],
    "letter": ["UiTheme.letter"],
    "fit_ellipsis": ["UiTheme.fit_ellipsis"],
    "_has_glyph": ["UiTheme.has_glyph"],
    "draw_text": ["UiTheme.draw_text", "UiTheme.draw_text_centered"],
    "gradient_text": ["UiTheme.gradient_bands", "GradientText"],
    "outline_text": ["UiTheme.draw_outline_text"],
    "draw_icon": ["UiTheme.draw_icon", "UiTheme.icon_names",
                  "UiTheme.has_icon", "VectorIcon"],
    "corner_ticks": ["UiTheme.draw_corner_ticks"],
    "panel": ["UiTheme.draw_panel", "PygamePanel"],
    "panel_solid": ["UiTheme.draw_panel_solid"],
    "button": ["UiTheme.draw_button", "UiTheme.draw_button_visual",
               "UiTheme.button_hit_rect", "UiTheme.menu_button_colors",
               "UiTheme.button_label_cx", "PygameButton"],
    "pill": ["UiTheme.draw_pill", "UiTheme.draw_pill_visual",
             "UiTheme.pill_colors", "PygameButton"],
    "chip": ["UiTheme.draw_chip", "UiTheme.chip_rect", "UiTheme.chip_size",
             "UiTheme.chip_colors", "PygameChip"],
    "section_header": ["UiTheme.draw_section_header",
                       "UiTheme.section_header_geom",
                       "UiTheme.section_header_size", "SectionHeader"],
    "_dim": ["UiTheme.dim"],
    "toggle": ["UiTheme.draw_toggle", "UiTheme.draw_toggle_visual",
               "UiTheme.toggle_colors", "PygameToggle"],
    "slider": ["UiTheme.draw_slider", "UiTheme.slider_geom",
               "UiTheme.style_volume_slider", "PygameSlider"],
    "option_cycler": ["UiTheme.draw_option_cycler", "UiTheme.cycler_geom",
                      "OptionCycler"],
    "tab_width": ["UiTheme.tab_width", "UiTheme.tab_width_for"],
    "tab": ["UiTheme.draw_tab", "UiTheme.draw_tab_visual",
            "UiTheme.tab_colors", "PygameButton"],
    "screen_title": ["UiTheme.draw_screen_title", "UiTheme.screen_title_geom",
                     "UiTheme.draw_title_ornament", "UiTheme.draw_title_sub",
                     "ScreenTitle", "Flourish"],
    "back_button": ["UiTheme.draw_back_button", "UiTheme.back_button_rect",
                    "PygameButton.back_button"],
    "scroll_indicator": ["UiTheme.draw_scroll_indicator",
                         "UiTheme.scroll_thumb_rect", "ScrollIndicator"],
    "hp_bar": ["UiTheme.draw_hp_bar"],
    "progress_bar": ["UiTheme.draw_progress_bar",
                     "UiTheme.style_progress_bar"],
}

# Warna pygame yang dipakai komponen tapi bukan konstanta modul (nilai
# literal di dalam fungsi) — direkam oracle dari kunci cache/piksel, dan
# daftar ini hanya dipakai untuk memastikan UiTheme.gd tidak kehilangan
# salah satunya (dicek sebagai teks "#hex" atau Color8()).
LITERAL_PENTING = {
    "chip_top": (32, 38, 64),
    "chip_bottom": (18, 22, 40),
    "chip_solid": (22, 26, 46),
    "pill_owned_text": (190, 250, 200),
    "slider_track": (34, 38, 58),
    "slider_border": (120, 110, 86),
    "knob_shadow": (12, 14, 24),
    "knob_face": (245, 248, 255),
    "hp_track": (16, 18, 30),
    "hp_border": (86, 92, 120),
    "progress_track": (30, 34, 54),
    "progress_border": (96, 96, 126),
    "scroll_track": (28, 32, 52),
    "gold_deep_body": (196, 138, 40),
    "panel_shadow_solid": (6, 7, 14),
    # option_cycler (semua literal di dalam fungsi pygame)
    "cycler_box_top": (40, 48, 80),
    "cycler_box_bottom": (20, 24, 44),
    "cycler_box_solid": (28, 34, 58),
    "cycler_chevron_top": (42, 48, 74),
    "cycler_chevron_top_hover": (64, 74, 110),
    "cycler_chevron_bottom": (26, 30, 52),
    "cycler_border": (96, 106, 138),
    "cycler_border_hover": (150, 160, 196),
    "cycler_icon": (200, 210, 240),
    # toggle / button / tab / screen_title
    "toggle_label_on": (210, 255, 220),
    "button_badge": (12, 14, 26),
    "title_glow": (255, 205, 90),
    "title_plate_top": (26, 32, 58),
    "title_plate_bottom": (14, 18, 34),
    "title_plate_solid": (16, 20, 38),
}


def _read(path):
    return Path(path).read_text(encoding="utf-8")


# ══════════════════════════════════════════════════════════
#  Cek statis (tanpa pygame)
# ══════════════════════════════════════════════════════════

def _py_palette(src):
    out = {}
    for m in re.finditer(r"^([A-Z][A-Z0-9_]*)\s*=\s*\(([^)]*)\)", src, re.M):
        nums = [int(x) for x in re.findall(r"\d+", m.group(2))]
        if len(nums) >= 3:
            out[m.group(1)] = tuple(nums[:3])
    return out


def _gd_palette(src):
    out = {}
    for m in re.finditer(
            r'^const\s+([A-Z][A-Z0-9_]*)\s*:=\s*Color\("#([0-9a-fA-F]{6})"\)',
            src, re.M):
        h = m.group(2)
        out[m.group(1)] = tuple(int(h[i:i + 2], 16) for i in range(0, 6, 2))
    return out


def check_palette(py_src=None, gd_src=None):
    py_src = py_src or _read(ROOT / "ui_theme.py")
    gd_src = gd_src or _read(GD_THEME)
    py = _py_palette(py_src)
    gd = _gd_palette(gd_src)
    missing = sorted(set(py) - set(gd))
    if missing:
        raise AssertionError(
            "Konstanta warna ui_theme.py belum ada di UiTheme.gd: %s"
            % ", ".join(missing))
    bad = [(k, py[k], gd[k]) for k in sorted(set(py) & set(gd))
           if py[k] != gd[k]]
    if bad:
        raise AssertionError("Warna berbeda pygame vs Godot: %s"
                             % ", ".join("%s py=%s gd=%s" % b for b in bad))
    extra = sorted(set(gd) - set(py))
    print("[statis] PALET   : %d/%d konstanta identik (tambahan Godot: %s)"
          % (len(py), len(py), ", ".join(extra) or "-"))
    return py


def _py_defs(src):
    return [m.group(1) for m in re.finditer(r"^def\s+(\w+)\s*\(", src, re.M)]


def _gd_symbols():
    """Kumpulkan simbol yang tersedia di sisi Godot (UiTheme + widgets)."""
    sym = set()
    files = [GD_THEME] + sorted(GD_WIDGETS.glob("*.gd"))
    for path in files:
        src = _read(path)
        stem = path.stem
        for m in re.finditer(r"^\s*(?:static\s+)?func\s+(\w+)\s*\(", src, re.M):
            sym.add("%s.%s" % (stem, m.group(1)))
        for m in re.finditer(r"^\s*(?:static\s+)?var\s+(\w+)", src, re.M):
            sym.add("%s.%s" % (stem, m.group(1)))
        for m in re.finditer(r"^const\s+(\w+)", src, re.M):
            sym.add("%s.%s" % (stem, m.group(1)))
        for m in re.finditer(r"^class_name\s+(\w+)", src, re.M):
            sym.add(m.group(1))
    return sym


def check_coverage():
    src = _read(ROOT / "ui_theme.py")
    defs = _py_defs(src)
    unmapped = [d for d in defs if d not in PEMETAAN]
    if unmapped:
        raise AssertionError(
            "def ui_theme.py belum punya padanan Godot (tambahkan ke tabel "
            "PEMETAAN di tools/test_godot_ui_theme_parity.py lalu port): %s"
            % ", ".join(unmapped))
    stale = [d for d in PEMETAAN if d not in defs]
    if stale:
        raise AssertionError(
            "Tabel PEMETAAN menyebut def yang tidak ada lagi di ui_theme.py: %s"
            % ", ".join(stale))
    sym = _gd_symbols()
    hilang = []
    for py_def, targets in PEMETAAN.items():
        for t in targets:
            if t in sym:
                continue
            # PygameButton.back_button -> class + static func
            if "." in t:
                cls, fn = t.split(".", 1)
                if cls in sym and ("%s.%s" % (cls, fn)) in sym:
                    continue
            hilang.append("%s -> %s" % (py_def, t))
    if hilang:
        raise AssertionError(
            "Simbol Godot untuk port ui_theme.py tidak ditemukan: %s"
            % ", ".join(hilang))
    print("[statis] COVERAGE: %d def ui_theme.py -> %d simbol Godot (lengkap)"
          % (len(defs), len(sym)))
    return defs


def _py_icon_names(src):
    start = src.index("def draw_icon")
    end = src.index("def corner_ticks")
    body = src[start:end]
    names = set(re.findall(r'name\s*==\s*"([a-z_0-9]+)"', body))
    for group in re.findall(r"name\s+in\s+\(([^)]*)\)", body):
        names |= set(re.findall(r'"([a-z_0-9]+)"', group))
    return sorted(names)


def _gd_icon_names(src):
    m = re.search(r"const ICON_NAMES := \[(.*?)\]\n", src, re.S)
    if not m:
        raise AssertionError("ICON_NAMES tidak ditemukan di UiTheme.gd")
    return sorted(re.findall(r'"([a-z_0-9]+)"', m.group(1)))


def check_icons():
    py = _py_icon_names(_read(ROOT / "ui_theme.py"))
    gd = _gd_icon_names(_read(GD_THEME))
    if py != gd:
        raise AssertionError(
            "Daftar ikon berbeda — hanya pygame: %s | hanya Godot: %s"
            % (sorted(set(py) - set(gd)), sorted(set(gd) - set(py))))
    # Setiap nama harus punya lengan match di draw_icon (bukan cuma daftar).
    start = _read(GD_THEME).index("static func draw_icon")
    body = _read(GD_THEME)[start:]
    arms = set()
    for m in re.finditer(r'^\t\t"([a-z_, 0-9"]+)":$', body, re.M):
        # lengan tunggal -> "play"; lengan gabung -> 'chevron_l", "chevron_r'
        for part in m.group(1).split('", "'):
            arms.add(part.strip('"'))
    missing = sorted(set(py) - arms)
    if missing:
        raise AssertionError(
            "Ikon ada di ICON_NAMES tapi tidak digambar draw_icon(): %s"
            % ", ".join(missing))
    print("[statis] IKON    : %d nama ikon identik + semua punya lengan match"
          % len(py))
    return py


def check_literals():
    """Warna literal komponen harus tertulis di UiTheme.gd (hex atau Color8)."""
    src = _read(GD_THEME)
    hilang = []
    for name, rgb in LITERAL_PENTING.items():
        hexv = "#%02x%02x%02x" % rgb
        c8 = "Color8(%d, %d, %d)" % rgb
        if hexv not in src and c8 not in src:
            hilang.append("%s %s" % (name, hexv))
    if hilang:
        raise AssertionError(
            "Warna literal ui_theme.py hilang dari UiTheme.gd: %s"
            % ", ".join(hilang))
    print("[statis] LITERAL : %d warna literal komponen ada di UiTheme.gd"
          % len(LITERAL_PENTING))


def check_test_wiring(fixture):
    """Tes Godot harus memakai SETIAP seksi fixture (tidak ada oracle yatim)."""
    if not GD_TEST.exists():
        raise AssertionError("Tes replay hilang: %s"
                             % GD_TEST.relative_to(ROOT))
    src = _read(GD_TEST)
    if "fixtures/ui_theme.json" not in src:
        raise AssertionError("UiThemeParityTest.gd tidak membaca fixture "
                             "ui_theme.json")
    yatim = []
    for section in fixture:
        if section in ("meta",):
            continue
        if not re.search(r'"%s"|\[\"%s\"\]' % (section, section), src):
            yatim.append(section)
    if yatim:
        raise AssertionError(
            "Seksi fixture tidak diperiksa UiThemeParityTest.gd: %s"
            % ", ".join(yatim))
    print("[statis] WIRING  : %d seksi fixture dipakai UiThemeParityTest.gd"
          % (len(fixture) - 1))


# ══════════════════════════════════════════════════════════
#  Oracle pygame (butuh pygame-ce + SDL dummy)
# ══════════════════════════════════════════════════════════

class FakeFont:
    """Font deterministik: lebar = 7 px per karakter, tinggi 20 px.

    Oracle geometri memakai ini supaya angka yang dibandingkan TIDAK
    bergantung metrik font engine mana pun: sisi Godot memasukkan lebar
    terukur yang sama ke fungsi murninya (UiTheme.chip_rect, cycler_geom,
    tab_width_for, button_label_cx, section_header_geom).
    """

    def __init__(self, char_w=7, height=20):
        self.char_w = char_w
        self.height = height

    def size(self, text):
        return (self.char_w * len(str(text)), self.height)

    def render(self, text, _aa, color, _bg=None):
        import pygame
        w = max(1, self.char_w * len(str(text)))
        surf = pygame.Surface((w, self.height), pygame.SRCALPHA)
        surf.fill(tuple(color[:3]) + (255,))
        return surf

    def get_height(self):
        return self.height

    def get_ascent(self):
        return int(self.height * 0.8)

    def get_descent(self):
        return int(self.height * 0.2)


def _load_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    try:
        import pygame
    except Exception as exc:  # pragma: no cover - lingkungan tanpa pygame
        print("[oracle] pygame tidak tersedia (%s) — seksi oracle dilewati; "
              "cek statis tetap jalan" % exc)
        return None, None
    pygame.init()
    try:
        pygame.display.set_mode((1, 1))
    except Exception:
        pass
    import ui_theme

    # Stub `_core` (ui_theme mengimpornya di dalam fungsi: title_font/get_font).
    stub = types.ModuleType("_core")
    stub.title_font = lambda size=64: FakeFont()
    stub.get_font = lambda size=16, weight="body": FakeFont()
    sys.modules.setdefault("_core", stub)
    return pygame, ui_theme


def _screen(w=700, h=340):
    import pygame
    s = pygame.Surface((w, h))
    s.fill((1, 2, 3))
    return s


def _px(surf, x, y):
    c = surf.get_at((int(x), int(y)))
    return [c[0], c[1], c[2]]


def _grad_keys(ui_theme):
    return [{"w": k[0], "h": k[1], "top": list(k[2]), "bottom": list(k[3]),
             "radius": k[4]} for k in ui_theme._GRAD_CACHE]


def _glow_keys(ui_theme):
    return [{"w": k[0], "h": k[1], "color": list(k[2]), "alpha": k[3]}
            for k in ui_theme._GLOW_CACHE]


def _rect(r):
    return [r.x, r.y, r.w, r.h]


def _set_cheap(ui_theme, value):
    ui_theme.cheap_alpha = lambda: value


def _node_value(node, ui_theme):
    """Evaluasi node AST literal; Name diselesaikan ke konstanta ui_theme."""
    if isinstance(node, ast.Name):
        return getattr(ui_theme, node.id)
    if isinstance(node, ast.Tuple) or isinstance(node, ast.List):
        return tuple(_node_value(e, ui_theme) for e in node.elts)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_node_value(node.operand, ui_theme)
    raise AssertionError("Node tak terduga di tabel warna pill: %s"
                         % ast.dump(node))


def _pill_table(ui_theme):
    """Tabel warna pill dibaca dari AST sumber pygame (bukan salinan di sini).

    `pill()` menyimpan dict lokal `colors = {kind: (top, bot, edge, tcol)}`
    dengan beberapa nilai berupa konstanta modul (GOLD, SLATE, ...), jadi
    node Name diselesaikan ke atribut ui_theme.
    """
    src = inspect.getsource(ui_theme.pill)
    tree = ast.parse(src.lstrip())
    fn = tree.body[0]
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "colors"
                for t in node.targets):
            table = {}
            for key, value in zip(node.value.keys, node.value.values):
                kind = _node_value(key, ui_theme)
                table[kind] = [list(_node_value(v, ui_theme))
                               for v in value.elts]
            return table
    raise AssertionError("Tabel warna pill tidak ditemukan di ui_theme.pill")


def oracle_pill(pygame, ui_theme):
    out = {"table": _pill_table(ui_theme), "cases": []}
    font = FakeFont()
    for kind in sorted(out["table"]):
        for hover in (False, True):
            ui_theme.clear_caches()
            _set_cheap(ui_theme, True)
            btns = {}
            s = _screen()
            r = ui_theme.pill(s, btns, "k", "TEST", (120, 90, 170, 40),
                              kind, font, hover=hover)
            entry = {
                "kind": kind,
                "hover": hover,
                "rect": _rect(r),
                "btns": {k: _rect(v) for k, v in btns.items()},
                # kunci cache = warna gradasi PERSIS yang digambar
                "grad": _grad_keys(ui_theme),
            }
            entry["glow"] = _glow_keys(ui_theme)
            out["cases"].append(entry)
    # enabled=False: border 1px, teks TEXT_FAINT, dan TIDAK masuk btns.
    ui_theme.clear_caches()
    btns = {}
    s = _screen()
    r = ui_theme.pill(s, btns, "mati", "TEST", (120, 90, 170, 40), "gold",
                      font, enabled=False)
    out["disabled"] = {"rect": _rect(r), "btns": list(btns),
                       "input": [120, 90, 170, 40],
                       "border_px": _px(s, r.centerx, r.y)}
    return out


def oracle_toggle(pygame, ui_theme):
    cases = []
    font = FakeFont()
    for is_on in (True, False):
        for hover in (False, True):
            ui_theme.clear_caches()
            _set_cheap(ui_theme, True)
            btns = {}
            s = _screen()
            r = ui_theme.toggle(s, btns, "t", (200, 100, 60, 26), is_on, font,
                                hover=hover)
            cases.append({
                "is_on": is_on,
                "hover": hover,
                "rect": _rect(r),
                "btns": {k: _rect(v) for k, v in btns.items()},
                "grad": _grad_keys(ui_theme),
                "edge_px": _px(s, r.centerx, r.y + 1),
            })
    return {"cases": cases, "knob": 18}


def oracle_tab(pygame, ui_theme):
    cases = []
    font = FakeFont()
    accent = list(ui_theme.CYAN)
    for active in (True, False):
        for hover in (False, True):
            ui_theme.clear_caches()
            _set_cheap(ui_theme, True)
            btns = {}
            s = _screen()
            r = ui_theme.tab(s, btns, "tab", (100, 60, 180, 34), "STARTER",
                             tuple(accent), font, active, hover=hover)
            cases.append({
                "active": active,
                "hover": hover,
                "rect": _rect(r),
                "btns": {k: _rect(v) for k, v in btns.items()},
                "grad": _grad_keys(ui_theme),
                "border_px": _px(s, r.centerx, r.y + (1 if active else 0)),
                "underline_px": _px(s, r.centerx, r.bottom - 3) if active
                else None,
            })
    widths = [{"label": lab, "min_w": mw,
               "w": ui_theme.tab_width(font, lab, mw)}
              for lab, mw in (("STARTER", 150), ("A", 150), ("TRUE BOSS", 120))]
    return {"cases": cases, "tab_width": widths, "char_w": font.char_w}


def oracle_button(pygame, ui_theme):
    cases = []
    font = FakeFont()
    for hover in (False, True):
        for icon in (None, "play"):
            ui_theme.clear_caches()
            _set_cheap(ui_theme, True)
            btns = {}
            s = _screen()
            r = ui_theme.button(s, btns, "b", "MULAI GAME", 350, 170,
                                ui_theme.GOLD, font, w=300, h=50, icon=icon,
                                hover=hover)
            cases.append({
                "hover": hover,
                "icon": icon,
                "rect": _rect(r),
                "btns": {k: _rect(v) for k, v in btns.items()},
                "grad": _grad_keys(ui_theme),
                "glow": _glow_keys(ui_theme),
                "border_px": _px(s, r.x + (1 if hover else 0), r.y + 30),
            })
    # Pusat label: clamp pygame terhadap badge ikon & tepi kanan. Lebar teks
    # dikendalikan FakeFont (7 px/karakter) dan posisi blitNYA dibaca dari
    # piksel TEXT_WHITE di permukaan -> oracle pusat label tanpa menebak.
    # PENTING: `button()` default letter_gap=True, jadi lebar yang dimasukkan ke
    # oracle adalah lebar SETELAH letter() (persis yang diukur pygame).
    labels = []
    target = list(ui_theme.TEXT_WHITE)
    for chars, has_icon, gap, bw in ((10, False, True, 300),
                                     (10, True, True, 300),
                                     (30, True, True, 300),
                                     (60, True, True, 300),
                                     (130, True, True, 300),
                                     (40, False, True, 300),
                                     (30, True, False, 300),
                                     (10, True, False, 300),
                                     # Tombol sempit: badge mendorong label ke
                                     # kanan (clamp langkah-1 pygame).
                                     (4, True, True, 120),
                                     (10, True, True, 160),
                                     (20, True, True, 120),
                                     (4, False, True, 120)):
        ui_theme.clear_caches()
        _set_cheap(ui_theme, True)
        s = _screen()
        text = "X" * chars
        font = FakeFont()
        measured = font.size(ui_theme.letter(text) if gap else text)[0]
        btns = {}
        # Pusat label dibaca dari argumen `center=` yang DITERIMA draw_text,
        # bukan dari tengah blok piksel: teks yang lebih lebar dari permukaan
        # (700px) terpotong saat blit, jadi tengah pikselnya bukan tengah teks
        # (dulu menghasilkan 416.5 = text_w/2 untuk teks 60 karakter).
        captured = {}
        asli = ui_theme.draw_text

        def _spy(screen, font_, text_, color_, center=None, topleft=None,
                 shadow=True, offset=(2, 2)):
            captured["center"] = center
            return asli(screen, font_, text_, color_, center=center,
                        topleft=topleft, shadow=shadow, offset=offset)

        ui_theme.draw_text = _spy
        try:
            r = ui_theme.button(s, btns, "b", text, 350, 170, ui_theme.GOLD,
                                font, w=bw, h=50,
                                icon="play" if has_icon else None,
                                letter_gap=gap)
        finally:
            ui_theme.draw_text = asli
        if captured.get("center") is None:
            raise AssertionError("draw_text tidak menerima center= "
                                 "(chars=%d)" % chars)
        xs = [x for y in range(s.get_height()) for x in range(s.get_width())
              if _px(s, x, y) == target]
        if not xs:
            raise AssertionError("Teks tombol tidak ditemukan di permukaan "
                                 "(chars=%d icon=%s)" % (chars, has_icon))
        x0, x1 = min(xs), max(xs) + 1
        labels.append({"chars": chars, "text_w": measured, "w": bw,
                       "has_icon": has_icon, "letter_gap": gap,
                       "rect": _rect(r), "block": [x0, x1],
                       "clipped": bool(x0 <= 0 or x1 >= s.get_width()),
                       "center": float(captured["center"][0])})
    return {"cases": cases, "labels": labels, "char_w": 7}


def oracle_chip(pygame, ui_theme):
    cases = []
    font = FakeFont()
    for align in ("left", "right"):
        for icon in (None, "coin"):
            for value in (None, "1.234"):
                ui_theme.clear_caches()
                _set_cheap(ui_theme, True)
                s = _screen()
                r = ui_theme.chip(s, (300, 80), "HERO GOLD",
                                  ui_theme.GOLD, font, icon=icon,
                                  value=value, align=align)
                cases.append({
                    "align": align,
                    "icon": icon,
                    "value": value,
                    "label": "HERO GOLD",
                    "rect": _rect(r),
                    "text_w": font.size(ui_theme.letter("HERO GOLD"))[0],
                    "value_w": font.size(value)[0] if value else 0,
                    "grad": _grad_keys(ui_theme),
                })
    return {"cases": cases, "char_w": font.char_w, "height": 30}


def oracle_section_header(pygame, ui_theme):
    font = FakeFont()
    out = []
    for color in (ui_theme.CYAN, ui_theme.RED):
        ui_theme.clear_caches()
        _set_cheap(ui_theme, True)
        s = _screen()
        title = "AUDIO"
        next_y = ui_theme.section_header(s, 40, 60, title, "speaker", color,
                                         font, rule_w=240)
        tw = font.size(title)[0] + 28
        # Render kedua TANPA ikon (nama tak dikenal -> draw_icon no-op) supaya
        # rentang piksel garis tidak tercemar piksel ikon: ini mengunci
        # `tw = lebar_judul + 28` dan offset +14 / +26 secara persis.
        s2 = _screen()
        ui_theme.section_header(s2, 40, 60, title, "", color, font,
                                rule_w=240)
        # Baris garis aksen (y+14) BERIMPIT dengan teks letter-spaced yang
        # warnanya sama (quirk pygame: rule_w diukur dari judul TANPA
        # letter-spacing), jadi yang dikunci adalah UJUNG kanan garis =
        # x + title_w + 28 + 14 + rule_w.
        rule_xs = sorted({x for x, _ in _scan_color(
            s2, color, range(40, 660), [60 + 14])})
        dim_xs = sorted({x for x, _ in _scan_color(
            s2, ui_theme._dim(color), range(40, 660), [60 + 26])})
        if not rule_xs or not dim_xs:
            raise AssertionError("Garis section_header tidak terbaca oracle")
        out.append({
            "title": title,
            "color": list(color),
            "x": 40,
            "y": 60,
            "rule_w": 240,
            "title_w": font.size(title)[0],
            "next_y": next_y,
            "rule_px": _px(s, 40 + tw + 14 + 5, 60 + 14),
            "dim_px": _px(s, 40 + 30, 60 + 26),
            "dim_expected": list(ui_theme._dim(color)),
            "rule_end": rule_xs[-1] + 1,
            "dim_span": [dim_xs[0], dim_xs[-1] + 1],
        })
    return {"cases": out, "char_w": font.char_w}


def oracle_slider(pygame, ui_theme):
    cases = []
    for value in (0.0, 0.25, 0.5, 1.0, 1.7, -0.4):
        ui_theme.clear_caches()
        _set_cheap(ui_theme, True)
        s = _screen()
        kx = ui_theme.slider(s, 60, 120, 200, value)
        cases.append({
            "x": 60, "y": 120, "w": 200, "value": value, "knob_x": kx,
            "fill_w": int(200 * max(0.0, min(1.0, value))),
            "grad": _grad_keys(ui_theme),
            "track_px": _px(s, 255, 124) if value <= 0.0 else None,
        })
    ui_theme.clear_caches()
    _set_cheap(ui_theme, True)
    s = _screen()
    ui_theme.slider(s, 60, 120, 200, 0.5, knob_hover=True)
    return {"cases": cases, "glow": _glow_keys(ui_theme),
            "track_color": [34, 38, 58], "border_color": [120, 110, 86]}


def oracle_cycler(pygame, ui_theme):
    font_label = FakeFont()
    font_value = FakeFont()
    cases = []
    for value, width in (("1.0x", 340), ("TANPA BATAS", 340),
                         ("Bahasa Indonesia", 300), ("60 FPS", 500)):
        ui_theme.clear_caches()
        _set_cheap(ui_theme, True)
        btns = {}
        s = _screen()
        next_y = ui_theme.option_cycler(s, btns, "speed", "Game Speed", value,
                                        40, 80, width, font_label, font_value)
        prev = btns["speed_prev"]
        nxt = btns["speed_next"]
        box_x = prev.right + 6
        box_w = nxt.x - box_x - 6
        cases.append({
            "value": value,
            "x": 40, "y": 80, "width": width,
            "value_w": font_value.size(value)[0],
            "next_y": next_y,
            "prev": _rect(prev),
            "next": _rect(nxt),
            "box": [box_x, prev.y, box_w, prev.h],
            "grad": _grad_keys(ui_theme),
        })
    # hover chevron -> border kotak jadi EDGE_GOLD
    ui_theme.clear_caches()
    _set_cheap(ui_theme, True)
    btns = {}
    s = _screen()
    ui_theme.option_cycler(s, btns, "speed", "Game Speed", "1.0x", 40, 80,
                           340, font_label, font_value, hover="speed_next")
    hover_case = {"btns": {k: _rect(v) for k, v in btns.items()},
                  "grad": _grad_keys(ui_theme)}
    return {"cases": cases, "hover": hover_case, "char_w": font_value.char_w}


def oracle_scroll(pygame, ui_theme):
    cases = []
    for height, pos, maxs in ((300, 0, 400), (300, 200, 400), (300, 400, 400),
                              (200, 0, 0), (120, 30, 900)):
        ui_theme.clear_caches()
        # cheap_alpha False -> thumb digambar solid: posisi terbaca dari piksel
        _set_cheap(ui_theme, False)
        s = _screen()
        track = ui_theme.scroll_indicator(s, 500, 40, height, pos, maxs)
        gold = ui_theme.GOLD
        thumb_y, thumb_h = None, 0
        if maxs > 0:
            for y in range(40, 40 + height):
                if _px(s, 500 + 3, y) == list(gold):
                    if thumb_y is None:
                        thumb_y = y
                    thumb_h += 1
        cases.append({
            "x": 500, "y": 40, "height": height, "scroll_pos": pos,
            "max_scroll": maxs, "track": _rect(track),
            "thumb_y": thumb_y, "thumb_h": thumb_h,
        })
    ui_theme.clear_caches()
    _set_cheap(ui_theme, True)
    s = _screen()
    ui_theme.scroll_indicator(s, 500, 40, 300, 150, 400)
    return {"cases": cases, "grad": _grad_keys(ui_theme),
            "track_color": [28, 32, 52], "width": 6}


def oracle_bars(pygame, ui_theme):
    cases = []
    for ratio in (0.0, 0.02, 0.5, 1.0, 2.0):
        ui_theme.clear_caches()
        _set_cheap(ui_theme, True)
        s = _screen()
        ui_theme.hp_bar(s, 30, 30, 200, 14, ratio, color=ui_theme.GREEN)
        cases.append({"kind": "hp", "w": 200, "h": 14, "ratio": ratio,
                      "color": list(ui_theme.GREEN),
                      "fill_w": int(200 * max(0.0, min(1.0, ratio))),
                      "grad": _grad_keys(ui_theme)})
    for frac in (0.0, 0.25, 0.75, 1.0):
        ui_theme.clear_caches()
        _set_cheap(ui_theme, True)
        s = _screen()
        ui_theme.progress_bar(s, 30, 60, 160, frac, color=ui_theme.GOLD, h=8)
        cases.append({"kind": "progress", "w": 160, "h": 8, "ratio": frac,
                      "color": list(ui_theme.GOLD),
                      "fill_w": int(160 * max(0.0, min(1.0, frac))),
                      "grad": _grad_keys(ui_theme)})
    return {"cases": cases}


def oracle_panel(pygame, ui_theme):
    ui_theme.clear_caches()
    _set_cheap(ui_theme, True)
    s = _screen()
    ui_theme.panel(s, (50, 40, 300, 200))
    grad = _grad_keys(ui_theme)
    ui_theme.clear_caches()
    _set_cheap(ui_theme, False)
    s2 = _screen()
    ui_theme.panel(s2, (50, 40, 300, 200))
    solid_px = _px(s2, 200, 140)
    shadow_surf = ui_theme._shadow(300, 200, radius=12)
    return {"grad": grad, "solid_fill": solid_px,
            "shadow_size": list(shadow_surf.get_size()),
            "shadow_small": [max(4, 308 // 8), max(4, 208 // 8)]}


def oracle_gradient_text(pygame, ui_theme):
    ui_theme.clear_caches()
    ui_theme._GRAD_TEXT_CACHE.clear()
    _set_cheap(ui_theme, True)
    s = _screen()
    font = FakeFont()
    ui_theme.outline_text(s, font, "MYSTIC ARENA", None, (350, 100))
    keys = [[list(k[2]), list(k[3])] for k in ui_theme._GRAD_TEXT_CACHE]
    sig = inspect.signature(ui_theme.outline_text)
    # Warna per baris `gradient_text()` (FakeFont -> glif putih pekat, jadi
    # hasil BLEND_RGBA_MULT = warna gradasi baris itu). Mengunci rumus
    # `t = y / max(1, h - 1)` + truncation `int()` di sisi Godot.
    top, bottom = ui_theme.GOLD_BRIGHT, (196, 138, 40)
    surf = ui_theme.gradient_text(font, "MYSTIC ARENA", top, bottom)
    hh = surf.get_height()
    rows = [[surf.get_at((surf.get_width() // 2, y))[i] for i in range(3)]
            for y in range(hh)]
    return {"body": keys,
            "outline": list(sig.parameters["outline"].default),
            "outline_width": sig.parameters["width"].default,
            "text": "MYSTIC ARENA",
            "rows": rows,
            "row_top": list(top),
            "row_bottom": list(bottom)}


def _scan_color(surf, color, xs, ys):
    target = list(color)
    return [(x, y) for y in ys for x in xs if _px(surf, x, y) == target]


def _title_source_consts(ui_theme):
    """Konstanta posisi yang tidak terbaca dari piksel (glow alpha lembut)
    dibaca dari SUMBER pygame — bukan disalin manual di sini."""
    src = inspect.getsource(ui_theme.screen_title)
    glow = re.search(r"_radial\((\d+),\s*(\d+),\s*\(([^)]*)\),\s*(\d+)\)"
                     r",\s*\(cx\s*-\s*(\d+),\s*y\s*-\s*(\d+)\)", src)
    if not glow:
        raise AssertionError("Baris glow screen_title tidak dikenali oracle; "
                             "perbarui tools/test_godot_ui_theme_parity.py")
    fy = re.search(r"fy = y \+ (\d+)", src)
    if not fy:
        raise AssertionError("Baris `fy = y + N` screen_title tidak ditemukan")
    plate = re.search(r"plate = pygame\.Rect\(cx - \(sub_surf\.get_width\(\) "
                      r"\+ (\d+)\) // 2,\s*fy \+ (\d+),\s*"
                      r"sub_surf\.get_width\(\) \+ \d+,\s*(\d+)\)", src)
    if not plate:
        raise AssertionError("Baris plate subtitle screen_title tidak dikenali")
    return {
        "glow_offset": [-int(glow.group(5)), -int(glow.group(6))],
        "ornament_dy": int(fy.group(1)),
        "plate_pad": int(plate.group(1)),
        "plate_dy": int(plate.group(2)),
        "plate_h": int(plate.group(3)),
    }


def oracle_screen_title(pygame, ui_theme):
    ui_theme.clear_caches()
    _set_cheap(ui_theme, True)
    s = _screen(1400, 400)
    sub = "AUDIO & GAMEPLAY"
    cx, y = 700, 100
    ui_theme.screen_title(s, "PENGATURAN", cx, y, glow=True, sub=sub,
                          ornament=True)
    consts = _title_source_consts(ui_theme)
    fy = y + consts["ornament_dy"]

    # Garis ornamen EDGE_GOLD (lebar 2 -> scan beberapa baris di sekitar fy).
    line_pts = _scan_color(s, ui_theme.EDGE_GOLD, range(cx - 300, cx + 300),
                           range(fy - 3, fy + 4))
    if not line_pts:
        raise AssertionError("Garis ornamen screen_title tidak ditemukan")
    left_xs = sorted({x for x, _ in line_pts if x < cx})
    right_xs = sorted({x for x, _ in line_pts if x > cx})
    # Dot GOLD_BRIGHT r=3 di kedua ujung.
    dot_pts = _scan_color(s, ui_theme.GOLD_BRIGHT, range(cx - 300, cx + 300),
                          range(fy - 6, fy + 7))
    dot_xs = sorted({x for x, _ in dot_pts})
    # Wajik GOLD: rentang horizontal di baris fy, vertikal di kolom cx.
    gem_row = _scan_color(s, ui_theme.GOLD, range(cx - 20, cx + 20), [fy])
    gem_col = _scan_color(s, ui_theme.GOLD, [cx], range(fy - 12, fy + 13))
    # Plate subtitle: border EDGE_GOLD di sisi kiri/kanan (baris tengah plate,
    # jauh dari radius sudut) -> rect plate terbaca persis.
    plate_y = fy + consts["plate_dy"]
    mid_rows = range(plate_y + consts["plate_h"] // 2 - 3,
                     plate_y + consts["plate_h"] // 2 + 4)
    plate_pts = _scan_color(s, ui_theme.EDGE_GOLD, range(cx - 400, cx + 400),
                            mid_rows)
    plate_xs = sorted({x for x, _ in plate_pts})
    sub_w = FakeFont().size(ui_theme.letter(sub))[0]

    return {
        "cx": cx, "y": y, "sub": sub, "sub_w": sub_w,
        "ornament_y": fy,
        "glow": _glow_keys(ui_theme),
        "grad": _grad_keys(ui_theme),
        "consts": consts,
        "derived": {
            "line_left": cx - left_xs[0],
            "line_inner": cx - left_xs[-1],
            "dot": cx - (dot_xs[0] + 3),
            "gem_dx": gem_row[-1][0] - cx,
            "gem_dy": fy - gem_col[0][1],
            "plate_w": plate_xs[-1] + 1 - plate_xs[0],
            "plate_x": plate_xs[0],
            "plate_y": plate_y - y,
        },
    }


def oracle_math(pygame, ui_theme):
    vgrad = []
    for top, bottom, h in ((ui_theme.PANEL_TOP, ui_theme.PANEL_BOTTOM, 9),
                           (ui_theme.GOLD_BRIGHT, (196, 138, 40), 8),
                           ((255, 255, 255), (0, 0, 0), 5)):
        ui_theme.clear_caches()
        surf = ui_theme._vgrad(4, h, top, bottom)
        vgrad.append({"top": list(top), "bottom": list(bottom), "h": h,
                      "rows": [_px(surf, 0, y) for y in range(h)]})
    radial = []
    for w, h, color, alpha in ((42, 22, ui_theme.GOLD, 74),
                               (36, 36, ui_theme.GOLD, 80),
                               (620, 150, (255, 205, 90), 46)):
        ui_theme.clear_caches()
        surf = ui_theme._radial(w, h, color, alpha)
        samples = []
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                a = surf.get_at((x, y))[3]
                if a or (x == 0 and y == 0):
                    samples.append({"x": x, "y": y, "a": a})
                if len(samples) >= 40:
                    break
            if len(samples) >= 40:
                break
        radial.append({"w": w, "h": h, "color": list(color), "alpha": alpha,
                       "alpha_key": max(4, min(120, int(alpha) // 8 * 8)),
                       "samples": samples})
    shadow = []
    for w, h, radius, alpha, spread in ((100, 50, 12, 110, 4),
                                        (300, 200, 12, 110, 4),
                                        (60, 26, 7, 90, 3)):
        surf = ui_theme._shadow(w, h, radius=radius, alpha=alpha,
                                spread=spread)
        sw, sh = surf.get_size()
        shadow.append({"w": w, "h": h, "radius": radius, "alpha": alpha,
                       "spread": spread, "size": [sw, sh],
                       "small": [max(4, sw // 8), max(4, sh // 8)]})
    dim = [{"color": list(c), "f": f, "out": list(ui_theme._dim(c, f))}
           for c, f in ((ui_theme.GOLD, 0.55), (ui_theme.CYAN, 0.55),
                        (ui_theme.RED, 0.35), ((255, 255, 255), 0.55))]
    letter = [{"text": t, "gap": g, "out": ui_theme.letter(t, g)}
              for t, g in (("MULAI GAME", " "), ("ON", " "), ("A", " "),
                           ("BACK", ""), ("ID", "·"))]
    hyp = [{"x": x, "y": y, "out": ui_theme.math_hyp(x, y)}
           for x, y in ((3, 4), (0, 0), (20.5, 10.5))]
    ellipsis = []
    for text, max_w in (("MULAI GAME", 1000), ("MULAI GAME", 60),
                        ("MULAI GAME", 30), ("MULAI GAME", 8),
                        ("AB", 8)):
        ellipsis.append({"text": text, "max_w": max_w,
                         "out": ui_theme.fit_ellipsis(FakeFont(), text, max_w),
                         "char_w": 7})
    return {"vgrad": vgrad, "radial": radial, "shadow": shadow, "dim": dim,
            "letter": letter, "hyp": hyp, "ellipsis": ellipsis}


def oracle_back_button(pygame, ui_theme):
    ui_theme.clear_caches()
    _set_cheap(ui_theme, True)
    btns = {}
    s = _screen()
    r = ui_theme.back_button(s, btns, "back", 640, 600)
    hover_btns = {}
    s2 = _screen()
    r2 = ui_theme.back_button(s2, hover_btns, "back", 640, 600, hover=True)
    return {"rect": _rect(r), "btns": {k: _rect(v) for k, v in btns.items()},
            "hover_rect": _rect(r2),
            "hover_btns": {k: _rect(v) for k, v in hover_btns.items()}}


def build_oracle():
    pygame, ui_theme = _load_pygame()
    if ui_theme is None:
        return None
    fx = {
        "meta": {
            "source": "ui_theme.py",
            "generated_by": "tools/test_godot_ui_theme_parity.py",
            "note": "Oracle = modul pygame ASLI (SDL dummy). Metrik teks "
                    "memakai FakeFont 7px/karakter supaya geometri tidak "
                    "bergantung font engine.",
        },
        "math": oracle_math(pygame, ui_theme),
        "panel": oracle_panel(pygame, ui_theme),
        "button": oracle_button(pygame, ui_theme),
        "pill": oracle_pill(pygame, ui_theme),
        "chip": oracle_chip(pygame, ui_theme),
        "section_header": oracle_section_header(pygame, ui_theme),
        "toggle": oracle_toggle(pygame, ui_theme),
        "slider": oracle_slider(pygame, ui_theme),
        "cycler": oracle_cycler(pygame, ui_theme),
        "tab": oracle_tab(pygame, ui_theme),
        "screen_title": oracle_screen_title(pygame, ui_theme),
        "back_button": oracle_back_button(pygame, ui_theme),
        "scroll": oracle_scroll(pygame, ui_theme),
        "bars": oracle_bars(pygame, ui_theme),
        "gradient_text": oracle_gradient_text(pygame, ui_theme),
        "palette_live": {k: list(getattr(ui_theme, k))
                         for k in sorted(_py_palette(_read(ROOT / "ui_theme.py")))},
        "icons": _py_icon_names(_read(ROOT / "ui_theme.py")),
    }
    return fx


# ══════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-fixture", action="store_true",
                        help="tulis ulang godot/tests/fixtures/ui_theme.json")
    args = parser.parse_args()

    py_src = _read(ROOT / "ui_theme.py")
    palette = check_palette(py_src)
    check_coverage()
    icons = check_icons()
    check_literals()

    fixture = build_oracle()
    if fixture is None:
        # Tanpa pygame: cek statis sudah jalan; fixture tidak bisa diverifikasi.
        if not FIXTURE.exists():
            raise AssertionError("Fixture hilang: %s" % FIXTURE.relative_to(ROOT))
        stored = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if sorted(stored["icons"]) != icons:
            raise AssertionError("Fixture ui_theme.json tidak sinkron dengan "
                                 "daftar ikon ui_theme.py")
        if {k: list(v) for k, v in stored["palette_live"].items()} != \
                {k: list(v) for k, v in palette.items()}:
            raise AssertionError("Fixture ui_theme.json tidak sinkron dengan "
                                 "palet ui_theme.py")
        check_test_wiring(stored)
        print("[oracle] pygame tidak ada — fixture diverifikasi terhadap "
              "palet + ikon ui_theme.py saja")
        print("UI theme parity: OK (statik)")
        return 0

    # Palet hasil baca atribut modul harus sama dengan hasil parse sumber.
    if {k: tuple(v) for k, v in fixture["palette_live"].items()} != palette:
        raise AssertionError("Palet dari atribut modul != palet dari sumber")

    check_test_wiring(fixture)

    payload = json.dumps(fixture, indent=2, ensure_ascii=False,
                         sort_keys=True) + "\n"
    if args.write_fixture:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(payload, encoding="utf-8")
        print("[oracle] fixture ditulis: %s (%d seksi, %d kasus pill, "
              "%d kasus button, %d chip, %d cycler)"
              % (FIXTURE.relative_to(ROOT), len(fixture),
                 len(fixture["pill"]["cases"]),
                 len(fixture["button"]["cases"]),
                 len(fixture["chip"]["cases"]),
                 len(fixture["cycler"]["cases"])))
        return 0

    if not FIXTURE.exists():
        raise AssertionError(
            "Fixture hilang: %s — jalankan `python3 tools/%s --write-fixture`"
            % (FIXTURE.relative_to(ROOT), Path(__file__).name))
    current = FIXTURE.read_text(encoding="utf-8")
    if current != payload:
        stored = json.loads(current)
        stale = [s for s in fixture if s != "meta"
                 and stored.get(s) != fixture[s]]
        raise AssertionError(
            "Fixture ui_theme.json BASI terhadap ui_theme.py (seksi: %s) — "
            "regenerasi: python3 tools/%s --write-fixture"
            % (", ".join(stale) or "format/urutan", Path(__file__).name))
    print("[oracle] fixture segar: %d seksi, %d warna palet, %d ikon, "
          "%d kasus pill, %d kasus button, %d chip, %d cycler, %d scroll"
          % (len(fixture), len(fixture["palette_live"]), len(fixture["icons"]),
             len(fixture["pill"]["cases"]), len(fixture["button"]["cases"]),
             len(fixture["chip"]["cases"]), len(fixture["cycler"]["cases"]),
             len(fixture["scroll"]["cases"])))
    print("UI theme parity: OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print("FAIL: %s" % exc)
        sys.exit(1)
