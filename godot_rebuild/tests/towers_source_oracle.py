"""Whole-folder oracle for `towers/`: two files, four renderer namespaces.

`towers/` holds the four tower body renderers (archer, cannon, ice, mage) merged
into `_bundle.py` (7.274 lines), the shared `base_renderer` block and a 94-line
`sys.modules` shim.

The bodies are already native as baked atlases (layer 9bl): 50 sheets, one per
(type, team, level), 8 frames each (2 facings x 4 shoot-flash steps), driven by
the real `Tower._draw_tower_body` in `bake/bake_structure_atlas.py`. What was
still missing is the *geometry and data* half that runs live instead of being
painted:

* `get_<type>_top_y(tower_x, tower_y, level)` - where the HP bar sits;
* `get_archer_bow_position` / `get_cannon_muzzle_position(..., recoil)` /
  `get_ice_crystal_position` / `get_mage_crystal_position` - bullet spawn;
* `LEVEL_CONFIGS` per type (the `tower_h` / `*_tier` inputs of that geometry);
* `_get_palette(team)` per type - the colour tables the bake reads;
* `TOWER_RENDERERS` / `render_tower` - the dispatch chain.

This oracle imports the bundle against a **recording** pygame stub, so the real
geometry helpers run unmodified and their integer output is pinned as data.
Positions are ints already (`int()` truncation in the source), so the fixture
never depends on float formatting.

Every symbol of the folder is classified as `bake`, `native`, `data`, `dead` or
`meta`, with a target file and token that must exist. `dead` is transitive: a
helper reachable only from another dead helper counts as dead too.

Run: python godot_rebuild/tests/towers_source_oracle.py --write
"""

import argparse
import ast
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "towers"
BUNDLE = FOLDER / "_bundle.py"
SHIM = FOLDER / "__init__.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "towers_source.json"
CATALOG = Path(__file__).resolve().parents[1] / "data" / "towers" / "render_catalog.json"

MODULES = ["base_renderer", "archer_tower", "cannon_tower", "ice_tower", "mage_tower"]
NAMESPACES = ["archer", "cannon", "ice", "mage"]
SPAWN = {
    "archer": "get_archer_bow_position",
    "cannon": "get_cannon_muzzle_position",
    "ice": "get_ice_crystal_position",
    "mage": "get_mage_crystal_position",
}
POSITION_FN = {"archer": "get_archer_bow_position", "cannon": "get_cannon_muzzle_position",
               "ice": "get_ice_crystal_position", "mage": "get_mage_crystal_position"}
TOP_FN = {"archer": "get_archer_top_y", "cannon": "get_cannon_top_y",
          "ice": "get_ice_top_y", "mage": "get_mage_top_y"}
SCALE = 0.7
CANVAS = (140, 165)
GROUND_CY = 153  # `ch - 12`
FINAL_Y_OFFSET = -94  # -int(165 * 0.7) + int(30 * 0.7)

# Anchor matrix: every type, every level plus the clamp edges, both facings,
# two origins (one odd so `int()` truncation is exercised), cannon recoil.
LEVELS = [0, 1, 2, 3, 4, 5, 6, 7]
FACES = [1, -1]
ORIGINS = [(400, 300), (417, 285)]
CANNON_RECOILS = [0, 3, 7]


def _source(path):
    return Path(path).read_text(encoding="utf-8")


# ── pygame stub ────────────────────────────────────────────────────────────
class _Surface:
    """Enough of `pygame.Surface` for the module bodies; nothing is painted."""

    def __init__(self, size, flags=0):
        self.size = tuple(size)

    def blit(self, *args, **kwargs):
        return (0, 0, 0, 0)

    def fill(self, *args, **kwargs):
        return None


class _Draw:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def _boot():
    """Import the bundle against the stub, then restore sys.modules."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    saved = {name: sys.modules.get(name) for name in ("pygame",)}
    for name in [name for name in list(sys.modules)
                 if name == "towers" or name.startswith("towers.")]:
        sys.modules.pop(name, None)
    pygame = types.ModuleType("pygame")
    pygame.Surface = _Surface
    pygame.draw = _Draw()
    pygame.SRCALPHA = 65536
    sys.modules["pygame"] = pygame
    try:
        import importlib
        importlib.import_module("towers")
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    return sys.modules["towers"], sys.modules["towers._bundle"]


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
            if stripped.startswith(("# %s.py" % name, "# towers/%s.py" % name)):
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
    constants = {}
    functions = {}
    classes = {}
    class_constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and (target.id.isupper() or target.id.startswith("FIRE_")):
                try:
                    constants[target.id] = ast.literal_eval(node.value)
                except Exception:
                    constants[target.id] = "<call>"
        elif isinstance(node, ast.FunctionDef):
            functions[node.name] = [arg.arg for arg in node.args.args]
        elif isinstance(node, ast.ClassDef):
            methods = {}
            consts = {}
            for member in node.body:
                if isinstance(member, ast.FunctionDef):
                    methods[member.name] = [arg.arg for arg in member.args.args]
                elif isinstance(member, ast.Assign) and len(member.targets) == 1:
                    target = member.targets[0]
                    if isinstance(target, ast.Name):
                        try:
                            consts[target.id] = ast.literal_eval(member.value)
                        except Exception:
                            consts[target.id] = "<call>"
            classes[node.name] = list(methods)
            class_constants[node.name] = consts
    return {"constants": constants, "functions": functions, "classes": classes,
            "class_constants": class_constants}


_TREES = {}
_INDEX = {}


def _runtime_trees():
    """Every `.py` outside `godot_rebuild/`, parsed once."""
    if _TREES:
        return _TREES
    for path in sorted(ROOT.rglob("*.py")):
        rel = str(path.relative_to(ROOT))
        if any(part in rel for part in ("godot_rebuild", ".venv", "__pycache__")):
            continue
        try:
            _TREES[rel] = ast.parse(_source(path))
        except SyntaxError:
            continue
    return _TREES


def _index():
    """One walk of the runtime tree: call sites, plus `towers` imports."""
    if _INDEX:
        return _INDEX
    bare = {}
    qualified = {}
    imported = {}
    for rel, tree in _runtime_trees().items():
        inside = rel.startswith("towers/")
        imported[rel] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and not inside and (
                    node.module == "towers" or node.module.startswith("towers.")):
                for alias in node.names:
                    imported[rel][alias.asname or alias.name] = (node.module, node.lineno)
                continue
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            site = "%s:%d" % (rel, node.lineno)
            if isinstance(func, ast.Name):
                row = bare.setdefault(func.id, {"inside": [], "outside": []})
                row["inside" if inside else "outside"].append(site)
            elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                key = "%s.%s" % (func.value.id, func.attr)
                row = qualified.setdefault(key, {"inside": [], "outside": []})
                row["inside" if inside else "outside"].append(site)
    _INDEX.update({"bare": bare, "qualified": qualified, "imported": imported})
    return _INDEX


def call_index():
    """Every call in the runtime tree, by bare name and by `owner.attr`."""
    index = _index()
    return {"bare": index["bare"], "qualified": index["qualified"]}


def entry_sites():
    """Where the live game imports and calls the tower helpers, file:line."""
    index = _index()
    report = {}
    for rel, names in index["imported"].items():
        if not names:
            continue
        for name, (module, line) in names.items():
            row = report.setdefault(name, {"module": module, "imports": [], "calls": []})
            row["imports"].append("%s:%d" % (rel, line))
            row["calls"].extend(index["bare"].get(name, {"outside": []})["outside"])
    for row in report.values():
        row["calls"] = sorted(set(row["calls"]))
    return report


def _calls_in(node):
    names = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _row(sites, reachable, samples):
    return {"inside": len(sites["inside"]), "outside": len(sites["outside"]),
            "reachable": reachable, "samples": samples[:3]}


def dead_helpers(ast_data):
    """Transitive deadness: unreachable from the helpers the live game calls."""
    tree = ast.parse(_source(BUNDLE))
    index = call_index()
    bare = index["bare"]
    qualified = index["qualified"]
    report = {}
    # base_renderer: nothing outside `towers/` calls any of these, so the whole
    # block is dead unless something in the runtime tree imports it.
    base_bodies = {node.name: node for node in tree.body
                   if isinstance(node, ast.FunctionDef)}
    base_seen = set()
    base_stack = [name for name in base_bodies
                  if bare.get(name, {"outside": []})["outside"]]
    while base_stack:
        current = base_stack.pop()
        if current in base_seen or current not in base_bodies:
            continue
        base_seen.add(current)
        base_stack.extend(_calls_in(base_bodies[current]))
    for name in ast_data["functions"]:
        sites = bare.get(name, {"inside": [], "outside": []})
        report["base:" + name] = _row(sites, name in base_seen,
                                      sites["outside"] + sites["inside"])
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not node.name.startswith("_NS_"):
            continue
        kind = node.name[len("_NS_"):].replace("_tower", "")
        bodies = {member.name: member for member in node.body
                  if isinstance(member, ast.FunctionDef)}
        roots = [name for name in ("draw_%s" % kind, TOP_FN[kind], POSITION_FN[kind])
                 if name in bodies]
        seen = set()
        stack = list(roots)
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            for called in _calls_in(bodies[current]):
                if called in bodies and called not in seen:
                    stack.append(called)
        for name in bodies:
            sites = bare.get(name, {"inside": [], "outside": []})
            attributed = qualified.get("%s.%s" % (node.name, name),
                                       {"inside": [], "outside": []})
            reachable = name in seen or bool(attributed["outside"])
            samples = attributed["outside"] + sites["outside"] + sites["inside"]
            report["%s:%s" % (kind, name)] = _row(sites, reachable, samples)
    return report


def palettes(bundle):
    """`_get_palette(team)` of each namespace, both teams, as RGB lists."""
    report = {}
    for kind in NAMESPACES:
        namespace = getattr(bundle, "_NS_%s_tower" % kind)
        team_rows = {}
        for team in ("blue", "red"):
            team_rows[team] = {key: list(value) for key, value in
                               namespace._get_palette(team).items()}
        report[kind] = team_rows
    return report


def level_configs(bundle):
    report = {}
    for kind in NAMESPACES:
        namespace = getattr(bundle, "_NS_%s_tower" % kind)
        report[kind] = {str(level): dict(config)
                        for level, config in namespace.LEVEL_CONFIGS.items()}
    return report


def anchors(bundle):
    """Run the real anchor helpers over the matrix and keep their ints."""
    positions = []
    for kind in NAMESPACES:
        namespace = getattr(bundle, "_NS_%s_tower" % kind)
        function = getattr(namespace, POSITION_FN[kind])
        for x, y in ORIGINS:
            for level in LEVELS:
                for face in FACES:
                    recoils = CANNON_RECOILS if kind == "cannon" else [0]
                    for recoil in recoils:
                        if kind == "cannon":
                            out = function(x, y, level, face, recoil)
                        elif kind == "archer":
                            out = function(x, y, level, face)
                        else:
                            out = function(x, y, level, face)
                        positions.append({"type": kind, "x": x, "y": y, "level": level,
                                          "face": face, "recoil": recoil,
                                          "out": [int(out[0]), int(out[1])]})
    tops = []
    for kind in NAMESPACES:
        namespace = getattr(bundle, "_NS_%s_tower" % kind)
        function = getattr(namespace, TOP_FN[kind])
        for x, y in ORIGINS:
            for level in LEVELS:
                tops.append({"type": kind, "x": x, "y": y, "level": level,
                             "out": int(function(x, y, level))})
    # Level-one rows the baked manifest cannot hold (cannon/ice/mage art starts at 2)
    # plus the clamp edges, so the GDScript side is pinned on the whole domain.
    return {"positions": positions, "top_y": tops, "scale": SCALE,
            "canvas": list(CANVAS), "ground_cy": GROUND_CY,
            "final_y_offset": FINAL_Y_OFFSET}


def dispatch(towers, bundle):
    """`render_tower`: registry order, direct call, unknown-type warning."""
    text = _source(SHIM)
    cache_hooks = []
    for node in ast.parse(_source(BUNDLE)).body:
        if not isinstance(node, ast.ClassDef) or not node.name.startswith("_NS_"):
            continue
        kind = node.name[len("_NS_"):].replace("_tower", "")
        for member in node.body:
            if isinstance(member, ast.FunctionDef) and member.name == "draw_" + kind:
                if any(isinstance(sub, ast.ImportFrom) and sub.module == "sprite_cache"
                       for sub in ast.walk(member)):
                    cache_hooks.append(kind)
    return {
        "registry": list(towers.TOWER_RENDERERS),
        "renderers": {kind: "draw_%s" % kind for kind in towers.TOWER_RENDERERS},
        "warns_on_unknown": "[WARNING] Unknown tower type" in text,
        "direct_call": "renderer(surface, tower, x, y, size)" in text,
        "cache_hooks": cache_hooks,
        "cache_hook_count": len(cache_hooks),
        "spawn_helpers": dict(SPAWN),
        "top_helpers": dict(TOP_FN),
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


CATALOG_GD = "godot_rebuild/scripts/ui/tower_render_catalog.gd"
CATALOG_JSON = "godot_rebuild/data/towers/render_catalog.json"
BAKE = "godot_rebuild/bake/bake_structure_atlas.py"
ART_GD = "godot_rebuild/scripts/ui/structure_art.gd"
ORACLE = "godot_rebuild/tests/towers_source_oracle.py"

BASE_DEAD = {
    "get_team_palette": "every namespace ships its own `_get_palette`; nothing calls this one",
    "draw_torch": "each namespace has a private `_draw_torch` that it actually calls",
    "draw_aura": "no renderer calls it; the aura is per-namespace `_draw_magic_aura`",
    "draw_shield_emblem": "each namespace has a private `_draw_shield` instead",
    "draw_muzzle_flash": "the live flash is `_entity.Tower.draw` + `tower_fx_layout.gd`",
    "draw_sparks": "no renderer calls it",
    "draw_ground_shadow": "each namespace has a private `_draw_shadow`/`_draw_ground_base`",
    "draw_stone_block_pattern": "each namespace bakes its own brick pass",
    "draw_rivet": "only called by the dead `draw_metal_plate`",
    "draw_metal_plate": "no renderer calls it",
}


def classification(ast_data, dead):
    entries = {}
    for kind in NAMESPACES:
        entries["module:" + kind + "_tower"] = _entry(
            "bake", BAKE, "TOWER_TYPES = (",
            "namespace body is driven by the real Tower._draw_tower_body")
        entries["%s:LEVEL_CONFIGS" % kind] = _entry(
            "data", CATALOG_JSON, "\"level_configs\"",
            "tower_h / *_tier inputs of the live anchor geometry")
        entries["%s:HAS_AACIRCLE" % kind] = _entry(
            "bake", BAKE, "pygame.Surface((800, 600)",
            "anti-aliasing switch the baked renderer reads")
        entries["%s:_BASE_CACHE" % kind] = _entry(
            "bake", BAKE, "_TOWER_SPRITE_CACHE.clear()",
            "per-(face, shoot flash) frame memo cleared before every bake")
        entries["%s:_get_palette" % kind] = _entry(
            "data", CATALOG_JSON, "\"palettes\"",
            "colour table the bake reads; native copy keeps it inspectable")
        entries["%s:%s" % (kind, POSITION_FN[kind])] = _entry(
            "native", CATALOG_GD, "static func %s_position(" % kind,
            "bullet spawn point; face/recoil/level clamp are behavioural")
        entries["%s:%s" % (kind, TOP_FN[kind])] = _entry(
            "native", CATALOG_GD, "static func top_y(",
            "HP bar anchor; also pinned by the baked `tower_top_y` manifest")
        entries["%s:draw_%s" % (kind, kind)] = _entry(
            "bake", BAKE, "%s, team, level)" % "tower_type",
            "body pixels baked per (type, team, level, facing, shoot step)")
        namespace = "_NS_%s_tower" % kind
        for method in ast_data["classes"][namespace]:
            if method in (POSITION_FN[kind], TOP_FN[kind], "draw_%s" % kind,
                          "_get_palette"):
                continue
            if dead.get("%s:%s" % (kind, method), {}).get("reachable", True):
                entries["%s:%s" % (kind, method)] = _entry(
                    "bake", BAKE, "tower._draw_tower_body(",
                    "private draw helper; pixels land in the baked sheet")
            else:
                entries["%s:%s" % (kind, method)] = _entry(
                    "dead", ORACLE, "def dead_helpers(",
                    "unreachable from draw_%s/%s/%s" % (
                        kind, POSITION_FN[kind], TOP_FN[kind]))
    for name in ast_data["functions"]:
        if name in BASE_DEAD:
            entries["base:" + name] = _entry("dead", ORACLE, "def dead_helpers(",
                                             BASE_DEAD[name])
        else:
            entries["base:" + name] = _entry("bake", BAKE, "TOWER_TYPES = (",
                                             "shared helper reachable from the bake")
    for name in ("OUTLINE", "FIRE_ORANGE", "FIRE_YELLOW", "FIRE_PURPLE", "FIRE_PINK"):
        entries["base:" + name] = _entry(
            "data", CATALOG_JSON, "\"palettes\"",
            "fire/outline colours used by the palettes of both teams")
    entries["shim:TOWER_RENDERERS"] = _entry(
        "native", CATALOG_GD, "const TYPES :=", "registry of the four draw functions")
    entries["shim:render_tower"] = _entry(
        "native", CATALOG_GD, "static func has_type(", "dispatcher replaced by type lookup")
    entries["shim:_install_aliases"] = _entry(
        "meta", "towers/__init__.py", "_install_aliases", "sys.modules plumbing")
    return entries


def expected_symbols(ast_data):
    names = set()
    for name in ast_data["functions"]:
        names.add("base:" + name)
    for name in ("OUTLINE", "FIRE_ORANGE", "FIRE_YELLOW", "FIRE_PURPLE", "FIRE_PINK"):
        names.add("base:" + name)
    for kind in NAMESPACES:
        names.add("module:" + kind + "_tower")
        for name in ("LEVEL_CONFIGS", "HAS_AACIRCLE", "_BASE_CACHE", "_get_palette"):
            names.add("%s:%s" % (kind, name))
        for method in ast_data["classes"]["_NS_%s_tower" % kind]:
            names.add("%s:%s" % (kind, method))
    for name in ("TOWER_RENDERERS", "render_tower", "_install_aliases"):
        names.add("shim:" + name)
    return names


def source_fixture():
    towers, bundle = _boot()
    ast_data = ast_facts()
    dead = dead_helpers(ast_data)
    entries = classification(ast_data, dead)

    expected = expected_symbols(ast_data)
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
        "method_counts": {kind: len(ast_data["classes"]["_NS_%s_tower" % kind])
                          for kind in NAMESPACES},
        "dead": {name: row for name, row in sorted(dead.items())},
        "dead_helpers": sorted(name for name, row in dead.items() if not row["reachable"]),
        "palettes": palettes(bundle),
        "level_configs": level_configs(bundle),
        "anchors": anchors(bundle),
        "dispatch": dispatch(towers, bundle),
        "entry": entry_sites(),
        "classification": {name: entries[name] for name in sorted(entries)},
        "classification_kinds": {kind: kinds[kind] for kind in sorted(kinds)},
        "symbol_count": len(entries),
    }
    return json.loads(json.dumps(fixture))


def catalog_payload(fixture):
    """The runtime slice of the fixture: colour tables, level configs, geometry."""
    anchors = fixture["anchors"]
    return {
        "generator": "godot_rebuild/tests/towers_source_oracle.py --write",
        "source": "towers/_bundle.py (base_renderer + archer/cannon/ice/mage towers)",
        "canvas": anchors["canvas"],
        "ground_cy": anchors["ground_cy"],
        "final_y_offset": anchors["final_y_offset"],
        "scale": anchors["scale"],
        "constants": fixture["constants"],
        "palettes": fixture["palettes"],
        "level_configs": fixture["level_configs"],
        "dispatch": fixture["dispatch"],
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=1, sort_keys=True) + "\n",
                           encoding="utf-8")
        CATALOG.parent.mkdir(parents=True, exist_ok=True)
        CATALOG.write_text(json.dumps(catalog_payload(fixture), indent=1,
                                      sort_keys=True) + "\n", encoding="utf-8")
        print("wrote %s" % FIXTURE)
        print("wrote %s" % CATALOG)
        print("symbols %d kinds %s" % (fixture["symbol_count"],
                                       fixture["classification_kinds"]))
        print("dead helpers %s" % fixture["dead_helpers"])
        return 0
    if not FIXTURE.is_file():
        print("missing fixture: run with --write", file=sys.stderr)
        return 1
    if json.loads(FIXTURE.read_text(encoding="utf-8")) != fixture:
        print("towers/ inventory drifted from the source folder", file=sys.stderr)
        return 1
    print("towers/ inventory matches the source folder (%d symbols)"
          % fixture["symbol_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
