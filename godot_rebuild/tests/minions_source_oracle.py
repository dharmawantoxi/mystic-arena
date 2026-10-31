"""Whole-folder oracle for `minions/`: two files, five renderer namespaces.

`minions/` holds the five minion body renderers (goblin, orc, troll, undead,
dark_rider) merged into `_bundle.py` (9.531 lines) plus the shared
`base_renderer` helpers and a 94-line `sys.modules` shim.

The bodies are already native as baked atlases (layer 9bk): 50 sheets, one per
(type, team, nexus level), driven by the real `Minion.draw` in
`bake/bake_minion_atlas.py`. What was still missing is the *live overlay* half of
`base_renderer.py` - the HP bar, the slow aura, the slash arcs, the hurt flash
and the cache key - which the source draws after (or around) the cached sprite.

This oracle imports the bundle with a **recording** pygame stub: `Surface`,
`pygame.draw.rect/circle/ellipse/lines` capture primitives instead of painting,
so the real `draw_hp_bar`, `draw_slow_effect`, `draw_slash_effects`,
`apply_hurt_flash`, `calculate_animation_offsets` and `_minion_cache_key` run
unmodified and their output is pinned as data. Points are stored in micro-pixel
integers (`round(x * 10_000)` truncated) so the fixture never depends on float
formatting.

Every symbol of the folder is classified as `native`, `data`, `bake`,
`executed`, `meta`, `internal` or `dead` (defined but never called in the
runtime), with a target file and token that must exist.

Run: python godot_rebuild/tests/minions_source_oracle.py --write
"""

import argparse
import ast
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "minions"
BUNDLE = FOLDER / "_bundle.py"
SHIM = FOLDER / "__init__.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "minions_source.json"

MODULES = ["base_renderer", "goblin", "orc", "troll", "undead", "dark_rider"]
NAMESPACES = ["goblin", "orc", "troll", "undead", "dark_rider"]
CANVAS = (120, 120)
SCALE = 10000  # micro-units per pixel for recorded points


def _source(path):
    return Path(path).read_text(encoding="utf-8")


# ── recording pygame stub ───────────────────────────────────────────────────
class _Surface:
    """Pygame surface that records draw primitives instead of painting."""

    def __init__(self, size, flags=0):
        self.size = tuple(size)
        self.ops = []

    def blit(self, other, pos):
        dx, dy = pos
        for op in other.ops:
            self.ops.append(_shift(op, dx, dy))
        return (0, 0, other.size[0], other.size[1])

    def fill(self, *args, **kwargs):
        return None


def _shift(op, dx, dy):
    out = dict(op)
    if "rect" in op:
        rect = op["rect"]
        out["rect"] = [rect[0] + dx, rect[1] + dy, rect[2], rect[3]]
    if "center" in op:
        center = op["center"]
        out["center"] = [center[0] + dx, center[1] + dy]
    if "points" in op:
        # Points are already stored in micro-pixels, so the blit offset is scaled.
        out["points"] = [[point[0] + dx * SCALE, point[1] + dy * SCALE]
                         for point in op["points"]]
    return out


def _color(value):
    channels = [int(channel) for channel in value]
    if len(channels) == 3:
        channels.append(255)
    return channels


def _point(x, y):
    return [int(float(x) * SCALE), int(float(y) * SCALE)]


class _Draw:
    def rect(self, surface, color, rect, width=0):
        surface.ops.append({"kind": "rect", "rect": [int(v) for v in rect],
                           "color": _color(color), "width": int(width)})

    def circle(self, surface, color, center, radius, width=0):
        surface.ops.append({"kind": "circle",
                            "center": [int(center[0]), int(center[1])],
                            "radius": int(radius), "color": _color(color),
                            "width": int(width)})

    def ellipse(self, surface, color, rect, width=0):
        surface.ops.append({"kind": "ellipse", "rect": [int(v) for v in rect],
                            "color": _color(color), "width": int(width)})

    def lines(self, surface, color, closed, points, width=1):
        surface.ops.append({"kind": "lines",
                            "points": [_point(point[0], point[1]) for point in points],
                            "color": _color(color), "width": int(width)})

    def line(self, surface, color, start, end, width=1):
        self.lines(surface, color, False, [start, end], width)


def _boot():
    """Import the bundle against the recording stub, then restore sys.modules."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    saved = {name: sys.modules.get(name) for name in ("pygame", "settings")}
    for name in [name for name in list(sys.modules)
                 if name == "minions" or name.startswith("minions.")]:
        sys.modules.pop(name, None)
    pygame = types.ModuleType("pygame")
    pygame.Surface = _Surface
    pygame.draw = _Draw()
    pygame.SRCALPHA = 65536
    pygame.BLEND_RGB_MULT = 1
    pygame.BLEND_RGB_ADD = 2
    settings = types.ModuleType("settings")
    settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT = 1280, 720
    sys.modules["pygame"] = pygame
    sys.modules["settings"] = settings
    try:
        import importlib
        importlib.import_module("minions")
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    return sys.modules["minions._bundle"]


# ── inventory ──────────────────────────────────────────────────────────────
def inventory():
    files = {"_bundle.py": len(_source(BUNDLE).splitlines()),
             "__init__.py": len(_source(SHIM).splitlines())}
    return {"files": files, "count": len(files), "lines": sum(files.values())}


def module_ranges():
    lines = _source(BUNDLE).splitlines()
    found = []
    for index, text in enumerate(lines, start=1):
        stripped = text.strip()
        for name in MODULES:
            if stripped == "# minions/%s.py" % name:
                if not any(row["module"] == name for row in found):
                    found.append({"module": name, "start": index})
    for position, row in enumerate(found):
        end = found[position + 1]["start"] - 1 if position + 1 < len(found) else len(lines)
        row["end"] = end
        row["lines"] = end - row["start"] + 1
    return found


def ast_facts():
    tree = ast.parse(_source(BUNDLE))
    constants = {}
    functions = {}
    classes = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == target.id.upper() or (
                    isinstance(target, ast.Name) and target.id.startswith("_")):
                try:
                    constants[target.id] = ast.literal_eval(node.value)
                except Exception:
                    constants[target.id] = "<call>"
        elif isinstance(node, ast.FunctionDef):
            functions[node.name] = [arg.arg for arg in node.args.args]
            defaults = len(node.args.defaults)
            functions.setdefault("_defaults", {})[node.name] = defaults
        elif isinstance(node, ast.ClassDef):
            classes[node.name] = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
    functions.pop("_defaults", None)
    return {"constants": constants, "functions": functions, "classes": classes}


def aliases():
    tree = ast.parse(_source(SHIM))
    order = []
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.List):
            order.extend(element.value for element in node.iter.elts
                         if isinstance(element, ast.Constant) and isinstance(element.value, str))
    reexports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("minions."):
            reexports.extend(alias.name for alias in node.names)
    registry = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "MINION_RENDERERS":
                registry = [key.value for key in node.value.keys]
    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    return {"aliased": order, "reexports": sorted(set(reexports)),
            "registry": registry, "functions": functions}


def call_index():
    """One walk of the runtime tree: every called name -> its call sites."""
    index = {}
    for path in sorted(ROOT.rglob("*.py")):
        rel = str(path.relative_to(ROOT))
        if any(part in rel for part in ("godot_rebuild", ".venv", "__pycache__")):
            continue
        try:
            tree = ast.parse(_source(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else None)
            if name is None:
                continue
            inside = rel.startswith("minions/")
            index.setdefault(name, {"inside": [], "outside": []})[
                "inside" if inside else "outside"].append("%s:%d" % (rel, node.lineno))
    return index


def hp_bar_paths(modules):
    """Per module, the HP bar width/height offsets each renderer asks for."""
    lines = _source(BUNDLE).splitlines()
    report = {}
    for module in modules:
        rows = []
        for index in range(module["start"] - 1, module["end"]):
            text = lines[index]
            if "bar_w = " in text and "+" in text:
                rows.append(("width", int(text.rsplit("+", 1)[1].strip())))
            if text.strip().startswith("by = y -"):
                rows.append(("y", int(text.rsplit("-", 1)[1].strip())))
        width = next((value for kind, value in rows if kind == "width"), None)
        offset = next((value for kind, value in rows if kind == "y"), None)
        report[module["module"]] = [width, offset]
    return report


def dispatch():
    """`render_minion`: cache hook, direct call, and the unknown-type branch."""
    text = _source(SHIM)
    return {
        "cache_hook": "from mobile.spritecache import render_minion_cached" in text,
        "warns_on_unknown": "[WARNING] Unknown minions type" in text,
        "direct_call": "renderer(surface, minion, x, y)" in text,
    }


def dead_helpers(functions):
    """Defined in `base_renderer`, called nowhere in the runtime."""
    index = call_index()
    report = {}
    for name in functions:
        sites = index.get(name, {"inside": [], "outside": []})
        report[name] = {"inside": sites["inside"], "outside": sites["outside"],
                        "dead": not sites["inside"] and not sites["outside"]}
    return report


# ── executed overlay primitives ────────────────────────────────────────────
HP_CASES = [
    {"x": 100, "y": 50, "w": 26, "ratio": 1.0, "team": "blue"},
    {"x": 100, "y": 50, "w": 26, "ratio": 0.8, "team": "blue"},
    {"x": 100, "y": 50, "w": 26, "ratio": 0.6, "team": "blue"},
    {"x": 100, "y": 50, "w": 26, "ratio": 0.3, "team": "blue"},
    {"x": 100, "y": 50, "w": 26, "ratio": 0.0, "team": "red"},
    {"x": 100, "y": 50, "w": 26, "ratio": 0.65, "team": "red"},
    {"x": 100, "y": 50, "w": 26, "ratio": 1.8, "team": "blue"},
    {"x": 101, "y": 51, "w": 25, "ratio": -0.4, "team": "red"},
]
SLOW_CASES = [
    {"x": 100, "y": 200, "radius": 14, "timer": 0},
    {"x": 100, "y": 200, "radius": 14, "timer": 7},
    {"x": 100, "y": 200, "radius": 14, "timer": 23},
    {"x": 64, "y": 96, "radius": 9, "timer": 41},
]
SLASH_CASES = [
    {"name": "empty", "effects": []},
    {"name": "fresh", "effects": [{"life": 12, "max_life": 12, "angle": 0.0, "distance": 18}]},
    {"name": "half", "effects": [{"life": 6, "max_life": 12, "angle": 1.0, "distance": 20}]},
    {"name": "late", "effects": [{"life": 18, "max_life": 24, "angle": -2.4, "distance": 12}]},
    {"name": "expired", "effects": [{"life": 0, "max_life": 12, "angle": 0.0, "distance": 18}]},
    {"name": "defaults", "effects": [{}]},
    {"name": "stack", "effects": [
        {"life": 12, "max_life": 12, "angle": 0.0, "distance": 18},
        {"life": 6, "max_life": 12, "angle": 1.0, "distance": 20},
        {"life": 0, "max_life": 12, "angle": 2.0, "distance": 18},
    ]},
]
HURT_CASES = [
    {"color": [10, 20, 30], "timer": 5},
    {"color": [200, 200, 200], "timer": 1},
    {"color": [10, 20, 30], "timer": 0},
    {"color": [255, 0, 128], "timer": 3},
]
OFFSET_CASES = [
    {"moving": True, "walk_cycle": 1.3, "anim_time": 0},
    {"moving": True, "walk_cycle": 0.0, "anim_time": 0},
    {"moving": False, "walk_cycle": 0.0, "anim_time": 40},
    {"moving": False, "walk_cycle": 0.0, "anim_time": 13},
    {"moving": True, "walk_cycle": 2.0, "anim_time": 7},
]
KEY_CASES = [
    {"minion_type": "goblin", "team": "blue", "nexus_level": 1,
     "attack_anim_timer": 0, "is_moving": False, "walk_cycle": 0.0, "anim_time": 0,
     "direction": 1, "hurt_flash_timer": 0, "bleed_stacks": 0,
     "death_charge_active": False, "regen_active": False, "slow_timer": 0},
    {"minion_type": "orc", "team": "red", "nexus_level": 3,
     "attack_anim_timer": 7, "is_moving": True, "walk_cycle": 0.25, "anim_time": 12,
     "direction": -1, "hurt_flash_timer": 2, "bleed_stacks": 2,
     "death_charge_active": True, "regen_active": False, "slow_timer": 9},
    {"minion_type": "troll", "team": "blue", "nexus_level": 5,
     "attack_anim_timer": 0, "is_moving": True, "walk_cycle": 1.75, "anim_time": 80,
     "direction": 1, "hurt_flash_timer": 0, "bleed_stacks": 0,
     "death_charge_active": False, "regen_active": True, "slow_timer": 0},
    {"minion_type": "undead", "team": "red", "nexus_level": 2,
     "attack_anim_timer": 24, "is_moving": False, "walk_cycle": 0.5, "anim_time": 61,
     "direction": 1, "hurt_flash_timer": 0, "bleed_stacks": 5,
     "death_charge_active": False, "regen_active": False, "slow_timer": 1},
    {"minion_type": "dark_rider", "team": "blue", "nexus_level": 4,
     "attack_anim_timer": 0, "is_moving": False, "walk_cycle": 3.5, "anim_time": 137,
     "direction": -1, "hurt_flash_timer": 1, "bleed_stacks": 1,
     "death_charge_active": True, "regen_active": True, "slow_timer": 0},
]


class _FakeMinion:
    def __init__(self, fields):
        for key, value in fields.items():
            setattr(self, key, value)


def _key_tuple(key):
    return [key[0], key[1], int(key[2]), [key[3][0], int(key[3][1])], int(key[4]),
            int(bool(key[5])), int(key[6]), int(bool(key[7])), int(bool(key[8])),
            int(bool(key[9]))]


def executed(bundle):
    """Run the real helpers and keep the primitives they ask pygame to draw."""
    hp = []
    for case in HP_CASES:
        surface = _Surface((200, 200))
        bundle.draw_hp_bar(surface, case["x"], case["y"], case["w"],
                           case["ratio"], case["team"])
        hp.append({"case": case, "ops": surface.ops})

    slow = []
    for case in SLOW_CASES:
        surface = _Surface((300, 300))
        bundle.draw_slow_effect(surface, case["x"], case["y"],
                                case["radius"], case["timer"])
        slow.append({"case": case, "ops": surface.ops})

    slash = []
    for case in SLASH_CASES:
        surface = _Surface((300, 300))
        bundle.draw_slash_effects(surface, 100, 200, case["effects"])
        slash.append({"name": case["name"], "effects": case["effects"], "ops": surface.ops})

    guarded = _Surface((300, 300))
    bundle._RENDERING_TO_CACHE = True
    try:
        bundle.draw_hp_bar(guarded, 100, 50, 26, 0.5, "blue")
        bundle.draw_slash_effects(guarded, 100, 200, SLASH_CASES[1]["effects"])
    finally:
        bundle._RENDERING_TO_CACHE = False

    shadow = []
    for args in ({"w": 20, "h": 4, "alpha": 100}, {"w": -3, "h": 0, "alpha": 100},
                 {"w": 34, "h": 12, "alpha": 60}):
        surface = _Surface((300, 300))
        bundle.draw_shadow(surface, 100, 200, args["w"], args["h"], args["alpha"])
        shadow.append({"case": args, "ops": surface.ops})

    hurt = [{"case": case, "color": list(bundle.apply_hurt_flash(tuple(case["color"]),
                                                                case["timer"]))}
            for case in HURT_CASES]

    offsets = []
    for case in OFFSET_CASES:
        minion = _FakeMinion({"walk_cycle": case["walk_cycle"],
                              "is_moving": case["moving"],
                              "anim_time": case["anim_time"]})
        bob, sway, phase = bundle.calculate_animation_offsets(minion)
        offsets.append({"case": case, "bob": bob, "sway": sway, "phase": phase})

    keys = [{"case": case, "key": _key_tuple(bundle._minion_cache_key(_FakeMinion(case)))}
            for case in KEY_CASES]

    return {
        "hp_bar": hp,
        "slow_aura": slow,
        "slash": slash,
        "cache_guarded": guarded.ops,
        "shadow": shadow,
        "hurt_flash": hurt,
        "offsets": offsets,
        "cache_keys": keys,
        "canvas": list(CANVAS),
        "scale": SCALE,
    }


# ── classification ─────────────────────────────────────────────────────────
def _line_of(target, token):
    path = ROOT / target
    if not path.is_file():
        return None
    for index, row in enumerate(_source(path).splitlines(), start=1):
        if token in row:
            return index
    return None


def _entry(kind, target, token, note=""):
    return {"kind": kind, "target": target, "token": token, "note": note,
            "line": _line_of(target, token)}


OVERLAY_GD = "godot_rebuild/scripts/ui/minion_overlay.gd"
BAKE = "godot_rebuild/bake/bake_minion_atlas.py"


def classification(ast_data, alias_data, dead):
    entries = {}
    native_helpers = {
        "draw_hp_bar": (OVERLAY_GD, "static func hp_bar_ops(",
                        "drawn live after the sprite blit; exact rects and colours"),
        "draw_slow_effect": (OVERLAY_GD, "static func slow_aura_ops(",
                             "circle + three orbiting sparks; source freezes one frame"),
        "draw_slash_effects": (OVERLAY_GD, "static func slash_ops(",
                               "arbitrary angles, not only the 32 baked steps"),
        "_minion_cache_key": (OVERLAY_GD, "static func cache_key(",
                              "ten-part key; pose part matches minion_anim.pose_key"),
    }
    for name, (target, token, note) in native_helpers.items():
        entries["base:" + name] = _entry("native", target, token, note)
    entries["base:apply_hurt_flash"] = _entry(
        "delegated", OVERLAY_GD, "static func hurt_color(",
        "no runtime caller, but the atlas bake delegates the +90 flash to Godot")
    entries["base:calculate_animation_offsets"] = _entry(
        "dead", "godot_rebuild/tests/minions_source_oracle.py", "def dead_helpers(",
        "returned bob/sway but no renderer calls it; baked frames carry the bob")
    entries["base:draw_shadow"] = _entry(
        "dead", "godot_rebuild/tests/minions_source_oracle.py", "def dead_helpers(",
        "each namespace has its own _draw_ground_shadow; this one is never called")
    entries["base:cached_minion_draw"] = _entry(
        "bake", BAKE, "cached_minion_draw",
        "body render + red-team recolour + crop; overlays are split out natively")
    entries["base:OUTLINE"] = _entry("native", OVERLAY_GD, "const OUTLINE :=")
    entries["base:SHADOW"] = _entry("native", OVERLAY_GD, "const SHADOW :=")
    entries["base:_RENDERING_TO_CACHE"] = _entry(
        "native", OVERLAY_GD, "static var _rendering_to_cache")
    entries["base:_SHADOW_CACHE"] = _entry(
        "dead", "godot_rebuild/tests/minions_source_oracle.py", "def dead_helpers(",
        "memo for draw_shadow, which nothing calls")
    entries["base:_CANVAS_W"] = _entry("native", OVERLAY_GD, "const CANVAS :=")
    entries["base:_CANVAS_H"] = _entry("native", OVERLAY_GD, "const CANVAS :=")
    entries["base:MINION_CACHE_ENABLED"] = _entry(
        "native", OVERLAY_GD, "static func cache_enabled()")

    for module in NAMESPACES:
        entries["module:" + module] = _entry(
            "bake", BAKE, "TYPES = (", "namespace body is driven by the real Minion.draw")
        for method in ast_data["classes"]["_NS_" + module]:
            entries["%s:%s" % (module, method)] = _entry(
                "bake", BAKE, "minion.draw(pygame.Surface",
                "body pixels baked per (type, team, level, pose, facing)")

    entries["shim:MINION_RENDERERS"] = _entry(
        "native", OVERLAY_GD, "const TYPES :=", "registry of the five draw functions")
    entries["shim:render_minion"] = _entry(
        "native", OVERLAY_GD, "static func has_type(", "dispatcher replaced by type lookup")
    entries["shim:_install_aliases"] = _entry(
        "meta", "minions/__init__.py", "_install_aliases", "sys.modules plumbing")
    return entries, alias_data


def expected_symbols(ast_data, alias_data):
    names = set()
    for name in ast_data["functions"]:
        names.add("base:" + name)
    for name in ("OUTLINE", "SHADOW", "_RENDERING_TO_CACHE", "_SHADOW_CACHE",
                 "_CANVAS_W", "_CANVAS_H", "MINION_CACHE_ENABLED"):
        names.add("base:" + name)
    for module in NAMESPACES:
        names.add("module:" + module)
        for method in ast_data["classes"]["_NS_" + module]:
            names.add("%s:%s" % (module, method))
    for name in ("MINION_RENDERERS", "render_minion", "_install_aliases"):
        names.add("shim:" + name)
    return names


def source_fixture():
    bundle = _boot()
    ast_data = ast_facts()
    alias_data = aliases()
    dead = dead_helpers(ast_data["functions"])
    entries, _ = classification(ast_data, alias_data, dead)

    expected = expected_symbols(ast_data, alias_data)
    missing = sorted(expected - set(entries))
    broken = sorted(name for name, entry in entries.items() if entry["line"] is None)
    if missing or broken:
        raise AssertionError("unclassified symbols %s / no evidence %s" % (missing, broken))

    kinds = {}
    for entry in entries.values():
        kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1

    fixture = {
        "folder": inventory(),
        "modules": module_ranges(),
        "constants": ast_data["constants"],
        "functions": ast_data["functions"],
        "classes": ast_data["classes"],
        "method_counts": {module: len(ast_data["classes"]["_NS_" + module])
                          for module in NAMESPACES},
        "dead": dead,
        "hp_bar_paths": hp_bar_paths(module_ranges()),
        "dispatch": dispatch(),
        "dead_helpers": sorted(name for name, row in dead.items() if row["dead"]),
        "aliases": alias_data,
        "overlay": executed(bundle),
        "classification": {name: entries[name] for name in sorted(entries)},
        "classification_kinds": {kind: kinds[kind] for kind in sorted(kinds)},
        "symbol_count": len(entries),
    }
    return json.loads(json.dumps(fixture))


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=1, sort_keys=True) + "\n",
                           encoding="utf-8")
        print("wrote %s" % FIXTURE)
        print("symbols %d kinds %s" % (fixture["symbol_count"],
                                       fixture["classification_kinds"]))
        print("dead helpers %s" % fixture["dead_helpers"])
        return 0
    if not FIXTURE.is_file():
        print("missing fixture: run with --write", file=sys.stderr)
        return 1
    if json.loads(FIXTURE.read_text(encoding="utf-8")) != fixture:
        print("minions/ inventory drifted from the source folder", file=sys.stderr)
        return 1
    print("minions/ inventory matches the source folder (%d symbols)"
          % fixture["symbol_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
