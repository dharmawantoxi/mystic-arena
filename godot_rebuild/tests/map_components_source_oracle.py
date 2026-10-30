"""Whole-folder oracle for `map_components/`: two files, seven merged modules.

`map_components/` is the map renderer of the Pygame build. Seven former modules
(palettes, themes, generators, static_renderer, dynamic_renderer,
decoration_renderer, shop_renderer) now live inside `_bundle.py` (7.403 lines)
and `__init__.py` (101 lines) re-registers the old module names in
`sys.modules` so the old import lines keep working.

The native side already replays the folder in four ways:

* `data/levels/map_palette.json` - the 52 `palettes.py` colours plus
  `TILE_SIZE` (added by this layer so no Godot script hard-codes a palette
  colour again);
* `data/levels/theme_palette.json` + `data/art/map_dynamic.json` - the 54
  theme dictionaries, colour by colour and flag by flag;
* `data/levels/{terrain,river,lane,wall}_tiles.json` + `scripts/ui/*_tiles.gd`
  - the static renderer's rectangle command streams;
* `assets/art/map*/` + `data/art/map_{overlay,base}.json` - the decoration,
  shop and boss-dressing layers, which are pure pixel output.

What this oracle adds is the *accounting*: it imports the merged bundle with
`pygame`/`settings` stubbed out, **executes** the real `PathGenerator` and
`DecorationGenerator` at the source seed (`random.seed(42)`) and pins the
positions the runtime actually reads, then classifies every public symbol of
the folder as one of:

* `native`   - a Godot script reproduces the behaviour (file + exact token);
* `data`     - the values live in a JSON file the runtime loads;
* `bake`     - the symbol paints pixels only; the bake reproduces them;
* `executed` - the source itself is executed here and the output is pinned;
* `meta`     - Python import plumbing with no runtime meaning;
* `internal` - a memoisation helper whose absence cannot change the output.

Every entry carries a target file and a token that must exist in it (with the
line number recorded), so a classification cannot be a claim without evidence,
and the coverage assertion refuses to run when a symbol of the folder has no
entry.

Run: python godot_rebuild/tests/map_components_source_oracle.py --write
"""

import argparse
import ast
import json
import random
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "map_components"
BUNDLE = FOLDER / "_bundle.py"
SHIM = FOLDER / "__init__.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "map_components_source.json"
PALETTE_OUT = ROOT / "godot_rebuild" / "data" / "levels" / "map_palette.json"

SCREEN = (1280, 720)
SHOPS = [(340, 540), (940, 180)]
MODULES = ["palettes", "themes", "generators", "static_renderer",
           "dynamic_renderer", "decoration_renderer", "shop_renderer"]
NAMESPACED = ["generators", "static_renderer", "shop_renderer"]
PLAIN = ["palettes", "themes", "dynamic_renderer", "decoration_renderer"]


def _source(path):
    return Path(path).read_text(encoding="utf-8")


# ── importing the merged bundle without pygame ──────────────────────────────
class _Lazy(types.ModuleType):
    """Module whose every unknown attribute is a do-nothing callable."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _Anything()


class _Anything:
    def __getattr__(self, name):
        return _Anything()

    def __call__(self, *args, **kwargs):
        return _Anything()


def _boot():
    """Import the merged bundle with `pygame`/`settings` stubbed, then restore.

    The stubs only exist so the module body can bind names; every function this
    oracle calls (`PathGenerator`, `DecorationGenerator`, `get_theme`, the
    palettes) is pure Python. Other oracles in this tree already leave their own
    `settings`/`pygame` shims in `sys.modules`, so both names are saved before
    the import and put back afterwards - and the bundle is re-imported against
    the stub instead of a shim that may be missing `SCREEN_WIDTH`.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    saved = {name: sys.modules.get(name) for name in ("pygame", "settings")}
    for name in [name for name in list(sys.modules)
                 if name == "map_components" or name.startswith("map_components.")]:
        sys.modules.pop(name, None)
    for name in ("pygame", "settings"):
        stub = _Lazy(name)
        if name == "settings":
            stub.SCREEN_WIDTH, stub.SCREEN_HEIGHT = SCREEN
        sys.modules[name] = stub
    try:
        import importlib
        importlib.import_module("map_components")
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    return sys.modules["map_components._bundle"]


def _lines(path):
    return len(_source(path).splitlines())


def inventory():
    files = {"_bundle.py": _lines(BUNDLE), "__init__.py": _lines(SHIM)}
    return {"files": files, "count": len(files), "lines": sum(files.values())}


def module_ranges():
    """`# map_components/<module>.py` markers, in file order."""
    lines = _source(BUNDLE).splitlines()
    found = []
    for index, text in enumerate(lines, start=1):
        match = re.match(r"\s*# map_components/(\w+)\.py\s*$", text)
        if match and match.group(1) in MODULES:
            if not any(entry["module"] == match.group(1) for entry in found):
                found.append({"module": match.group(1), "start": index})
    for position, entry in enumerate(found):
        end = found[position + 1]["start"] - 1 if position + 1 < len(found) else len(lines)
        entry["end"] = end
        entry["lines"] = end - entry["start"] + 1
    return found


def ast_facts():
    tree = ast.parse(_source(BUNDLE))
    classes = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        members = [m.name for m in node.body
                   if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        nested = {}
        for inner in node.body:
            if isinstance(inner, ast.ClassDef):
                nested[inner.name] = [m.name for m in inner.body
                                      if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes[node.name] = {"methods": members, "nested": nested}
    functions = {node.name: [arg.arg for arg in node.args.args]
                 for node in tree.body if isinstance(node, ast.FunctionDef)}
    return {"classes": classes, "functions": functions}


def palette_constants():
    """Top-level constants of the `palettes` section, with their values."""
    text = _source(BUNDLE)
    tree = ast.parse(text)
    end = next(entry["start"] for entry in module_ranges() if entry["module"] == "themes")
    colors, tile = {}, None
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or node.lineno >= end:
            continue
        try:
            value = ast.literal_eval(node.value)
        except Exception:
            continue
        if isinstance(value, tuple) and len(value) == 3 and all(isinstance(v, int) for v in value):
            colors[target.id] = list(value)
        elif isinstance(value, int) and target.id == "TILE_SIZE":
            tile = value
    return {"colors": colors, "tile_size": tile}


def theme_facts(bundle):
    themes = bundle.THEMES
    names = sorted(themes)
    consts = {}
    for name, value in vars(bundle).items():
        if name.endswith("_THEME") and name.isupper():
            for key in names:
                if themes[key] is value:
                    consts[key] = name
    union = sorted({key for theme in themes.values() for key in theme})
    meta = {}
    for key in names:
        theme = themes[key]
        meta[key] = {
            "name": theme.get("name"),
            "boss_identity": theme.get("boss_identity", ""),
            "boss_title": theme.get("boss_title", ""),
            "particle_type": theme.get("particle_type", "firefly"),
            "particle_count": theme.get("particle_count"),
            "fog_enabled": bool(theme.get("fog_enabled")),
            "fog_count": theme.get("fog_count"),
            "color_keys": len([k for k, v in theme.items() if isinstance(v, list)]),
            "gate_keys": sorted(k for k, v in theme.items() if v is True),
            "key_count": len(theme),
        }
    return {"count": len(names), "names": names, "consts": consts,
            "key_count": len(union), "keys": union, "meta": meta}


def aliases():
    tree = ast.parse(_source(SHIM))
    tables = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in ("_EXTRA", "_PLAIN_SYMS"):
                tables[target.id] = ast.literal_eval(node.value)
    reexports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("map_components."):
            reexports.extend(alias.name for alias in node.names)
    order = []
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.List):
            order.extend(
                element.value for element in node.iter.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )
    return {
        "extra": {key: tables.get("_EXTRA", {}).get(key, []) for key in NAMESPACED},
        "plain": {key: tables.get("_PLAIN_SYMS", {}).get(key, []) for key in PLAIN},
        "aliased": order,
        "reexports": sorted(set(reexports)),
    }


def seeds():
    out = []
    for index, text in enumerate(_source(BUNDLE).splitlines(), start=1):
        match = re.search(r"random\.seed\(([^)]*)\)", text)
        if match:
            argument = match.group(1).strip()
            out.append({"line": index,
                        "argument": argument,
                        "kind": "fixed" if argument else "entropy"})
    return out


def runtime_arrays():
    """Decoration arrays the live renderer reads, as `mr.<name>` or getattr."""
    tree = ast.parse(_source(BUNDLE))
    attrs, literals = set(), set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "self" and node.value.attr == "mr"):
            attrs.add(node.attr)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "getattr" and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)):
            literals.add(node.args[1].value)
    return sorted(attrs | literals)


def generated(bundle):
    """Execute the real generators at the source seed and keep the output."""
    generators = sys.modules["map_components.generators"]
    width, height = SCREEN
    lanes = generators.PathGenerator.generate_lanes(width, height)
    river = generators.PathGenerator.generate_river(width, height)
    points = lanes[0] + lanes[1] + lanes[2]
    decorator = generators.DecorationGenerator(width, height, points, river, SHOPS)
    data = decorator.generate_all()
    again = decorator.generate_all()
    repeatable = json.dumps(data, sort_keys=True) == json.dumps(again, sort_keys=True)
    return {
        "lanes": {
            "counts": [len(lane) for lane in lanes],
            "first": [list(point) for point in lanes[0][:2]],
            "last": [list(point) for point in lanes[0][-2:]],
        },
        "river": {"count": len(river),
                  "first": [list(point) for point in river[:2]],
                  "last": [list(point) for point in river[-2:]],
                  "points": [list(point) for point in river]},
        "lane_points": [[list(point) for point in lane] for lane in lanes],
        "decorations": {key: [list(entry) if isinstance(entry, (tuple, list)) else entry
                              for entry in values]
                        for key, values in sorted(data.items())},
        "counts": {key: len(values) for key, values in sorted(data.items())},
        "repeatable": repeatable,
        "seed": 42,
    }


def theme_fallback(bundle):
    return {"unknown_name": "__missing__",
            "equals_forest": bundle.get_theme("__missing__") is bundle.THEMES["forest"],
            "known_returns_self": bundle.get_theme("desert") is bundle.THEMES["desert"]}


# ── classification: every symbol of the folder, with file+token evidence ────
def _line_of(entry):
    """First line of the target that carries the token, or None."""
    path = ROOT / entry["target"]
    if not path.is_file() or not entry["token"]:
        return None
    for index, row in enumerate(_source(path).splitlines(), start=1):
        if entry["token"] in row:
            return index
    return None


def _entry(kind, target, token, note=""):
    path = ROOT / target
    text = _source(path) if path.is_file() else ""
    line = None
    if token:
        for index, row in enumerate(text.splitlines(), start=1):
            if token in row:
                line = index
                break
    # The line number is recomputed for the report instead of being stored: a
    # cosmetic edit elsewhere in a target file must not invalidate the fixture,
    # while a missing token still fails (``line is None`` below).
    return {"kind": kind, "target": target, "token": token, "note": note,
            }


def classification(bundle, palette, themes, arrays, ast_data, alias_data):
    entries = {}
    for name in sorted(palette["colors"]):
        entries["palettes:" + name] = _entry(
            "data", "godot_rebuild/data/levels/map_palette.json",
            '"%s":' % name.lower())
    entries["palettes:TILE_SIZE"] = _entry(
        "data", "godot_rebuild/data/levels/map_palette.json", '"tile_size":')
    for key in themes["names"]:
        entries["themes:" + themes["consts"].get(key, key.upper() + "_THEME")] = _entry(
            "data", "godot_rebuild/data/art/map_dynamic.json", '"%s":{"states"' % key)
    entries["themes:THEMES"] = _entry("data", "godot_rebuild/data/art/map_dynamic.json",
                                      '"themes":{')
    entries["themes:get_theme"] = _entry(
        "native", "godot_rebuild/scripts/ui/terrain_palette.gd",
        'palettes.get("forest"', "unknown theme falls back to forest, like the source")

    pathgen = {
        "make_curved_path": ("native", "godot_rebuild/scripts/data/lane_layout.gd",
                             "static func curved_path(", ""),
        "generate_lanes": ("native", "godot_rebuild/scripts/data/lane_layout.gd",
                           "static func create_paths(", ""),
        "generate_river": ("native", "godot_rebuild/scripts/ui/terrain_palette.gd",
                           "river_path.json", "fixed control points, 61 points"),
    }
    for method, (kind, target, token, note) in pathgen.items():
        entries["generators:PathGenerator." + method] = _entry(kind, target, token, note)
    for method in ast_data["classes"]["_NS_generators"]["nested"]["DecorationGenerator"]:
        entries["generators:DecorationGenerator." + method] = _entry(
            "executed", "godot_rebuild/tests/map_components_source_oracle.py",
            "def generated(bundle):",
            "seed 42 positions are pinned by executing the source in this oracle")

    static = {
        "draw_terrain": ("native", "godot_rebuild/scripts/ui/terrain_tiles.gd",
                         "res://data/levels/terrain_tiles.json", ""),
        "draw_terrain_details": ("bake", "godot_rebuild/bake/bake_map_base.py",
                                 "StaticRenderer.draw_terrain_details",
                                 "seeded 100, then reseeded from entropy: baked once"),
        "draw_river": ("native", "godot_rebuild/scripts/ui/river_tiles.gd",
                       "res://data/levels/river_tiles.json", ""),
        "draw_lane": ("native", "godot_rebuild/scripts/ui/lane_tiles.gd",
                      "res://data/levels/lane_tiles.json", ""),
        "_draw_cobblestone_tile": ("native", "godot_rebuild/scripts/ui/lane_tiles.gd",
                                   "res://data/levels/lane_tiles.json", ""),
        "_draw_lane_border_stone": ("native", "godot_rebuild/scripts/ui/lane_tiles.gd",
                                    "res://data/levels/lane_tiles.json", ""),
        "draw_border_wall": ("native", "godot_rebuild/scripts/ui/wall_tiles.gd",
                             "res://data/levels/wall_tiles.json", ""),
        "_draw_dark_stone_block": ("native", "godot_rebuild/scripts/ui/wall_tiles.gd",
                                   "res://data/levels/wall_tiles.json", ""),
        "_draw_wall_spike": ("native", "godot_rebuild/scripts/ui/wall_tiles.gd",
                             "res://data/levels/wall_tiles.json", ""),
    }
    for method, (kind, target, token, note) in static.items():
        entries["static_renderer:StaticRenderer." + method] = _entry(kind, target, token, note)

    dynamic = {
        "__init__": ("native", "godot_rebuild/scripts/ui/dynamic_map_renderer.gd",
                     'func configure(requested: String, level: String = "high") -> void:', ""),
        "_cached_surf": ("internal", "godot_rebuild/scripts/ui/dynamic_map_renderer.gd",
                         '"res://data/art/map_dynamic.json"',
                         "400-entry pygame surface memo; Godot rebuilds the op list instead"),
        "_init_particles": ("native", "godot_rebuild/scripts/ui/dynamic_map_renderer.gd",
                            "func configure_state(state: Dictionary) -> void:", ""),
        "_init_fog": ("native", "godot_rebuild/scripts/ui/dynamic_map_renderer.gd",
                      "func configure_state(state: Dictionary) -> void:", ""),
        "update": ("native", "godot_rebuild/scripts/ui/dynamic_map_renderer.gd",
                   "func update() -> void:", ""),
        "draw": ("native", "godot_rebuild/scripts/ui/dynamic_map_renderer.gd",
                 "func draw(canvas: CanvasItem, t: int) -> void:", ""),
        "_draw_fog": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                      "static func _fog_ops(renderer) -> Array:", ""),
        "_draw_river_animation": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                                  "static func _river_ops(renderer, t: int) -> Array:", ""),
        "_draw_shop_glow": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                            "static func _shop_glow_ops(renderer, t: int) -> Array:", ""),
        "_draw_shop_smoke": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                             "static func _shop_smoke_ops(renderer, t: int) -> Array:", ""),
        "_draw_particles": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                            "static func _particle_ops(renderer) -> Array:", ""),
        "_draw_torches": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                          "static func torch_ops(renderer, t: int) -> Array:", ""),
        "_draw_flame_a": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                     "static func _flame_a(result: Array, tx: int, ty: int, palette: Dictionary) -> void:", ""),
        "_draw_flame_b": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                     "static func _flame_b(result: Array, tx: int, ty: int, palette: Dictionary) -> void:", ""),
        "_draw_flame_c": ("native", "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
                     "static func _flame_c(result: Array, tx: int, ty: int, palette: Dictionary) -> void:", ""),
    }
    for method, (kind, target, token, note) in dynamic.items():
        entries["dynamic_renderer:DynamicRenderer." + method] = _entry(kind, target, token, note)

    boss = {
        "_boss_init_particles": "func _update_boss_particles(particle_type: String) -> void:",
        "_boss_update": "func update() -> void:",
        "_boss_draw_particles": "static func _particle_ops(",
        "_draw_boss_environment": "static func _boss_ops(",
        "_boss_dynamic_draw": "static func _boss_ops(",
    }
    for name, token in boss.items():
        entries["boss:" + name] = _entry(
            "native", "godot_rebuild/scripts/ui/dynamic_map_renderer.gd"
            if name in ("_boss_update", "_boss_init_particles")
            else "godot_rebuild/scripts/ui/dynamic_map_layout.gd",
            token)
    for name in ("_draw_true_boss_decorations", "_draw_true_boss_decorations_filled"):
        entries["boss:" + name] = _entry(
            "bake", "godot_rebuild/bake/bake_map_overlay.py", "DecorationRenderer.draw_all",
            "runs inside draw_all, so the overlay bake carries it")

    for method in ast_data["classes"]["DecorationRenderer"]["methods"]:
        entries["decoration_renderer:DecorationRenderer." + method] = _entry(
            "bake", "godot_rebuild/bake/bake_map_overlay.py", "DecorationRenderer.draw_all",
            "draw_all is the bake entry point and calls this method")
    for method in ast_data["classes"]["_NS_shop_renderer"]["nested"]["ShopRenderer"]:
        entries["shop_renderer:ShopRenderer." + method] = _entry(
            "bake", "godot_rebuild/bake/bake_map_overlay.py", "ShopRenderer.draw")

    layout_keys = set(json.loads(_source(
        ROOT / "godot_rebuild" / "data" / "art" / "map_dynamic.json"))["layout"])
    for key in sorted(arrays["decorations"]):
        if key in layout_keys:
            entries["generators:data." + key] = _entry(
                "data", "godot_rebuild/data/art/map_dynamic.json", '"%s":[' % key,
                "read every frame by the dynamic renderer")
        else:
            entries["generators:bake." + key] = _entry(
                "bake", "godot_rebuild/bake/bake_map_overlay.py", "DecorationRenderer.draw_all",
                "painted once into the overlay; no runtime reader")

    entries["__init__:aliases"] = _entry("meta", "map_components/__init__.py", "_EXTRA")
    entries["__init__:reexports"] = _entry("meta", "map_components/__init__.py", "_install_aliases")
    return entries


def _expected_symbols(palette, themes, ast_data, alias_data):
    names = set()
    for name in palette["colors"]:
        names.add("palettes:" + name)
    names.add("palettes:TILE_SIZE")
    for key in themes["names"]:
        names.add("themes:" + themes["consts"].get(key, key.upper() + "_THEME"))
    names.update({"themes:THEMES", "themes:get_theme"})
    for method in ast_data["classes"]["_NS_generators"]["nested"]["PathGenerator"]:
        names.add("generators:PathGenerator." + method)
    for method in ast_data["classes"]["_NS_generators"]["nested"]["DecorationGenerator"]:
        names.add("generators:DecorationGenerator." + method)
    for method in ast_data["classes"]["_NS_static_renderer"]["nested"]["StaticRenderer"]:
        names.add("static_renderer:StaticRenderer." + method)
    for method in ast_data["classes"]["DynamicRenderer"]["methods"]:
        names.add("dynamic_renderer:DynamicRenderer." + method)
    for name in ast_data["functions"]:
        names.add("boss:" + name if name.startswith(("_boss", "_draw_true", "_draw_boss"))
                  else "themes:" + name)
    for method in ast_data["classes"]["DecorationRenderer"]["methods"]:
        names.add("decoration_renderer:DecorationRenderer." + method)
    for method in ast_data["classes"]["_NS_shop_renderer"]["nested"]["ShopRenderer"]:
        names.add("shop_renderer:ShopRenderer." + method)
    names.update({"__init__:aliases", "__init__:reexports"})
    return names


def source_fixture():
    bundle = _boot()
    palette = palette_constants()
    themes = theme_facts(bundle)
    ast_data = ast_facts()
    alias_data = aliases()
    arrays = generated(bundle)
    entries = classification(bundle, palette, themes, arrays, ast_data, alias_data)

    expected = _expected_symbols(palette, themes, ast_data, alias_data)
    missing = sorted(expected - set(entries))
    stale = sorted(set(entries) - expected - {key for key in entries if key.startswith("generators:")})
    broken = sorted(name for name, entry in entries.items()
                    if not (ROOT / entry["target"]).is_file() or entry["token"] is None
                    or _line_of(entry) is None)
    if missing or broken:
        raise AssertionError("unclassified symbols %s / no evidence %s" % (missing, broken))

    kinds = {}
    for entry in entries.values():
        kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1

    fixture = {
        "folder": inventory(),
        "modules": module_ranges(),
        "palette": palette,
        "themes": themes,
        "fallback": theme_fallback(bundle),
        "generators": arrays,
        "seeds": seeds(),
        "runtime_arrays": runtime_arrays(),
        "decoration_reads": sorted(set(runtime_arrays()) & set(arrays["decorations"])),
        "bake_only_arrays": sorted(set(runtime_arrays()) & set(arrays["decorations"])
                                   - set(json.loads(_source(ROOT / "godot_rebuild" / "data"
                                                            / "art" / "map_dynamic.json"))["layout"])),
        "classes": ast_data["classes"],
        "functions": ast_data["functions"],
        "aliases": alias_data,
        "classification": {name: entries[name] for name in sorted(entries)},
        "classification_kinds": {kind: kinds[kind] for kind in sorted(kinds)},
        "stale_entries": stale,
        "symbol_count": len(entries),
    }
    return json.loads(json.dumps(fixture))


def palette_payload(fixture):
    return {
        "generator": "godot_rebuild/tests/map_components_source_oracle.py",
        "source": "map_components/_bundle.py::palettes",
        "tile_size": fixture["palette"]["tile_size"],
        "colors": {name.lower(): value
                   for name, value in sorted(fixture["palette"]["colors"].items())},
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        PALETTE_OUT.write_text(
            json.dumps(palette_payload(fixture), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote %s" % FIXTURE)
        print("wrote %s" % PALETTE_OUT)
        print("symbols %d kinds %s" % (fixture["symbol_count"], fixture["classification_kinds"]))
        return 0
    if not FIXTURE.is_file():
        print("missing fixture: run with --write", file=sys.stderr)
        return 1
    on_disk = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if on_disk != fixture:
        print("map_components/ inventory drifted from the source folder", file=sys.stderr)
        return 1
    if json.loads(PALETTE_OUT.read_text(encoding="utf-8")) != palette_payload(fixture):
        print("data/levels/map_palette.json drifted from palettes.py", file=sys.stderr)
        return 1
    print("map_components/ inventory matches the source folder (%d symbols)"
          % fixture["symbol_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
