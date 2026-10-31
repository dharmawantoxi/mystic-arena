"""Whole-folder oracle for `ui_components/`: two files, 11 merged modules.

`ui_components/` holds the eleven UI components pygame paints over the match
(base_ui, build_popup, build_slots, hero_panel, hero_shop, hero_portraits,
hover_indicators, notification, overlay, popup_renderer, shop_hints) merged into
`_bundle.py` (4.160 lines) plus a 140-line `sys.modules` shim.

Most of the folder is already native from earlier layers: `build_popup_layout.gd`
(9bv7), `hero_panel_layout.gd` (9bv8), `shop_hint_layout.gd` (9bv3),
`end_overlay_layout.gd` (9bv5/9bv10), `tower_hover_layout.gd` (9bv11),
`slot_hover_layout.gd` (9bv12), the baked slot atlas (9bm) and the hero portrait
renders. What was still missing is the shared `BaseUIComponent` toolbox
(`_draw_shadow_rect`, `_draw_hp_bar`, `_draw_close_button`), `_popup_di_panel` and
the whole **tower popup** (`PopupRenderer.draw` for `popup_type == "tower"`: the
panel frame, connector line, HP bar, stat lines, specials, regen-shield section,
MAX LEVEL + sell, the four path buttons and the upgrade button).

This oracle harvests the real source with `ast` and runs it against the shared
recording pygame shim (`draw_recorder`), so every fixture op is what the source
actually asks for. `ui_theme.pill`, `hp_bar`, `draw_icon` and `corner_ticks` are
recorded as one op each (they are `ui_theme.py` code ported in other layers); the
draw methods themselves are unmodified.

Every symbol of the folder is classified as `ported` (an existing Godot module
carries it), `native` (this layer), `bake`, `dead`, `stub` or `meta`, with a
target file and a token that must exist.

Run: python godot_rebuild/tests/ui_components_source_oracle.py --write
"""

import argparse
import ast
import json
import sys
import textwrap
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "ui_components"
BUNDLE = FOLDER / "_bundle.py"
SHIM = FOLDER / "__init__.py"
CORE = ROOT / "_core.py"
UI_THEME = ROOT / "ui_theme.py"
PLATFORM_UTILS = ROOT / "mobile" / "platform_utils.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ui_components_source.json"
TOWER_DATA = ROOT / "godot_rebuild" / "data" / "towers" / "upgrade_paths.json"

MODULES = ["base_ui", "hero_portraits", "build_popup", "build_slots", "hero_panel",
           "hero_shop", "hover_indicators", "notification", "overlay",
           "popup_renderer", "shop_hints"]
NAMESPACES = ["hero_portraits", "build_popup", "build_slots", "hero_panel", "hero_shop",
              "hover_indicators", "notification", "overlay", "popup_renderer", "shop_hints"]
SECTIONS = ("_draw_close_button", "_draw_tower_content", "_draw_regen_shield_section",
            "_draw_tower_max_level", "_draw_tower_path_buttons", "_draw_single_path_button",
            "_draw_tower_upgrade_button")

BASE_CLASS = "BaseUIComponent"
POPUP_CLASS = "PopupRenderer"


def _source(path):
    return Path(path).read_text(encoding="utf-8")


# ── source harvesting ──────────────────────────────────────────────────────
def _constant(path, name):
    for node in ast.parse(_source(path)).body:
        if isinstance(node, ast.Assign) and any(
                getattr(target, "id", "") == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s not found in %s" % (name, Path(path).name))


def _core_dicts(names, extra=()):
    """Evaluate `_core.py` assignments whose values are literal dicts of literals."""
    text = _source(CORE)
    namespace = {}
    wanted = set(names) | {"ARCHER_LEVELS", "CANNON_LEVELS", "ICE_LEVELS", "MAGE_LEVELS"}
    for node in ast.parse(text).body:
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id in wanted:
            try:
                namespace[target.id] = ast.literal_eval(node.value)
            except Exception:
                segment = ast.get_source_segment(text, node)
                exec(compile(segment, str(CORE), "exec"), namespace)
    for name in extra:
        namespace[name] = _constant(CORE, name)
    missing = wanted - set(namespace)
    if missing:
        raise AssertionError("%s not found in _core.py" % sorted(missing))
    return namespace


def _find_class(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _class_text(text, name):
    node = _find_class(ast.parse(text), name)
    if node is None:
        raise AssertionError("%s not found in %s" % (name, Path(BUNDLE).name))
    return textwrap.dedent(ast.get_source_segment(text, node))


# ── recording stubs ────────────────────────────────────────────────────────
def _surface_with(op, w, h):
    surface = rec.Surface((w, h))
    surface.ops.append(op)
    return surface


def _ui_theme(pygame, cheap_flag):
    module = types.ModuleType("ui_theme")
    module.pygame = pygame
    for name in ("GOLD", "GOLD_BRIGHT", "GOLD_TEXT", "TEXT_BODY", "TEXT_DIM", "CYAN_SOFT",
                 "SLATE", "GREEN", "YELLOW", "RED", "WHITE", "GRAY"):
        try:
            setattr(module, name, _constant(UI_THEME, name))
        except AssertionError:
            continue
    module.cheap_alpha = lambda: cheap_flag["cheap"]

    def radial(w, h, color, alpha):
        a = max(4, min(120, int(alpha) // 8 * 8))
        return _surface_with({"kind": "radial", "rect": [0, 0, int(w), int(h)],
                              "color": list(color), "alpha": a, "mult": 255}, w, h)

    def shadow(w, h, radius=12, alpha=110, spread=4):
        sw, sh = int(w) + spread * 2, int(h) + spread * 2
        return _surface_with({"kind": "shadow", "rect": [0, 0, sw, sh], "radius": int(radius),
                              "alpha": int(alpha), "mult": 255}, sw, sh)

    def vgrad(w, h, top, bottom, radius=0):
        return _surface_with({"kind": "vgrad", "rect": [0, 0, int(w), int(h)],
                              "top": list(top), "bottom": list(bottom),
                              "radius": int(radius), "mult": 255}, w, h)

    def pill(screen, btns, bid, label, rect, kind, font, hover=False, enabled=True,
             icon=None, letter_gap=True):
        box = rec.Rect(rect)
        screen.ops.append({"kind": "pill", "id": bid, "text": str(label),
                           "rect": list(box), "style": kind, "hover": bool(hover),
                           "enabled": bool(enabled), "icon": icon,
                           "letter_gap": bool(letter_gap),
                           "size": font.font_size, "font": font.style, "mult": 255})
        if btns is not None:
            btns[bid] = box
        return box

    def hp_bar(screen, x, y, w, h, ratio, color=None):
        screen.ops.append({"kind": "hp_bar", "rect": [int(x), int(y), int(w), int(h)],
                           "ratio": float(ratio),
                           "color": list(color if color is not None else module.GREEN),
                           "mult": 255})

    def draw_icon(surf, name, cx, cy, color, s=1.0):
        surf.ops.append({"kind": "icon", "name": name, "center": [rec.num(cx), rec.num(cy)],
                         "color": list(color), "s": s, "mult": 255})

    def corner_ticks(screen, rect, color, length=11, width=2, inset=2):
        screen.ops.append({"kind": "corner_ticks", "rect": list(rec.Rect(rect)),
                           "color": list(color), "length": int(length),
                           "width": int(width), "inset": int(inset), "mult": 255})

    module._radial, module._shadow, module._vgrad = radial, shadow, vgrad
    module.pill, module.hp_bar = pill, hp_bar
    module.draw_icon, module.corner_ticks = draw_icon, corner_ticks
    module._has_glyph = lambda font, char: False
    for segment in rec.harvest(UI_THEME, ["letter", "fit_ellipsis"]):
        exec(compile(segment, UI_THEME.name, "exec"), module.__dict__)
    return module


def _environment(cheap_flag, clock):
    """Everything the harvested `PopupRenderer` / `BaseUIComponent` globals need."""
    pygame = rec.make_pygame(clock)
    core = _core_dicts(("TOWER_TYPE_INFO", "TOWER_TYPE_COLORS", "TOWER_UPGRADE_PATHS",
                        "TOWER_REGEN_SHIELD_MIN_LEVEL"),
                       extra=("GREEN", "YELLOW", "RED", "WHITE", "GRAY", "RED_LIGHT",
                              "GOLD", "SCREEN_WIDTH", "SCREEN_HEIGHT", "TOP_BAR_HEIGHT"))
    namespace = {
        "pygame": pygame, "math": __import__("math"),
        "ui_theme": _ui_theme(pygame, cheap_flag),
        "get_font": lambda size, style="body", bold=False: rec.Font(size, style),
        "title_font": lambda size, bold=True: rec.Font(max(8, min(int(size), 220)), "title"),
    }
    namespace.update(core)
    return pygame, namespace


def _harvest_base(namespace):
    text = _source(BUNDLE)
    body = _class_text(text, BASE_CLASS).split("\n", 1)[1]
    exec(compile("class %s:\n%s" % (BASE_CLASS, body), str(BUNDLE), "exec"), namespace)
    return namespace[BASE_CLASS]


def _harvest_popup(namespace):
    text = _source(BUNDLE)
    body = _class_text(text, POPUP_CLASS).split("\n", 1)[1]
    exec(compile("class %s(%s):\n%s" % (POPUP_CLASS, BASE_CLASS, body), str(BUNDLE), "exec"),
         namespace)
    cls = namespace[POPUP_CLASS]
    for name in SECTIONS:
        original = getattr(cls, name)

        def wrapped(self, surface, *args, _original=original, _name=name, **kwargs):
            surface.ops.append({"kind": "section", "name": _name})
            return _original(self, surface, *args, **kwargs)

        setattr(cls, name, wrapped)
    return cls


# ── inventory ──────────────────────────────────────────────────────────────
def inventory():
    files = {"_bundle.py": len(_source(BUNDLE).splitlines()),
             "__init__.py": len(_source(SHIM).splitlines())}
    return {"files": files, "count": len(files), "lines": sum(files.values())}


def module_ranges():
    lines = _source(BUNDLE).splitlines()
    markers = []
    for index, text in enumerate(lines, start=1):
        stripped = text.strip()
        for name in MODULES:
            if stripped.startswith(("# %s.py" % name, "# ui_components/%s.py" % name)):
                if not any(row["module"] == name for row in markers):
                    markers.append({"module": name, "marker": index})
    found = []
    for row in markers:
        start = row["marker"] - 1 if lines[row["marker"] - 2].startswith("# ====") \
            else row["marker"]
        found.append({"module": row["module"], "start": start})
    found.sort(key=lambda row: row["start"])
    for position, row in enumerate(found):
        end = found[position + 1]["start"] - 1 if position + 1 < len(found) else len(lines)
        row["end"] = end
        row["lines"] = end - row["start"] + 1
    return found


def ast_facts():
    tree = ast.parse(_source(BUNDLE))
    classes = {}
    constants = {}
    functions = {}
    members = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes[node.name] = sorted(member.name for member in node.body
                                        if isinstance(member, ast.FunctionDef))
            if node.name.startswith("_NS_"):
                rows = []
                for member in node.body:
                    if isinstance(member, ast.ClassDef):
                        rows.append({"kind": "class", "name": member.name,
                                     "methods": [sub.name for sub in member.body
                                                 if isinstance(sub, ast.FunctionDef)]})
                    elif isinstance(member, ast.FunctionDef):
                        rows.append({"kind": "function", "name": member.name, "methods": []})
                members[node.name] = rows
        elif isinstance(node, ast.FunctionDef):
            functions[node.name] = [arg.arg for arg in node.args.args]
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                constants[target.id] = ast.literal_eval(node.value)
    return {"classes": classes, "functions": functions, "constants": constants,
            "class_members": members}


def stubs():
    """Functions whose whole body is `pass` (or a docstring and `pass`)."""
    found = []
    tree = ast.parse(_source(BUNDLE))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef,)):
            continue
        body = [statement for statement in node.body
                if not (isinstance(statement, ast.Expr)
                        and isinstance(statement.value, ast.Constant)
                        and isinstance(statement.value.value, str))]
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            found.append({"name": node.name, "line": node.lineno})
    return sorted(found, key=lambda row: row["line"])


DUPLICATE_NAMES = ("Notification", "_FakeEntity", "_make_fake_boss", "_make_fake_hero")


def duplicates():
    """The folder keeps two `Notification` copies, two fake entities and two factory pairs."""
    tree = ast.parse(_source(BUNDLE))
    found = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef)) or node.name not in DUPLICATE_NAMES:
            continue
        found.setdefault(node.name, []).append(node)
    report = {}
    for name, nodes in found.items():
        dumps = {ast.dump(node) for node in nodes}
        report[name] = {"copies": len(nodes), "identical": len(dumps) == 1,
                        "lines": sorted(node.lineno for node in nodes)}
    return report


def call_index():
    if _INDEX:
        return _INDEX
    bare = {}
    qualified = {}
    for path in sorted(ROOT.rglob("*.py")):
        rel = str(path.relative_to(ROOT))
        if any(part in rel for part in ("godot_rebuild", ".venv", "__pycache__")):
            continue
        try:
            tree = ast.parse(_source(path))
        except SyntaxError:
            continue
        inside = rel.startswith("ui_components/")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            site = "%s:%d" % (rel, node.lineno)
            if isinstance(func, ast.Name):
                bare.setdefault(func.id, {"inside": [], "outside": []})[
                    "inside" if inside else "outside"].append(site)
            elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                key = "%s.%s" % (func.value.id, func.attr)
                qualified.setdefault(key, {"inside": [], "outside": []})[
                    "inside" if inside else "outside"].append(site)
    _INDEX.update({"bare": bare, "qualified": qualified})
    return _INDEX


_INDEX = {}


# ── executed: BaseUIComponent toolbox ──────────────────────────────────────
SHADOW_CASES = [
    {"rect": [100, 50, 200, 80], "alpha": 150, "border_radius": 8, "offset": [5, 5]},
    {"rect": [0, 0, 40, 40], "alpha": 90, "border_radius": 0, "offset": [3, 3]},
    {"rect": [640, 360, 380, 440], "alpha": 200, "border_radius": 12, "offset": [7, 2]},
]
HP_CASES = [
    {"x": 10, "y": 20, "w": 100, "h": 10, "ratio": 1.0, "show_bg": True},
    {"x": 10, "y": 20, "w": 100, "h": 10, "ratio": 0.51, "show_bg": True},
    {"x": 10, "y": 20, "w": 100, "h": 10, "ratio": 0.5, "show_bg": True},
    {"x": 10, "y": 20, "w": 100, "h": 10, "ratio": 0.26, "show_bg": True},
    {"x": 10, "y": 20, "w": 100, "h": 10, "ratio": 0.25, "show_bg": True},
    {"x": 10, "y": 20, "w": 99, "h": 6, "ratio": 0.0, "show_bg": False},
    {"x": 0, "y": 0, "w": 37, "h": 8, "ratio": 1.8, "show_bg": True},
]
CLOSE_CASES = [
    {"x": 340, "y": 6, "size": 22, "style": "rect", "hover": False},
    {"x": 340, "y": 6, "size": 22, "style": "rect", "hover": True},
    {"x": 100, "y": 100, "size": 44, "style": "rect", "hover": False},
    {"x": 100, "y": 100, "size": 44, "style": "circle", "hover": False},
    {"x": 100, "y": 100, "size": 44, "style": "circle", "hover": True},
]


def executed_base(namespace, base_cls):
    pygame = namespace["pygame"]
    shadow = []
    for case in SHADOW_CASES:
        surface = rec.Surface((1280, 720))
        component = base_cls.__new__(base_cls)
        component.game = SimpleNamespace(ui_buttons={})
        component._draw_shadow_rect(surface, pygame.Rect(case["rect"]), case["alpha"],
                                    case["border_radius"], tuple(case["offset"]))
        shadow.append({"case": case, "ops": surface.ops})
    hp = []
    for case in HP_CASES:
        surface = rec.Surface((200, 200))
        component = base_cls.__new__(base_cls)
        component.game = SimpleNamespace(ui_buttons={})
        component._draw_hp_bar(surface, case["x"], case["y"], case["w"], case["h"],
                               case["ratio"], case["show_bg"])
        hp.append({"case": case, "ops": surface.ops})
    close = []
    for case in CLOSE_CASES:
        surface = rec.Surface((1280, 720))
        component = base_cls.__new__(base_cls)
        component.game = SimpleNamespace(ui_buttons={})
        point = (case["x"] + case["size"] // 2, case["y"] + case["size"] // 2) \
            if case["hover"] else (0, 0)
        pygame.mouse = SimpleNamespace(get_pos=lambda point=point: point)
        rect = component._draw_close_button(surface, case["x"], case["y"], case["size"],
                                            "close", case["style"])
        close.append({"case": case, "ops": surface.ops,
                      "rect": list(rect), "buttons": {"close": list(rect)}})
    return {"shadow": shadow, "hp_bar": hp, "close_button": close,
            "green": list(namespace["GREEN"]), "yellow": list(namespace["YELLOW"]),
            "red": list(namespace["RED"]), "white": list(namespace["WHITE"])}


# ── executed: `_popup_di_panel` ────────────────────────────────────────────
PANEL_CASES = [
    {"label": "classic", "w": 380, "h": 440, "panel": None},
    {"label": "wide_fit", "w": 328, "h": 440, "panel": [1280, 0, 344, 720]},
    {"label": "narrow_fit", "w": 104, "h": 440, "panel": [1280, 0, 120, 720]},
    {"label": "too_wide", "w": 380, "h": 440, "panel": [1280, 0, 344, 720]},
    {"label": "tall", "w": 328, "h": 740, "panel": [1280, 0, 344, 720]},
]


def executed_popup_panel(namespace, display_state):
    found = []
    for case in PANEL_CASES:
        panel = case["panel"]
        if panel is None:
            display_state["panel"] = None
            display_state["full"] = None
        else:
            display_state["panel"] = namespace["pygame"].Rect(panel)
            display_state["full"] = rec.Surface((panel[0] + panel[2], panel[1] + panel[3]))
        result = namespace["_popup_di_panel"](case["w"], case["h"])
        if result is None:
            found.append({"case": case, "result": None})
            continue
        surface, x, y = result
        found.append({"case": case, "result": {"x": int(x), "y": int(y),
                                               "surface": list(surface.get_size())}})
    display_state["panel"] = None
    display_state["full"] = None
    return found


# ── executed: tower popup ─────────────────────────────────────────────────
class _FakeTower:
    """The `Tower` surface `PopupRenderer` touches, fields taken from `_entity.py`."""

    def __init__(self, **overrides):
        self.name = "Archer Tower"
        self.level = 3
        self.tower_type = "archer"
        self.color = (100, 220, 120)
        self.hp = 620.0
        self.max_hp = 1100
        self.damage = 26
        self.range = 190
        self.kills = 7
        self.lane = "mid"
        self.is_player_built = True
        self.regen_shield_active = False
        self.regen_shield_cost_value = 300
        self.regen_shield_ready = False
        self.splash = 0
        self.slow = 0.0
        self.chain = 1
        self.double_shot = False
        self.burn_dps = 0
        self.atk_slow = 0.0
        self.skill_down = 0.0
        self.x = 640.0
        self.y = 420.0
        self.__dict__.update(overrides)

    def can_upgrade(self):
        return self.level < 6

    def can_activate_regen_shield(self):
        return self.regen_shield_ready

    def regen_shield_cost(self):
        return self.regen_shield_cost_value

    def sell_value(self):
        return 40 + self.level * 25

    def upgrade_cost(self, path_type=None):
        return 325


TOWER_FRAMES = [
    {"label": "enemy", "tower": {"is_player_built": False, "level": 3}, "gold": 500,
     "hover": None, "cheap": True, "panel": None},
    {"label": "path_lv1", "tower": {"level": 1}, "gold": 9999, "hover": "popup_upgrade_path_ice",
     "cheap": True, "panel": None},
    {"label": "upgrade_locked", "tower": {"level": 3}, "gold": 100, "hover": None,
     "cheap": True, "panel": None},
    {"label": "upgrade_hover", "tower": {"level": 3}, "gold": 9999,
     "hover": "popup_upgrade_tower", "cheap": False, "panel": None},
    {"label": "max_level", "tower": {"level": 6}, "gold": 500,
     "hover": "popup_sell_tower", "cheap": True, "panel": None},
    {"label": "regen_buy", "tower": {"level": 4, "regen_shield_ready": True}, "gold": 900,
     "hover": "popup_regen_shield", "cheap": True, "panel": None},
    {"label": "regen_on", "tower": {"level": 4, "regen_shield_ready": True,
                                    "regen_shield_active": True}, "gold": 100,
     "hover": None, "cheap": True, "panel": None},
    {"label": "specials", "tower": {"level": 5, "splash": 40, "slow": 0.35, "chain": 3,
                                    "double_shot": True, "burn_dps": 8, "atk_slow": 0.2,
                                    "skill_down": 0.25}, "gold": 9999, "hover": None,
     "cheap": True, "panel": None},
    {"label": "panel_wide", "tower": {"level": 2}, "gold": 9999, "hover": "popup_close",
     "cheap": True, "panel": [1280, 0, 344, 720]},
    {"label": "panel_narrow", "tower": {"level": 1}, "gold": 0, "hover": None,
     "cheap": True, "panel": [1280, 0, 180, 720]},
]


def _tower_frames(namespace, cls, pygame, display_state, cheap_flag):
    frames = []
    for frame in TOWER_FRAMES:
        cheap_flag["cheap"] = frame["cheap"]
        panel_rect = frame["panel"]
        screen = rec.Surface((1280, 720))
        if panel_rect is None:
            display_state["panel"] = None
            display_state["full"] = screen
        else:
            display_state["panel"] = pygame.Rect(panel_rect)
            display_state["full"] = rec.Surface((panel_rect[0] + panel_rect[2],
                                                 panel_rect[1] + panel_rect[3]))
        # pass 1: no mouse, learn where the buttons land
        pygame.mouse = SimpleNamespace(get_pos=lambda: (0, 0))
        popup = cls.__new__(cls)
        popup.game = SimpleNamespace(popup_target=_FakeTower(**frame["tower"]),
                                     popup_type="tower", gold=frame["gold"],
                                     ui_buttons={}, blue_base=None, red_base=None)
        popup.ui = SimpleNamespace(font_small=rec.Font(14, "body_medium"))
        popup.draw(screen)
        buttons = {key: list(value) for key, value in popup.game.ui_buttons.items()}
        point = (0, 0)
        if frame["hover"] is not None and frame["hover"] in buttons:
            box = buttons[frame["hover"]]
            point = (int(box[0] + box[2] // 2), int(box[1] + box[3] // 2))
        pygame.mouse = SimpleNamespace(get_pos=lambda point=point: point)
        screen = rec.Surface((1280, 720))
        if panel_rect is None:
            display_state["panel"] = None
            display_state["full"] = screen
        else:
            display_state["panel"] = pygame.Rect(panel_rect)
            display_state["full"] = rec.Surface((panel_rect[0] + panel_rect[2],
                                                 panel_rect[1] + panel_rect[3]))
        popup = cls.__new__(cls)
        popup.game = SimpleNamespace(popup_target=_FakeTower(**frame["tower"]),
                                     popup_type="tower", gold=frame["gold"],
                                     ui_buttons={}, blue_base=None, red_base=None)
        popup.ui = SimpleNamespace(font_small=rec.Font(14, "body_medium"))
        popup.draw(screen)
        buttons = {key: list(value) for key, value in popup.game.ui_buttons.items()}
        target = display_state["full"]
        ops = list(target.ops) if target is not screen else list(screen.ops)
        frames.append({"label": frame["label"], "tower": frame["tower"],
                       "gold": frame["gold"], "hover": frame["hover"],
                       "cheap_alpha": frame["cheap"],
                       "panel": panel_rect, "mouse": [int(point[0]), int(point[1])],
                       "target_surface": [int(target.get_size()[0]), int(target.get_size()[1])],
                       "buttons": buttons, "ops": ops})
    display_state["panel"] = None
    display_state["full"] = None
    return frames


SPECIAL_CASES = [
    {"label": "plain", "tower": {}},
    {"label": "splash_slow", "tower": {"splash": 40, "slow": 0.35}},
    {"label": "chain_double", "tower": {"chain": 3, "double_shot": True}},
    {"label": "burn_slow", "tower": {"burn_dps": 8, "atk_slow": 0.2}},
    {"label": "skill_down", "tower": {"skill_down": 0.25}},
    {"label": "all", "tower": {"splash": 40, "slow": 0.35, "chain": 3, "double_shot": True,
                               "burn_dps": 8, "atk_slow": 0.2, "skill_down": 0.25}},
]


def executed_specials(cls):
    found = []
    popup = cls.__new__(cls)
    for case in SPECIAL_CASES:
        tower = _FakeTower(**case["tower"])
        found.append({"case": case, "specials": list(cls._get_tower_specials(popup, tower))})
    return found


# ── classification ─────────────────────────────────────────────────────────
NOTE_PORTRAIT = "baked/native portrait painters take (id, definition) instead of a fake entity"
NOTE_SHOP = "Control nodes paint the card; the op painter itself is superseded"
NOTE_NOTIFY = "source disabled notifications (``_core.UI.add_notification`` is a no-op)"
NOTE_TOWER = "this layer ports the tower popup frame + content"

MODULE_TARGETS = {
    "base_ui": ("native", "scripts/ui/ui_component_base.gd", "func shadow_ops(", ""),
    "hero_portraits": ("ported", "scripts/ui/hero_portrait.gd", "const GENERIC_PAINTER",
                       NOTE_PORTRAIT),
    "build_popup": ("ported", "scripts/ui/build_popup_layout.gd", "_tower_buttons(", ""),
    "build_slots": ("bake", "bake/bake_slot_atlas.py", "BuildSlots", ""),
    "hero_panel": ("ported", "scripts/ui/hero_panel_layout.gd", "static func ops(", ""),
    "hero_shop": ("ported", "scripts/ui/hero_shop_panel.gd", "func _build() -> void:", NOTE_SHOP),
    "hover_indicators": ("ported", "scripts/ui/tower_hover_layout.gd", "static func ops(", ""),
    "notification": ("dead", "", "", NOTE_NOTIFY),
    "overlay": ("ported", "scripts/ui/end_overlay_layout.gd", "static func ops(", ""),
    "popup_renderer": ("native", "scripts/ui/tower_popup_layout.gd", "func ops(", NOTE_TOWER),
    "shop_hints": ("ported", "scripts/ui/shop_hint_layout.gd", "static func ops(", ""),
}

CLASS_TARGETS = {
    "base_ui:BaseUIComponent": ("native", "scripts/ui/ui_component_base.gd", "func shadow_ops(", ""),
    "hero_portraits:HeroPortraits": ("ported", "scripts/ui/hero_portrait.gd",
                                     "const GENERIC_PAINTER", NOTE_PORTRAIT),
    "hero_portraits:_FakeEntity": ("ported", "scripts/ui/hero_portrait.gd",
                                   "func setup(id: String", NOTE_PORTRAIT),
    "build_popup:BuildPopup": ("ported", "scripts/ui/build_popup_layout.gd", "_tower_buttons(", ""),
    "build_slots:BuildSlots": ("bake", "bake/bake_slot_atlas.py", "BuildSlots", ""),
    "hero_panel:HeroPanel": ("ported", "scripts/ui/hero_panel_layout.gd", "static func ops(", ""),
    "hero_panel:_FakeEntity": ("dead", "", "", "panel copy of the portrait fake entity"),
    "hero_shop:HeroShop": ("ported", "scripts/ui/hero_shop_panel.gd", "func _build() -> void:",
                           NOTE_SHOP),
    "hover_indicators:HoverIndicators": ("ported", "scripts/ui/tower_hover_layout.gd",
                                         "static func ops(", ""),
    "hover_indicators:Notification": ("dead", "", "", NOTE_NOTIFY),
    "notification:Notification": ("dead", "", "", NOTE_NOTIFY),
    "overlay:Overlay": ("ported", "scripts/ui/end_overlay_layout.gd", "static func ops(", ""),
    "popup_renderer:PopupRenderer": ("native", "scripts/ui/tower_popup_layout.gd", "func ops(",
                                     NOTE_TOWER),
    "shop_hints:ShopHints": ("ported", "scripts/ui/shop_hint_layout.gd", "static func ops(", ""),
}

METHOD_TARGETS = {
    "_bundle:_popup_di_panel": ("native", "scripts/ui/ui_component_base.gd",
                                "func panel_position(", ""),
    "base_ui:BaseUIComponent.__init__": ("native", "scripts/ui/ui_component_base.gd",
                                         "func shadow_ops(", ""),
    "base_ui:BaseUIComponent.draw": ("meta", "", "", "abstract hook; Godot uses op builders"),
    "base_ui:BaseUIComponent._draw_shadow_rect": ("native", "scripts/ui/ui_component_base.gd",
                                                  "func shadow_ops(", ""),
    "base_ui:BaseUIComponent._draw_hp_bar": ("native", "scripts/ui/ui_component_base.gd",
                                             "func hp_bar_ops(", ""),
    "base_ui:BaseUIComponent._draw_close_button": ("native", "scripts/ui/ui_component_base.gd",
                                                   "func close_button_ops(", ""),
    "hero_portraits:HeroPortraits.draw": ("ported", "scripts/ui/hero_portrait.gd",
                                          "func setup(id: String", NOTE_PORTRAIT),
    "hero_portraits:HeroPortraits._try_auto_render": ("ported", "scripts/ui/hero_portrait.gd",
                                                      "const GENERIC_PAINTER", ""),
    "hero_portraits:HeroPortraits._try_boss_renderer": ("ported", "scripts/ui/hero_portrait.gd",
                                                        "static func custom_ids()", ""),
    "hero_portraits:HeroPortraits._try_hero_renderer": ("ported", "scripts/ui/hero_portrait.gd",
                                                        "static func has_custom(", ""),
    "hero_portraits:HeroPortraits._crop_and_scale": ("ported", "scripts/ui/hero_portrait.gd",
                                                     "func _scale(box: Rect2)", ""),
    "hero_portraits:HeroPortraits._apply_grayscale": ("deviation", "", "",
                                                      "un-owned portrait desaturation is not "
                                                      "reproduced; the locked card tint carries "
                                                      "the state (see doc, deviation D1)"),
    "hero_portraits:HeroPortraits.clear_cache": ("meta", "", "", "no portrait cache in Godot"),
    "hero_portraits:HeroPortraits._draw_generic": ("ported", "scripts/ui/hero_portrait_generic.gd",
                                                   "static func paint(", ""),
    "hero_portraits:_make_fake_boss": ("ported", "scripts/ui/hero_portrait.gd",
                                       "func setup(id: String", NOTE_PORTRAIT),
    "hero_portraits:_make_fake_hero": ("ported", "scripts/ui/hero_portrait.gd",
                                       "func setup(id: String", NOTE_PORTRAIT),
    "build_popup:BuildPopup.draw": ("ported", "scripts/ui/build_popup_layout.gd",
                                    "static func ops(", ""),
    "build_popup:BuildPopup._draw_tower_buttons": ("ported",
                                                   "scripts/ui/build_popup_layout.gd",
                                                   "_tower_buttons(", ""),
    "build_slots:BuildSlots.draw": ("bake", "bake/bake_slot_atlas.py", "BuildSlots", ""),
    "build_slots:BuildSlots._render_blue_slot_surface": ("bake", "bake/bake_slot_atlas.py",
                                                         "BuildSlots", ""),
    "build_slots:BuildSlots._render_red_slot_surface": ("bake", "bake/bake_slot_atlas.py",
                                                        "BuildSlots", ""),
    "build_slots:BuildSlots._draw_blue_slot": ("ported", "scripts/ui/slot_art.gd",
                                               "static func manifest()", ""),
    "build_slots:BuildSlots._draw_red_slot": ("ported", "scripts/ui/slot_art.gd",
                                              "const BLUE := 0", ""),
    "hero_panel:HeroPanel.draw": ("ported", "scripts/ui/hero_panel_layout.gd",
                                  "static func ops(", ""),
    "hero_panel:HeroPanel._draw_item_shop_button": ("ported",
                                                    "scripts/ui/hero_panel_layout.gd",
                                                    "_item_shop_button(", ""),
    "hero_panel:HeroPanel._draw_upgrade_button": ("ported", "scripts/ui/hero_panel_layout.gd",
                                                  "_upgrade_button(", ""),
    "hero_panel:HeroPanel._draw_autocast_toggle": ("ported", "scripts/ui/hero_panel_layout.gd",
                                                   "_autocast_toggle(", ""),
    "hero_panel:HeroPanel._skill_key_label": ("ported", "scripts/ui/hero_panel_layout.gd",
                                              "key_letter", ""),
    "hero_panel:HeroPanel._draw_skill_slot": ("ported", "scripts/ui/hero_panel_layout.gd",
                                              "_draw_skill_slot(", ""),
    "hero_panel:_make_fake_boss": ("dead", "", "", "panel copy of the portrait fake entity"),
    "hero_panel:_make_fake_hero": ("dead", "", "", "panel copy of the portrait fake entity"),
    "hover_indicators:HoverIndicators.update": ("ported",
                                                "scenes/prototype/prototype_view.gd",
                                                "func _draw_tower_hover() -> void:", ""),
    "hover_indicators:HoverIndicators.draw": ("ported", "scenes/prototype/prototype_view.gd",
                                              "func _draw_slot_hover() -> void:", ""),
    "hover_indicators:HoverIndicators._draw_tower_range_hover": ("ported",
                                                                 "scripts/ui/tower_hover_layout.gd",
                                                                 "static func ops(", ""),
    "hover_indicators:HoverIndicators._draw_tower_tooltip": ("ported",
                                                             "scripts/ui/tower_hover_layout.gd",
                                                             "static func ops(", ""),
    "hover_indicators:HoverIndicators._draw_slot_hover": ("ported",
                                                          "scripts/ui/slot_hover_layout.gd",
                                                          "static func ops(", ""),
    "overlay:Overlay.__init__": ("ported", "scripts/ui/end_overlay_layout.gd",
                                 "static func ops(", ""),
    "overlay:Overlay.draw": ("ported", "scripts/ui/end_overlay_layout.gd", "static func ops(", ""),
    "overlay:Overlay._update_unlock_popup": ("ported", "scripts/ui/end_overlay_layout.gd",
                                             "_update_unlock_popup", ""),
    "overlay:Overlay._get_newly_unlocked_level": ("ported",
                                                  "scenes/prototype/prototype_screen.gd",
                                                  "newly_unlocked", ""),
    "popup_renderer:PopupRenderer.draw": ("native", "scripts/ui/tower_popup_layout.gd",
                                          "func ops(", NOTE_TOWER),
    "popup_renderer:PopupRenderer._draw_nexus_content": ("ported",
                                                         "scripts/ui/castle_panel_layout.gd",
                                                         "static func shield_rect(", ""),
    "popup_renderer:PopupRenderer._draw_castle_shield_section": ("ported",
                                                                 "scripts/ui/castle_panel_layout.gd",
                                                                 "\"castle_shield\":", ""),
    "popup_renderer:PopupRenderer._draw_nexus_upgrade": ("ported",
                                                         "scripts/ui/castle_panel_layout.gd",
                                                         "\"castle_upgrade\":", ""),
    "popup_renderer:PopupRenderer._draw_tower_content": ("native",
                                                         "scripts/ui/tower_popup_layout.gd",
                                                         "static func _content_ops(", NOTE_TOWER),
    "popup_renderer:PopupRenderer._draw_regen_shield_section": ("native",
                                                                "scripts/ui/tower_popup_layout.gd",
                                                                "func regen_section(", ""),
    "popup_renderer:PopupRenderer._get_tower_specials": ("native",
                                                         "scripts/ui/tower_popup_layout.gd",
                                                         "static func tower_specials(", ""),
    "popup_renderer:PopupRenderer._draw_tower_max_level": ("native",
                                                           "scripts/ui/tower_popup_layout.gd",
                                                           "func max_level_ops(", ""),
    "popup_renderer:PopupRenderer._draw_tower_path_buttons": ("native",
                                                              "scripts/ui/tower_popup_layout.gd",
                                                              "func path_buttons_ops(", ""),
    "popup_renderer:PopupRenderer._draw_single_path_button": ("native",
                                                              "scripts/ui/tower_popup_layout.gd",
                                                              "func path_button_ops(", ""),
    "popup_renderer:PopupRenderer._draw_tower_upgrade_button": ("native",
                                                                "scripts/ui/tower_popup_layout.gd",
                                                                "func upgrade_button_ops(", ""),
    "shop_hints:ShopHints.draw": ("ported", "scripts/ui/shop_hint_layout.gd",
                                  "static func ops(", ""),
    "shop_hints:ShopHints._draw_single_hint": ("ported", "scripts/ui/shop_hint_layout.gd",
                                               "static func ops(", ""),
    "shim:_EXTRA": ("meta", "", "", "sys.modules shim for the 10 merged namespaces"),
    "shim:_PLAIN_SYMS": ("meta", "", "", "sys.modules shim for base_ui"),
    "shim:_install_aliases": ("meta", "", "", "no shim needed: Godot has real modules"),
}

HERO_SHOP_SYMBOLS = ["draw", "_render_shop", "_draw_overlay", "_draw_panel", "_draw_header",
                     "_draw_title", "_draw_gold_info", "_draw_owned_info",
                     "_draw_shop_close_button", "_draw_hero_cards", "_draw_compact_card",
                     "_draw_scroll_indicator", "_draw_card", "_draw_card_bg",
                     "_draw_card_border", "_draw_card_portrait", "_draw_card_info",
                     "_draw_card_stats", "_draw_card_skill", "_draw_card_button",
                     "_draw_button_owned", "_draw_button_max", "_draw_button_buy",
                     "_draw_button_cant_afford"]


def symbol_list():
    found = ["module:" + name for name in MODULES]
    tree = ast.parse(_source(BUNDLE))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            found.append("_bundle:" + node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    found.append("bundle_alias:" + target.attr)
    for name, methods in ast_facts()["classes"].items():
        if name.startswith("_NS_"):
            namespace = name[4:]
            for member in ast_facts()["class_members"].get(name, []):
                if member["kind"] == "class":
                    found.append("%s:%s" % (namespace, member["name"]))
                    for method in member["methods"]:
                        found.append("%s:%s.%s" % (namespace, member["name"], method))
                else:
                    found.append("%s:%s" % (namespace, member["name"]))
        elif name == BASE_CLASS:
            found.append("base_ui:BaseUIComponent")
            for method in methods:
                found.append("base_ui:BaseUIComponent.%s" % method)
    found += ["shim:_EXTRA", "shim:_PLAIN_SYMS", "shim:_install_aliases"]
    return found


def _resolve(symbol):
    if symbol in METHOD_TARGETS:
        return METHOD_TARGETS[symbol]
    if symbol.startswith("module:"):
        return MODULE_TARGETS[symbol.split(":", 1)[1]]
    if symbol in CLASS_TARGETS:
        return CLASS_TARGETS[symbol]
    if symbol.startswith("bundle_alias:"):
        return ("meta", "", "", "re-export of the hero_portraits class into hero_panel")
    if ":" in symbol:
        namespace, rest = symbol.split(":", 1)
        key = "%s:%s" % (namespace, rest.split(".", 1)[0])
        if key in CLASS_TARGETS:
            return CLASS_TARGETS[key]
        if namespace == "hero_shop" and rest.split(".", 1)[0] == "HeroShop":
            return ("ported", "scripts/ui/hero_shop_card.gd", "func _init() -> void:", NOTE_SHOP)
    raise AssertionError("unclassified symbol: %s" % symbol)


def classification():
    rows = []
    for symbol in symbol_list():
        kind, target, token, note = _resolve(symbol)
        if target and not target.startswith("godot_rebuild/"):
            target = "godot_rebuild/" + target
        rows.append({"symbol": symbol, "kind": kind, "target": target, "token": token,
                     "note": note})
    kinds = {}
    for row in rows:
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
    return {"rows": rows, "kinds": kinds, "count": len(rows)}


def dead_helpers():
    """Source methods no live path reaches (bare or attribute calls, anywhere in the tree)."""
    called = set()
    for path in sorted(ROOT.rglob("*.py")):
        rel = str(path.relative_to(ROOT))
        if any(part in rel for part in ("godot_rebuild", ".venv", "__pycache__")):
            continue
        try:
            tree = ast.parse(_source(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name:
                    called.add(name)
            elif isinstance(node, ast.Attribute):
                called.add(node.attr)
            elif isinstance(node, ast.Name):
                called.add(node.id)
    found = []
    for symbol in symbol_list():
        if ":" not in symbol or "." not in symbol.split(":", 1)[1]:
            continue
        name = symbol.rsplit(".", 1)[1]
        if name.startswith("__") or name in called:
            continue
        found.append({"symbol": symbol, "calls": 0})
    return found


def notification_evidence():
    text = _source(CORE)
    lines = text.splitlines()
    hits = [index for index, line in enumerate(lines, start=1)
            if line.strip().startswith("def add_notification") or
            "SISTEM NOTIFIKASI" in line or "notifikasi in-game tidak lagi" in line or
            "notifikasi DIHAPUS" in line]
    return {"lines": hits, "note": "`_core.UI.add_notification` is documented as removed; "
                                  "`draw_notifications` returns immediately"}


# ── fixture ────────────────────────────────────────────────────────────────
def _clean_ops(ops):
    cleaned = []
    for op in ops:
        row = {key: value for key, value in op.items() if key != "mult"}
        cleaned.append(row)
    return cleaned


def _clean_frame(frame):
    row = dict(frame)
    row["ops"] = _clean_ops(frame["ops"])
    return row


def source_fixture():
    if not hasattr(rec.Rect, "center"):
        rec.Rect.center = property(lambda self: (self.x + self.w // 2, self.y + self.h // 2))
    clock = {"ticks": 0}
    cheap_flag = {"cheap": True}
    pygame, namespace = _environment(cheap_flag, clock)
    display_state = {"panel": None, "full": None}
    mobile = types.ModuleType("mobile")
    platform_utils = types.ModuleType("mobile.platform_utils")
    platform_utils._display_state = display_state
    platform_utils.get_panel_rect = lambda: display_state["panel"]
    platform_utils.get_full_surface = lambda: display_state["full"]
    for segment in rec.harvest(PLATFORM_UTILS, ["panel_popup_pos"]):
        exec(compile(segment, str(PLATFORM_UTILS), "exec"), platform_utils.__dict__)
    mobile.platform_utils = platform_utils
    with rec.installed({"mobile": mobile, "mobile.platform_utils": platform_utils}):
        for segment in rec.harvest(BUNDLE, ["_popup_di_panel"]):
            exec(compile(segment, str(BUNDLE), "exec"), namespace)
        base_cls = _harvest_base(namespace)
        popup_cls = _harvest_popup(namespace)
        base = executed_base(namespace, base_cls)
        for key in ("shadow", "hp_bar", "close_button"):
            base[key] = [dict(row, ops=_clean_ops(row["ops"])) for row in base[key]]
        panel = executed_popup_panel(namespace, display_state)
        specials = executed_specials(popup_cls)
        tower_frames = _tower_frames(namespace, popup_cls, pygame, display_state, cheap_flag)
    data = inventory()
    facts = ast_facts()
    table = classification()
    symbols = symbol_list()
    class_count = sum(1 for symbol in symbols if symbol in CLASS_TARGETS)
    method_count = sum(1 for symbol in symbols
                       if ":" in symbol and "." in symbol.split(":", 1)[1])
    helper_count = len(symbols) - len(MODULES) - class_count - method_count
    return {
        "folder": data,
        "modules": module_ranges(),
        "namespaces": NAMESPACES,
        "symbols": {"count": table["count"], "modules": len(MODULES),
                    "classes": class_count, "methods": method_count,
                    "helpers": helper_count},
        "classification": {row["symbol"]: {"kind": row["kind"], "target": row["target"],
                                           "token": row["token"], "note": row["note"]}
                           for row in table["rows"]},
        "classification_kinds": table["kinds"],
        "classes": facts["classes"],
        "constants": facts["constants"],
        "stubs": stubs(),
        "duplicates": duplicates(),
        "dead_helpers": dead_helpers(),
        "notifications": notification_evidence(),
        "glyph_factor": rec.GLYPH_FACTOR,
        "colors": {"gold": list(namespace["GOLD"]), "white": list(namespace["WHITE"]),
                   "red_light": list(namespace["RED_LIGHT"])},
        "base": {"shadow": base["shadow"], "hp_bar": base["hp_bar"],
                 "close_button": base["close_button"],
                 "green": base["green"], "yellow": base["yellow"], "red": base["red"]},
        "popup_panel": panel,
        "specials": specials,
        "tower_popup": [_clean_frame(frame) for frame in tower_frames],
        "tower_data": {"types": sorted(tower_data()["types"]),
                       "levels": {name: sorted(levels)
                                  for name, levels in tower_data()["paths"].items()}},
    }


def tower_data():
    """`_core.py` tower tables the popup renders, shipped as runtime data."""
    core = _core_dicts(("TOWER_TYPE_INFO", "TOWER_TYPE_COLORS", "TOWER_UPGRADE_PATHS"))
    types = {}
    for name in sorted(core["TOWER_TYPE_INFO"]):
        info = core["TOWER_TYPE_INFO"][name]
        types[name] = {
            "name": info["name"],
            "special": info["special"],
            "desc": info["desc"],
            "color": list(core["TOWER_TYPE_COLORS"][name]["main"]),
        }
    paths = {}
    for name in sorted(core["TOWER_UPGRADE_PATHS"]):
        paths[name] = {str(level): dict(stats)
                       for level, stats in sorted(core["TOWER_UPGRADE_PATHS"][name].items())}
    return {
        "source": "ui_components/_bundle.py PopupRenderer path/upgrade buttons + _core.py "
                  "TOWER_TYPE_INFO / TOWER_TYPE_COLORS / TOWER_UPGRADE_PATHS",
        "types": types,
        "paths": paths,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the JSON fixture")
    parser.add_argument("--check", action="store_true", help="compare against the fixture")
    args = parser.parse_args(argv)
    data = source_fixture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(data, indent=1, sort_keys=False) + "\n", encoding="utf-8")
        TOWER_DATA.write_text(json.dumps(tower_data(), indent=1) + "\n", encoding="utf-8")
        print("wrote %s (%d symbols, %d tower frames) and %s" %
              (FIXTURE, data["symbols"]["count"], len(data["tower_popup"]), TOWER_DATA))
        return 0
    existing = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.exists() else None
    if args.check and existing != data:
        print("FAIL: fixture is stale; rerun with --write")
        return 1
    print(json.dumps({key: data[key] for key in
                      ("symbols", "classification_kinds", "stubs", "duplicates", "dead_helpers")},
                     indent=1)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
