#!/usr/bin/env python3
"""Transpile ui_components/_bundle.py -> C++ GDExtension (godot++).

    python3 tools/gen_ui_cpp.py           # regenerasi
    python3 tools/gen_ui_cpp.py --check   # CI: berkas ter-commit harus identik

Bagian dari migrasi `ui_components/` -> godot++ (FASE 36). Pola sama dengan
`tools/gen_maps_cpp.py` (map_components -> MysticMaps):

  * DATA (ukuran panel, kartu menara, tab toko, nama castle, label) diekstrak
    dari AST `_bundle.py` — bukan disalin tangan. Generator MENOLAK (bukan
    menebak) kalau literal/ekspresi yang dibutuhkan hilang atau berubah
    bentuk, jadi angka C++ tidak bisa basi tanpa CI merah.
  * LOGIKA (geometri + state + label) di-emit di sini dengan rujukan baris
    Python; kebenarannya dikunci oracle `tools/test_godot_ui_components_parity.py`
    (menjalankan draw pygame ASLI lewat surface spy) + self-test C++ tanpa
    engine `tools/test_ui_cpp_selftest.py`.

Yang dibangkitkan:

  godot/gdext/mystic_ui/src/ui_processor.h
  godot/gdext/mystic_ui/src/ui_processor.cpp

Cakupan: SELURUH 11 submodul ui_components (base_ui, hero_portraits,
build_popup, build_slots, hero_panel, hero_shop, hover_indicators,
notification, overlay, popup_renderer, shop_hints) — lapisan LAYOUT + STATE +
LABEL. Yang SENGAJA tidak diport: piksel (pygame.draw, Surface, cache
tekstur, RNG partikel) dan METRIK FONT; lebar/tinggi teks diterima sebagai
parameter supaya kedua backend memakai angka identik tanpa bergantung font
engine (pola sama dengan oracle ui_theme FASE 31 yang memakai font palsu).

Konvensi angka:
  * int64_t untuk koordinat/ukuran (pygame Rect int) — pembagian memakai `/`
    C++ yang memotong ke arah nol, SAMA dengan `//` Python untuk nilai >= 0
    (semua input di sini non-negatif setelah clamp; kasus negatif dikunci
    oracle).
  * double hanya untuk rasio (HP, cooldown, scroll) — ekspresi diteruskan
    verbatim dari sumber supaya round-off-nya identik.
  * `py_round` = round-half-even CPython; `thousands` = f"{v:,}".
"""
import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "ui_components" / "_bundle.py"
SETTINGS_SRC = ROOT / "_core.py"          # settings.py digabung ke sini
THEME_SRC = ROOT / "ui_theme.py"
OUT_H = ROOT / "godot" / "gdext" / "mystic_ui" / "src" / "ui_processor.h"
OUT_CPP = ROOT / "godot" / "gdext" / "mystic_ui" / "src" / "ui_processor.cpp"
OUT_DISPATCH = (ROOT / "godot" / "gdext" / "mystic_ui" / "selftest"
                / "ui_dispatch.inc")

CLASS = "MysticUI"
LIBRARY = "mystic_ui"

MODULES = [
    "base_ui", "hero_portraits", "build_popup", "build_slots", "hero_panel",
    "hero_shop", "hover_indicators", "notification", "overlay",
    "popup_renderer", "shop_hints",
]


class UiError(Exception):
    """Data ui_components/_bundle.py tidak memenuhi kontrak generator."""


def require(cond, message):
    if not cond:
        raise UiError(message)


# ══════════════════════════════════════════════════════════
#  AST helpers
# ══════════════════════════════════════════════════════════


def parse_bundle():
    source = SRC.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(SRC)), source


def ns_class(tree, name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "_NS_" + name:
            return node
    raise UiError("_NS_%s tidak ditemukan di %s" % (name, SRC.name))


def top_class(tree, name):
    """Class level modul (base_ui TIDAK dibungkus `_NS_base_ui` di bundle)."""
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise UiError("class level modul %s tidak ditemukan di %s"
                  % (name, SRC.name))


def inner_class(ns_node, name):
    for node in ns_node.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise UiError("class %s tidak ditemukan di %s" % (name, ns_node.name))


def method(class_node, name):
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise UiError("method %s.%s tidak ditemukan" % (class_node.name, name))


def fn_src(fn_node):
    return ast.unparse(fn_node)


def assigns(fn_node):
    out = {}
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue
            out.setdefault(node.targets[0].id, (value, node.lineno))
    return out


def literal(fn_node, target, where):
    table = assigns(fn_node)
    require(target in table,
            "%s: literal `%s = ...` tidak ditemukan (generator menolak "
            "menebak)" % (where, target))
    return table[target]


def dict_literal(fn_node, key, where):
    """Nilai literal sebuah kunci dict di badan method (mis. `'timer': 180`)."""
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == key:
                    try:
                        return ast.literal_eval(v), node.lineno
                    except (ValueError, SyntaxError) as exc:
                        raise UiError(
                            "%s: nilai dict `%s` bukan literal (%s)"
                            % (where, key, exc)) from exc
    raise UiError("%s: kunci dict `%s` tidak ditemukan" % (where, key))


def attr_literal(fn_node, attr, where):
    """Nilai literal `self.<attr> = ...` di badan method."""
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Attribute) \
                and node.targets[0].attr == attr:
            try:
                return ast.literal_eval(node.value), node.lineno
            except (ValueError, SyntaxError) as exc:
                raise UiError(
                    "%s: self.%s bukan literal (%s)" % (where, attr, exc)
                ) from exc
    raise UiError("%s: self.%s tidak ditemukan" % (where, attr))


def arg_default(fn_node, arg_name, where):
    args = fn_node.args
    names = [a.arg for a in args.args] + [a.arg for a in args.kwonlyargs]
    defaults = list(args.defaults) + [d for d in args.kw_defaults if d]
    require(len(defaults) <= len(names),
            "%s: bentuk signature tidak didukung generator" % where)
    # default Python menempel pada argumen TERAKHIR
    for name, default in zip(names[len(names) - len(defaults):], defaults):
        if name == arg_name:
            return ast.literal_eval(default), fn_node.lineno
    raise UiError("%s: argumen `%s` tanpa default" % (where, arg_name))


def module_literals(path, names, where):
    """Ambil konstanta literal level-modul dari berkas (gagal kalau bukan
    literal murni — generator tidak menghitung ekspresi)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            nid = node.targets[0].id
            if nid in names:
                try:
                    found[nid] = ast.literal_eval(node.value)
                except (ValueError, SyntaxError) as exc:
                    raise UiError(
                        "%s: %s bukan literal murni (%s) — generator menolak "
                        "menghitung ekspresi" % (where, nid, exc)) from exc
    missing = [n for n in names if n not in found]
    require(not missing,
            "%s: konstanta %s tidak ditemukan" % (where, ", ".join(missing)))
    return found


def extract_tower_cards(fn_node, colors_table):
    """tower_types = [('archer', 'Archer', 'Fast single',
    TOWER_TYPE_COLORS['archer']['main']), ...] — warna diambil dari tabel
    settings, bukan disalin."""
    import re as _re
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == "tower_types" \
                and isinstance(node.value, ast.List):
            rows = []
            for elt in node.value.elts:
                require(isinstance(elt, ast.Tuple) and len(elt.elts) == 4,
                        "BuildPopup._draw_tower_buttons: kartu bukan 4-tuple")
                ttype = ast.literal_eval(elt.elts[0])
                name = ast.literal_eval(elt.elts[1])
                desc = ast.literal_eval(elt.elts[2])
                expr = ast.unparse(elt.elts[3])
                match = _re.match(
                    r"TOWER_TYPE_COLORS\['([a-z_]+)'\]\['(main|dark)'\]$",
                    expr)
                require(match,
                        "BuildPopup._draw_tower_buttons: warna kartu `%s` "
                        "bukan acuan TOWER_TYPE_COLORS[...]" % expr)
                color = colors_table[match.group(1)][match.group(2)]
                rows.append((ttype, name, desc, color))
            return rows, node.lineno
    raise UiError("BuildPopup._draw_tower_buttons: `tower_types` tidak "
                  "ditemukan")


def _norm_ws(text):
    """Normalisasi pembanding: whitespace runtuh + kutip disamakan (ast.unparse
    menormalkan f-string ke kutip tunggal)."""
    import re as _re
    return _re.sub(r"\s+", " ", text).replace('"', "'")


def need(text, needles, where):
    norm = _norm_ws(text)
    missing = [n for n in needles if _norm_ws(n) not in norm]
    require(not missing,
            "%s: ekspresi %s hilang — generator menolak (layout berubah?)"
            % (where, " / ".join("`%s`" % m for m in missing)))


# ══════════════════════════════════════════════════════════
#  Spesifikasi angka dari AST
# ══════════════════════════════════════════════════════════


class Spec:
    def __init__(self):
        self.values = {}
        self.lines = {}

    def take(self, key, value, line):
        self.values[key] = value
        self.lines[key] = line
        return value

    def lit(self, key, ns, cls, fn, target):
        node = method(inner_class(ns_class(self.tree, ns), cls), fn)
        value, line = literal(node, target, "%s.%s" % (cls, fn))
        return self.take(key, value, line)

    def __getitem__(self, key):
        require(key in self.values, "spesifikasi `%s` belum diekstrak" % key)
        return self.values[key]

    def line(self, key):
        return self.lines.get(key, 0)


def build_spec():
    tree, source = parse_bundle()
    spec = Spec()
    spec.tree = tree
    spec.source = source

    # ── base_ui ────────────────────────────────────────────────
    base = top_class(tree, "BaseUIComponent")
    close = method(base, "_draw_close_button")
    size, cline = arg_default(close, "size",
                              "BaseUIComponent._draw_close_button")
    spec.take("close_size", size, cline)
    need(fn_src(close), ["get_font(28", "pygame.Rect(x, y, size, size)"],
         "BaseUIComponent._draw_close_button")
    hp = method(base, "_draw_hp_bar")
    need(fn_src(hp), ["hp_ratio > 0.5", "hp_ratio > 0.25"],
         "BaseUIComponent._draw_hp_bar")
    spec.take("hp_thresholds", (0.5, 0.25), hp.lineno)

    # ── hero_portraits ─────────────────────────────────────────
    hp_cls_src = fn_src(inner_class(ns_class(tree, "hero_portraits"),
                                    "HeroPortraits"))
    need(hp_cls_src, ["for sy in range(0, ch, 2)",
                      "if pixel[3] > 10:",
                      "min_x = max(0, min_x - pad)",
                      "scale = min(scale_x, scale_y, 1.0)",
                      "new_w = max(1, int(crop_w * scale))",
                      "arr[:, :, 0] * 0.299",
                      "arr[:, :, 2] * 0.114"],
         "HeroPortraits")
    spec.take("portrait_scan_step", 2,
              method(inner_class(ns_class(tree, "hero_portraits"),
                                 "HeroPortraits"), "_crop_and_scale").lineno)
    spec.take("portrait_alpha_min", 10,
              method(inner_class(ns_class(tree, "hero_portraits"),
                                 "HeroPortraits"), "_crop_and_scale").lineno)
    spec.take("portrait_pad", 4, 0)
    spec.take("portrait_target", (60, 70), 0)
    spec.take("gray_weights", (0.299, 0.587, 0.114), 0)

    # ── build_popup ────────────────────────────────────────────
    bp = inner_class(ns_class(tree, "build_popup"), "BuildPopup")
    spec.lit("build_popup_w", "build_popup", "BuildPopup", "draw", "popup_w")
    spec.lit("build_popup_h", "build_popup", "BuildPopup", "draw", "popup_h")
    bdraw = method(bp, "draw")
    need(fn_src(bdraw), ["px = int(slot['x']) - popup_w // 2",
                         "py = int(slot['y']) - popup_h - 30",
                         "px = SCREEN_WIDTH - popup_w - 10",
                         "py = int(slot['y']) + 30",
                         "py = SCREEN_HEIGHT - popup_h - 10",
                         "popup_w = min(popup_w, max(1, _panel.width - 16))"],
         "BuildPopup.draw")
    btns = method(bp, "_draw_tower_buttons")
    settings = module_literals(SETTINGS_SRC, {
        "TOWER_TYPE_COLORS", "GOLD", "WHITE", "GRAY", "GREEN", "YELLOW",
        "RED", "BLUE_LIGHT", "RED_LIGHT", "TOP_BAR_HEIGHT",
        "TOWER_REGEN_SHIELD_MIN_LEVEL", "MAX_HEROES_OWNED", "MAX_HERO_LEVEL",
        "SCREEN_WIDTH", "SCREEN_HEIGHT"}, "_core.py (settings)")
    spec.take("settings", settings, 0)
    theme = module_literals(THEME_SRC, {
        "GOLD_TEXT", "TEXT_BODY", "TEXT_DIM", "CYAN_SOFT"}, "ui_theme.py")
    spec.take("theme", theme, 0)
    cards, cardline = extract_tower_cards(btns, settings["TOWER_TYPE_COLORS"])
    spec.take("tower_cards", cards, cardline)
    spec.lit("build_cost", "build_popup", "BuildPopup", "_draw_tower_buttons",
             "cost")
    spec.lit("build_btn_h", "build_popup", "BuildPopup", "_draw_tower_buttons",
             "btn_h")
    need(fn_src(btns), ["btn_w = (popup_w - 50) // 2", "start_y = py + 62",
                        "bx = px + 15 + col * (btn_w + 12)",
                        "by = start_y + row * (btn_h + 10)"],
         "BuildPopup._draw_tower_buttons")

    # ── build_slots ────────────────────────────────────────────
    bs = inner_class(ns_class(tree, "build_slots"), "BuildSlots")
    need(fn_src(bs), ["pygame.Surface((40, 38)", "(sx - 20, sy - 17)",
                      "cost_bg = pygame.Rect(sx - 18, sy + 18, 36, 14)",
                      "pulse = math.sin(g.animation_time * 0.08) * 2",
                      "pk = int(round(pulse))"],
         "_NS_build_slots.BuildSlots")
    spec.take("slot_surface", (40, 38), method(bs, "draw").lineno)
    spec.take("slot_blit", (-20, -17), method(bs, "draw").lineno)
    spec.take("slot_cost", (18, 18, 36, 14),
              method(bs, "_draw_blue_slot").lineno)

    # ── hero_panel ─────────────────────────────────────────────
    hp_cls = inner_class(ns_class(tree, "hero_panel"), "HeroPanel")
    spec.lit("hero_panel_w", "hero_panel", "HeroPanel", "draw", "panel_w")
    spec.lit("hero_panel_h", "hero_panel", "HeroPanel", "draw", "panel_h")
    spec.lit("hero_panel_x", "hero_panel", "HeroPanel", "draw", "px")
    hp_draw = method(hp_cls, "draw")
    need(fn_src(hp_draw), [
        "y = py + 34", "bar_w = panel_w - 24", "y += 32",
        "skill_size = 38", "skill_gap = 10", "start_x = px + 14",
        "y += skill_size + 14", "y += 30", "y += 38", "y += 28",
        "py = SCREEN_HEIGHT - panel_h - 20", "px + panel_w - 26, py + 6"],
        "HeroPanel.draw")
    slot = method(hp_cls, "_draw_skill_slot")
    need(fn_src(slot), [
        "fsize = 14 if len(label) <= 2 else 12 if len(label) <= 4 else 10",
        "kw = kf.size(label)[0] + 6",
        "badge = pygame.Rect(x + size - kw - 2, y + size - 13, kw, 11)",
        "pygame.draw.rect(surface, (10, 12, 22), badge, border_radius=3)",
        "cd_seconds = cooldown // 60 + 1",
        "cd_height = int(size * cd_ratio)"],
        "HeroPanel._draw_skill_slot")
    need(fn_src(method(hp_cls, "_draw_item_shop_button")),
         ['f"ITEM FORGE  ({used}/{MAX_ITEM_SLOTS})"',
          "rect = pygame.Rect(px + 10, y, panel_w - 20, 22)"],
         "HeroPanel._draw_item_shop_button")
    need(fn_src(method(hp_cls, "_draw_upgrade_button")),
         ['f"UPGRADE HERO ({cost}G)"', 'ui_theme.letter("MAX LEVEL")',
          "rect = pygame.Rect(px + 10, y, panel_w - 20, 22)"],
         "HeroPanel._draw_upgrade_button")
    need(fn_src(method(hp_cls, "_draw_autocast_toggle")),
         ['"AUTO-CAST ON" if is_auto else "AUTO-CAST OFF"'],
         "HeroPanel._draw_autocast_toggle")
    spec.take("hero_close_inset", 26, hp_draw.lineno)
    spec.take("hero_skill", (38, 10), hp_draw.lineno)

    # ── hero_shop ──────────────────────────────────────────────
    shop = inner_class(ns_class(tree, "hero_shop"), "HeroShop")
    spec.lit("shop_panel_w", "hero_shop", "HeroShop", "_render_shop", "panel_w")
    spec.lit("shop_panel_h", "hero_shop", "HeroShop", "_render_shop", "panel_h")
    spec.lit("shop_header_h", "hero_shop", "HeroShop", "_render_shop",
             "header_h")
    cards_fn = method(shop, "_draw_hero_cards")
    tabs, tabline = literal(cards_fn, "tabs", "HeroShop._draw_hero_cards")
    require(all(len(row) == 3 for row in tabs),
            "HeroShop._draw_hero_cards: tab bukan 3-tuple (id, label, warna)")
    spec.take("shop_tabs", tabs, tabline)
    for key, target in [("shop_tab_w", "tab_w"), ("shop_tab_h", "tab_h"),
                        ("shop_card_w", "card_w"), ("shop_card_h", "card_h"),
                        ("shop_per_row", "cards_per_row"),
                        ("shop_gap_x", "gap_x"), ("shop_gap_y", "gap_y")]:
        spec.lit(key, "hero_shop", "HeroShop", "_draw_hero_cards", target)
    need(fn_src(cards_fn), [
        "total_tab_w = tab_w * len(tabs) + 10",
        "tab_start_x = panel_x + (panel_w - total_tab_w) // 2",
        "tab_y = panel_y + header_h + 10",
        "content_top = tab_y + tab_h + 10",
        "content_bottom = panel_y + 700 - 20",
        "total_width = card_w * cards_per_row + gap_x",
        "start_x = panel_x + (panel_w - total_width) // 2",
        "total_rows = (len(hero_list) + cards_per_row - 1) // cards_per_row",
        "total_content_h = total_rows * (card_h + gap_y)",
        "max_scroll = max(0, total_content_h - content_height)",
        "if cy + card_h < content_top or cy > content_bottom",
        "scroll_up_rect = pygame.Rect("],
        "HeroShop._draw_hero_cards")
    compact = method(shop, "_draw_compact_card")
    need(fn_src(compact), [
        'cost = stats.get("cost", 400)', "portrait_size = 60",
        "portrait_x = cx + 10", "portrait_y = cy + (ch - portrait_size) // 2",
        "info_x = cx + 10 + portrait_size + 12", "info_y = cy + 10",
        "stats_y = info_y + 68", "sx = info_x + j * 56",
        "btn_w = 90", "btn_h = 30", "btn_x = cx + cw - btn_w - 12",
        "btn_y = cy + (ch - btn_h) // 2"],
        "HeroShop._draw_compact_card")
    need(fn_src(method(shop, "_draw_scroll_indicator")),
         ["thumb_ratio = height / (height + max_scroll)",
          "thumb_h = max(20, int(height * thumb_ratio))",
          "thumb_y = y + int((height - thumb_h) *"],
         "HeroShop._draw_scroll_indicator")
    need(fn_src(shop), ['g.ui_buttons[f\'shop_buy_{hero_type}\'] = btn_rect',
                        '"shop_scroll_up"', '"shop_scroll_down"',
                        'msg = "No boss heroes unlocked yet"',
                        'hint = "Defeat bosses to unlock their hero!"',
                        'msg = "No starter heroes unlocked"',
                        'hint = "Visit Hero Shop from Main Menu!"'],
         "HeroShop")
    spec.take("shop_portrait", 60, compact.lineno)
    spec.take("shop_btn", (90, 30), compact.lineno)
    spec.take("shop_cost_default", 400, compact.lineno)

    # ── hover_indicators ───────────────────────────────────────
    hi = inner_class(ns_class(tree, "hover_indicators"), "HoverIndicators")
    upd = method(hi, "update")
    need(fn_src(upd), ["if g.shop_open or g.popup_target or g.build_popup_slot",
                       "dist <= 25", "dist <= 20", "if slot['taken']:"],
         "HoverIndicators.update")
    need(fn_src(method(hi, "_draw_tower_tooltip")),
         ['f"{tower.name} Lv.{tower.level}"',
          'f"DMG: {tower.damage}  RNG: {tower.range}"',
          'f"Kills: {tower.kills}"', "tooltip_x = int(tower.x)",
          "tooltip_y = int(tower.y - 60)", "bg_x = tooltip_x - bg_w // 2",
          "bg_y = tooltip_y - bg_h", "shadow = pygame.Surface((bg_w + 4, bg_h + 4",
          "total_height += surf.get_height() + 2"],
         "HoverIndicators._draw_tower_tooltip")
    need(fn_src(method(hi, "_draw_slot_hover")),
         ['"TAP TO BUILD"',
          "hint_bg = pygame.Rect(slot['x'] - 50, slot['y'] - 36, 100, 18)",
          "glow_surf = pygame.Surface((80, 80)"],
         "HoverIndicators._draw_slot_hover")
    spec.take("hover_tower_r", 25, upd.lineno)
    spec.take("hover_slot_r", 20, upd.lineno)

    # ── notification ───────────────────────────────────────────
    nt = inner_class(ns_class(tree, "notification"), "Notification")
    timer, nline = dict_literal(method(nt, "add_notification"), "timer",
                                "Notification.add_notification")
    spec.take("notification_timer", timer, nline)

    # ── overlay ────────────────────────────────────────────────
    ov = inner_class(ns_class(tree, "overlay"), "Overlay")
    delay, delay_line = attr_literal(
        method(ov, "__init__"), "unlock_popup_delay",
        "Overlay.__init__")
    spec.take("unlock_delay", delay, delay_line)
    need(fn_src(ov), [
        "slide_duration = 30", "eased = 1 - (1 - slide_progress) ** 3",
        "offset_x = int((1 - eased) * 400)",
        "alpha = min(255, int(255 * (elapsed_after_delay / 15)))",
        "popup_w = 340", "popup_h = 220", "popup_x = cx + 220 + offset_x",
        "popup_y = cy - 100", "panel_w = 500",
        "panel_h = len(stats) * 38 + 24", "panel_x = cx - panel_w // 2",
        "panel_y = cy - 100", "y = panel_y + 15 + i * 32", "badge_w = 118",
        "badge_h = 22", "badge_x = panel_x + panel_w // 2 - 30",
        "badge_y = y - 3", "ach_y = cy + 250",
        "total_w = 26 + ach_text.get_width()",
        "if next_lvl not in completed:", "if current_lvl in completed:"],
        "Overlay")
    spec.take("overlay_unlock", (340, 220, 220, 100, 30, 15, 400), ov.lineno)
    spec.take("overlay_stats", (500, 38, 24, 15, 32, 118, 22, 30, 3), ov.lineno)

    # ── popup_renderer ─────────────────────────────────────────
    pr = inner_class(ns_class(tree, "popup_renderer"), "PopupRenderer")
    spec.lit("popup_w", "popup_renderer", "PopupRenderer", "draw", "popup_w")
    spec.lit("popup_h", "popup_renderer", "PopupRenderer", "draw", "popup_h")
    need(fn_src(pr), [
        "px = int(target.x) - popup_w // 2",
        "py = int(target.y) - popup_h - 40", "if py < TOP_BAR_HEIGHT + 10:",
        "py = SCREEN_HEIGHT - popup_h - 10", "castle_names = {",
        "btn_w = (popup_w - 46) // 2", "btn_h = 68", "btn_h = 40",
        'paths = ["archer", "cannon", "ice", "mage"]',
        "sell_rect = pygame.Rect(px + (popup_w - 150) // 2, y,",
        "sell_rect = pygame.Rect(px + 27 + btn_w, y, btn_w, btn_h)",
        '"CASTLE SHIELD: FREE (WAVE 1-10)"', '"CASTLE SHIELD: ON"',
        '"ACTIVATE SHIELD (%dG)" % cost', '"REGEN SHIELD: ON"',
        '"REGEN SHIELD (%dG)" % cost',
        "special.append(f'Splash {tower.splash}')",
        "special.append(f'Slow {int(tower.slow * 100)}%')",
        "special.append(f'Chain x{tower.chain}')",
        "special.append('Double Shot')",
        "special.append(f'Burn {tower.burn_dps}/s')",
        "special.append(f'AtkSlow {int(tower.atk_slow * 100)}%')",
        "special.append(f'SkillDown {int(tower.skill_down * 100)}%')",
        "f'Minion Power: x{nx_data[\'minion_scale\']}'",
        "f'AI Level: {nx_data[\'minion_ai_level\']}/5'",
        "f'DMG: {nexus.damage}  RNG: {nexus.range}'",
        'name_text = info["name"].replace(" Tower", "")', 'f"{cost}G"',
        'title_text = f"Lv.{tower.level} {tower.tower_type.title()}"'],
        "PopupRenderer")
    castle, cline = literal(method(pr, "_draw_nexus_content"), "castle_names",
                            "PopupRenderer._draw_nexus_content")
    require(isinstance(castle, dict) and len(castle) == 5,
            "PopupRenderer._draw_nexus_content: castle_names bukan 5 entri")
    spec.take("castle_names", castle, cline)
    spec.take("tower_paths", ["archer", "cannon", "ice", "mage"],
              method(pr, "_draw_tower_path_buttons").lineno)


    # ── shop_hints ─────────────────────────────────────────────
    sh = inner_class(ns_class(tree, "shop_hints"), "ShopHints")
    sh_draw = method(sh, "draw")
    need(fn_src(sh_draw),
         ["pulse = int(math.sin(g.animation_time * 0.06) * 2)"],
         "ShopHints.draw")
    # anchor tabel: [(pos, label, (ax, ay)), ...] — dibaca struktural
    anchors = None
    for node in ast.walk(sh_draw):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.List):
            rows = []
            for elt in node.iter.elts:
                require(isinstance(elt, ast.Tuple) and len(elt.elts) == 3,
                        "ShopHints.draw: entri hint bukan 3-tuple")
                rows.append((ast.literal_eval(elt.elts[1]),
                             ast.literal_eval(elt.elts[2])))
            anchors = rows
    require(anchors,
            "ShopHints.draw: tabel [(pos, label, anchor)] tidak ditemukan")
    spec.take("hint_anchor", anchors, sh_draw.lineno)
    hint = method(sh, "_draw_single_hint")
    need(fn_src(hint), ["hint_x = sx + ax_off", "hint_y = sy + ay_off + pulse",
                        "hint_rect = hint_text.get_rect(center=(hint_x, hint_y))",
                        "bg_rect = hint_rect.inflate(16, 8)",
                        'get_font(14, "body_bold")'],
         "ShopHints._draw_single_hint")
    spec.take("hint_inflate", (16, 8), hint.lineno)

    # ── warna lintas komponen: dari AST _core.py (settings) + ui_theme.py ──
    spec.take("gold", settings["GOLD"], 0)
    spec.take("white", settings["WHITE"], 0)
    spec.take("gray", settings["GRAY"], 0)
    spec.take("green", settings["GREEN"], 0)
    spec.take("yellow", settings["YELLOW"], 0)
    spec.take("red", settings["RED"], 0)
    spec.take("red_light", settings["RED_LIGHT"], 0)
    spec.take("top_bar_h", settings["TOP_BAR_HEIGHT"], 0)
    spec.take("regen_min_level", settings["TOWER_REGEN_SHIELD_MIN_LEVEL"], 0)
    spec.take("gold_text", theme["GOLD_TEXT"], 0)
    spec.take("text_body", theme["TEXT_BODY"], 0)
    spec.take("text_dim", theme["TEXT_DIM"], 0)
    spec.take("cyan_soft", theme["CYAN_SOFT"], 0)
    spec.take("tower_type_colors", settings["TOWER_TYPE_COLORS"], 0)
    return spec


# ══════════════════════════════════════════════════════════
#  Emisi C++
# ══════════════════════════════════════════════════════════


def c8(triple):
    r, g, b = triple
    return "Color(%d.0f / 255.0f, %d.0f / 255.0f, %d.0f / 255.0f)" % (r, g, b)


def tpl(text, **values):
    for key, value in values.items():
        text = text.replace("@%s@" % key.upper(), str(value))
    return text


_FUNCS = []


def fn(name, comment, ret, args, body):
    """args: [(tipe, nama)] — C++ mentah."""
    _FUNCS.append((name, comment, ret, args, body))


def arglist(args):
    return ", ".join("%s %s" % (t, n) for t, n in args)


def signatures(funcs):
    for name, _comment, ret, args, _body in funcs:
        yield name, "    static %s %s(%s);" % (ret, name, arglist(args))


def build_functions(spec):
    del _FUNCS[:]

    # ── meta + data ────────────────────────────────────────────
    fn("module_names",
       "Daftar submodul ui_components (urutan bundle) — oracle memakai daftar "
       "ini untuk audit closed-world.",
       "Array", [], """
    Array out;
%s
    return out;""" % "\n".join('    out.push_back(String("%s"));' % m
                               for m in MODULES))
    fn("module_names_string",
       "Gabungan module_names() dengan koma (untuk cap jari + log).",
       "String", [], """
    String out;
    Array names = module_names();
    for (int64_t i = 0; i < names.size(); i++) {
        if (i > 0) {
            out += String(",");
        }
        out += (String)names[i];
    }
    return out;""")
    fn("api_signature",
       "Cap jari API: jumlah modul + fungsi (dipakai loader membuktikan backend "
       "C++ benar-benar jalan, dicetak sekali per perubahan backend).",
       "String", [], """
    return String("ui_v1:@MODS@mod:@FNS@fn:");""")
    colors = spec["tower_type_colors"]
    color_rows = []
    for ttype in ("archer", "cannon", "ice", "mage"):
        color_rows.append(tpl("""
    Dictionary @TYPE@;
    @TYPE@["main"] = @MAIN@;
    @TYPE@["dark"] = @DARK@;
    out["@TYPE@"] = @TYPE@;""", type=ttype,
            main=c8(colors[ttype]["main"]), dark=c8(colors[ttype]["dark"])))
    fn("tower_type_colors",
       "TOWER_TYPE_COLORS (settings/_core.py, via AST) — warna main/dark 4 "
       "tipe menara.",
       "Dictionary", [], "    Dictionary out;" + "".join(color_rows)
       + "\n    return out;")
    card_rows = []
    for i, (ttype, name, desc, color) in enumerate(spec["tower_cards"]):
        card_rows.append(tpl("""
    Dictionary c@I@;
    c@I@["type"] = String("@TYPE@");
    c@I@["name"] = String("@NAME@");
    c@I@["desc"] = String("@DESC@");
    c@I@["color"] = @COLOR@;
    out.push_back(c@I@);""", i=i, type=ttype, name=name, desc=desc,
                                  color=c8(color)))
    fn("tower_cards",
       "Kartu 4 tipe menara di BuildPopup (BuildPopup._draw_tower_buttons "
       "baris %d) — urutan = urutan grid 2x2." % spec.line("tower_cards"),
       "Array", [], "    Array out;" + "".join(card_rows) + "\n    return out;")
    fn("build_cost",
       "Biaya bangun menara (BuildPopup._draw_tower_buttons).",
       "int64_t", [], "    return %d;" % spec["build_cost"])
    fn("notification_duration",
       "Durasi satu notifikasi dalam frame (Notification.add_notification: "
       "'timer': %d — 3 detik @60fps)." % spec["notification_timer"],
       "int64_t", [], "    return %d;" % spec["notification_timer"])

    # ── base_ui ────────────────────────────────────────────────
    fn("close_button_rect",
       "Rect tombol X (BaseUIComponent._draw_close_button baris %d; default "
       "size=%d)." % (spec.line("close_size"), spec["close_size"]),
       "Rect2", [("int64_t", "x"), ("int64_t", "y"), ("int64_t", "size")],
       """
    return Rect2((double)x, (double)y, (double)size, (double)size);""")
    fn("hp_bar_color",
       "Warna isi HP bar (BaseUIComponent._draw_hp_bar: >0.5 hijau, >0.25 "
       "kuning, selain itu merah; batas %s / %s)."
       % (spec["hp_thresholds"][0], spec["hp_thresholds"][1]),
       "Color", [("double", "ratio")], tpl("""
    if (ratio > @HIGH@) {
        return @GREEN@;
    }
    if (ratio > @LOW@) {
        return @YELLOW@;
    }
    return @RED@;""",
       high=spec["hp_thresholds"][0], low=spec["hp_thresholds"][1],
       green=c8(spec["green"]), yellow=c8(spec["yellow"]),
       red=c8(spec["red"])))
    fn("hp_bar_fill",
       "Lebar isi HP bar: int(w * ratio) — trunc, bukan pembulatan.",
       "int64_t", [("int64_t", "w"), ("double", "ratio")],
       """
    return (int64_t)((double)w * ratio);""")
    fn("shadow_rect",
       "Rect surface bayangan (_draw_shadow_rect: surface = rect + 2*offset, "
       "blit di rect - offset).",
       "Rect2", [("const Rect2 &", "rect"), ("const Vector2 &", "offset")],
       """
    return Rect2(rect.position.x - offset.x, rect.position.y - offset.y,
            rect.size.x + offset.x * 2.0, rect.size.y + offset.y * 2.0);""")

    # ── penempatan popup ───────────────────────────────────────
    fn("popup_width",
       "Lebar popup setelah pemadatan panel kanan (BuildPopup.draw / "
       "PopupRenderer.draw: w = min(w, max(1, panel_w - 16))); panel_w<=0 = "
       "tidak ada panel.",
       "int64_t", [("int64_t", "design_w"), ("int64_t", "panel_w")], """
    if (panel_w <= 0) {
        return design_w;
    }
    int64_t limit = panel_w - 16;
    if (limit < 1) {
        limit = 1;
    }
    return design_w < limit ? design_w : limit;""")
    fn("build_popup_rect",
       "Posisi popup build di atas peta (BuildPopup.draw baris %d: px = "
       "slot_x - w//2, py = slot_y - h - 30, seluruh clamp layar). Balasan: "
       "x/y/w/h + konektor ke slot." % spec.line("build_popup_w"),
       "Dictionary",
       [("int64_t", "slot_x"), ("int64_t", "slot_y"), ("int64_t", "screen_w"),
        ("int64_t", "screen_h")], tpl("""
    int64_t w = @W@;
    int64_t h = @H@;
    int64_t px = slot_x - w / 2;
    int64_t py = slot_y - h - 30;
    if (px < 10) {
        px = 10;
    }
    if (px + w > screen_w - 10) {
        px = screen_w - w - 10;
    }
    if (py < 10) {
        py = slot_y + 30;
    }
    if (py + h > screen_h - 10) {
        py = screen_h - h - 10;
    }
    if (py < 10) {
        py = 10;
    }
    Dictionary out;
    out["x"] = (int64_t)px;
    out["y"] = (int64_t)py;
    out["w"] = (int64_t)w;
    out["h"] = (int64_t)h;
    Array line;
    line.push_back(Vector2((double)(px + w / 2), (double)(py + h)));
    line.push_back(Vector2((double)slot_x, (double)(slot_y - 10)));
    out["connector"] = line;
    return out;""", w=spec["build_popup_w"], h=spec["build_popup_h"]))
    fn("target_popup_rect",
       "Posisi popup menara/nexus di atas peta (PopupRenderer.draw baris %d: "
       "380x440; py < TOP_BAR_HEIGHT+10 digeser ke BAWAH target lalu di-clamp "
       "lagi)." % spec.line("popup_w"),
       "Dictionary",
       [("int64_t", "target_x"), ("int64_t", "target_y"),
        ("int64_t", "screen_w"), ("int64_t", "screen_h"),
        ("int64_t", "top_bar_h")], tpl("""
    int64_t w = @W@;
    int64_t h = @H@;
    int64_t px = target_x - w / 2;
    int64_t py = target_y - h - 40;
    if (px < 10) {
        px = 10;
    }
    if (px + w > screen_w - 10) {
        px = screen_w - w - 10;
    }
    if (py < top_bar_h + 10) {
        py = target_y + 40;
    }
    if (py + h > screen_h - 10) {
        py = screen_h - h - 10;
    }
    if (py < top_bar_h + 10) {
        py = top_bar_h + 10;
    }
    Dictionary out;
    out["x"] = (int64_t)px;
    out["y"] = (int64_t)py;
    out["w"] = (int64_t)w;
    out["h"] = (int64_t)h;
    Array line;
    line.push_back(Vector2((double)(px + w / 2), (double)(py + h)));
    line.push_back(Vector2((double)target_x, (double)(target_y - 10)));
    out["connector"] = line;
    return out;""", w=spec["popup_w"], h=spec["popup_h"]))

    # ── build_popup ────────────────────────────────────────────
    fn("build_popup_buttons",
       "Grid 2x2 kartu menara (BuildPopup._draw_tower_buttons baris %d: "
       "btn_w=(popup_w-50)//2, h=%d, start_y=py+62, gap 12/10)."
       % (spec.line("build_btn_h"), spec["build_btn_h"]),
       "Array",
       [("int64_t", "px"), ("int64_t", "py"), ("int64_t", "popup_w")], tpl("""
    Array out;
    int64_t btn_w = (popup_w - 50) / 2;
    int64_t btn_h = @H@;
    int64_t start_y = py + 62;
    for (int64_t i = 0; i < 4; i++) {
        int64_t col = i % 2;
        int64_t row = i / 2;
        int64_t bx = px + 15 + col * (btn_w + 12);
        int64_t by = start_y + row * (btn_h + 10);
        out.push_back(Rect2((double)bx, (double)by, (double)btn_w,
                (double)btn_h));
    }
    return out;""", h=spec["build_btn_h"]))
    fn("build_gold_text",
       "Teks gold popup build (f\"Gold: {gold:,}  (Cost: %d)\")."
       % spec["build_cost"],
       "String", [("int64_t", "gold")],
       tpl("""
    return String("Gold: ") + thousands(gold) + String("  (Cost: @COST@)");""",
           cost=spec["build_cost"]))
    fn("build_button_style",
       "Warna kartu menara (BuildPopup._draw_tower_buttons): fill gradasi "
       "dark/lighter dari warna tipe + border + warna teks nama/desc/biaya.",
       "Dictionary",
       [("bool", "can_afford"), ("bool", "hover"), ("const Color &", "color")],
       tpl("""
    int64_t cr = color.r8();
    int64_t cg = color.g8();
    int64_t cb = color.b8();
    int64_t dr = (int64_t)((double)cr * 0.30) + 18;
    int64_t dg = (int64_t)((double)cg * 0.30) + 18;
    int64_t db = (int64_t)((double)cb * 0.30) + 18;
    int64_t lr = (int64_t)((double)cr * 0.45) + 40;
    if (lr > 255) { lr = 255; }
    int64_t lg = (int64_t)((double)cg * 0.45) + 40;
    if (lg > 255) { lg = 255; }
    int64_t lb = (int64_t)((double)cb * 0.45) + 40;
    if (lb > 255) { lb = 255; }
    int64_t br = (int64_t)((double)cr * 0.22) + 12;
    int64_t bg = (int64_t)((double)cg * 0.22) + 12;
    int64_t bb = (int64_t)((double)cb * 0.22) + 12;
    Dictionary out;
    out["fill_top"] = Color((double)(hover ? lr : dr) / 255.0,
            (double)(hover ? lg : dg) / 255.0,
            (double)(hover ? lb : db) / 255.0);
    out["fill_bottom"] = Color((double)br / 255.0, (double)bg / 255.0,
            (double)bb / 255.0);
    out["border"] = can_afford ? color
            : Color(70.0 / 255.0, 70.0 / 255.0, 80.0 / 255.0);
    out["name_color"] = can_afford ? @WHITE@ : @GRAY@;
    out["desc_color"] = can_afford ? @DESC@ : @GRAY@;
    out["cost_color"] = can_afford ? @GOLD_TEXT@ : @GRAY@;
    out["corner_ticks"] = can_afford;
    out["interactive"] = can_afford;
    return out;""", white=c8(spec["white"]), gray=c8(spec["gray"]),
       gold_text=c8(spec["gold_text"]), desc=c8((215, 222, 240))))
    fn("hover_hit",
       "Hover pygame (rect.collidepoint) yang digerbangi flag enabled — "
       "dipakai semua kartu/pill interaktif.",
       "bool",
       [("const Rect2 &", "rect"), ("const Vector2 &", "mouse"),
        ("bool", "enabled")], """
    if (!enabled) {
        return false;
    }
    return rect.has_point(mouse);""")

    # ── build_slots ────────────────────────────────────────────
    fn("slot_blit_offset",
       "Offset blit surface slot (BuildSlots.draw baris %d: (sx-20, sy-17))."
       % spec.line("slot_blit"),
       "Vector2", [], "    return Vector2(%d, %d);" % spec["slot_blit"])
    fn("slot_surface_rect",
       "Rect surface slot %dx%d di koordinat layar (origin lokal (20,17))."
       % spec["slot_surface"],
       "Rect2", [("int64_t", "sx"), ("int64_t", "sy")],
       "    return Rect2((double)(sx %+d), (double)(sy %+d), %d.0, %d.0);"
       % (spec["slot_blit"][0], spec["slot_blit"][1],
          spec["slot_surface"][0], spec["slot_surface"][1]))
    fn("slot_pulse",
       "Denyut slot: int(round(sin(t*0.08)*2)) — round Python half-to-even, "
       "dipakai sebagai kunci cache + radius glow/plus.",
       "int64_t", [("double", "animation_time")],
       """
    return py_round(std::sin(animation_time * 0.08) * 2.0);""")
    fn("slot_cost_bg",
       "Rect label biaya '100G' di slot biru (BuildSlots._draw_blue_slot: "
       "Rect(sx-18, sy+18, 36, 14)).",
       "Rect2", [("int64_t", "sx"), ("int64_t", "sy")],
       "    return Rect2((double)(sx %+d), (double)(sy + %d), %d.0, %d.0);"
       % (-spec["slot_cost"][0], spec["slot_cost"][1],
          spec["slot_cost"][2], spec["slot_cost"][3]))
    fn("slot_cost_text",
       "Label biaya slot menara (hard-coded di surface slot).",
       "String", [], '    return String("%dG");' % spec["build_cost"])

    # ── hero_portraits (matematika crop/scale; pemindaian piksel tetap di
    #    renderer masing-masing — pure fungsi menerima hasil scan) ──
    fn("portrait_scan_step",
       "Langkah pemindaian bbox portrait (HeroPortraits._crop_and_scale: "
       "range(0, ch, 2)).",
       "int64_t", [], "    return %d;" % spec["portrait_scan_step"])
    fn("portrait_alpha_min",
       "Ambang alpha bbox portrait (HeroPortraits._crop_and_scale: "
       "pixel[3] > 10).",
       "int64_t", [], "    return %d;" % spec["portrait_alpha_min"])
    fn("portrait_crop_box",
       "Kotak crop dari bbox hasil scan + padding (HeroPortraits."
       "_crop_and_scale: pad %d, clamp ke canvas, None kalau kosong)."
       % spec["portrait_pad"],
       "Dictionary",
       [("int64_t", "min_x"), ("int64_t", "min_y"), ("int64_t", "max_x"),
        ("int64_t", "max_y"), ("int64_t", "canvas_w"),
        ("int64_t", "canvas_h")], tpl("""
    Dictionary out;
    if (max_x <= min_x || max_y <= min_y) {
        out["valid"] = false;
        return out;
    }
    int64_t pad = @PAD@;
    if (min_x - pad > 0) { min_x -= pad; } else { min_x = 0; }
    if (min_y - pad > 0) { min_y -= pad; } else { min_y = 0; }
    if (max_x + pad < canvas_w) { max_x += pad; } else { max_x = canvas_w; }
    if (max_y + pad < canvas_h) { max_y += pad; } else { max_y = canvas_h; }
    int64_t crop_w = max_x - min_x;
    int64_t crop_h = max_y - min_y;
    if (crop_w <= 0 || crop_h <= 0) {
        out["valid"] = false;
        return out;
    }
    out["valid"] = true;
    out["x"] = (int64_t)min_x;
    out["y"] = (int64_t)min_y;
    out["w"] = (int64_t)crop_w;
    out["h"] = (int64_t)crop_h;
    return out;""", pad=spec["portrait_pad"]))
    fn("portrait_scale_size",
       "Ukuran hasil smoothscale portrait (HeroPortraits._crop_and_scale: "
       "scale = min(tw/cw, th/ch, 1.0), new = max(1, int(crop*scale))).",
       "Dictionary",
       [("int64_t", "crop_w"), ("int64_t", "crop_h"), ("int64_t", "target_w"),
        ("int64_t", "target_h")], """
    double scale_x = (double)target_w / (double)crop_w;
    double scale_y = (double)target_h / (double)crop_h;
    double scale = scale_x < scale_y ? scale_x : scale_y;
    if (scale > 1.0) {
        scale = 1.0;
    }
    int64_t new_w = (int64_t)((double)crop_w * scale);
    int64_t new_h = (int64_t)((double)crop_h * scale);
    if (new_w < 1) { new_w = 1; }
    if (new_h < 1) { new_h = 1; }
    Dictionary out;
    out["w"] = (int64_t)new_w;
    out["h"] = (int64_t)new_h;
    out["scale"] = (double)scale;
    return out;""")
    fn("portrait_gray_weight",
       "Bobot grayscale portrait (HeroPortraits._apply_grayscale: 0.299/0.587/"
       "0.114) — pemanggil mengalikan kanal dan trunc ke uint8.",
       "Dictionary", [], tpl("""
    Dictionary out;
    out["r"] = (double)@WR@;
    out["g"] = (double)@WG@;
    out["b"] = (double)@WB@;
    return out;""", wr=spec["gray_weights"][0], wg=spec["gray_weights"][1],
       wb=spec["gray_weights"][2]))

    # ── hero_panel ─────────────────────────────────────────────
    fn("hero_panel_rect",
       "Panel hero bottom-left %dx%d (HeroPanel.draw baris %d: (20, H-296), "
       "atau posisi panel kanan dari platform)."
       % (spec["hero_panel_w"], spec["hero_panel_h"],
          spec.line("hero_panel_h")),
       "Rect2", [("int64_t", "screen_h")],
       "    return Rect2((double)%d, (double)(screen_h - %d), %d.0, %d.0);"
       % (spec["hero_panel_x"], spec["hero_panel_h"] + 20,
          spec["hero_panel_w"], spec["hero_panel_h"]))
    fn("hero_panel_layout",
       "Semua rect HeroPanel relatif ke (px, py) — baris %d: HP bar, 4 skill "
       "slot (%dpx gap %d), toggle auto-cast, item forge, upgrade (masing-"
       "masing 22px, jarak 30/38/28)."
       % (spec.line("hero_panel_h"), spec["hero_skill"][0],
          spec["hero_skill"][1]),
       "Dictionary", [("int64_t", "px"), ("int64_t", "py")], tpl("""
    Dictionary out;
    out["panel"] = Rect2((double)px, (double)py, @W@.0, @H@.0);
    out["close"] = close_button_rect(px + @CLOSE_INSET@, py + 6, 22);
    out["title_y"] = (int64_t)(py + 10);
    out["level_y"] = (int64_t)(py + 18);
    out["hp_bar"] = Rect2((double)(px + 12), (double)(py + 34), @HPW@.0, 8.0);
    out["hp_text_y"] = (int64_t)(py + 46);
    Array skills;
    int64_t start_x = px + 14;
    int64_t y = py + 66;
    for (int64_t i = 0; i < 4; i++) {
        skills.push_back(Rect2((double)(start_x + i * (@SIZE@ + @GAP@)),
                (double)y, @SIZE@.0, @SIZE@.0));
    }
    out["skills"] = skills;
    out["autocast"] = Rect2((double)(px + 10), (double)(py + 118),
            @INNER@.0, 22.0);
    out["item_slots_y"] = (int64_t)(py + 148);
    out["item_forge"] = Rect2((double)(px + 10), (double)(py + 186),
            @INNER@.0, 22.0);
    out["upgrade"] = Rect2((double)(px + 10), (double)(py + 214), @INNER@.0,
            22.0);
    return out;""", w=spec["hero_panel_w"], h=spec["hero_panel_h"],
       close_inset=spec["hero_close_inset"], hpw=spec["hero_panel_w"] - 24,
       size=spec["hero_skill"][0], gap=spec["hero_skill"][1],
       inner=spec["hero_panel_w"] - 20))
    fn("skill_key_font_size",
       "Ukuran font badge tombol skill (HeroPanel._draw_skill_slot: <=2 huruf "
       "14, <=4 huruf 12, selain itu 10).",
       "int64_t", [("int64_t", "label_len")], """
    if (label_len <= 2) {
        return 14;
    }
    if (label_len <= 4) {
        return 12;
    }
    return 10;""")
    fn("skill_badge_rect",
       "Badge huruf tombol skill di pojok kanan-bawah slot (kw = lebar teks + "
       "6; Rect(x+size-kw-2, y+size-13, kw, 11)).",
       "Rect2",
       [("int64_t", "x"), ("int64_t", "y"), ("int64_t", "size"),
        ("int64_t", "key_w")], """
    return Rect2((double)(x + size - key_w - 2), (double)(y + size - 13),
            (double)key_w, 11.0);""")
    fn("cooldown_seconds",
       "Label detik cooldown pygame: cooldown // 60 + 1 (frame <= 0 = siap / "
       "tanpa label).",
       "int64_t", [("int64_t", "frames")], """
    if (frames <= 0) {
        return 0;
    }
    return frames / 60 + 1;""")
    fn("cooldown_overlay_h",
       "Tinggi overlay gelap cooldown: int(size * cooldown / cooldown_max) "
       "(HeroPanel._draw_skill_slot). Argumen double → pembagian float Python. "
       "cooldown_max 0 dijaga eksplisit: Python melempar ZeroDivisionError, C++ "
       "mengembalikan 0 (tanpa guard, int() dari NaN/Inf tidak terdefinisi).",
       "int64_t",
       [("int64_t", "size"), ("double", "cooldown"),
        ("double", "cooldown_max")], """
    if (cooldown_max <= 0.0) {
        return 0;
    }
    return (int64_t)((double)size * (cooldown / cooldown_max));""")
    fn("item_forge_label",
       "Label tombol ITEM FORGE (DUA spasi sebelum kurung — persis pygame).",
       "String", [("int64_t", "used"), ("int64_t", "max_slots")], """
    return String("ITEM FORGE  (") + String::num_int64(used) + String("/")
            + String::num_int64(max_slots) + String(")");""")
    fn("hero_upgrade_label",
       "Label tombol upgrade hero: UPGRADE HERO ({cost}G).",
       "String", [("int64_t", "cost")], """
    return String("UPGRADE HERO (") + String::num_int64(cost) + String("G)");""")
    fn("max_level_label",
       "Label MAX LEVEL — ui_theme.letter() menyisipkan spasi antar huruf, "
       "jadi teksnya 17 karakter (dipakai pemanggil untuk mengukur lebar).",
       "String", [],
       '    return String("M A X   L E V E L");')
    fn("autocast_label",
       "Label toggle auto-cast.",
       "String", [("bool", "is_auto")], """
    return is_auto ? String("AUTO-CAST ON") : String("AUTO-CAST OFF");""")

    # ── hero_shop ──────────────────────────────────────────────
    fn("shop_panel_rect",
       "Panel HERO SHOP %dx%d terpusat (HeroShop._render_shop baris %d; "
       "panel_y minimal 16 supaya tombol X tidak keluar frame)."
       % (spec["shop_panel_w"], spec["shop_panel_h"],
          spec.line("shop_panel_w")),
       "Rect2", [("int64_t", "screen_w"), ("int64_t", "screen_h")], tpl("""
    int64_t panel_x = (screen_w - @W@) / 2;
    int64_t panel_y = (screen_h - @H@) / 2;
    if (panel_y < 16) {
        panel_y = 16;
    }
    return Rect2((double)panel_x, (double)panel_y, @W@.0, @H@.0);""",
       w=spec["shop_panel_w"], h=spec["shop_panel_h"]))
    tab_rows = []
    for i, (tab_id, label, color) in enumerate(spec["shop_tabs"]):
        tab_rows.append(tpl("""
    Dictionary t@I@;
    t@I@["id"] = String("@ID@");
    t@I@["label"] = String("@LABEL@");
    t@I@["color"] = @COLOR@;
    t@I@["rect"] = Rect2((double)(tab_start_x + @STEP@ * (tab_w + 10)),
            (double)tab_y, (double)tab_w, (double)tab_h);
    out.push_back(t@I@);""", i=i, id=tab_id, label=label, color=c8(color),
                                  step=i))
    fn("shop_tabs",
       "Tab toko hero (HeroShop._draw_hero_cards baris %d: tab_w %d, tab_h %d, "
       "total lebar = n*tab_w + 10, terpusat pada panel)."
       % (spec.line("shop_tabs"), spec["shop_tab_w"], spec["shop_tab_h"]),
       "Array",
       [("int64_t", "panel_x"), ("int64_t", "panel_w"), ("int64_t", "panel_y"),
        ("int64_t", "header_h")], tpl("""
    Array out;
    int64_t tab_w = @TAB_W@;
    int64_t tab_h = @TAB_H@;
    int64_t tab_y = panel_y + header_h + 10;
    int64_t total_tab_w = tab_w * @NTABS@ + 10;
    int64_t tab_start_x = panel_x + (panel_w - total_tab_w) / 2;@ROWS@
    return out;""", tab_w=spec["shop_tab_w"], tab_h=spec["shop_tab_h"],
       ntabs=len(tab_rows), rows="".join(tab_rows)))
    fn("shop_content",
       "Area konten kartu (HeroShop._draw_hero_cards: tab_y = panel_y + "
       "header_h + 10, content_top = tab_y + tab_h + 10, content_bottom = "
       "panel_y + %d - 20)." % spec["shop_panel_h"],
       "Dictionary",
       [("int64_t", "panel_y"), ("int64_t", "header_h")], tpl("""
    int64_t tab_y = panel_y + header_h + 10;
    int64_t content_top = tab_y + @TAB_H@ + 10;
    int64_t content_bottom = panel_y + @PANEL_H@ - 20;
    Dictionary out;
    out["tab_y"] = (int64_t)tab_y;
    out["top"] = (int64_t)content_top;
    out["bottom"] = (int64_t)content_bottom;
    out["height"] = (int64_t)(content_bottom - content_top);
    return out;""", tab_h=spec["shop_tab_h"], panel_h=spec["shop_panel_h"]))
    fn("shop_hero_list",
       "Filter daftar hero per tab (HeroShop._draw_hero_cards: tab starter = "
       "bukan boss, tab boss = boss; hero yang tidak ada di katalog dibuang, "
       "urutan = urutan array purchased).",
       "Array",
       [("const Array &", "purchased"), ("const Dictionary &", "is_boss"),
        ("const String &", "tab")], """
    Array out;
    for (int64_t i = 0; i < purchased.size(); i++) {
        String ht = purchased[i];
        if (!is_boss.has(ht)) {
            continue;
        }
        bool boss = (bool)is_boss[ht];
        if (tab == String("starter") && !boss) {
            out.push_back(ht);
        } else if (tab == String("boss") && boss) {
            out.push_back(ht);
        }
    }
    return out;""")
    fn("shop_grid",
       "Tata letak grid kartu + scroll (HeroShop._draw_hero_cards baris %d: "
       "kartu %dx%d, %d per baris, gap %d/%d, scroll di-clamp 0..max, kartu di "
       "luar content ditandai tidak terlihat)."
       % (spec.line("shop_card_w"), spec["shop_card_w"], spec["shop_card_h"],
          spec["shop_per_row"], spec["shop_gap_x"], spec["shop_gap_y"]),
       "Dictionary",
       [("int64_t", "panel_x"), ("int64_t", "panel_w"),
        ("int64_t", "content_top"), ("int64_t", "content_bottom"),
        ("int64_t", "count"), ("int64_t", "scroll")], tpl("""
    int64_t card_w = @CARD_W@;
    int64_t card_h = @CARD_H@;
    int64_t per_row = @PER_ROW@;
    int64_t gap_x = @GAP_X@;
    int64_t gap_y = @GAP_Y@;
    int64_t content_height = content_bottom - content_top;
    int64_t total_width = card_w * per_row + gap_x;
    int64_t start_x = panel_x + (panel_w - total_width) / 2;
    int64_t total_rows = (count + per_row - 1) / per_row;
    int64_t total_content_h = total_rows * (card_h + gap_y);
    int64_t max_scroll = total_content_h - content_height;
    if (max_scroll < 0) {
        max_scroll = 0;
    }
    int64_t clamped = scroll;
    if (clamped < 0) {
        clamped = 0;
    }
    if (clamped > max_scroll) {
        clamped = max_scroll;
    }
    Array rects;
    Array visible;
    for (int64_t i = 0; i < count; i++) {
        int64_t col = i % per_row;
        int64_t row = i / per_row;
        int64_t cx = start_x + col * (card_w + gap_x);
        int64_t cy = content_top + row * (card_h + gap_y) - clamped;
        rects.push_back(Rect2((double)cx, (double)cy, (double)card_w,
                (double)card_h));
        bool shown = !(cy + card_h < content_top || cy > content_bottom);
        visible.push_back(shown);
    }
    Dictionary out;
    out["card_w"] = (int64_t)card_w;
    out["card_h"] = (int64_t)card_h;
    out["per_row"] = (int64_t)per_row;
    out["gap_x"] = (int64_t)gap_x;
    out["gap_y"] = (int64_t)gap_y;
    out["start_x"] = (int64_t)start_x;
    out["total_rows"] = (int64_t)total_rows;
    out["total_height"] = (int64_t)total_content_h;
    out["max_scroll"] = (int64_t)max_scroll;
    out["scroll"] = (int64_t)clamped;
    out["rects"] = rects;
    out["visible"] = visible;
    return out;""", card_w=spec["shop_card_w"], card_h=spec["shop_card_h"],
       per_row=spec["shop_per_row"], gap_x=spec["shop_gap_x"],
       gap_y=spec["shop_gap_y"]))
    fn("shop_card_rects",
       "Isi kartu hero compact (HeroShop._draw_compact_card baris %d: portrait "
       "%d di kiri, info mulai x+%d, baris statistik y+%d jarak %d, tombol "
       "%dx%d di kanan)."
       % (spec.line("shop_portrait"), spec["shop_portrait"],
          10 + spec["shop_portrait"] + 12, 68, 56, spec["shop_btn"][0],
          spec["shop_btn"][1]),
       "Dictionary",
       [("int64_t", "cx"), ("int64_t", "cy"), ("int64_t", "cw"),
        ("int64_t", "ch")], tpl("""
    int64_t portrait = @PORTRAIT@;
    int64_t btn_w = @BTN_W@;
    int64_t btn_h = @BTN_H@;
    Dictionary out;
    out["card"] = Rect2((double)cx, (double)cy, (double)cw, (double)ch);
    out["portrait"] = Rect2((double)(cx + 10),
            (double)(cy + (ch - portrait) / 2), (double)portrait,
            (double)portrait);
    out["info_x"] = (int64_t)(cx + 10 + portrait + 12);
    out["info_y"] = (int64_t)(cy + 10);
    out["title_y"] = (int64_t)(cy + 34);
    out["role_y"] = (int64_t)(cy + 54);
    out["stats_y"] = (int64_t)(cy + 78);
    out["stat_gap"] = (int64_t)56;
    out["button"] = Rect2((double)(cx + cw - btn_w - 12),
            (double)(cy + (ch - btn_h) / 2), (double)btn_w, (double)btn_h);
    return out;""", portrait=spec["shop_portrait"], btn_w=spec["shop_btn"][0],
       btn_h=spec["shop_btn"][1]))
    fn("shop_card_state",
       "State tombol kartu hero (HeroShop._draw_compact_card): owned -> ACTIVE, "
       "hero penuh -> MAX, gold kurang -> harga (abu), selain itu beli (dua "
       "nada hover). Balasan: state/label/warna/interactive.",
       "Dictionary",
       [("bool", "owned"), ("int64_t", "hero_count"),
        ("int64_t", "max_owned"), ("int64_t", "gold"), ("int64_t", "cost")],
       tpl("""
    Dictionary out;
    String label = String::num_int64(cost) + String("G");
    if (owned) {
        out["state"] = String("owned");
        out["label"] = String("ACTIVE");
        out["bg"] = @OWNED_BG@;
        out["border"] = @OWNED_BORDER@;
        out["text_color"] = @OWNED_TEXT@;
        out["interactive"] = false;
        return out;
    }
    if (hero_count >= max_owned) {
        out["state"] = String("max");
        out["label"] = String("MAX");
        out["bg"] = @MAX_BG@;
        out["border"] = @MAX_BORDER@;
        out["text_color"] = @MAX_TEXT@;
        out["interactive"] = false;
        return out;
    }
    if (gold < cost) {
        out["state"] = String("cant_afford");
        out["label"] = label;
        out["bg"] = @CANT_BG@;
        out["border"] = @CANT_BORDER@;
        out["text_color"] = @CANT_TEXT@;
        out["interactive"] = false;
        return out;
    }
    out["state"] = String("buy");
    out["label"] = label;
    out["bg"] = @BUY_BG@;
    out["bg_hover"] = @BUY_BG_HOVER@;
    out["border"] = @BUY_BORDER@;
    out["border_hover"] = @BUY_BORDER_HOVER@;
    out["text_color"] = @BUY_TEXT@;
    out["interactive"] = true;
    return out;""",
       owned_bg=c8((40, 80, 40)), owned_border=c8((100, 180, 100)),
       owned_text=c8((150, 255, 150)),
       max_bg=c8((60, 40, 40)), max_border=c8((180, 80, 80)),
       max_text=c8((255, 150, 150)),
       cant_bg=c8((50, 50, 50)), cant_border=c8((130, 130, 130)),
       cant_text=c8((200, 150, 150)),
       buy_bg=c8((35, 140, 45)), buy_bg_hover=c8((40, 170, 50)),
       buy_border=c8((100, 220, 100)), buy_border_hover=c8((130, 255, 130)),
       buy_text=c8(spec["white"])))
    fn("shop_scroll_thumb",
       "Thumb scroll (HeroShop._draw_scroll_indicator: ratio = h/(h+max), "
       "thumb_h = max(20, int(h*ratio)), thumb_y = y + int((h-thumb_h)*"
       "pos/max)). max_scroll <= 0 -> Rect kosong.",
       "Rect2",
       [("int64_t", "x"), ("int64_t", "y"), ("int64_t", "height"),
        ("int64_t", "scroll"), ("int64_t", "max_scroll")], """
    if (max_scroll <= 0) {
        return Rect2();
    }
    double ratio = (double)height / (double)(height + max_scroll);
    int64_t thumb_h = (int64_t)((double)height * ratio);
    if (thumb_h < 20) {
        thumb_h = 20;
    }
    int64_t thumb_y = y + (int64_t)((double)(height - thumb_h)
            * ((double)scroll / (double)max_scroll));
    return Rect2((double)x, (double)thumb_y, 8.0, (double)thumb_h);""")
    fn("shop_scroll_buttons",
       "Tombol scroll atas/bawah 20x20 (HeroShop._draw_hero_cards; hanya "
       "didaftarkan bila max_scroll > 0 — keputusan pemanggil).",
       "Array",
       [("int64_t", "panel_x"), ("int64_t", "panel_w"),
        ("int64_t", "content_top"), ("int64_t", "content_bottom")], """
    Array out;
    out.push_back(Rect2((double)(panel_x + panel_w - 25),
            (double)content_top, 20.0, 20.0));
    out.push_back(Rect2((double)(panel_x + panel_w - 25),
            (double)(content_bottom - 20), 20.0, 20.0));
    return out;""")
    fn("shop_gold_text",
       "Teks badge gold header toko (f\"GOLD: {gold:,}\").",
       "String", [("int64_t", "gold")],
       '    return String("GOLD: ") + thousands(gold);')
    fn("shop_owned_text",
       "Teks badge kepemilikan hero (f\"{n}/{max} Heroes\").",
       "String", [("int64_t", "owned"), ("int64_t", "max_owned")], """
    return String::num_int64(owned) + String("/")
            + String::num_int64(max_owned) + String(" Heroes");""")
    fn("shop_empty_state",
       "Pesan state kosong per tab (HeroShop._draw_hero_cards).",
       "Dictionary", [("const String &", "tab")], """
    Dictionary out;
    if (tab == String("boss")) {
        out["msg"] = String("No boss heroes unlocked yet");
        out["hint"] = String("Defeat bosses to unlock their hero!");
    } else {
        out["msg"] = String("No starter heroes unlocked");
        out["hint"] = String("Visit Hero Shop from Main Menu!");
    }
    return out;""")

    # ── hover_indicators ───────────────────────────────────────
    fn("hover_target",
       "Target hover (HoverIndicators.update baris %d): popup/shop terbuka = "
       "tidak ada; menara radius %d, slot radius %d; yang pertama menang."
       % (spec.line("hover_tower_r"), spec["hover_tower_r"],
          spec["hover_slot_r"]),
       "Dictionary",
       [("double", "mx"), ("double", "my"), ("const Array &", "towers"),
        ("const Array &", "slots"), ("bool", "blocked")], tpl("""
    Dictionary out;
    out["kind"] = String("-");
    out["index"] = (int64_t)-1;
    if (blocked) {
        return out;
    }
    for (int64_t i = 0; i < towers.size(); i++) {
        Vector2 p = towers[i];
        if (std::sqrt((p.x - mx) * (p.x - mx) + (p.y - my) * (p.y - my))
                <= @TOWER_R@) {
            out["kind"] = String("tower");
            out["index"] = (int64_t)i;
            return out;
        }
    }
    for (int64_t i = 0; i < slots.size(); i++) {
        Vector2 p = slots[i];
        if (std::sqrt((p.x - mx) * (p.x - mx) + (p.y - my) * (p.y - my))
                <= @SLOT_R@) {
            out["kind"] = String("slot");
            out["index"] = (int64_t)i;
            return out;
        }
    }
    return out;""", tower_r=spec["hover_tower_r"], slot_r=spec["hover_slot_r"]))
    fn("tower_tooltip_lines",
       "Isi tooltip menara (HoverIndicators._draw_tower_tooltip: nama+Lv, "
       "DMG/RNG, Kills).",
       "Array",
       [("const String &", "name"), ("int64_t", "level"),
        ("int64_t", "damage"), ("int64_t", "range"), ("int64_t", "kills")],
       """
    Array out;
    out.push_back(name + String(" Lv.") + String::num_int64(level));
    out.push_back(String("DMG: ") + String::num_int64(damage)
            + String("  RNG: ") + String::num_int64(range));
    out.push_back(String("Kills: ") + String::num_int64(kills));
    return out;""")
    fn("tooltip_rects",
       "Kotak tooltip dari lebar/tinggi teks yang SUDAH diukur pemanggil "
       "(HoverIndicators._draw_tower_tooltip: tooltip y = int(y-60), bg = "
       "(x - w//2, y - h), shadow +4, panah bawah 5px).",
       "Dictionary",
       [("double", "tower_x"), ("double", "tower_y"), ("int64_t", "bg_w"),
        ("int64_t", "bg_h")], """
    int64_t tooltip_x = (int64_t)tower_x;
    int64_t tooltip_y = (int64_t)(tower_y - 60.0);
    int64_t bg_x = tooltip_x - bg_w / 2;
    int64_t bg_y = tooltip_y - bg_h;
    Dictionary out;
    out["x"] = (int64_t)bg_x;
    out["y"] = (int64_t)bg_y;
    out["bg"] = Rect2((double)bg_x, (double)bg_y, (double)bg_w, (double)bg_h);
    out["shadow"] = Rect2((double)(bg_x - 2), (double)(bg_y - 2),
            (double)(bg_w + 4), (double)(bg_h + 4));
    Array arrow;
    arrow.push_back(Vector2((double)(tooltip_x - 4), (double)(bg_y + bg_h)));
    arrow.push_back(Vector2((double)tooltip_x, (double)(bg_y + bg_h + 5)));
    arrow.push_back(Vector2((double)(tooltip_x + 4), (double)(bg_y + bg_h)));
    out["arrow"] = arrow;
    return out;""")
    fn("slot_hover_rects",
       "Glow + kotak hint slot (HoverIndicators._draw_slot_hover: glow 80x80 "
       "di (slot-40), hint 100x18 di (slot-50, slot-36)).",
       "Dictionary", [("int64_t", "sx"), ("int64_t", "sy")], """
    Dictionary out;
    out["glow"] = Rect2((double)(sx - 40), (double)(sy - 40), 80.0, 80.0);
    out["hint"] = Rect2((double)(sx - 50), (double)(sy - 36), 100.0, 18.0);
    return out;""")
    fn("slot_hint_text",
       "Label hint saat slot di-hover.",
       "String", [], '    return String("TAP TO BUILD");')
    fn("hover_pulses",
       "Alpha animasi hover (HoverIndicators: pulse range = sin(t*0.1)*0.2+0.8, "
       "glow slot = sin(t*0.15)*0.3+0.7; alpha pygame = int(30*pulse) dan "
       "int(180*pulse)).",
       "Dictionary", [("double", "animation_time")], """
    double range_pulse = std::sin(animation_time * 0.1) * 0.2 + 0.8;
    double slot_pulse = std::sin(animation_time * 0.15) * 0.3 + 0.7;
    Dictionary out;
    out["range_fill_alpha"] = (int64_t)(30.0 * range_pulse);
    out["range_border_alpha"] = (int64_t)(180.0 * range_pulse);
    out["slot_pulse"] = slot_pulse;
    return out;""")

    # ── notification ───────────────────────────────────────────
    fn("notification_entry",
       "Entri satu notifikasi (Notification.add_notification: text/color/"
       "timer=%d)." % spec["notification_timer"],
       "Dictionary", [("const String &", "text"), ("const Color &", "color")],
       tpl("""
    Dictionary out;
    out["text"] = text;
    out["color"] = color;
    out["timer"] = (int64_t)@TIMER@;
    return out;""", timer=spec["notification_timer"]))
    fn("notification_push",
       "Antrean notifikasi: salinan baru dengan satu entri ditambahkan "
       "(add_notification.append) — sumber tidak pernah menyisipkan ke tengah.",
       "Array",
       [("const Array &", "messages"), ("const String &", "text"),
        ("const Color &", "color")], """
    Array out = messages.duplicate();
    out.push_back(notification_entry(text, color));
    return out;""")

    # ── overlay ────────────────────────────────────────────────
    fn("newly_unlocked_level",
       "Level yang BARU terbuka (Overlay._get_newly_unlocked_level: level "
       "sekarang sudah selesai dan level berikutnya belum). Balasan -1 = "
       "tidak ada.",
       "int64_t",
       [("int64_t", "current"), ("const Array &", "completed"),
        ("int64_t", "next_level")], """
    if (next_level <= 0) {
        return -1;
    }
    bool current_done = false;
    bool next_done = false;
    for (int64_t i = 0; i < completed.size(); i++) {
        int64_t v = completed[i];
        if (v == current) {
            current_done = true;
        }
        if (v == next_level) {
            next_done = true;
        }
    }
    if (current_done && !next_done) {
        return next_level;
    }
    return -1;""")
    fn("unlock_popup",
       "Popup LEVEL UNLOCKED (Overlay._draw_level_unlock_popup baris %d: slide "
       "30 frame ease-out-cubic 400px, alpha ramp 15 frame, %dx%d di "
       "(cx+%d+slide, cy-%d))."
       % (spec.line("unlock_delay"), spec["overlay_unlock"][0],
          spec["overlay_unlock"][1], spec["overlay_unlock"][2],
          spec["overlay_unlock"][3]),
       "Dictionary",
       [("int64_t", "timer"), ("int64_t", "delay"), ("int64_t", "cx"),
        ("int64_t", "cy")], tpl("""
    int64_t elapsed = timer - delay;
    Dictionary out;
    out["visible"] = elapsed >= 0;
    if (elapsed < 0) {
        out["slide_x"] = (int64_t)0;
        out["alpha"] = (int64_t)0;
        out["rect"] = Rect2();
        return out;
    }
    int64_t slide_duration = @SLIDE@;
    int64_t offset_x = 0;
    if (elapsed < slide_duration) {
        double progress = (double)elapsed / (double)slide_duration;
        double eased = 1.0 - std::pow(1.0 - progress, 3.0);
        offset_x = (int64_t)((1.0 - eased) * (double)@SLIDE_PX@);
    }
    int64_t alpha = (int64_t)(255.0 * ((double)elapsed / (double)@RAMP@));
    if (alpha > 255) {
        alpha = 255;
    }
    out["slide_x"] = (int64_t)offset_x;
    out["alpha"] = (int64_t)alpha;
    out["rect"] = Rect2((double)(cx + @DX@ + offset_x), (double)(cy - @DY@),
            (double)@PW@, (double)@PH@);
    return out;""", slide=spec["overlay_unlock"][4], slide_px=spec["overlay_unlock"][6],
       ramp=spec["overlay_unlock"][5], dx=spec["overlay_unlock"][2],
       dy=spec["overlay_unlock"][3], pw=spec["overlay_unlock"][0],
       ph=spec["overlay_unlock"][1]))
    fn("overlay_stats_panel",
       "Panel statistik akhir match (Overlay._draw_stats baris %d: lebar %d, "
       "tinggi rows*%d+%d, baris y+%d+i*%d, badge NEW BEST %dx%d)."
       % (spec.line("overlay_stats"), spec["overlay_stats"][0],
          spec["overlay_stats"][1], spec["overlay_stats"][2],
          spec["overlay_stats"][3], spec["overlay_stats"][4],
          spec["overlay_stats"][5], spec["overlay_stats"][6]),
       "Dictionary",
       [("int64_t", "cx"), ("int64_t", "cy"), ("int64_t", "rows")], tpl("""
    int64_t panel_w = @PANEL_W@;
    int64_t panel_h = rows * @ROW_H@ + @PAD_H@;
    int64_t panel_x = cx - panel_w / 2;
    int64_t panel_y = cy - @PANEL_Y@;
    Dictionary out;
    out["rect"] = Rect2((double)panel_x, (double)panel_y, (double)panel_w,
            (double)panel_h);
    out["label_x"] = (int64_t)(panel_x + 20);
    out["value_right_x"] = (int64_t)(panel_x + panel_w - 20);
    Array rows_out;
    for (int64_t i = 0; i < rows; i++) {
        int64_t y = panel_y + @ROW_TOP@ + i * @ROW_STEP@;
        Dictionary row;
        row["y"] = (int64_t)y;
        row["badge"] = Rect2((double)(panel_x + panel_w / 2 - @BADGE_DX@),
                (double)(y - 3), @BADGE_W@.0, @BADGE_H@.0);
        rows_out.push_back(row);
    }
    out["rows"] = rows_out;
    return out;""", panel_w=spec["overlay_stats"][0], row_h=spec["overlay_stats"][1],
       pad_h=spec["overlay_stats"][2], panel_y=spec["overlay_unlock"][3],
       row_top=spec["overlay_stats"][3], row_step=spec["overlay_stats"][4],
       badge_w=spec["overlay_stats"][5], badge_h=spec["overlay_stats"][6],
       badge_dx=spec["overlay_stats"][7]))
    fn("overlay_stats_rows",
       "Isi 5 baris statistik akhir match (Overlay._draw_stats: skor ribuan, "
       "waktu m:ss dari pemanggil, wave, kill, combo xN + flag NEW BEST).",
       "Array",
       [("int64_t", "score"), ("const String &", "time_str"),
        ("int64_t", "waves"), ("int64_t", "kills"), ("int64_t", "combo"),
        ("bool", "best_score"), ("bool", "best_time")], """
    Array out;
    String labels[5] = { String("Final Score"), String("Match Time"),
            String("Waves Survived"), String("Total Kills"),
            String("Max Combo") };
    String values[5] = { thousands(score), time_str, String::num_int64(waves),
            String::num_int64(kills),
            String("x") + String::num_int64(combo) };
    bool bests[5] = { best_score, best_time, false, false, false };
    for (int64_t i = 0; i < 5; i++) {
        Dictionary row;
        row["label"] = labels[i];
        row["value"] = values[i];
        row["new_best"] = bests[i];
        out.push_back(row);
    }
    return out;""")
    fn("action_hint_tokens",
       "Parse hint aksi (Overlay._draw_action_hint: re.findall "
       "'\\[([^\\]]+)\\]\\s*([^[\\]]*)' + re.sub sisa teks). Balasan items "
       "(key/desc berpasangan) + plain (teks di luar keycap). Pemindai di sini "
       "meniru regex itu LANGKAH DEMI LANGKAH: kunci = isi [...] tanpa ']', "
       "spasi setelah ']' dimakan (\\s* di luar grup), desc = sampai '[' / ']' "
       "berikutnya.",
       "Dictionary", [("const String &", "action")], """
    Dictionary out;
    Array items;
    String plain;
    int64_t i = 0;
    int64_t length = action.length();
    while (i < length) {
        String ch = action.substr(i, 1);
        if (ch == String("[")) {
            int64_t close = -1;
            for (int64_t j = i + 1; j < length; j++) {
                if (action.substr(j, 1) == String("]")) {
                    close = j;
                    break;
                }
            }
            if (close > i + 1) {
                String key = action.substr(i + 1, close - i - 1);
                int64_t k = close + 1;
                while (k < length && action.substr(k, 1).strip_edges().length() == 0) {
                    k++;
                }
                int64_t m = k;
                while (m < length && action.substr(m, 1) != String("[")
                        && action.substr(m, 1) != String("]")) {
                    m++;
                }
                Dictionary item;
                item["key"] = key;
                item["desc"] = action.substr(k, m - k).strip_edges();
                items.push_back(item);
                i = m;
                continue;
            }
        }
        plain += ch;
        i++;
    }
    out["items"] = items;
    out["plain"] = plain.strip_edges();
    return out;""")
    fn("achievements_text",
       "Teks jumlah achievement (Overlay._draw_achievements).",
       "String", [("int64_t", "count")],
       """
    return String::num_int64(count) + String(" Achievements Unlocked!");""")
    fn("achievements_layout",
       "Layout ikon + teks achievement (Overlay._draw_achievements baris %d: "
       "total = 26 + lebar teks, ikon tx+11, teks tx+26, y = cy+250)."
       % spec.line("overlay_unlock"),
       "Dictionary",
       [("int64_t", "cx"), ("int64_t", "cy"), ("int64_t", "text_w")], """
    int64_t total_w = 26 + text_w;
    int64_t tx = cx - total_w / 2;
    Dictionary out;
    out["text_x"] = (int64_t)(tx + 26);
    out["text_y"] = (int64_t)(cy + 241);
    out["icon_x"] = (int64_t)(tx + 11);
    out["icon_y"] = (int64_t)(cy + 250);
    out["total_w"] = (int64_t)total_w;
    return out;""")

    # ── popup_renderer ─────────────────────────────────────────
    fn("tower_specials",
       "Daftar ability khusus menara (PopupRenderer._get_tower_specials baris "
       "%d) — ambang > 0, urutan tetap: Splash, Slow, Chain, Double Shot, "
       "Burn, AtkSlow, SkillDown."
       % spec.line("tower_paths"),
       "Array",
       [("int64_t", "splash"), ("double", "slow"), ("int64_t", "chain"),
        ("bool", "double_shot"), ("int64_t", "burn_dps"),
        ("double", "atk_slow"), ("double", "skill_down")], """
    Array out;
    if (splash > 0) {
        out.push_back(String("Splash ") + String::num_int64(splash));
    }
    if (slow > 0.0) {
        out.push_back(String("Slow ")
                + String::num_int64((int64_t)(slow * 100.0)) + String("%"));
    }
    if (chain > 1) {
        out.push_back(String("Chain x") + String::num_int64(chain));
    }
    if (double_shot) {
        out.push_back(String("Double Shot"));
    }
    if (burn_dps > 0) {
        out.push_back(String("Burn ") + String::num_int64(burn_dps)
                + String("/s"));
    }
    if (atk_slow > 0.0) {
        out.push_back(String("AtkSlow ")
                + String::num_int64((int64_t)(atk_slow * 100.0))
                + String("%"));
    }
    if (skill_down > 0.0) {
        out.push_back(String("SkillDown ")
                + String::num_int64((int64_t)(skill_down * 100.0))
                + String("%"));
    }
    return out;""")
    fn("tower_title",
       "Judul popup menara (PopupRenderer._draw_tower_content: kalau "
       "\"{name} Lv.{n}\" lebih lebar dari popup_w-90 -> \"Lv.{n} {Tipe}\" "
       "dengan Title-Case ala Python str.title()).",
       "String",
       [("const String &", "name"), ("int64_t", "level"),
        ("int64_t", "title_w"), ("int64_t", "popup_w"),
        ("const String &", "tower_type")], """
    String full = name + String(" Lv.") + String::num_int64(level);
    if (title_w > popup_w - 90) {
        return String("Lv.") + String::num_int64(level) + String(" ")
                + tower_type.capitalize();
    }
    return full;""")
    fn("nexus_stat_lines",
       "Tiga baris stat nexus (PopupRenderer._draw_nexus_content: minion power "
       "diformat pemanggil = str(minion_scale) ala Python).",
       "Array",
       [("const String &", "minion_scale"), ("int64_t", "ai_level"),
        ("int64_t", "damage"), ("int64_t", "range")], """
    Array out;
    out.push_back(String("Minion Power: x") + minion_scale);
    out.push_back(String("AI Level: ") + String::num_int64(ai_level)
            + String("/5"));
    out.push_back(String("DMG: ") + String::num_int64(damage)
            + String("  RNG: ") + String::num_int64(range));
    return out;""")
    fn("castle_name",
       "Nama castle dari level nexus (PopupRenderer._draw_nexus_content baris "
       "%d: 1..5, selain itu CITADEL)." % spec.line("castle_names"),
       "String", [("int64_t", "nexus_level")], """
    if (nexus_level == 1) { return String("OUTPOST"); }
    if (nexus_level == 2) { return String("WATCHTOWER"); }
    if (nexus_level == 3) { return String("FORTRESS"); }
    if (nexus_level == 4) { return String("STRONGHOLD"); }
    if (nexus_level == 5) { return String("ROYAL CASTLE"); }
    return String("CITADEL");""")
    fn("castle_shield_section",
       "Bagian castle shield popup nexus (PopupRenderer._draw_castle_shield_"
       "section): gratis wave 1-10 / sudah dibeli / bisa dibeli (gold cukup) / "
       "- (tidak ada). `next_y` = y+46 kalau pill digambar.",
       "Dictionary",
       [("bool", "free_shield"), ("bool", "purchased"), ("bool", "can_buy"),
        ("int64_t", "cost"), ("int64_t", "gold")], """
    Dictionary out;
    out["state"] = String("-");
    out["label"] = String();
    out["next_y"] = (int64_t)0;
    if (free_shield) {
        out["state"] = String("free");
        out["label"] = String("CASTLE SHIELD: FREE (WAVE 1-10)");
        out["kind"] = String("cyan");
        out["next_y"] = (int64_t)46;
        return out;
    }
    if (purchased) {
        out["state"] = String("on");
        out["label"] = String("CASTLE SHIELD: ON");
        out["kind"] = String("success");
        out["next_y"] = (int64_t)46;
        return out;
    }
    if (can_buy) {
        out["state"] = String("buy");
        out["label"] = String("ACTIVATE SHIELD (") + String::num_int64(cost)
                + String("G)");
        out["kind"] = gold >= cost ? String("gold") : String("locked");
        out["interactive"] = gold >= cost;
        out["next_y"] = (int64_t)46;
        return out;
    }
    return out;""")
    fn("regen_shield_section",
       "Bagian regen shield menara level >= %d (PopupRenderer._draw_regen_"
       "shield_section)." % spec["regen_min_level"],
       "Dictionary",
       [("bool", "active"), ("bool", "can_buy"), ("int64_t", "cost"),
        ("int64_t", "gold")], """
    Dictionary out;
    out["state"] = String("-");
    if (active) {
        out["state"] = String("on");
        out["label"] = String("REGEN SHIELD: ON");
        out["kind"] = String("success");
        return out;
    }
    if (can_buy) {
        out["state"] = String("buy");
        out["label"] = String("REGEN SHIELD (") + String::num_int64(cost)
                + String("G)");
        out["kind"] = gold >= cost ? String("gold") : String("locked");
        out["interactive"] = gold >= cost;
        return out;
    }
    return out;""")
    fn("tower_path_buttons",
       "4 kartu pilihan path level 1 (PopupRenderer._draw_tower_path_buttons "
       "baris %d: btn_w = (popup_w-46)//2, h 68, gap 12/8, mulai y+26)."
       % spec.line("tower_paths"),
       "Array",
       [("int64_t", "px"), ("int64_t", "y"), ("int64_t", "popup_w")], """
    Array out;
    int64_t btn_w = (popup_w - 46) / 2;
    int64_t btn_h = 68;
    int64_t start_y = y + 26;
    for (int64_t i = 0; i < 4; i++) {
        int64_t col = i % 2;
        int64_t row = i / 2;
        int64_t bx = px + 15 + col * (btn_w + 12);
        int64_t by = start_y + row * (btn_h + 8);
        out.push_back(Rect2((double)bx, (double)by, (double)btn_w,
                (double)btn_h));
    }
    return out;""")
    fn("path_button_name",
       "Nama pada kartu path (info['name'] tanpa suffix ' Tower').",
       "String", [("const String &", "tower_info_name")],
       """
    return tower_info_name.replace(String(" Tower"), String());""")
    fn("path_cost_text",
       "Label biaya kartu path / tombol.",
       "String", [("int64_t", "cost")],
       """
    return String::num_int64(cost) + String("G");""")
    fn("tower_upgrade_buttons",
       "Tombol UPGRADE + SELL level 2+ (PopupRenderer._draw_tower_upgrade_"
       "button: btn_w = (popup_w-46)//2, h 40, sell di px+27+btn_w).",
       "Dictionary",
       [("int64_t", "px"), ("int64_t", "y"), ("int64_t", "popup_w")], """
    int64_t btn_w = (popup_w - 46) / 2;
    int64_t btn_h = 40;
    Dictionary out;
    out["upgrade"] = Rect2((double)(px + 15), (double)y, (double)btn_w,
            (double)btn_h);
    out["sell"] = Rect2((double)(px + 27 + btn_w), (double)y, (double)btn_w,
            (double)btn_h);
    return out;""")
    fn("tower_max_layout",
       "Panel MAX LEVEL + jual (PopupRenderer._draw_tower_max_level: MAX "
       "terpusat y+14, tombol SELL 150x34 (popup_w-150)//2 di y+36 bila nilai "
       "jual > 0).",
       "Dictionary",
       [("int64_t", "px"), ("int64_t", "y"), ("int64_t", "popup_w"),
        ("int64_t", "sell_value")], """
    Dictionary out;
    out["max_center_x"] = (int64_t)(px + popup_w / 2);
    out["max_center_y"] = (int64_t)(y + 14);
    if (sell_value > 0) {
        out["sell"] = Rect2((double)(px + (popup_w - 150) / 2),
                (double)(y + 36), 150.0, 34.0);
    } else {
        out["sell"] = Rect2();
    }
    return out;""")
    fn("upgrade_preview_text",
       "Baris preview upgrade (PopupRenderer._draw_tower_upgrade_button: "
       "\"Lv{n}: DMG {dmg} HP {hp}\").",
       "String",
       [("int64_t", "next_level"), ("int64_t", "damage"), ("int64_t", "hp")],
       """
    return String("Lv") + String::num_int64(next_level) + String(": DMG ")
            + String::num_int64(damage) + String(" HP ")
            + String::num_int64(hp);""")

    # ── shop_hints ─────────────────────────────────────────────
    fn("shop_hint_pos",
       "Posisi hint toko di peta (ShopHints.draw baris %d: shop_pos + anchor + "
       "pulse vertikal; anchor ITEM FORGE (82,-30), HERO SHOP (-82,44))."
       % spec.line("hint_anchor"),
       "Vector2",
       [("double", "sx"), ("double", "sy"), ("int64_t", "ax"),
        ("int64_t", "ay"), ("int64_t", "pulse")], """
    return Vector2(sx + (double)ax, sy + (double)ay + (double)pulse);""")
    fn("shop_hint_bg",
       "Kotak pill hint dari teks terukur (ShopHints._draw_single_hint: "
       "get_rect(center) lalu inflate(16, 8) — center integer pygame).",
       "Rect2",
       [("int64_t", "center_x"), ("int64_t", "center_y"), ("int64_t", "text_w"),
        ("int64_t", "text_h")], tpl("""
    int64_t bg_w = text_w + @IX@;
    int64_t bg_h = text_h + @IY@;
    return Rect2((double)(center_x - text_w / 2 - @HX@),
            (double)(center_y - text_h / 2 - @HY@), (double)bg_w,
            (double)bg_h);""",
       ix=spec["hint_inflate"][0], iy=spec["hint_inflate"][1],
       hx=spec["hint_inflate"][0] // 2, hy=spec["hint_inflate"][1] // 2))
    fn("shop_hint_pulse",
       "Denyut vertikal hint toko: int(sin(t*0.06)*2) — trunc ke arah nol, "
       "BUKAN round.",
       "int64_t", [("double", "animation_time")], """
    return (int64_t)(std::sin(animation_time * 0.06) * 2.0);""")

    # cap jari API (jumlah fungsi sudah final)
    total = len(_FUNCS)
    for i, (name, comment, ret, args, body) in enumerate(_FUNCS):
        if name == "api_signature":
            _FUNCS[i] = (name, comment, ret, args,
                         body.replace("@MODS@", str(len(MODULES)))
                         .replace("@FNS@", str(total)))
    return list(_FUNCS)


CPP_HEAD = '''#include "ui_processor.h"

#include <godot_cpp/core/class_db.hpp>

#include <cmath>

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : ui_components/_bundle.py
// Generator : tools/gen_ui_cpp.py
// Regenerasi: python3 tools/gen_ui_cpp.py
// Cek CI    : python3 tools/gen_ui_cpp.py --check
//
// Setiap fungsi menyebut baris sumber Python yang direplikasi. Angka yang
// diekstrak generator datang dari AST (bukan salinan tangan); perilakunya
// dikunci oracle pygame + self-test tanpa engine.

namespace godot {

'''

CPP_TAIL = '''
void MysticUI::_bind_methods() {
%s
}

} // namespace godot
'''


def emit_h(funcs):
    decls = "\n".join(decl for _n, decl in signatures(funcs))
    return """#ifndef MYSTIC_UI_PROCESSOR_H
#define MYSTIC_UI_PROCESSOR_H

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : ui_components/_bundle.py (11 submodul komponen UI)
// Generator : tools/gen_ui_cpp.py (AST Python -> C++, bukan terjemahan tangan)
// Regenerasi: python3 tools/gen_ui_cpp.py
// Cek CI    : python3 tools/gen_ui_cpp.py --check
// Desain    : docs/UI_COMPONENTS_GODOTPP.md
//
// Port ui_components/_bundle.py ke Godot C++ GDExtension: lapisan LAYOUT +
// STATE + LABEL (geometri panel/kartu/tombol, state machine tombol, label,
// predikat hover). Renderer piksel (pygame.draw / Control Godot) tidak diport
// dan memanggil angka dari sini.

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/color.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/rect2.hpp>
#include <godot_cpp/variant/string.hpp>
#include <godot_cpp/variant/variant.hpp>
#include <godot_cpp/variant/vector2.hpp>
#include <cstdint>

namespace godot {

class MysticUI : public RefCounted {
    GDCLASS(MysticUI, RefCounted);

public:
%s

    // ── helper internal (dipakai fungsi ter-bind; TIDAK di-bind) ──
    static int64_t py_round(double value);
    static String thousands(int64_t value);

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_UI_PROCESSOR_H
""" % decls


def emit_cpp(funcs):
    parts = [CPP_HEAD]
    parts.append('''// Replika round() CPython: half-to-even (round(2.5) == 2, round(-2.5) == -2).
int64_t MysticUI::py_round(double value) {
    double floored = std::floor(value);
    double diff = value - floored;
    if (diff > 0.5) {
        return (int64_t)(floored + 1.0);
    }
    if (diff < 0.5) {
        return (int64_t)floored;
    }
    int64_t parity = (int64_t)floored;
    return (parity % 2 == 0) ? parity : parity + 1;
}

// Replika f"{value:,}" Python (pemisah ribuan).
String MysticUI::thousands(int64_t value) {
    bool neg = value < 0;
    int64_t mag = neg ? -(value + 1) + 1 : value;
    String digits = String::num_int64(mag);
    String out;
    while (digits.length() > 3) {
        out = String(",") + digits.substr(digits.length() - 3, 3) + out;
        digits = digits.substr(0, digits.length() - 3);
    }
    return (neg ? String("-") : String()) + digits + out;
}

''')
    for name, comment, ret, args, body in funcs:
        cpp_sig = "%s %s::%s(%s) {" % (ret, CLASS, name, arglist(args))
        parts.append("// %s\n%s\n%s\n}\n\n" % (comment, cpp_sig, body))
    binds = "\n".join(
        '    ClassDB::bind_static_method("%s", D_METHOD("%s"%s), &%s::%s);'
        % (CLASS, name, "".join(', "%s"' % a[1] for a in args), CLASS, name)
        for name, _c, _r, args, _b in funcs)
    parts.append(CPP_TAIL % binds)
    return "".join(parts)


# Tipe argumen C++ -> fungsi konversi Variant di harness self-test.
ARG_CONVERT = {
    "int64_t": "to_int",
    "double": "to_double",
    "bool": "to_bool",
    "const String &": "to_string",
    "const Color &": "to_color",
    "const Vector2 &": "to_vector2",
    "const Rect2 &": "to_rect2",
    "const Array &": "to_array",
    "const Dictionary &": "to_dict",
}


def emit_dispatch(funcs):
    """Tabel perintah harness self-test: satu entri per fungsi ter-bind.

    Ditulis generator supaya setiap fungsi baru WAJIB punya perintah — tidak
    ada cabang `if (cmd == ...)` yang bisa lupa diperbarui. Harness
    (ui_selftest.cpp) hanya menyediakan parser Variant + konverter tipe.
    """
    lines = [
        "// ═══ GENERATED — JANGAN SUNTING TANGAN ═══",
        "// Tabel perintah self-test untuk SELURUH API MysticUI (80 fungsi).",
        "// Dibangkitkan tools/gen_ui_cpp.py bersama ui_processor.{h,cpp};",
        "// diperiksa ulang oleh tools/test_ui_cpp_selftest.py (closed-world:",
        "// jumlah entri == jumlah bind_static_method di _bind_methods).",
        "",
        "// {nama, jumlah argumen, pemanggil}",
    ]
    for name, _comment, ret, args, _body in funcs:
        conv = []
        for i, (atype, _aname) in enumerate(args):
            if atype not in ARG_CONVERT:
                raise UiError(
                    "%s: tipe argumen belum punya konverter self-test: %s"
                    % (name, atype))
            conv.append("%s(a[%d], e)" % (ARG_CONVERT[atype], i))
        call = "MysticUI::%s(%s)" % (name, ", ".join(conv))
        # void: tidak ada di API (semua mengembalikan nilai)
        lines.append(
            '    {"%s", %d, [](const std::vector<Variant> &a, std::string &e) '
            '-> Variant {' % (name, len(args)))
        lines.append("        (void)a; (void)e;")
        lines.append("        return Variant(%s);" % call)
        lines.append("    }},")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="CI: berkas ter-commit harus identik")
    args = parser.parse_args()

    spec = build_spec()
    funcs = build_functions(spec)
    header = emit_h(funcs)
    cpp = emit_cpp(funcs)
    dispatch = emit_dispatch(funcs)

    if args.check:
        ok = True
        for path, expected in ((OUT_H, header), (OUT_CPP, cpp),
                               (OUT_DISPATCH, dispatch)):
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                print("[gen_ui_cpp] BEDA: %s" % path.relative_to(ROOT))
                ok = False
        if not ok:
            print("[gen_ui_cpp] jalankan: python3 tools/gen_ui_cpp.py")
            return 1
        print("[gen_ui_cpp] --check OK (%d fungsi, %d modul)"
              % (len(funcs), len(MODULES)))
        return 0

    OUT_H.parent.mkdir(parents=True, exist_ok=True)
    OUT_H.write_text(header, encoding="utf-8")
    OUT_CPP.write_text(cpp, encoding="utf-8")
    OUT_DISPATCH.parent.mkdir(parents=True, exist_ok=True)
    OUT_DISPATCH.write_text(dispatch, encoding="utf-8")
    print("[gen_ui_cpp] tulis %s" % OUT_H.relative_to(ROOT))
    print("[gen_ui_cpp] tulis %s (%d fungsi, %d modul)"
          % (OUT_CPP.relative_to(ROOT), len(funcs), len(MODULES)))
    print("[gen_ui_cpp] tulis %s" % OUT_DISPATCH.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
