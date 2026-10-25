"""Layer 9bv8: record the real HeroPanel and six-slot item renderer.

The source methods run with the shared draw recorder and the real ui_theme
helpers; gradients, radial glows and shadows are represented by the same
single cached-surface operations used by the other Godot draw oracles. The
fixture records six representative panel states plus button geometry.

Run: python godot_rebuild/tests/hero_panel_draw_source_oracle.py
"""
import ast
import json
import textwrap
import types
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "ui_components" / "_bundle.py"
HERO_ITEMS = ROOT / "hero_items.py"
CORE = ROOT / "_core.py"
UI_THEME = ROOT / "ui_theme.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_panel_draw_source.json"
PANEL_METHODS = (
    "draw",
    "_draw_item_shop_button",
    "_draw_upgrade_button",
    "_draw_autocast_toggle",
    "_skill_key_label",
    "_draw_skill_slot",
)
THEME_COLORS = (
    "PANEL_TOP",
    "PANEL_BOTTOM",
    "PANEL_FILL",
    "EDGE_GOLD",
    "GOLD",
    "GOLD_TEXT",
    "TEXT_WHITE",
    "TEXT_BODY",
    "TEXT_DIM",
    "TEXT_FAINT",
    "SLATE",
    "GREEN",
    "RED",
)
ACTIVE_TIMERS = (
    "blood_frenzy_timer",
    "guard_timer",
    "veil_timer",
    "static_timer",
    "rend_timer",
    "thorn_timer",
    "gale_timer",
    "ghost_timer",
)


def _item(item_id, name, color, glow, active=False, cooldown=0):
    return {
        "id": item_id,
        "name": name,
        "color": list(color),
        "glow": list(glow),
        "active": bool(active),
        "cooldown": int(cooldown),
    }


# Input state is kept next to the harvested source ops so the GDScript replay
# covers empty/filled inventory, all cooldown states, hover, affordability,
# max level, the mobile panel anchor and the cheap-alpha fallback.
FRAMES = [
    {
        "label": "ready_fallback",
        "state": {
            "alive": True,
            "name": "Kaizen",
            "level": 1,
            "max_level": 15,
            "hp": 900,
            "max_hp": 1000,
            "color": [100, 190, 245],
            "gold": 500,
            "upgrade_cost": 300,
            "auto_cast": False,
            "cooldowns": [0, 0, 0, 0],
            "cooldown_max": [180, 240, 420, 900],
            "items": [],
            "mouse": [160, 621],
            "cheap_alpha": True,
            "panel_pos": None,
            "ticks": 0,
        },
    },
    {
        "label": "low_hp_autocast",
        "state": {
            "alive": True,
            "name": "Thorne",
            "level": 4,
            "max_level": 15,
            "hp": 250,
            "max_hp": 1000,
            "color": [175, 100, 78],
            "gold": 2400,
            "upgrade_cost": 1200,
            "auto_cast": True,
            "cooldowns": [45, 0, 160, 600],
            "cooldown_max": [180, 240, 420, 900],
            "items": [
                _item("demon_maw", "Demon Maw", (180, 30, 30), (255, 70, 70), False, 440),
            ],
            "mouse": [160, 553],
            "cheap_alpha": True,
            "panel_pos": None,
            "ticks": 125,
        },
    },
    {
        "label": "locked_flat",
        "state": {
            "alive": True,
            "name": "A Very Long Hero Name That Must Be Truncated",
            "level": 7,
            "max_level": 15,
            "hp": 600,
            "max_hp": 1200,
            "color": [225, 112, 82],
            "gold": 300,
            "upgrade_cost": 4800,
            "auto_cast": False,
            "cooldowns": [1, 30, 210, 899],
            "cooldown_max": [180, 240, 420, 900],
            "items": [
                _item("steel_aegis", "Steel Aegis", (180, 200, 230), (120, 170, 255)),
            ],
            "mouse": [160, 649],
            "cheap_alpha": False,
            "panel_pos": None,
            "ticks": 0,
        },
    },
    {
        "label": "mobile_anchor_hover_close",
        "state": {
            "alive": True,
            "name": "The Unreasonably Long Hero Title",
            "level": 10,
            "max_level": 15,
            "hp": 750,
            "max_hp": 1000,
            "color": [150, 130, 235],
            "gold": 20000,
            "upgrade_cost": 8000,
            "auto_cast": True,
            "cooldowns": [0, 0, 120, 0],
            "cooldown_max": [180, 240, 420, 900],
            "items": [
                _item("demon_maw", "Demon Maw", (180, 30, 30), (255, 70, 70), True, 0),
            ],
            "mouse": [1240, 437],
            "cheap_alpha": True,
            "panel_pos": [975, 420],
            "ticks": 231,
        },
    },
    {
        "label": "max_level_full_inventory_flat",
        "state": {
            "alive": True,
            "name": "Nyxareth",
            "level": 15,
            "max_level": 15,
            "hp": 1520,
            "max_hp": 1520,
            "color": [178, 88, 220],
            "gold": 99999,
            "upgrade_cost": 0,
            "auto_cast": False,
            "cooldowns": [0, 0, 0, 0],
            "cooldown_max": [180, 240, 420, 900],
            "items": [
                _item("steel_aegis", "Steel Aegis", (180, 200, 230), (120, 170, 255)),
                _item("dead_edge", "Dead Edge", (220, 60, 60), (255, 90, 90)),
                _item("demon_maw", "Demon Maw", (180, 30, 30), (255, 70, 70), False, 0),
                _item("thunder_coil", "Thunder Coil", (160, 190, 255), (100, 140, 255), False),
                _item("tempest_vane", "Tempest Vane", (90, 190, 220), (100, 230, 255), False),
                _item("sanguine_thorn", "Sanguine Thorn", (190, 60, 110), (255, 90, 145), False),
            ],
            "mouse": [0, 0],
            "cheap_alpha": False,
            "panel_pos": None,
            "ticks": 0,
        },
    },
    {
        "label": "hover_upgrade",
        "state": {
            "alive": True,
            "name": "Garruk",
            "level": 2,
            "max_level": 15,
            "hp": 325,
            "max_hp": 1000,
            "color": [170, 190, 110],
            "gold": 600,
            "upgrade_cost": 500,
            "auto_cast": True,
            "cooldowns": [55, 0, 1, 300],
            "cooldown_max": [180, 240, 420, 900],
            "items": [],
            "mouse": [160, 649],
            "cheap_alpha": True,
            "panel_pos": None,
            "ticks": 500,
        },
    },
]


def _constant(path, name):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("%s not found in %s" % (name, path.name))


def _class_node(text, name, top_level=False):
    nodes = ast.parse(text).body
    if not top_level:
        nodes = list(ast.walk(ast.Module(body=nodes, type_ignores=[])))
    return next(
        (node for node in nodes if isinstance(node, ast.ClassDef) and node.name == name),
        None,
    )


def _method(text, class_name, name):
    tree = ast.parse(text)
    owner = next(
        (node for node in ast.walk(tree)
         if isinstance(node, ast.ClassDef) and node.name == class_name),
        None,
    )
    if owner is None:
        raise AssertionError("%s not found in %s" % (class_name, BUNDLE.name))
    method = next(
        (node for node in owner.body
         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name),
        None,
    )
    if method is None:
        raise AssertionError("%s.%s not found in %s" % (class_name, name, BUNDLE.name))
    return ast.get_source_segment(text, method, padded=True)


def _compile_hero_panel(namespace):
    text = BUNDLE.read_text(encoding="utf-8")
    methods = [
        ("BaseUIComponent", "_draw_close_button"),
        *(("HeroPanel", name) for name in PANEL_METHODS),
    ]
    body = "".join(
        textwrap.indent(textwrap.dedent(_method(text, owner, name)), "    ") + "\n"
        for owner, name in methods
    )
    exec(compile("class HeroPanel:\n%s" % body, BUNDLE.name, "exec"), namespace)
    return namespace["HeroPanel"]


def _surface_with(op, width, height):
    surface = rec.Surface((width, height))
    surface.ops.append(op)
    return surface


def _ui_theme(pygame, cheap_flag):
    module = types.ModuleType("ui_theme")
    module.pygame = pygame
    for name in THEME_COLORS:
        value = _constant(UI_THEME, name)
        setattr(module, name, list(value) if isinstance(value, tuple) else value)
    module.cheap_alpha = lambda: bool(cheap_flag["cheap"])
    module._has_glyph = lambda _font, _character: False

    def radial(width, height, color, alpha):
        actual_alpha = max(4, min(120, int(alpha) // 8 * 8))
        op = {
            "kind": "radial",
            "rect": [0, 0, int(width), int(height)],
            "color": list(color),
            "alpha": actual_alpha,
            "mult": 255,
        }
        return _surface_with(op, width, height)

    def shadow(width, height, radius=12, alpha=110, spread=4):
        out_w, out_h = int(width) + spread * 2, int(height) + spread * 2
        op = {
            "kind": "shadow",
            "rect": [0, 0, out_w, out_h],
            "radius": int(radius),
            "alpha": int(alpha),
            "mult": 255,
        }
        return _surface_with(op, out_w, out_h)

    def vgrad(width, height, top, bottom, radius=0):
        op = {
            "kind": "vgrad",
            "rect": [0, 0, int(width), int(height)],
            "top": list(top),
            "bottom": list(bottom),
            "radius": int(radius),
            "mult": 255,
        }
        return _surface_with(op, width, height)

    module._radial, module._shadow, module._vgrad = radial, shadow, vgrad
    for segment in rec.harvest(
        UI_THEME, ["letter", "draw_text", "draw_icon", "corner_ticks", "panel", "hp_bar", "pill", "fit_ellipsis"]
    ):
        exec(compile(segment, UI_THEME.name, "exec"), module.__dict__)
    return module


def _patch_recorder_geometry():
    if not hasattr(rec.Rect, "center"):
        rec.Rect.center = property(lambda rect: (rect.x + rect.w // 2, rect.y + rect.h // 2))
    if not hasattr(rec.Rect, "move"):
        rec.Rect.move = lambda rect, dx, dy: rec.Rect(rect.x + dx, rect.y + dy, rect.w, rect.h)
    if not getattr(rec.Surface, "_hero_panel_midleft", False):
        original = rec.Surface.get_rect

        def get_rect(surface, **anchors):
            if "midleft" in anchors:
                x, y = anchors["midleft"]
                return rec.Rect(int(x), int(y) - surface.h // 2, surface.w, surface.h)
            return original(surface, **anchors)

        rec.Surface.get_rect = get_rect
        rec.Surface._hero_panel_midleft = True


def _item_renderer(item_namespace):
    text = HERO_ITEMS.read_text(encoding="utf-8")
    owner = _class_node(text, "HeroItemRenderer", top_level=True)
    if owner is None:
        raise AssertionError("HeroItemRenderer not found in %s" % HERO_ITEMS.name)
    segment = ast.get_source_segment(text, owner)
    exec(compile(segment, HERO_ITEMS.name, "exec"), item_namespace)
    icon = next(
        node for node in ast.parse(text).body
        if isinstance(node, ast.FunctionDef) and node.name == "get_icon"
    )
    exec(compile(ast.get_source_segment(text, icon), HERO_ITEMS.name, "exec"), item_namespace)
    return item_namespace["HeroItemRenderer"], item_namespace["get_icon"]


def _make_inventory(state):
    slots = [None] * _constant(HERO_ITEMS, "MAX_ITEM_SLOTS")
    item_catalog = {}
    timer_values = {name: 0 for name in ACTIVE_TIMERS}
    blood_frenzy_cd = 0
    for index, item in enumerate(state["items"]):
        if not item:
            continue
        slots[index] = item["id"]
        item_catalog[item["id"]] = {
            "name": item["name"],
            "icon": item["id"] + ".png",
            "color": tuple(item["color"]),
            "glow": tuple(item["glow"]),
        }
        if item["id"] == "demon_maw":
            timer_values["blood_frenzy_timer"] = 90 if item["active"] else 0
            blood_frenzy_cd = int(item["cooldown"])
        elif item["id"] == "scarlet_bulwark":
            timer_values["guard_timer"] = 90 if item["active"] else 0
        elif item["id"] == "tempest_vane":
            timer_values["veil_timer"] = 90 if item["active"] else 0
        elif item["id"] == "thunder_coil":
            timer_values["static_timer"] = 90 if item["active"] else 0
        elif item["id"] == "sanguine_thorn":
            timer_values["rend_timer"] = 90 if item["active"] else 0
        elif item["id"] == "razor_carapace":
            timer_values["thorn_timer"] = 90 if item["active"] else 0
        elif item["id"] == "gale_pike":
            timer_values["gale_timer"] = 90 if item["active"] else 0
        elif item["id"] == "spectral_charm":
            timer_values["ghost_timer"] = 90 if item["active"] else 0
    inventory = types.SimpleNamespace(
        slots=slots,
        blood_frenzy_cd=blood_frenzy_cd,
        **timer_values,
    )
    return inventory, item_catalog


def _rects(values):
    return {
        key: [int(rect.x), int(rect.y), int(rect.w), int(rect.h)]
        for key, rect in values.items()
    }


def source_fixture():
    _patch_recorder_geometry()
    clock = {"ticks": 0}
    pygame = rec.make_pygame(clock)
    cheap_flag = {"cheap": True}
    theme = _ui_theme(pygame, cheap_flag)
    game_holder = {"game": None}

    item_namespace = {
        "pygame": pygame,
        "os": __import__("os"),
        "MAX_ITEM_SLOTS": _constant(HERO_ITEMS, "MAX_ITEM_SLOTS"),
        "ITEM_CATALOG": {},
        "_ICON_CACHE": {},
        "_ITEMS_DIR": str(ROOT / "assets" / "items"),
        "get_font": lambda size, style="body": rec.Font(size, style),
        "_get_game": lambda: game_holder["game"],
        "__file__": str(HERO_ITEMS),
    }
    item_renderer, get_icon = _item_renderer(item_namespace)
    item_module = types.ModuleType("hero_items")
    item_module.HeroItemRenderer = item_renderer
    item_module.MAX_ITEM_SLOTS = item_namespace["MAX_ITEM_SLOTS"]

    namespace = {
        "pygame": pygame,
        "math": __import__("math"),
        "ui_theme": theme,
        "SCREEN_HEIGHT": _constant(CORE, "SCREEN_HEIGHT"),
        "MAX_HERO_LEVEL": _constant(CORE, "MAX_HERO_LEVEL"),
        "RED": _constant(CORE, "RED"),
        "WHITE": _constant(CORE, "WHITE"),
        "get_font": lambda size, style="body": rec.Font(size, style),
    }
    panel_class = _compile_hero_panel(namespace)

    platform_utils = types.ModuleType("mobile.platform_utils")
    mobile = types.ModuleType("mobile")
    mobile.platform_utils = platform_utils
    frames = []
    modules = {
        "mobile": mobile,
        "mobile.platform_utils": platform_utils,
        "hero_items": item_module,
    }
    with rec.installed(modules):
        for spec in FRAMES:
            state = spec["state"]
            cheap_flag["cheap"] = bool(state["cheap_alpha"])
            clock["ticks"] = int(state["ticks"])
            pygame.mouse = types.SimpleNamespace(get_pos=lambda p=state["mouse"]: tuple(p))
            panel_pos = state["panel_pos"]
            platform_utils.panel_pos_bawah = lambda _w, _h, pos=panel_pos: pos
            screen = rec.Surface((1280, 720))
            platform_utils.get_full_surface = lambda screen=screen: screen

            inventory, item_catalog = _make_inventory(state)
            item_namespace["ITEM_CATALOG"] = item_catalog
            item_namespace["_ICON_CACHE"].clear()
            hero = types.SimpleNamespace(
                alive=bool(state["alive"]),
                name=state["name"],
                level=int(state["level"]),
                hp=int(state["hp"]),
                max_hp=int(state["max_hp"]),
                color=tuple(state["color"]),
                auto_cast_enabled=bool(state["auto_cast"]),
                skill_timer=int(state["cooldowns"][0]),
                skill_cooldown_max=int(state["cooldown_max"][0]),
                w_cooldown=int(state["cooldowns"][1]),
                w_cooldown_max=int(state["cooldown_max"][1]),
                e_cooldown=int(state["cooldowns"][2]),
                e_cooldown_max=int(state["cooldown_max"][2]),
                r_cooldown=int(state["cooldowns"][3]),
                r_cooldown_max=int(state["cooldown_max"][3]),
                items=inventory,
                upgrade_cost=lambda s=state: int(s["upgrade_cost"]),
            )
            game = types.SimpleNamespace(
                selected_hero=hero,
                gold=int(state["gold"]),
                ui_buttons={},
            )
            game_holder["game"] = game
            ui = types.SimpleNamespace(
                font_small=rec.Font(24, "body_medium"),
                font_tiny=rec.Font(20, "body"),
            )
            panel = panel_class.__new__(panel_class)
            panel.ui = ui
            panel.game = game
            panel.draw(screen)
            frames.append({
                "label": spec["label"],
                "state": state,
                "cheap_alpha": bool(state["cheap_alpha"]),
                "mouse": list(state["mouse"]),
                "ops": screen.ops,
                "buttons": _rects(game.ui_buttons),
                "ui_rects": _rects(game.ui_rects),
            })
    return {
        "source": "ui_components/_bundle.py::HeroPanel.draw + hero_items.py::HeroItemRenderer.draw",
        "glyph_factor": rec.GLYPH_FACTOR,
        "colors": {name.lower(): list(_constant(UI_THEME, name)) for name in THEME_COLORS},
        "core_colors": {
            "red": list(_constant(CORE, "RED")),
            "white": list(_constant(CORE, "WHITE")),
        },
        "frames": frames,
    }


def main():
    data = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    total = sum(len(frame["ops"]) for frame in data["frames"])
    print("hero panel oracle: %d frames, %d ops -> %s" % (len(data["frames"]), total, FIXTURE.name))


if __name__ == "__main__":
    main()
