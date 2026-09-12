#!/usr/bin/env python3
"""Self-test ui_processor.cpp di luar engine (butuh g++ saja, tanpa godot-cpp).

    python3 tools/test_ui_cpp_selftest.py

Menyalakan kode C++ hasil tools/gen_ui_cpp.py APA ADANYA lewat stub Variant
(godot/gdext/mystic_ui/selftest), lalu membandingkan balasannya dengan oracle:

  * godot/tests/fixtures/match_parity.json seksi `ui_hud` — angka yang direkam
    dari DRAW PYGAME ASLI (tools/test_godot_match_parity.py): geometri popup
    build (4 posisi slot), rect panel hero, cooldown, slide popup unlock,
    tombol-tombol popup tower/nexus, teks popup.
  * `_core.py` (settings) + `ui_theme.py` — konstanta & warna (di-import apa
    adanya, bukan dibaca ulang dari generator).
  * built-in Python: round() half-to-even, f"{v:,}", int(), //.

Pola tools/test_maps_cpp_selftest.py. Sengaja jalan SEBELUM build godot-cpp di
CI: regresi layout/label gagal cepat (±detik) dan murah.

Selain membandingkan nilai, skrip ini mengunci tiga invarian struktural:

  * jumlah entri tabel perintah (ui_dispatch.inc) == jumlah
    bind_static_method di _bind_methods == jumlah deklarasi di .h;
  * daftar module_names() == 11 submodul `ui_components`;
  * semua nama fungsi di tabel unik (tidak ada tabrakan perintah).
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

SELFTEST = ROOT / "godot" / "gdext" / "mystic_ui" / "selftest"
SRC = ROOT / "godot" / "gdext" / "mystic_ui" / "src"
FIXTURE = ROOT / "godot" / "tests" / "fixtures" / "match_parity.json"

MODULES = [
    "base_ui", "hero_portraits", "build_popup", "build_slots", "hero_panel",
    "hero_shop", "hover_indicators", "notification", "overlay",
    "popup_renderer", "shop_hints",
]

_checks = 0
_failures = []


def expect(cond, message):
    global _checks
    _checks += 1
    if not cond:
        _failures.append(message)
        print("[ui_selftest] FAIL: %s" % message)


def section(title):
    print("[ui_selftest] ── %s ──" % title)


# ══════════════════════════════════════════════════════════
#  Parser teks Variant (balasan protokol)
# ══════════════════════════════════════════════════════════


def _split_top(text, sep):
    out, cur, depth = [], [], 0
    for ch in text:
        if ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append("".join(cur))
    return out


def _split_atoms(inner):
    raw = _split_top(inner, ",")
    out = []
    for part in raw:
        if out and not re.match(
                r"^(nil|bool:|int:|float:|str:|color:|v2:|rect:|v2s:|pc:|"
                r"array:|dict:|\[|\{)", part):
            out[-1] += "," + part
        else:
            out.append(part)
    return out


def parse_reply(text):
    """Teks Variant -> nilai Python (int/float/bool/str/tuple/list/dict/None)."""
    if text is None:
        return None
    if text.startswith("error:"):
        return ("ERROR", text[6:])
    if text == "nil:null":
        return None
    if text.startswith("bool:"):
        return text[5:] == "true"
    if text.startswith("int:"):
        return int(text[4:])
    if text.startswith("float:"):
        return float(text[6:])
    if text.startswith("str:"):
        return text[4:]
    if text.startswith("color:"):
        return tuple(int(v) for v in text[6:].split(","))
    if text.startswith("v2:"):
        return tuple(float(v) for v in text[3:].split(","))
    if text.startswith("rect:"):
        return tuple(float(v) for v in text[5:].split(","))
    if text.startswith("v2s:[") or text.startswith("pc:["):
        prefix = 4 if text.startswith("v2s:") else 3
        inner = text[prefix + 1:-1]
        return [parse_reply(p) for p in _split_atoms(inner)] if inner else []
    if text.startswith("array:["):
        inner = text[7:-1]
        return [parse_reply(p) for p in _split_atoms(inner)] if inner else []
    if text.startswith("dict:{"):
        inner = text[6:-1]
        out = {}
        for part in (_split_atoms(inner) if inner else []):
            eq = _find_top_eq(part)
            out[parse_reply(part[:eq])] = parse_reply(part[eq + 1:])
        return out
    raise ValueError("balasan tak dikenal: %r" % text[:80])


def as_tuple(value):
    """Nilai protokol -> tuple float dibulatkan (rect/v2/color)."""
    if isinstance(value, (list, tuple)):
        return tuple(round(float(v), 6) for v in value)
    return value


def _find_top_eq(part):
    depth = 0
    for i, ch in enumerate(part):
        if ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
        elif ch == "=" and depth == 0:
            return i
    raise ValueError("dict tanpa '=': %r" % part)


# ══════════════════════════════════════════════════════════
#  Oracle
# ══════════════════════════════════════════════════════════


def load_hud_fixture():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data["ui_hud"]


class _Settings:
    """Konstanta settings + tema yang dipakai oracle.

    Sumbernya `_core.py` (settings) dan `ui_theme.py` — berkas yang sama yang
    dibaca generator, bukan salinan angka di skrip ini.
    """

    def __init__(self, **kw):
        self.__dict__.update(kw)


def _ast_constants(path, names):
    import ast as _ast
    tree = _ast.parse(Path(path).read_text(encoding="utf-8"),
                      filename=str(path))
    found = {}
    for node in tree.body:
        if isinstance(node, _ast.Assign) and len(node.targets) == 1 and \
                isinstance(node.targets[0], _ast.Name):
            name = node.targets[0].id
            if name in names:
                found[name] = _ast.literal_eval(node.value)
    missing = sorted(set(names) - set(found))
    assert not missing, "%s: konstanta hilang %s" % (path, missing)
    return found


def load_settings():
    """Konstanta dari modul ASLI kalau pygame ada, kalau tidak dari AST berkas
    yang sama (CI godot-check belum memasang pygame di langkah ini)."""
    sys.path.insert(0, str(ROOT))
    settings_names = ["TOWER_TYPE_COLORS", "GOLD", "WHITE", "GRAY", "GREEN",
                      "YELLOW", "RED", "BLUE_LIGHT", "RED_LIGHT"]
    theme_names = ["GOLD_TEXT", "TEXT_BODY", "TEXT_DIM", "CYAN_SOFT"]
    try:
        import _core  # noqa: F401  (memasang alias `settings`)
        values = {n: getattr(_core, n) for n in settings_names}
        theme = _ast_constants(ROOT / "ui_theme.py", theme_names)
        values.update(theme)
        return _Settings(**values)
    except ImportError as exc:
        print("[ui_selftest] pygame tidak ada (%s) — konstanta dibaca dari AST "
              "_core.py/ui_theme.py" % exc.name)
        values = _ast_constants(ROOT / "_core.py", settings_names)
        values.update(_ast_constants(ROOT / "ui_theme.py", theme_names))
        return _Settings(**values)


def color_text(rgb, alpha=255):
    return "color:%d,%d,%d,%d" % (rgb[0], rgb[1], rgb[2], alpha)


# ══════════════════════════════════════════════════════════
#  Perintah
# ══════════════════════════════════════════════════════════

def build_commands(hud):
    """Perintah uji + oracle-nya.

    Setiap ekspektasi HARUS berasal dari sumber, bukan tebakan:
      * fixture `ui_hud` (angka direkam dari draw pygame asli) untuk geometri
        popup/panel/slide yang benar-benar dilihat pemain;
      * rumus Python yang dirujuk komentar generator (dihitung ulang di sini
        dengan semantik Python: `/` float, `//` floor, `int()` trunc, `round()`
        half-to-even);
      * `_core.py` / `ui_theme.py` yang di-import apa adanya.
    """
    import math

    cmds = []

    def add(cid, fn, args, kind, expected):
        cmds.append((cid, fn, args, kind, expected))

    meta = hud["meta"]
    rules = hud["rules"]

    # ── meta + data ────────────────────────────────────────
    add("modules", "module_names", [], "list_str", MODULES)
    add("modules_str", "module_names_string", [], "str", ",".join(MODULES))
    add("sig", "api_signature", [], "regex", r"^ui_v1:11mod:\d+fn:$")
    add("cost", "build_cost", [], "int", 100)
    add("notif", "notification_duration", [], "int", 180)

    core = load_settings()
    colors = core.TOWER_TYPE_COLORS
    add("tower_colors", "tower_type_colors", [], "color_map",
        {t: dict(colors[t]) for t in ("archer", "cannon", "ice", "mage")})
    add("cards", "tower_cards", [], "tower_cards",
        [("archer", "Archer", "Fast single", colors["archer"]["main"]),
         ("cannon", "Cannon", "AOE + Burn", colors["cannon"]["main"]),
         ("ice", "Ice", "Slow move+atk", colors["ice"]["main"]),
         ("mage", "Mage", "Chain + Debuff", colors["mage"]["main"])])

    # ── base_ui ────────────────────────────────────────────
    add("close", "close_button_rect", ["int:10", "int:20", "int:22"],
        "rect", (10, 20, 22, 22))
    add("hp_hi", "hp_bar_color", ["float:0.75"], "color", core.GREEN)
    add("hp_bound_hi", "hp_bar_color", ["float:0.5"], "color", core.YELLOW)
    add("hp_bound_lo", "hp_bar_color", ["float:0.25"], "color", core.RED)
    add("hp_zero", "hp_bar_color", ["float:0.0"], "color", core.RED)
    add("hp_fill", "hp_bar_fill", ["int:100", "float:0.5"], "int", 50)
    add("hp_fill_third", "hp_bar_fill",
        ["int:100", "float:%.17g" % (1.0 / 3.0)], "int", 33)
    add("shadow", "shadow_rect", ["rect:10,20,30,40", "v2:5,5"], "rect",
        (5, 15, 40, 50))

    # ── build_popup ────────────────────────────────────────
    for name, row in sorted(hud["build_pos"].items()):
        sx, sy = row["slot"]
        add("bpanel_%s" % name, "build_popup_rect",
            ["int:%d" % sx, "int:%d" % sy, "int:1280", "int:720"], "dict_int",
            dict(zip(("x", "y", "w", "h"), row["panel"])))
    add("pwidth_none", "popup_width", ["int:400", "int:0"], "int", 400)
    add("pwidth_panel", "popup_width", ["int:400", "int:344"], "int",
        min(400, max(1, 344 - 16)))
    center = hud["scenarios"]["build_pos_center"]
    panel = tuple(hud["build_pos"]["center"]["panel"])
    add("gold_text", "build_gold_text", ["int:500"], "str", center["texts"][1])
    add("bbuttons", "build_popup_buttons",
        ["int:%d" % panel[0], "int:%d" % panel[1], "int:%d" % panel[2]],
        "rect_list", [tuple(b["rect"]) for b in center["buttons"][1:]])
    def dark(rgb, factor, add):
        return tuple(min(255, int(c * factor) + add) for c in rgb)

    gold = tuple(core.GOLD)
    add("bstyle_afford", "build_button_style",
        ["bool:true", "bool:false", color_text(core.GOLD)], "dict_color",
        {"fill_top": dark(gold, 0.30, 18), "fill_bottom": dark(gold, 0.22, 12),
         "border": gold, "name_color": core.WHITE,
         "cost_color": tuple(core.GOLD_TEXT), "interactive": True,
         "corner_ticks": True})
    add("bstyle_hover", "build_button_style",
        ["bool:true", "bool:true", color_text(core.GOLD)], "dict_color",
        {"fill_top": dark(gold, 0.45, 40)})
    add("bstyle_locked", "build_button_style",
        ["bool:false", "bool:true", color_text(core.GOLD)], "dict_color",
        {"fill_top": dark(gold, 0.45, 40), "border": (70, 70, 80),
         "fill_bottom": dark(gold, 0.22, 12),
         "name_color": core.GRAY, "cost_color": core.GRAY,
         "interactive": False, "corner_ticks": False})
    add("hover_on", "hover_hit", ["rect:10,10,50,50", "v2:20,20",
                                  "bool:true"], "bool", True)
    add("hover_edge", "hover_hit", ["rect:10,10,50,50", "v2:60,20",
                                    "bool:true"], "bool", False)
    add("hover_disabled", "hover_hit", ["rect:10,10,50,50", "v2:20,20",
                                        "bool:false"], "bool", False)

    # ── build_slots ────────────────────────────────────────
    add("slot_off", "slot_blit_offset", [], "v2", (-20, -17))
    add("slot_surf", "slot_surface_rect", ["int:100", "int:200"], "rect",
        (80, 183, 40, 38))
    add("slot_cost_bg", "slot_cost_bg", ["int:100", "int:200"], "rect",
        (82, 218, 36, 14))
    add("slot_cost", "slot_cost_text", [], "str", "100G")
    for t in (0.0, 0.5, 1.0, 2.5, 7.25):
        add("pulse_%s" % t, "slot_pulse", ["float:%s" % t], "int",
            round(math.sin(t * 0.08) * 2.0))

    # ── hero_panel ─────────────────────────────────────────
    add("panel", "hero_panel_rect", ["int:720"], "rect", (20, 424, 280, 276))
    add("panel_layout", "hero_panel_layout", ["int:20", "int:424"],
        "layout_panel", (20, 424, 280, 276))
    add("panel_close", "hero_panel_layout", ["int:20", "int:424"],
        "dict_rect", {"close": (46, 430, 22, 22),
                      "hp_bar": (32, 458, 256, 8),
                      "autocast": (30, 542, 260, 22)})
    add("key_font", "skill_key_font_size", ["int:1"], "int", 14)
    add("key_font2", "skill_key_font_size", ["int:2"], "int", 14)
    add("key_font4", "skill_key_font_size", ["int:4"], "int", 12)
    add("key_font5", "skill_key_font_size", ["int:5"], "int", 10)
    add("badge", "skill_badge_rect", ["int:0", "int:0", "int:44", "int:20"],
        "rect", (44 - 20 - 2, 44 - 13, 20, 11))
    for frames, expected in hud["formats"]["cooldown"].items():
        add("cd_%s" % frames, "cooldown_seconds", ["int:%s" % frames], "int",
            expected if expected is not None else 0)
    add("cd_overlay", "cooldown_overlay_h",
        ["int:44", "float:30.0", "float:60.0"], "int", 22)
    add("cd_overlay_zero", "cooldown_overlay_h",
        ["int:44", "float:0.0", "float:60.0"], "int", 0)
    add("cd_overlay_full", "cooldown_overlay_h",
        ["int:44", "float:60.0", "float:60.0"], "int", 44)
    add("item_forge", "item_forge_label", ["int:2", "int:6"], "str",
        "ITEM FORGE  (2/6)")
    add("item_forge_full", "item_forge_label", ["int:6", "int:6"], "str",
        "ITEM FORGE  (6/6)")
    add("upgrade_lbl", "hero_upgrade_label", ["int:300"], "str",
        "UPGRADE HERO (300G)")
    add("max_lbl", "max_level_label", [], "str", "M A X   L E V E L")
    add("autocast_on", "autocast_label", ["bool:true"], "str", "AUTO-CAST ON")
    add("autocast_off", "autocast_label", ["bool:false"], "str",
        "AUTO-CAST OFF")

    # ── hero_shop ──────────────────────────────────────────
    shop = hud["scenarios"]["shop_starter_empty"]["geometry"]["panel"]
    add("shop_panel", "shop_panel_rect", ["int:1280", "int:720"], "rect",
        tuple(shop))
    add("shop_tabs", "shop_tabs", ["int:%d" % shop[0], "int:%d" % shop[2],
                                   "int:%d" % shop[1], "int:60"], "tabs",
        "starter")
    add("shop_content", "shop_content", ["int:%d" % shop[1], "int:60"],
        "dict_int", {"tab_y": shop[1] + 70, "top": shop[1] + 110,
                     "bottom": shop[1] + 680,
                     "height": (shop[1] + 680) - (shop[1] + 110)})
    content_top = shop[1] + 110
    content_bottom = shop[1] + 680
    add("shop_grid", "shop_grid",
        ["int:%d" % shop[0], "int:%d" % shop[2], "int:%d" % content_top,
         "int:%d" % content_bottom, "int:6", "int:0"], "grid",
        (290, content_top, 0))
    add("shop_grid_scroll", "shop_grid",
        ["int:%d" % shop[0], "int:%d" % shop[2], "int:%d" % content_top,
         "int:%d" % content_bottom, "int:6", "int:2"], "grid",
        (290, content_top, 0))
    add("shop_grid_10", "shop_grid",
        ["int:%d" % shop[0], "int:%d" % shop[2], "int:%d" % content_top,
         "int:%d" % content_bottom, "int:10", "int:1000"], "grid_clamp",
        (5 * 132 - (content_bottom - content_top)))
    add("shop_card", "shop_card_rects", ["int:0", "int:0", "int:280",
                                         "int:110"], "dict_rect",
        {"portrait": (10, 25, 60, 60), "card": (0, 0, 280, 110),
         "button": (178, 40, 90, 30)})
    add("state_owned", "shop_card_state",
        ["bool:true", "int:5", "int:5", "int:100000", "int:400"],
        "dict_str", {"state": "owned", "label": "ACTIVE",
                     "interactive": False})
    add("state_max", "shop_card_state",
        ["bool:false", "int:5", "int:5", "int:100000", "int:400"],
        "dict_str", {"state": "max", "label": "MAX", "interactive": False})
    add("state_poor", "shop_card_state",
        ["bool:false", "int:1", "int:5", "int:50", "int:400"],
        "dict_str", {"state": "cant_afford", "label": "400G",
                     "interactive": False})
    add("state_buy", "shop_card_state",
        ["bool:false", "int:1", "int:5", "int:100000", "int:400"],
        "dict_str", {"state": "buy", "label": "400G", "interactive": True})
    add("scroll_thumb", "shop_scroll_thumb",
        ["int:100", "int:200", "int:400", "int:0", "int:100"], "rect",
        (100, 200, 8, 320))
    add("scroll_thumb_bot", "shop_scroll_thumb",
        ["int:100", "int:200", "int:400", "int:100", "int:100"], "rect",
        (100, 280, 8, 320))
    add("scroll_thumb_none", "shop_scroll_thumb",
        ["int:100", "int:200", "int:400", "int:0", "int:0"], "rect",
        (0, 0, 0, 0))
    add("scroll_buttons", "shop_scroll_buttons",
        ["int:%d" % shop[0], "int:%d" % shop[2], "int:%d" % content_top,
         "int:%d" % content_bottom], "rect_list",
        [(shop[0] + shop[2] - 25, content_top, 20, 20),
         (shop[0] + shop[2] - 25, content_bottom - 20, 20, 20)])
    add("gold_txt", "shop_gold_text", ["int:12345"], "str", "GOLD: 12,345")
    add("owned_txt", "shop_owned_text", ["int:2", "int:5"], "str",
        "2/5 Heroes")
    add("empty_starter", "shop_empty_state", ["str:starter"], "dict_str",
        {"msg": "No starter heroes unlocked",
         "hint": "Visit Hero Shop from Main Menu!"})
    add("empty_boss", "shop_empty_state", ["str:boss"], "dict_str",
        {"msg": "No boss heroes unlocked yet",
         "hint": "Defeat bosses to unlock their hero!"})

    # ── hover_indicators ───────────────────────────────────
    add("tooltip_lines", "tower_tooltip_lines",
        ["str:Archer", "int:3", "int:25", "int:120", "int:7"], "list_str",
        ["Archer Lv.3", "DMG: 25  RNG: 120", "Kills: 7"])
    add("tooltip_rects", "tooltip_rects",
        ["float:640.0", "float:300.0", "int:120", "int:46"], "dict_int",
        {"x": 580, "y": 194})
    add("tooltip_rects_geo", "tooltip_rects",
        ["float:640.0", "float:300.0", "int:120", "int:46"], "dict_rect",
        {"bg": (580, 194, 120, 46), "shadow": (578, 192, 124, 50)})
    add("slot_hover", "slot_hover_rects", ["int:100", "int:200"], "dict_rect",
        {"glow": (60, 160, 80, 80), "hint": (50, 164, 100, 18)})
    add("slot_hint", "slot_hint_text", [], "str", "TAP TO BUILD")
    for t in (0.0, 1.0, 2.5):
        rp = math.sin(t * 0.1) * 0.2 + 0.8
        sp = math.sin(t * 0.15) * 0.3 + 0.7
        add("pulses_%s" % t, "hover_pulses", ["float:%s" % t], "dict_num",
            {"range_fill_alpha": int(30.0 * rp),
             "range_border_alpha": int(180.0 * rp), "slot_pulse": sp})

    # ── notification ───────────────────────────────────────
    add("notif_entry", "notification_entry",
        ["str:TEST", color_text(core.WHITE)], "dict_str",
        {"text": "TEST", "timer": 180})
    add("notif_entry_color", "notification_entry",
        ["str:TEST", color_text(core.GOLD)], "dict_color",
        {"color": tuple(core.GOLD)})
    add("notif_push_empty", "notification_push",
        ["[]", "str:X", color_text(core.WHITE)], "len", 1)
    add("notif_push_one", "notification_push",
        ["[{%s}]" % ",".join(["str:text=str:A", "str:timer=int:5"]),
         "str:B", color_text(core.WHITE)], "len", 2)

    # ── overlay ────────────────────────────────────────────
    add("unlock_cur", "newly_unlocked_level", ["int:1", "[int:1]", "int:2"],
        "int", 2)
    add("unlock_next_done", "newly_unlocked_level",
        ["int:1", "[int:1,int:2]", "int:2"], "int", -1)
    add("unlock_cur_open", "newly_unlocked_level", ["int:1", "[int:2]",
                                                    "int:2"], "int", -1)
    add("unlock_none", "newly_unlocked_level", ["int:1", "[int:1]", "int:0"],
        "int", -1)
    for timer, blit in sorted(hud["unlock_slide"].items(),
                              key=lambda kv: int(kv[0])):
        # fixture merekam blit SHADOW (popup_x - 5, popup_y - 5)
        add("unlock_%s" % timer, "unlock_popup",
            ["int:%s" % timer, "int:90", "int:640", "int:360"], "unlock_rect",
            (blit[0] + 5, blit[1] + 5))
    add("stats_panel", "overlay_stats_panel", ["int:640", "int:360", "int:5"],
        "dict_rect", {"rect": (390, 260, 500, 214)})
    add("stats_rows", "overlay_stats_rows",
        ["int:1000", "str:1:23", "int:5", "int:40", "int:12", "bool:true",
         "bool:false"], "stats_rows",
        [("Final Score", "1,000", True), ("Match Time", "1:23", False),
         ("Waves Survived", "5", False), ("Total Kills", "40", False),
         ("Max Combo", "x12", False)])
    add("hint_tokens", "action_hint_tokens", ["str:%s" % "[SPACE] CONTINUE"],
        "hint_tokens", [("SPACE", "CONTINUE")])
    add("hint_plain", "action_hint_tokens", ["str:CONTINUE"], "hint_plain",
        "CONTINUE")
    add("ach_text", "achievements_text", ["int:3"], "str",
        "3 Achievements Unlocked!")
    add("ach_layout", "achievements_layout", ["int:640", "int:360",
                                              "int:180"], "dict_int",
        {"text_x": 563, "text_y": 601, "icon_x": 548, "icon_y": 610,
         "total_w": 206})

    # ── popup_renderer ─────────────────────────────────────
    add("specials_ice", "tower_specials",
        ["int:0", "float:0.25", "int:0", "bool:false", "int:0",
         "float:0.15", "float:0.0"], "list_str",
        ["Slow 25%", "AtkSlow 15%"])
    add("specials_cannon", "tower_specials",
        ["int:45", "float:0.0", "int:0", "bool:false", "int:8",
         "float:0.0", "float:0.0"], "list_str", ["Splash 45", "Burn 8/s"])
    add("specials_mage", "tower_specials",
        ["int:0", "float:0.0", "int:0", "bool:false", "int:0", "float:0.0",
         "float:0.2"], "list_str", ["SkillDown 20%"])
    add("specials_archer", "tower_specials",
        ["int:0", "float:0.0", "int:0", "bool:true", "int:0", "float:0.0",
         "float:0.0"], "list_str", ["Double Shot"])
    add("specials_none", "tower_specials",
        ["int:0", "float:0.0", "int:0", "bool:false", "int:0", "float:0.0",
         "float:0.0"], "list_str", [])
    add("title_short", "tower_title",
        ["str:Archer", "int:3", "int:100", "int:400", "str:archer"], "str",
        "Archer Lv.3")
    add("title_long", "tower_title",
        ["str:Royal Archer", "int:12", "int:380", "int:400", "str:archer"],
        "str", "Lv.12 Archer")
    add("nexus_lines", "nexus_stat_lines",
        ["str:1.5", "int:3", "int:60", "int:150"], "list_str",
        ["Minion Power: x1.5", "AI Level: 3/5", "DMG: 60  RNG: 150"])
    for lvl in range(1, 7):
        add("castle_%d" % lvl, "castle_name", ["int:%d" % lvl], "str",
            rules["nexus_names"].get(str(lvl), "CITADEL"))
    add("shield_free", "castle_shield_section",
        ["bool:true", "bool:false", "bool:false", "int:850", "int:100"],
        "dict_str", {"state": "free", "next_y": 46, "kind": "cyan"})
    add("shield_on", "castle_shield_section",
        ["bool:false", "bool:true", "bool:false", "int:850", "int:100"],
        "dict_str", {"state": "on", "next_y": 46, "kind": "success"})
    add("shield_buy", "castle_shield_section",
        ["bool:false", "bool:false", "bool:true", "int:850", "int:1000"],
        "dict_str", {"state": "buy", "kind": "gold", "interactive": True})
    add("shield_locked", "castle_shield_section",
        ["bool:false", "bool:false", "bool:true", "int:850", "int:100"],
        "dict_str", {"state": "buy", "kind": "locked", "interactive": False})
    add("shield_off", "castle_shield_section",
        ["bool:false", "bool:false", "bool:false", "int:850", "int:100"],
        "dict_str", {"state": "-", "next_y": 0})
    add("regen_off", "regen_shield_section",
        ["bool:false", "bool:true", "int:850", "int:1000"], "dict_str",
        {"state": "buy", "kind": "gold", "interactive": True})
    add("regen_locked", "regen_shield_section",
        ["bool:false", "bool:true", "int:850", "int:100"], "dict_str",
        {"state": "buy", "kind": "locked", "interactive": False})
    add("regen_on", "regen_shield_section",
        ["bool:true", "bool:true", "int:850", "int:1000"], "dict_str",
        {"state": "on", "kind": "success"})
    add("path_buttons", "tower_path_buttons", ["int:440", "int:70", "int:400"],
        "rect_list", [(455, 96, 177, 68), (644, 96, 177, 68),
                      (455, 172, 177, 68), (644, 172, 177, 68)])
    add("path_name", "path_button_name", ["str:Archer Tower"], "str", "Archer")
    add("path_cost", "path_cost_text", ["int:175"], "str", "175G")
    add("upgrade_buttons", "tower_upgrade_buttons",
        ["int:440", "int:70", "int:400"], "dict_rect",
        {"upgrade": (455, 70, 177, 40), "sell": (644, 70, 177, 40)})
    add("max_layout", "tower_max_layout",
        ["int:440", "int:70", "int:400", "int:1600"], "dict_int",
        {"max_center_x": 640, "max_center_y": 84})
    add("max_layout_sell", "tower_max_layout",
        ["int:440", "int:70", "int:400", "int:1600"], "dict_rect",
        {"sell": (565, 106, 150, 34)})
    add("max_layout_free", "tower_max_layout",
        ["int:440", "int:70", "int:400", "int:0"], "dict_rect",
        {"sell": (0, 0, 0, 0)})
    add("preview", "upgrade_preview_text",
        ["int:4", "int:55", "int:700"], "str", "Lv4: DMG 55 HP 700")

    # ── portrait (matematika crop/scale; piksel tetap di renderer) ──
    add("p_scan", "portrait_scan_step", [], "int", 2)
    add("p_alpha", "portrait_alpha_min", [], "int", 10)
    add("p_gray", "portrait_gray_weight", [], "dict_num",
        {"r": 0.299, "g": 0.587, "b": 0.114})
    add("p_crop", "portrait_crop_box",
        ["int:10", "int:20", "int:50", "int:70", "int:100", "int:200"],
        "dict_int", {"valid": True, "x": 6, "y": 16, "w": 48, "h": 58})
    add("p_crop_clamp", "portrait_crop_box",
        ["int:0", "int:0", "int:100", "int:200", "int:100", "int:200"],
        "dict_int", {"valid": True, "x": 0, "y": 0, "w": 100, "h": 200})
    add("p_crop_empty", "portrait_crop_box",
        ["int:20", "int:20", "int:20", "int:40", "int:100", "int:200"],
        "dict_int", {"valid": False})
    add("p_scale", "portrait_scale_size",
        ["int:60", "int:120", "int:60", "int:70"], "dict_int",
        {"w": 35, "h": 70})
    add("p_scale_up", "portrait_scale_size",
        ["int:10", "int:10", "int:60", "int:70"], "dict_int", {"w": 10,
                                                               "h": 10})
    add("p_scale_num", "portrait_scale_size",
        ["int:60", "int:120", "int:60", "int:70"], "dict_num",
        {"scale": 70.0 / 120.0})

    # ── popup target (popup menara nexus/menara musuh) ──────
    add("tpop_center", "target_popup_rect",
        ["int:640", "int:400", "int:1280", "int:720", "int:40"], "dict_int",
        {"x": 450, "y": 270, "w": 380, "h": 440})
    add("tpop_top", "target_popup_rect",
        ["int:640", "int:80", "int:1280", "int:720", "int:40"], "dict_int",
        {"x": 450, "y": 120})
    add("tpop_edge", "target_popup_rect",
        ["int:20", "int:700", "int:1280", "int:720", "int:40"], "dict_int",
        {"x": 10, "y": 220})

    # ── daftar hero per tab (HeroShop._draw_hero_cards) ────
    boss_map = "{str:kaizen=bool:false,str:grimjaw=bool:false," \
               "str:vex=bool:true}"
    add("hero_list_starter", "shop_hero_list",
        ["[str:kaizen,str:grimjaw,str:vex,str:unknown]", boss_map,
         "str:starter"], "list_str", ["kaizen", "grimjaw"])
    add("hero_list_boss", "shop_hero_list",
        ["[str:kaizen,str:grimjaw,str:vex,str:unknown]", boss_map, "str:boss"],
        "list_str", ["vex"])

    # ── hover_target ───────────────────────────────────────
    towers = "[v2:100,100,v2:300,300]"
    slots = "[v2:500,500]"
    add("hover_tower", "hover_target",
        ["float:110.0", "float:100.0", towers, slots, "bool:false"],
        "dict_str", {"kind": "tower", "index": 0})
    add("hover_slot", "hover_target",
        ["float:500.0", "float:510.0", towers, slots, "bool:false"],
        "dict_str", {"kind": "slot", "index": 0})
    add("hover_tower2", "hover_target",
        ["float:300.0", "float:320.0", towers, slots, "bool:false"],
        "dict_str", {"kind": "tower", "index": 1})
    add("hover_blocked", "hover_target",
        ["float:100.0", "float:100.0", towers, slots, "bool:true"],
        "dict_str", {"kind": "-", "index": -1})
    add("hover_none", "hover_target",
        ["float:50.0", "float:50.0", "[]", "[]", "bool:false"],
        "dict_str", {"kind": "-", "index": -1})

    # ── shop_hints ─────────────────────────────────────────
    add("hint_pos", "shop_hint_pos",
        ["float:340.0", "float:540.0", "int:82", "int:-30", "int:0"], "v2",
        (422, 510))
    add("hint_pos_pulse", "shop_hint_pos",
        ["float:940.0", "float:180.0", "int:-82", "int:44", "int:2"], "v2",
        (858, 226))
    add("hint_bg", "shop_hint_bg", ["int:422", "int:510", "int:90",
                                    "int:22"], "rect", (369, 495, 106, 30))
    for t in (0.0, 5.0, 10.0, 26.0):
        add("hint_pulse_%s" % t, "shop_hint_pulse", ["float:%s" % t], "int",
            int(math.sin(t * 0.06) * 2.0))

    return cmds


# ══════════════════════════════════════════════════════════
#  Bandingkan
# ══════════════════════════════════════════════════════════

def compare(cid, kind, expected, got):
    if isinstance(got, tuple) and got and got[0] == "ERROR":
        expect(False, "%s: C++ error: %s" % (cid, got[1]))
        return
    if kind == "int":
        expect(got == expected, "%s: %r != %r" % (cid, got, expected))
    elif kind == "bool":
        expect(bool(got) == bool(expected),
               "%s: %r != %r" % (cid, got, expected))
    elif kind == "str":
        expect(got == expected, "%s: %r != %r" % (cid, got, expected))
    elif kind == "regex":
        expect(re.match(expected, str(got)) is not None,
               "%s: %r !~ %s" % (cid, got, expected))
    elif kind == "list_str":
        expect(list(got or []) == list(expected),
               "%s: %r != %r" % (cid, got, expected))
    elif kind == "len":
        expect(len(got or []) == expected,
               "%s: len %r != %r" % (cid, len(got or []), expected))
    elif kind in ("rect", "v2"):
        expect(as_tuple(got) == as_tuple(expected),
               "%s: %r != %r" % (cid, got, expected))
    elif kind == "color":
        want = tuple(int(v) for v in expected)
        if len(want) == 3:
            want = want + (255,)
        expect(as_tuple(got) == want, "%s: %r != %r" % (cid, got, expected))
    elif kind == "color_map":
        def same_color(raw, want):
            if isinstance(want, dict):
                return (isinstance(raw, dict) and set(raw) == set(want)
                        and all(same_color(raw[k], want[k]) for k in want))
            if isinstance(raw, (str, type(None))):
                return False
            return as_tuple(raw)[:3] == as_tuple(want)[:3]
        expect(same_color(got, expected), "%s: %r != %r" % (cid, got,
                                                            expected))
    elif kind == "tower_cards":
        ok = isinstance(got, list) and len(got) == len(expected)
        if ok:
            for row, (ttype, name, desc, col) in zip(got, expected):
                ok = ok and row.get("type") == ttype
                ok = ok and row.get("name") == name and row.get("desc") == desc
                ok = ok and as_tuple(row.get("color", ()))[:3] == \
                    as_tuple(col)[:3]
        expect(ok, "%s: %r != %r" % (cid, got, expected))
    elif kind == "rect_list":
        got_list = [as_tuple(r) for r in (got or [])]
        want_list = [as_tuple(r) for r in expected]
        expect(got_list == want_list, "%s: %r != %r" % (cid, got_list,
                                                        want_list))
    elif kind == "tabs":
        want = [("starter", "STARTER", (485, 86, 150, 30)),
                ("boss", "BOSS HEROES", (645, 86, 150, 30))]
        ok = isinstance(got, list) and len(got) == len(want)
        if ok:
            for row, (tid, label, rect) in zip(got, want):
                ok = ok and row.get("id") == tid
                ok = ok and row.get("label") == label
                ok = ok and as_tuple(row.get("rect", ())) == as_tuple(rect)
        expect(ok, "%s: %r != %r" % (cid, got, want))
    elif kind in ("dict_subset", "dict_int", "dict_str", "dict_rect",
                  "dict_num", "dict_color"):
        ok = isinstance(got, dict)
        if ok:
            for key, value in expected.items():
                if key not in got:
                    ok = False
                    break
                gv = got[key]
                if kind == "dict_rect" or isinstance(value, tuple):
                    want_t = as_tuple(value)
                    got_t = as_tuple(gv)
                    if kind == "dict_color" and len(want_t) == 3:
                        want_t = want_t + (255.0,)
                    ok = ok and got_t == want_t
                elif isinstance(value, float):
                    ok = ok and abs(float(gv) - value) < 1e-9
                else:
                    ok = ok and gv == value
        expect(ok, "%s: %r tidak memuat %r" % (cid, got, expected))
    elif kind == "grid":
        start_x, first_y, max_scroll = expected
        ok = isinstance(got, dict)
        if ok:
            ok = (got.get("per_row") == 2 and got.get("card_w") == 340
                  and got.get("start_x") == start_x
                  and got.get("max_scroll") == max_scroll)
            rects = got.get("rects") or []
            ok = ok and len(rects) == 6
            if rects:
                ok = ok and as_tuple(rects[0]) == (start_x, first_y, 340, 120)
                ok = ok and as_tuple(rects[1]) == (start_x + 360, first_y,
                                                   340, 120)
                ok = ok and as_tuple(rects[2]) == (start_x, first_y + 132,
                                                   340, 120)
        expect(ok, "%s: %r (start_x=%d y=%d)" % (cid, got, start_x, first_y))
    elif kind == "grid_clamp":
        ok = isinstance(got, dict)
        if ok:
            ok = (got.get("total_rows") == 5 and got.get("scroll") == expected
                  and got.get("max_scroll") == expected
                  and got.get("total_height") == 5 * 132)
        expect(ok, "%s: %r (max_scroll=%d)" % (cid, got, expected))
    elif kind == "layout_panel":
        ok = isinstance(got, dict) and \
            as_tuple(got.get("panel", ())) == as_tuple(expected)
        expect(ok, "%s: %r != %r" % (cid, got, expected))
    elif kind == "unlock_rect":
        want_x, want_y = expected
        got_rect = as_tuple((got or {}).get("rect", ()))
        ok = (got_rect[:2] == (want_x, want_y)
              and got_rect[2:] == (340.0, 220.0))
        expect(ok, "%s: rect %r != (%r, %r)" % (cid, got_rect, want_x,
                                                want_y))
    elif kind == "stats_rows":
        ok = isinstance(got, list) and len(got) == len(expected)
        if ok:
            for row, (label, value, best) in zip(got, expected):
                ok = ok and row.get("label") == label
                ok = ok and row.get("value") == value
                ok = ok and bool(row.get("new_best")) == best
        expect(ok, "%s: %r != %r" % (cid, got, expected))
    elif kind == "hint_tokens":
        want = [{"key": k, "desc": d} for k, d in expected]
        expect(got and got.get("items") == want, "%s: %r != %r"
               % (cid, got, want))
    elif kind == "hint_plain":
        expect(got and got.get("plain") == expected and not got.get("items"),
               "%s: %r != %r" % (cid, got, expected))
    else:  # pragma: no cover
        raise AssertionError("kind tak dikenal: %s" % kind)




# ══════════════════════════════════════════════════════════
#  Build + jalan
# ══════════════════════════════════════════════════════════


def find_compiler():
    for name in ("g++", "clang++", "c++"):
        path = shutil.which(name)
        if path:
            return path
    return None


def compile_selftest(compiler, out_path):
    cmd = [
        compiler, "-std=c++17", "-O0", "-Wall",
        "-I", str(SELFTEST), "-I", str(SELFTEST / "shim"),
        "-o", str(out_path), str(SELFTEST / "ui_selftest.cpp"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-4000:])
        return False, proc.stderr
    return True, proc.stderr


def run_binary(binary, commands):
    lines = []
    for cid, fn, args, _kind, _expected in commands:
        fields = [cid, "fn", fn] + list(args)
        lines.append("\t".join(fields))
    lines.insert(0, "count\tcount")
    lines.insert(1, "bind\tbind")
    proc = subprocess.run([str(binary)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout[-2000:])
        print(proc.stderr[-2000:])
        raise SystemExit("[ui_selftest] harness gagal jalan")
    replies = {}
    for line in proc.stdout.splitlines():
        cid, _, payload = line.partition("\t")
        replies[cid] = payload
    return replies


def structural_checks(replies, commands):
    """Tiga sisi harus sepakat: tabel perintah hasil generator, bind_static_method
    di _bind_methods, dan deklarasi di .h. Ditambah closed-world: setiap fungsi
    di tabel WAJIB dipakai minimal satu perintah uji, dan tidak ada perintah
    yang memanggil fungsi di luar tabel."""
    section("struktur (closed-world)")
    count = parse_reply(replies.get("count"))
    header = (SRC / "ui_processor.h").read_text(encoding="utf-8")
    cpp = (SRC / "ui_processor.cpp").read_text(encoding="utf-8")
    table = re.findall(r'^\s*\{"([a-z_0-9]+)", (\d+),', 
                       (SELFTEST / "ui_dispatch.inc").read_text(encoding="utf-8"),
                       re.M)
    table_names = [name for name, _argc in table]
    binds = cpp.count('bind_static_method("MysticUI"')
    # deklarasi publik + helper internal (py_round, thousands) + _bind_methods
    decls = len(re.findall(r"^    static [A-Za-z_:<>0-9 ]+ [a-z_]+\(",
                           header, re.M)) - 3
    used = [c[1] for c in commands]
    ids = [c[0] for c in commands]
    expect(count == len(table_names),
           "count (%s) != entri tabel perintah (%d)" % (count, len(table_names)))
    expect(count == binds, "tabel perintah (%s) != bind (%d)" % (count, binds))
    expect(binds == decls, "bind (%d) != deklarasi .h (%d)" % (binds, decls))
    missing = sorted(set(table_names) - set(used))
    expect(not missing, "fungsi belum diuji: %s" % ", ".join(missing))
    unknown = sorted(set(used) - set(table_names))
    expect(not unknown, "perintah di luar tabel: %s" % ", ".join(unknown))
    expect(len(set(ids)) == len(ids), "id perintah duplikat")
    expect(parse_reply(replies.get("bind")) is None, "bind tidak nil")
    expect("ui_v1:11mod:%dfn:" % binds in cpp,
           "api_signature tidak menyebut %d fungsi" % binds)


def wiring_checks():
    """Audit wiring statis (tanpa engine): berkas yang harus ada, entry symbol
    .gdextension, allowlist SEMPIT godot_log_gate, dan rujukan di kedua
    workflow. Pola sama dengan seksi M oracle maps (FASE 35)."""
    section("wiring (statis)")
    ext = ROOT / "godot" / "gdext" / "mystic_ui"
    addon = ROOT / "godot" / "addons" / "mystic_ui"
    for needle, path in (("mystic_ui_library_init",
                          ext / "src" / "register_types.cpp"),
                         ("ClassDB::register_class<MysticUI>()",
                          ext / "src" / "register_types.cpp"),
                         ("mystic_ui_library_init",
                          addon / "mystic_ui.gdextension"),
                         ('compatibility_minimum = "4.3"',
                          addon / "mystic_ui.gdextension"),
                         ("libmystic_ui.linux.template_debug.x86_64.so",
                          addon / "mystic_ui.gdextension"),
                         ("env", ext / "SConstruct"),
                         ("ui_dispatch.inc", ext / "selftest" / "ui_selftest.cpp"),
                         ("MYSTIC_UI_SELFTEST_GODOT_STUB_H",
                          ext / "selftest" / "godot_stub.hpp")):
        expect(path.exists() and needle in path.read_text(encoding="utf-8"),
               "%s tidak memuat/ada: %s" % (path.name, needle))
    expect((addon / "bin" / ".gitkeep").exists(),
           "addons/mystic_ui/bin/.gitkeep hilang (folder bin tidak ikut git)")

    # godot_log_gate.py: lib .so TIDAK ikut repo, jadi langkah "Import project"
    # di godot-check selalu mencetak
    # "Failed loading resource: res://addons/mystic_ui/mystic_ui.gdextension".
    # Tanpa allowlist SEMPIT itu, gate menganggapnya fatal (persis kegagalan CI
    # PR #234). Pola telanjang r"mystic_ui" dilarang: itu akan memaafkan baris
    # gagal harness UI.
    gate = (ROOT / "godot" / "tools" / "godot_log_gate.py").read_text(
        encoding="utf-8")
    for needle in (r'r"addons/mystic_ui"', r'r"libmystic_ui"',
                   r'r"Failed loading resource.*mystic_ui"'):
        expect(needle in gate,
               "godot_log_gate.py kehilangan allowlist %s (import headless "
               "gagal tanpa lib)" % needle)
    expect('\n    r"mystic_ui",' not in gate,
           'godot_log_gate.py punya allowlist telanjang r"mystic_ui" — terlalu '
           "lebar, bisa memaafkan baris FAIL harness UI")

    check_yml = (ROOT / ".github" / "workflows" / "godot-check.yml").read_text(
        encoding="utf-8")
    gdext_yml = (ROOT / ".github" / "workflows" / "godot-gdext.yml").read_text(
        encoding="utf-8")
    for needle in ("tools/gen_ui_cpp.py --check",
                   "tools/test_ui_cpp_selftest.py", "'ui_components/**'"):
        expect(needle in check_yml,
               "godot-check.yml tak merujuk %s" % needle)
    for needle in ("tools/gen_ui_cpp.py --check",
                   "tools/test_ui_cpp_selftest.py",
                   "godot/gdext/mystic_ui",
                   "libmystic_ui.linux.template_debug.x86_64.so",
                   "mystic_ui_library_init",
                   "for lib in mystic_skills mystic_levels mystic_maps mystic_ui"):
        expect(needle in gdext_yml,
               "godot-gdext.yml tak merujuk %s" % needle)
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    expect("godot/addons/mystic_ui/bin/*.so" in gitignore,
           ".gitignore tidak mengabaikan lib mystic_ui")


def main():
    hud = load_hud_fixture()
    commands = build_commands(hud)

    compiler = find_compiler()
    if compiler is None:
        print("[ui_selftest] compiler C++ tidak ditemukan — hanya oracle "
              "Python yang dijalankan")
        return 1

    out = Path("/tmp/ui_selftest_bin")
    ok, _ = compile_selftest(compiler, out)
    expect(ok, "ui_selftest.cpp gagal dikompilasi")
    if not ok:
        return 1

    replies = run_binary(out, commands)
    structural_checks(replies, commands)
    wiring_checks()

    section("nilai (C++ vs oracle pygame/_core)")
    for cid, _fn, _args, kind, expected in commands:
        if cid not in replies:
            expect(False, "%s: tidak ada balasan" % cid)
            continue
        try:
            parsed = parse_reply(replies[cid])
        except Exception as exc:  # noqa: BLE001
            expect(False, "%s: balasan tak terparse (%s): %r"
                   % (cid, exc, replies[cid][:120]))
            continue
        try:
            compare(cid, kind, expected, parsed)
        except Exception as exc:  # noqa: BLE001
            expect(False, "%s: pembanding error (%s) atas %r"
                   % (cid, exc, replies[cid][:120]))

    print()
    if _failures:
        print("[ui_selftest] GAGAL: %d dari %d cek" % (len(_failures), _checks))
        return 1
    print("[ui_selftest] OK: %d cek lolos (compiler=%s)"
          % (_checks, Path(compiler).name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
