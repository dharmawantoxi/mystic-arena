"""Layer 9cp: replay every helper of the design system `ui_theme.py` (1011 lines).

The real module is imported under the recording pygame shim of `draw_recorder.py`,
so every function below runs its own source code instead of a copy:

  * text/string helpers (`letter`, `tab_width`, `fit_ellipsis`, `math_hyp`, `_dim`);
  * the four cache primitives are stand-ins with one recorded op each (`vgrad`,
    `shadow`, `radial`) - their pixels come from the 9br bake, their signature is
    what the fixture pins;
  * `draw_icon` records one `icon` op (the glyphs live in `assets/art/ui/icons.png`);
  * `gradient_text` records one `gradtext` op (the body gradient of `outline_text`);
  * `_has_glyph` answers True (Barlow and Cinzel both carry the ellipsis glyph), so
    `fit_ellipsis` always uses the single-character ellipsis;
  * `cheap_alpha()` is replaced per case; the source body only probes
    `mobile.perf.Quality.cheap_alpha`.

`tests/fixtures/ui_theme_source.json` keeps the ops, the button registry and the
return value of 30 cases; `tests/fixtures/ui_theme_inventory.json` classifies all
68 module symbols.

Run: python godot_rebuild/tests/ui_theme_source_oracle.py [--write]
"""
import ast
import json
import re
import sys
import types
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "ui_theme.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ui_theme_source.json"
INVENTORY = Path(__file__).resolve().parent / "fixtures" / "ui_theme_inventory.json"

BODY = rec.Font(26, "body_semibold")
VALUE = rec.Font(22, "body_medium")
TITLE = rec.Font(64, "title")


# ── recorded stand-ins (signatures of the real helpers) ──────────────────
def _vgrad(w, h, top, bottom, radius=0):
    w, h = max(2, int(w)), max(2, int(h))
    surface = rec.Surface((w, h))
    surface.ops.append({
        "kind": "vgrad", "rect": [0, 0, w, h], "top": list(top),
        "bottom": list(bottom), "radius": int(radius), "mult": 255,
    })
    return surface


def _shadow(w, h, radius=12, alpha=110, spread=4):
    w, h = max(2, int(w) + spread * 2), max(2, int(h) + spread * 2)
    surface = rec.Surface((w, h))
    surface.ops.append({
        "kind": "shadow", "rect": [0, 0, w, h], "radius": int(radius),
        "alpha": int(alpha), "spread": int(spread), "mult": 255,
    })
    return surface


def _radial(w, h, color, alpha):
    w, h = max(8, int(w)), max(8, int(h))
    graded = max(4, min(120, int(alpha) // 8 * 8))
    surface = rec.Surface((w, h))
    surface.ops.append({
        "kind": "radial", "rect": [0, 0, w, h], "color": list(color),
        "alpha": graded, "mult": 255,
    })
    return surface


def _draw_icon(surface, name, cx, cy, color, s=1.0):
    surface.ops.append({
        "kind": "icon", "name": name, "center": [rec.num(cx), rec.num(cy)],
        "color": rec.rgba(color), "scale": rec.num(s), "mult": 255,
    })


def _gradient_text(font, text, top, bottom):
    width = rec.glyph_width(font.font_size) * len(text)
    height = max(1, font.font_size)
    surface = rec.Surface((width, height))
    surface.ops.append({
        "kind": "gradtext", "text": text, "size": font.font_size, "style": font.style,
        "top": list(top), "bottom": list(bottom), "width": width, "height": height,
        "mult": 255,
    })
    return surface


def _fake_core():
    module = types.ModuleType("_core")
    module.title_font = lambda size: rec.Font(size, "title")
    module.get_font = lambda size, style="body", bold=False: rec.Font(size, style)
    return module


# ── pure helpers ────────────────────────────────────────────────────────
def _strings(ui):
    def fitting(font, text, max_w):
        return ui.fit_ellipsis(font, text, max_w)

    return [
        {"label": "letter_default", "text": "PLAY", "gap": " ",
         "result": ui.letter("PLAY")},
        {"label": "letter_dot", "text": "HEROES", "gap": "·",
         "result": ui.letter("HEROES", "·")},
        {"label": "letter_empty", "text": "", "gap": " ", "result": ui.letter("")},
        {"label": "tab_width_min", "label_text": "HEROES", "size": 26,
         "result": ui.tab_width(BODY, "HEROES")},
        {"label": "tab_width_long", "label_text": "VERY LONG LABEL", "size": 26,
         "result": ui.tab_width(BODY, "VERY LONG LABEL")},
        {"label": "fit_ellipsis_fits", "text": "SHORT", "max_w": 400,
         "result": fitting(BODY, "SHORT", 400)},
        {"label": "fit_ellipsis_cut", "text": "A VERY LONG SETTING LABEL", "max_w": 150,
         "result": fitting(BODY, "A VERY LONG SETTING LABEL", 150)},
        {"label": "fit_ellipsis_tiny", "text": "ABCDEFG", "max_w": 6,
         "result": fitting(BODY, "ABCDEFG", 6)},
        {"label": "math_hyp", "x": 3, "y": 4, "result": ui.math_hyp(3, 4)},
        {"label": "dim", "color": [255, 205, 85], "factor": 0.55,
         "result": list(ui._dim((255, 205, 85), 0.55))},
    ]


# ── recorded cases ──────────────────────────────────────────────────────
def _cases():
    return [
        ("panel_rich", True, lambda ui, s, b: ui.panel(s, (40, 30, 260, 140))),
        ("panel_cheap", False, lambda ui, s, b: ui.panel(s, (40, 30, 260, 140))),
        ("panel_solid", True, lambda ui, s, b: ui.panel_solid(s, (60, 40, 200, 90))),
        ("pill_gold_hover", True, lambda ui, s, b: ui.pill(
            s, b, "play", "PLAY", (20, 20, 160, 44), "gold", BODY, hover=True, icon="play")),
        ("pill_locked_disabled", True, lambda ui, s, b: ui.pill(
            s, b, "locked", "LOCKED", (20, 90, 160, 44), "locked", BODY, enabled=False)),
        ("button_hover_icon", True, lambda ui, s, b: ui.button(
            s, b, "continue", "CONTINUE", 640, 300, (140, 225, 255), BODY,
            w=360, h=54, icon="continue", hover=True)),
        ("button_plain", False, lambda ui, s, b: ui.button(
            s, b, "credits", "CREDITS", 640, 420, (200, 130, 210), BODY)),
        ("toggle_on_hover", True, lambda ui, s, b: ui.toggle(
            s, b, "audio", (100, 200, 60, 26), True, BODY, hover=True)),
        ("toggle_off", True, lambda ui, s, b: ui.toggle(
            s, b, "audio", (100, 240, 60, 26), False, BODY)),
        ("tab_active", True, lambda ui, s, b: ui.tab(
            s, b, "tab_starter", (0, 0, 200, 40), "STARTER", (100, 200, 255), BODY, True)),
        ("tab_hover", True, lambda ui, s, b: ui.tab(
            s, b, "tab_mini", (0, 60, 200, 40), "MINI", (255, 150, 100), BODY, False,
            hover=True)),
        ("slider_half_hover", True,
         lambda ui, s, b: ui.slider(s, 100, 300, 240, 0.5, knob_hover=True)),
        ("chip_icon_value", True, lambda ui, s, b: ui.chip(
            s, (30, 20), "GOLD", (255, 205, 85), BODY, icon="coin", value="+3/s")),
        ("chip_right_no_value", True, lambda ui, s, b: ui.chip(
            s, (1250, 40), "WAVE", (110, 195, 255), BODY, align="right")),
        ("section_header", True, lambda ui, s, b: ui.section_header(
            s, 60, 100, "HERO SHOP", "swords", (255, 205, 85), BODY, rule_w=240)),
        ("option_cycler", True, lambda ui, s, b: ui.option_cycler(
            s, b, "lang", "Language", "English", 60, 200, 400, BODY, VALUE)),
        ("option_cycler_hover_long", True, lambda ui, s, b: ui.option_cycler(
            s, b, "lang", "Language", "Bahasa Indonesia", 60, 250, 400, BODY, VALUE,
            hover="lang_prev")),
        ("screen_title_full", True,
         lambda ui, s, b: ui.screen_title(s, "MYSTIC ARENA", 640, 120)),
        ("screen_title_sub_solid", False, lambda ui, s, b: ui.screen_title(
            s, "DEFEAT", 640, 140, glow=False, sub="TRY AGAIN", sub_color=(255, 168, 96))),
        ("back_button_hover", True,
         lambda ui, s, b: ui.back_button(s, b, "back", 640, 660, hover=True)),
        ("back_button_plain", True, lambda ui, s, b: ui.back_button(s, b, "back", 640, 660)),
        ("scroll_indicator_mid", True,
         lambda ui, s, b: ui.scroll_indicator(s, 1240, 100, 300, 120, 240)),
        ("scroll_indicator_none", False,
         lambda ui, s, b: ui.scroll_indicator(s, 1240, 440, 200, 0, 0)),
        ("hp_bar_70", True, lambda ui, s, b: ui.hp_bar(s, 60, 600, 220, 16, 0.7)),
        ("hp_bar_cheap_20", False,
         lambda ui, s, b: ui.hp_bar(s, 60, 630, 220, 16, 0.2, (255, 108, 108))),
        ("progress_bar_half", True,
         lambda ui, s, b: ui.progress_bar(s, 60, 660, 220, 0.45)),
        ("progress_bar_zero", False, lambda ui, s, b: ui.progress_bar(s, 60, 680, 220, 0.0)),
        ("draw_text_center", True, lambda ui, s, b: ui.draw_text(
            s, BODY, "VICTORY", (240, 244, 255), center=(640, 200))),
        ("draw_text_topleft", True, lambda ui, s, b: ui.draw_text(
            s, BODY, "GOLD +125", (255, 220, 110), topleft=(40, 60), shadow=False)),
        ("outline_text_default", True,
         lambda ui, s, b: ui.outline_text(s, TITLE, "VICTORY", None, (640, 220))),
        ("outline_text_custom", False, lambda ui, s, b: ui.outline_text(
            s, TITLE, "DEFEAT", None, (640, 260), width=3,
            body_top=(255, 108, 108), body_bottom=(132, 44, 44))),
    ]


def _jsonable(value):
    if isinstance(value, (rec.Rect, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, rec.Text):
        return [value.text, value.font_size, value.w, value.h]
    if isinstance(value, rec.Surface):
        return [value.w, value.h]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _run_case(ui, label, cheap, call):
    ui.cheap_alpha = lambda: cheap
    screen = rec.Surface((1280, 720))
    buttons = {}
    result = call(ui, screen, buttons)
    return {
        "label": label,
        "cheap_alpha": cheap,
        "result": _jsonable(result),
        "ops": screen.ops,
        "buttons": {key: list(rect) for key, rect in buttons.items()},
    }


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    with rec.installed({"pygame": pygame, "_core": _fake_core()}):
        import ui_theme  # noqa: PLC0415 - needs the shim in `sys.modules`

        ui_theme._vgrad = _vgrad
        ui_theme._shadow = _shadow
        ui_theme._radial = _radial
        ui_theme.draw_icon = _draw_icon
        ui_theme.gradient_text = _gradient_text
        ui_theme._has_glyph = lambda font, character: True
        strings = _strings(ui_theme)
        cases = [_run_case(ui_theme, label, cheap, call)
                 for label, cheap, call in _cases()]
        palette = {name: list(value) for name, value in sorted(vars(ui_theme).items())
                   if name.isupper() and isinstance(value, tuple) and len(value) == 3}
    return {
        "source": "ui_theme.py (whole module) under draw_recorder.py",
        "glyph_factor": rec.GLYPH_FACTOR,
        "palette": palette,
        "strings": strings,
        "cases": cases,
    }


# ── inventory: every module symbol classified ───────────────────────────
CLASSIFICATION = {
    # 32 palette constants: baked into the 9br manifest, pinned by ui_skin_checks.gd.
    **{
        name: ("data", "data/art/ui_theme.json", '"%s"' % name,
               "baked into the palette table of the 9br manifest; "
               "tests/ui_skin_checks.gd pins nine of them and the 32-colour size")
        for name in (
            "BG_DEEP", "PANEL_TOP", "PANEL_BOTTOM", "PANEL_FILL", "GOLD", "GOLD_BRIGHT",
            "GOLD_DEEP", "GOLD_TEXT", "EDGE_GOLD", "EDGE_GOLD_DIM", "CYAN", "CYAN_SOFT",
            "VIOLET", "ORANGE", "GREEN", "GREEN_DEEP", "RED", "RED_DEEP", "SLATE",
            "TEXT_WHITE", "TEXT_BODY", "TEXT_DIM", "TEXT_FAINT", "LOCKED_BG_TOP",
            "LOCKED_BG_BOTTOM", "LOCKED_EDGE", "DONE_BG_TOP", "DONE_BG_BOTTOM",
            "DONE_EDGE", "OPEN_BG_TOP", "OPEN_BG_BOTTOM", "OPEN_EDGE",
        )
    },
    # Surface caches: the sheets are baked and Godot caches resources itself.
    "_GRAD_CACHE": ("folded", "scripts/ui/ui_skin.gd", "static func panels_texture()",
                    "gradients are baked into panels.png / pills.png / buttons.png"),
    "_GLOW_CACHE": ("folded", "scripts/ui/ui_skin.gd", "static func slider_glow_texture()",
                    "the only radial glow kept at runtime is the baked 36x36 slider glow"),
    "_SHADOW_CACHE": ("folded", "scripts/ui/ui_skin.gd", "static func panel_box(",
                      "soft shadows are part of the nine-patch expand margin"),
    "_GRAD_TEXT_CACHE": ("folded", "scripts/ui/ui_theme.gd", "const GRAD_TEXT_CACHE_LIMIT",
                         "gold title bodies are op-level `gradtext`, drawn by the title node"),
    "pygame": ("folded", "scripts/ui/shop_hint_layout.gd", '"kind": "vgrad"',
               "the shim becomes op dictionaries; no Python or pygame at runtime"),
    # Pure helpers and op builders: native module of this layer.
    "letter": ("ported", "scripts/ui/ui_theme.gd", "static func letter(",
               "`gap.join(list(text))`; the two older local copies stay untouched"),
    "fit_ellipsis": ("ported", "scripts/ui/ui_theme.gd", "static func fit_ellipsis(",
                     "same candidate loop; `_has_glyph` becomes the ellipsis parameter"),
    "math_hyp": ("ported", "scripts/ui/ui_theme.gd", "static func math_hyp(",
                 "`(x*x + y*y) ** 0.5`"),
    "_dim": ("ported", "scripts/ui/ui_theme.gd", "static func dim(",
             "`int(c * f)` per channel, f defaults to 0.55"),
    "tab_width": ("ported", "scripts/ui/ui_theme.gd", "static func tab_width(",
                  "`max(min_w, width(letter(label)) + 36)`"),
    "draw_text": ("ported", "scripts/ui/ui_theme.gd", "static func draw_text_ops(",
                  "body + optional (5, 6, 12) shadow offset by (2, 2)"),
    "gradient_text": ("ported", "scripts/ui/ui_theme.gd", "static func _gradtext(",
                      "one `gradtext` op; `outline_text` blits it over the outline"),
    "outline_text": ("ported", "scripts/ui/ui_theme.gd", "static func outline_text_ops(",
                     "8 outline blits when cheap_alpha(), 4 otherwise, then the body"),
    "corner_ticks": ("ported", "scripts/ui/ui_theme.gd", "static func corner_ticks_ops(",
                     "length 11, width 2, inset 2 defaults; eight lines"),
    "panel": ("ported", "scripts/ui/ui_theme.gd", "static func panel_ops(",
              "shadow + gradient + border + ticks when cheap, flat (6, 7, 14) drop shadow "
              "otherwise"),
    "panel_solid": ("ported", "scripts/ui/ui_theme.gd", "static func panel_solid_ops(",
                    "PANEL_FILL + EDGE_GOLD + gold ticks, no alpha at all"),
    "button": ("ported", "scripts/ui/ui_theme.gd", "static func button_ops(",
               "hover inflate (18, 8), glow, bevel, left accent, badge and clamped label"),
    "pill": ("ported", "scripts/ui/ui_theme.gd", "static func pill_ops(",
             "eight kind rows, hover brightening (+18 / +14), radius 7"),
    "toggle": ("ported", "scripts/ui/ui_theme.gd", "static func toggle_ops(",
               "knob 18 px, label on the opposite side of the knob"),
    "tab": ("ported", "scripts/ui/ui_theme.gd", "static func tab_ops(",
            "active accent underline at the bottom edge, radius 8"),
    "slider": ("ported", "scripts/ui/ui_theme.gd", "static func slider_ops(",
               "track 8 px, gold gradient fill, 11/8 px knob; also a Control node"),
    "chip": ("ported", "scripts/ui/ui_theme.gd", "static func chip_ops(",
             "auto width 26 + 22 icon + text + 10 + value, height 30, pill radius"),
    "section_header": ("ported", "scripts/ui/ui_theme.gd", "static func section_header_ops(",
                       "icon, letter-spaced title, hairline and a dim underline"),
    "option_cycler": ("ported", "scripts/ui/ui_theme.gd", "static func option_cycler_ops(",
                      "value box width `max(110, text + 26)` clamped to `width - 66`"),
    "screen_title": ("ported", "scripts/ui/ui_theme.gd", "static func screen_title_ops(",
                     "620x150 glow, gold ornament and an optional subtitle plate"),
    "back_button": ("ported", "scripts/ui/ui_theme.gd", "static func back_button_ops(",
                    "200x42 neutral pill with the `back` icon"),
    "scroll_indicator": ("ported", "scripts/ui/ui_theme.gd", "static func scroll_indicator_ops(",
                         "thumb height `max(18, int(height * ratio))`"),
    "hp_bar": ("ported", "scripts/ui/ui_theme.gd", "static func hp_bar_ops(",
               "track (16, 18, 30), lightened fill, (86, 92, 120) border"),
    "progress_bar": ("ported", "scripts/ui/ui_theme.gd", "static func progress_bar_ops(",
                     "track (30, 34, 54), +40 fill, (96, 96, 126) border"),
    "clear_caches": ("ported", "scripts/ui/ui_theme.gd", "static func clear_caches(",
                     "drops the gradient texture cache and the UiSkin sheet cache"),
    # Baked pixels / folded runtime.
    "_vgrad": ("baked", "bake/bake_ui_theme.py", "ui_theme.panel(canvas",
               "vertical gradients are painted into the sheets by the real pygame helper"),
    "_shadow": ("baked", "bake/bake_ui_theme.py", "ui_theme.panel(canvas",
                "the soft shadow ring is baked into panels.png and its expand margin"),
    "_radial": ("baked", "bake/bake_ui_theme.py", "glow = ui_theme._radial(36, 36",
                "the only runtime radial glow is assets/art/ui/slider_glow.png"),
    "draw_icon": ("baked", "bake/bake_ui_theme.py", "ui_theme.draw_icon(canvas",
                  "30 vector glyphs land in icons.png; the native side places the frame"),
    "cheap_alpha": ("folded", "scripts/ui/shop_hint_layout.gd", "cheap_alpha: bool = true",
                    "every layout takes the quality flag from the adaptive quality runtime"),
    "_has_glyph": ("folded", "scripts/ui/ui_theme.gd", "ellipsis: String = \"…\"",
                   "Godot fonts report glyph coverage; the source check is a fallback pair"),
}

POLICY = {
    "palette_colors": 32,
    "grad_text_cache_limit": 400,
    "tick_length": 11,
    "tick_width": 2,
    "tick_inset": 2,
    "panel_radius": 12,
    "pill_radius": 7,
    "tab_radius": 8,
    "slider_track": 8,
    "slider_knob": 11,
    "slider_knob_core": 8,
    "toggle_knob": 18,
    "chip_height": 30,
    "chip_pad": 26,
    "chip_icon_pad": 22,
    "chip_value_pad": 10,
    "tab_min_width": 150,
    "tab_pad": 36,
    "option_min_box": 110,
    "option_box_pad": 26,
    "back_button": [200, 42],
    "title_glow": [620, 150, 46],
    "ornament_span": 220,
    "scroll_min_thumb": 18,
}


def _native_functions(target):
    text = (PROJECT / target).read_text(encoding="utf-8")
    return set(re.findall(r"^static func ([A-Za-z_0-9]+)\(", text, re.M))


def symbol_inventory():
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imports, functions, assigns = [], [], []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigns.append(target.id)
    names = imports + functions + assigns
    return {
        "file": {
            "file": "ui_theme.py",
            "lines": len(text.splitlines()),
            "classes": 0,
            "functions": len(functions),
            "assigns": len(assigns),
            "imports": len(imports),
        },
        "symbols": {"count": len(names), "names": names},
        "imports": imports,
        "functions": functions,
        "assigns": assigns,
    }


def folder_fixture():
    inventory = symbol_inventory()
    classification = {}
    for name in inventory["symbols"]["names"]:
        if name not in CLASSIFICATION:
            raise AssertionError("ui_theme.py symbol without a classification: " + name)
        kind, target, token, note = CLASSIFICATION[name]
        classification[name] = {"kind": kind, "target": target, "token": token, "note": note}
    kinds = {}
    for row in classification.values():
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
    ported = sorted(name for name, row in classification.items() if row["kind"] == "ported")
    native = _native_functions("scripts/ui/ui_theme.gd") if (
        PROJECT / "scripts/ui/ui_theme.gd").is_file() else set()
    return {
        "source": "ui_theme.py",
        "file": inventory["file"],
        "symbols": inventory["symbols"],
        "classification": classification,
        "kinds": dict(sorted(kinds.items())),
        "ported": ported,
        "native_only": sorted(native),
        "baked": sorted(name for name, row in classification.items() if row["kind"] == "baked"),
        "folded": sorted(name for name, row in classification.items() if row["kind"] == "folded"),
        "policy": POLICY,
    }


def verify_folder():
    expected = json.loads(INVENTORY.read_text(encoding="utf-8"))
    actual = folder_fixture()
    if actual != expected:
        raise AssertionError("ui_theme.py inventory drift; rerun with --write")
    for name, row in actual["classification"].items():
        target = PROJECT / row["target"]
        if not target.is_file() or row["token"] not in target.read_text(encoding="utf-8"):
            raise AssertionError("ui_theme.py symbol %s lost its live target" % name)
    return actual["symbols"]["count"] + len(actual["policy"])


def main():
    arguments = sys.argv[1:]
    with redirect_stdout(StringIO()):
        actual = source_fixture()
    expected = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.exists() else None
    folder = folder_fixture()
    folder_expected = (
        json.loads(INVENTORY.read_text(encoding="utf-8")) if INVENTORY.exists() else None
    )
    if "--write" in arguments or expected != actual or folder_expected != folder:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=1, sort_keys=True) + "\n",
                           encoding="utf-8")
        INVENTORY.write_text(json.dumps(folder, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        if "--write" not in arguments and expected is not None:
            raise SystemExit("FAIL: ui_theme fixture drift (fixtures refreshed)")
        print("WROTE: " + FIXTURE.name + " + " + INVENTORY.name)
        return
    ops = sum(len(case["ops"]) for case in actual["cases"])
    print("PASS: %d ui_theme cases (%d ops) + %d strings + %d inventory facts"
          % (len(actual["cases"]), ops, len(actual["strings"]), verify_folder()))


if __name__ == "__main__":
    main()
