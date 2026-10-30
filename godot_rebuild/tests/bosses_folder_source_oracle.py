"""Whole-folder oracle for `bosses/`: the 61 Pygame files as one coverage map.

`docs/BOSSES_FOLDER_MIGRATION.md` claims every file in the folder is either
ported or explicitly classified. That claim is only worth something if the
inventory behind it is derived from the source instead of typed by hand, so
this oracle re-derives it from `bosses/` itself:

* `_boss_index.py` -> the exact `id -> (module, draw_fn)` lazy-import map that
  `heroes/__init__.py` uses (216 entries over 54 level modules);
* every top-level `draw_*` function per module (219) plus the one that no
  index entry points at (`level5.draw_morgath`, dead since `morgath` is
  indexed to `level3`);
* the 79 `Boss._smart_ai_*` methods and the `Boss.update` dispatch order that
  calls them, so a native arm cannot be missing, renamed or reordered;
* `boss_data.py` executed with `runpy` (it imports no pygame): the 216 stat
  rows split 162 mini / 54 true, `hero_unlock` costs, `MINI_BOSS_WAVES`,
  `LEVEL_TRUE_BOSS`, the three true-boss curves and `MELEE_ROLE_HINTS`;
* the three procedural renderers (`*_v4.py`) and which level bundle
  re-exports each one;
* who actually reads the construction-only tables outside `bosses/` - the
  converter in `tools/` and nothing at runtime - which is why they need no
  native mirror.

Everything lands in `tests/fixtures/bosses_folder_source.json`. Nothing here
runs pygame: `base_boss.py` and the level bundles need a display, so they are
only parsed with `ast`.

Run: python godot_rebuild/tests/bosses_folder_source_oracle.py --write
"""

import argparse
import ast
import json
import re
import runpy
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOSSES = ROOT / "bosses"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bosses_folder_source.json"

# Files in `bosses/` that are not one draw module per level.
STRUCTURAL = ("__init__.py", "_boss_index.py", "base_boss.py", "boss_data.py")
RENDERERS = ("nyzrak_v4.py", "razak_v4.py", "thalgryn_v4.py")
# level bundle -> renderer module it re-exports
RENDERER_EXPORTERS = {"level2.py": "razak_v4", "level3.py": "nyzrak_v4", "level6.py": "thalgryn_v4"}
# Tables in `boss_data.py` that only exist to build the per-boss rows.
BUILD_INPUTS = (
    "MINI_BOSS_WAVES",
    "LEVEL_TRUE_BOSS",
    "TRUE_BOSS_HP_CURVE",
    "TRUE_BOSS_DMG_CURVE",
    "TRUE_BOSS_ABILITY_CURVE",
    "MELEE_ROLE_HINTS",
)


def _source(path):
    return path.read_text(encoding="utf-8")


def file_inventory():
    """Every `.py` in the folder with its line count."""
    return {
        path.name: len(_source(path).splitlines())
        for path in sorted(BOSSES.glob("*.py"))
    }


def boss_index():
    """`BOSS_INDEX` from `_boss_index.py`, parsed (never imported)."""
    tree = ast.parse(_source(BOSSES / "_boss_index.py"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "BOSS_INDEX" for t in node.targets
        ):
            raw = ast.literal_eval(node.value)
            return {name: [module, draw] for name, (module, draw) in raw.items()}
    raise AssertionError("BOSS_INDEX missing from bosses/_boss_index.py")


def draw_functions():
    """Top-level `draw_*` functions and `_NS_*` renderer classes per level module."""
    modules = {}
    for path in sorted(BOSSES.glob("level*.py")):
        tree = ast.parse(_source(path))
        draws = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("draw_")
        ]
        namespaces = [
            node.name
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name.startswith("_NS_")
        ]
        modules[path.stem] = {"draw": draws, "namespaces": namespaces}
    return modules


def renderer_namespaces():
    """The `_NS_<boss>` classes the three v4 pixel renderers expose."""
    found = {}
    for renderer in RENDERERS:
        tree = ast.parse(_source(BOSSES / renderer))
        found[renderer] = [
            node.name
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name.startswith("_NS_")
        ]
    return found


def _method_source(source, class_name, method):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method:
                    lines = source.splitlines()
                    return "\n".join(lines[item.lineno - 1:item.end_lineno])
    raise AssertionError("%s.%s missing from bosses/base_boss.py" % (class_name, method))


def smart_ai():
    """The 79 `_smart_ai_*` methods and the `update()` dispatch that calls them."""
    source = _source(BOSSES / "base_boss.py")
    tree = ast.parse(source)
    methods = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Boss":
            methods = [
                item.name
                for item in node.body
                if isinstance(item, ast.FunctionDef) and item.name.startswith("_smart_ai_")
            ]
            break
    update = _method_source(source, "Boss", "update")
    # `ignis_drachorn` carries a trailing `# TAMBAH` comment on its arm.
    pairs = re.findall(
        r'self\.boss_type == "([a-z0-9_]+)"\s*:[^\n]*\n\s*self\._smart_ai_([a-z0-9_]+)\(enemies, dist\)',
        update,
    )
    assert pairs, "Boss.update no longer dispatches _smart_ai_* by boss_type"
    for boss_type, handler in pairs:
        assert boss_type == handler, "dispatch %s calls _smart_ai_%s" % (boss_type, handler)
    dispatch = [boss_type for boss_type, _handler in pairs]
    assert len(dispatch) == len(set(dispatch)), "duplicate boss_type in Boss.update dispatch"
    return {
        "methods": sorted(methods),
        "dispatch": dispatch,
    }


def boss_tables():
    """`boss_data.py` executed directly: it imports no pygame and no display."""
    namespace = runpy.run_path(str(BOSSES / "boss_data.py"))
    mini = namespace["MINI_BOSS_TYPES"]
    true = namespace["TRUE_BOSS_TYPES"]
    rows = {}
    for name, row in mini.items():
        rows[name] = row
    for name, row in true.items():
        assert name not in rows, "%s is both a mini and a true boss" % name
        rows[name] = row
    assert set(rows) == set(namespace["get_all_boss_types"]())
    return {
        "rows": rows,
        "rows_by_class": {"mini": sorted(mini), "true": sorted(true)},
        "counts": {"mini": len(mini), "true": len(true), "total": len(rows)},
        "mini_waves": {str(k): v for k, v in sorted(namespace["MINI_BOSS_WAVES"].items())},
        "level_true_boss": {str(k): v for k, v in sorted(namespace["LEVEL_TRUE_BOSS"].items())},
        "curves": {
            "hp": dict(namespace["TRUE_BOSS_HP_CURVE"]),
            "damage": dict(namespace["TRUE_BOSS_DMG_CURVE"]),
            "ability": dict(namespace["TRUE_BOSS_ABILITY_CURVE"]),
        },
        "melee_role_hints": sorted(namespace["MELEE_ROLE_HINTS"]),
    }


_PY_SOURCES = None


def py_sources():
    """Every `.py` outside `bosses/` and `godot_rebuild/`, read once."""
    global _PY_SOURCES
    if _PY_SOURCES is None:
        cached = {}
        for path in ROOT.rglob("*.py"):
            relative = path.relative_to(ROOT)
            if relative.parts[0] in ("bosses", "godot_rebuild", ".git"):
                continue
            cached[str(relative)] = _source(path)
        _PY_SOURCES = cached
    return _PY_SOURCES


def build_inputs_consumers():
    """Where each construction-only table is read from, outside the folder."""
    sources = py_sources()
    hits = {}
    for name in BUILD_INPUTS:
        pattern = re.compile(r"\b%s\b" % name)
        hits[name] = sorted(file for file, text in sources.items() if pattern.search(text))
    return hits


def renderer_exports():
    """Which level bundle re-exports each procedural renderer, and its callers."""
    exports = {}
    for bundle, renderer in RENDERER_EXPORTERS.items():
        text = _source(BOSSES / bundle)
        match = re.search(r"from\s+(?:\w+\.)?%s\s+import\s+(\w+)" % re.escape(renderer), text)
        assert match, "%s does not import %s" % (bundle, renderer)
        exports[renderer] = {"bundle": bundle, "namespace": match.group(1)}
    sources = py_sources()
    callers = {}
    for renderer in RENDERERS:
        pattern = re.compile(r"\b%s\b" % renderer[: -len(".py")])
        callers[renderer] = sorted(file for file, text in sources.items() if pattern.search(text))
    return {"exported_by": exports, "cited_outside_bosses": callers}


def source_fixture():
    """The whole inventory, derived from the source folder."""
    files = file_inventory()
    index = boss_index()
    draws = draw_functions()
    smart = smart_ai()
    tables = boss_tables()
    rows = tables["rows"]

    indexed_draws = set()
    for module, draw in index.values():
        indexed_draws.add("%s.%s" % (module, draw))
    defined_draws = set()
    duplicates = []
    definitions = 0
    for module, entry in draws.items():
        for draw in entry["draw"]:
            definitions += 1
            qualified = "%s.%s" % (module, draw)
            if qualified in defined_draws and qualified not in duplicates:
                duplicates.append(qualified)
            defined_draws.add(qualified)

    missing_draws = sorted(indexed_draws - defined_draws)
    unindexed = sorted(defined_draws - indexed_draws)
    shared = sorted(
        draw for draw, count in Counter(
            "%s.%s" % (module, draw) for module, draw in index.values()
        ).items() if count > 1
    )
    assert not missing_draws, "index points at missing draw functions: %s" % missing_draws
    for entry in index.values():
        module = entry[0]
        assert module in draws, "index module %s does not exist" % module
    unused_modules = sorted(set(draws) - {module for module, _draw in index.values()})

    assert set(index) == set(rows), "boss index and boss_data disagree:\n%s" % (
        sorted(set(index) ^ set(rows))
    )
    assert set(smart["methods"]) == {"_smart_ai_" + name for name in smart["dispatch"]}, (
        "Boss.update dispatch and the _smart_ai_* methods disagree"
    )
    for name in smart["dispatch"]:
        assert name in rows, "dispatch for unknown boss %s" % name

    return {
        "source": "bosses/ (Pygame, read-only oracle)",
        "files": files,
        "counts": {
            "files": len(files),
            "level_modules": len(draws),
            "structural": len(STRUCTURAL),
            "renderers": len(RENDERERS),
            "draw_definitions": definitions,
            "draw_functions": len(defined_draws),
            "index_entries": len(index),
            "smart_ai": len(smart["dispatch"]),
            "mini_bosses": tables["counts"]["mini"],
            "true_bosses": tables["counts"]["true"],
            "total_bosses": tables["counts"]["total"],
        },
        "structural": {
            name: files[name] for name in STRUCTURAL
        },
        "index": index,
        "draw_functions": {module: entry["draw"] for module, entry in draws.items()},
        "draw_namespaces": {
            module: entry["namespaces"]
            for module, entry in draws.items()
            if entry["namespaces"]
        },
        "unindexed_draw_functions": unindexed,
        "shadowed_draw_functions": sorted(duplicates),
        "shared_draw_functions": shared,
        "unused_level_modules": unused_modules,
        "smart_ai": smart["dispatch"],
        "smart_ai_methods": smart["methods"],
        "smart_ai_dispatch": smart["dispatch"],
        "boss_classes": {
            name: row.get("boss_class", "") for name, row in rows.items()
        },
        "hero_unlock_costs": {
            name: int(row.get("hero_unlock", {}).get("cost", -1)) for name, row in rows.items()
        },
        "hero_unlock_names": {
            name: row.get("hero_unlock", {}).get("name", "") for name, row in rows.items()
        },
        "mini_waves": tables["mini_waves"],
        "level_true_boss": tables["level_true_boss"],
        "curves": tables["curves"],
        "melee_role_hinta": tables["melee_role_hints"],
        "build_input_consumers": build_inputs_consumers(),
        "renderers": renderer_exports(),
        "renderer_namespaces": renderer_namespaces(),
    }


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the fixture")
    args = parser.parse_args(argv)
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote %s" % FIXTURE)
    on_disk = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.is_file() else None
    counts = fixture["counts"]
    print(
        "files %(files)d (levels %(level_modules)d, structural %(structural)d, renderers %(renderers)d) "
        "bosses %(total_bosses)d (mini %(mini_bosses)d, true %(true_bosses)d) "
        "draw defs %(draw_definitions)d index %(index_entries)d smart_ai %(smart_ai)d" % counts
    )
    if on_disk is not None and on_disk != fixture:
        print("fixture drift: rerun with --write", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
