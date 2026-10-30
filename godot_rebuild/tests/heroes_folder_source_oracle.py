"""Whole-folder oracle for `heroes/`: all 34 modules, every symbol accounted for.

`heroes/` is the largest folder in the Pygame tree (~101.000 lines) and it is
two very different things at once:

* the **hero rendering pipeline** -- `HERO_RENDERERS` (six starters), the
  measured-scale formula, the sprite cache, the pose/quantum cache and the
  per-frame budgets. Godot already carries that half as pre-baked atlases
  (`data/art/heroes.json`, 222 heroes, 8 phases) plus `scripts/ui/hero_art.gd`
  and `scripts/ui/hero_anim.gd`;
* the **live FX layer** -- 27 `*_fx.py` directors (particles, trails, ground
  decals, projectiles) driven by a shared bus in `__init__.py` that owns the
  combat-load governor hooks (`begin_fx_frame`, `count_busy_fx_heroes`) and a
  per-frame ground-layer budget.

This oracle parses the folder with `ast` only: nothing executes, so no pygame,
no display and no `settings`/`sound_manager` imports are needed. The native
side must answer for the result in `tests/heroes_folder_checks.gd`, and
`docs/HEROES_FOLDER_MIGRATION.md` must classify every module in the folder.

What the fixture pins:

* the folder inventory: 34 files, per-file line counts, 27 FX modules, 4 `_v1`
  pixel-art renderers;
* the live-FX bus: the 27 hero ids in registry order, the module path of each,
  the ground-layer budget default (99), the `MYSTIC_FX_GROUND` opt-out, the
  "attach + tick still run when the ground budget is exhausted" rule;
* the combat-load governor that the bus feeds (`mobile/perf.py`): smoothing
  0.40, one free hero, exponent 1.5, floor 0.10, spawn tokens 140/18/10 with
  refund floors 56/10/5;
* the quality presets those knobs are read from: particle ratio 0.20/0.40/0.70,
  pose floors skill 12/8/4 and attack 6/4/3, ground budget 2/3/6, full-render
  budget 3/4/8;
* the renderer pipeline constants: scale 0.78 global, 65 px target height,
  1.6 reference aspect, 0.0 width weight, 0.65 fallback, clamp 0.40-1.70,
  8 animation phases, `HERO_ATK_QUANT` 4 / `HERO_SKILL_QUANT` 6 (the source
  values, not the preset floors);
* every FX module's own surface: how many `def`s, which of the twelve shared
  entry points it exposes, and its particle caps;
* the four `_v1` modules and the `install(legacy_cls)` hook that makes them the
  *effective* renderer for kaizen/vex/grimjaw/sylara inside `_bundle.py`;
* `combat_feel.py`'s hit-stop/fixed-timestep constants and public helpers.

Run: python godot_rebuild/tests/heroes_folder_source_oracle.py --write
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEROES = ROOT / "heroes"
PERF = ROOT / "mobile" / "perf.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "heroes_folder_source.json"

# The twelve shared entry points every live FX module exposes. The native bus
# declares the same contract so a future port cannot silently drop one.
FX_CONTRACT = (
    "attach",
    "owns",
    "tick",
    "draw_ground_layer",
    "draw_live_layer",
    "reset_all",
    "stats",
    "total_particles",
    "MAX_PARTICLES",
    "Particle",
    "ParticleSystem",
    "ProjectileSystem",
)

V1_MODULES = ("kaizen_v1", "vex_v1", "grimjaw_v1", "sylara_v1")
CONST_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
CAP_NAME = re.compile(r"MAX|CAP|LIMIT")


def _source(path):
    return path.read_text(encoding="utf-8")


def _eval(node, consts):
    """Evaluate `0.40`, `HIT_STOP_MIN`, `1.0 / 60.0`, `-1` style module values."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return consts.get(node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _eval(node.operand, consts)
        return -value if isinstance(value, (int, float)) else None
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, consts)
        right = _eval(node.right, consts)
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            return None
        if isinstance(node.op, ast.Div) and right:
            return left / right
        if isinstance(node.op, ast.Mult):
            return left * right
    return None


def _literal(node, default=None):
    try:
        return ast.literal_eval(node)
    except Exception:
        return default


def _modules():
    return sorted(p for p in HEROES.glob("*.py") if p.is_file())


def _top_functions(tree):
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def _top_classes(tree):
    return [n.name for n in tree.body if isinstance(n, ast.ClassDef)]


def _top_constants(tree):
    """Module-level UPPER_CASE assignments with literal values."""
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if not CONST_NAME.match(target.id):
                continue
            value = _literal(node.value)
            if isinstance(value, (int, float, str, bool)) and not isinstance(value, bool):
                out[target.id] = value
            elif isinstance(value, bool):
                out[target.id] = value
    return out


def _assigned(tree, name):
    """Value of a module-level `name = <literal>`."""
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                return _literal(node.value, "<non-literal>")
    return None


def _cond_values(node):
    """Turn `a if low else (b if med else c)` into {'low': a, 'medium': b, 'high': c}."""
    out = {}
    while isinstance(node, ast.IfExp):
        key = None
        if isinstance(node.test, ast.Name):
            key = node.test.id
        elif isinstance(node.test, ast.Attribute):
            key = node.test.attr
        if key == "low":
            key = "low"
        elif key == "med":
            key = "medium"
        if key is not None:
            value = _literal(node.body)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out[key] = value
        node = node.orelse
    value = _literal(node)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        out["high"] = value
    return out


def _preset(tree, attribute):
    """Read `self.<attribute> = <ternary>` out of `_Quality.apply`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Attribute) or target.attr != attribute:
                continue
            values = _cond_values(node.value)
            if values:
                return values
    return {}


def _reset_floor(tree, target_name):
    """Literal floor of `<target_name> = max(N, ...)` inside `_reset_fx_tokens`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if not any(isinstance(t, ast.Name) and t.id == target_name for t in node.targets):
            continue
        func = node.value.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        if name not in ("max", "min"):
            continue
        for arg in node.value.args:
            value = _literal(arg)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
    return None


def _function_source(path, name):
    """Raw source lines of a top-level function (for clamp regexes)."""
    text = _source(path)
    tree = ast.parse(text)
    lines = text.splitlines()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return "\n".join(lines[node.lineno - 1: node.end_lineno])
    return ""


def live_fx(tree):
    """`_LIVE_FX_HEROES` is a set literal; keep a stable sorted list."""
    heroes = _assigned(tree, "_LIVE_FX_HEROES")
    paths = _assigned(tree, "_LIVE_FX_PATHS")
    if isinstance(heroes, (set, frozenset, list, tuple)):
        names = sorted(h for h in heroes if isinstance(h, str))
    else:
        names = []
    return {
        "heroes": names,
        "heroes_kind": "set" if isinstance(heroes, (set, frozenset)) else "sequence",
        "paths": paths if isinstance(paths, dict) else {},
    }


def renderers(tree):
    """`HERO_RENDERERS["<hero>"] = draw_<hero>` assignment order."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Subscript):
                continue
            base = getattr(target.value, "id", None)
            if base != "HERO_RENDERERS":
                continue
            key = _literal(target.slice)
            if isinstance(key, str):
                out.append(key)
    return out


def scale_block():
    path = HEROES / "__init__.py"
    tree = ast.parse(_source(path))
    body = _function_source(path, "_get_hero_scale")
    clamp = re.findall(r"max\(([0-9.]+), min\(([0-9.]+)", body)
    lo, hi = (float(clamp[-1][0]), float(clamp[-1][1])) if clamp else (0.0, 0.0)
    return {
        "global_scale": _assigned(tree, "HERO_GLOBAL_SCALE"),
        "target_height": _assigned(tree, "HERO_TARGET_HEIGHT"),
        "ref_aspect": _assigned(tree, "_HERO_REF_ASPECT"),
        "width_weight": _assigned(tree, "HERO_SIZE_WIDTH_WEIGHT"),
        "default_scale": _assigned(tree, "_DEFAULT_HERO_SCALE"),
        "clamp_min": lo,
        "clamp_max": hi,
        "anim_phases": _assigned(tree, "HERO_ANIM_PHASES"),
        "atk_quant": _assigned(tree, "HERO_ATK_QUANT"),
        "skill_quant": _assigned(tree, "HERO_SKILL_QUANT"),
        "scale_override": _assigned(tree, "_HERO_SCALE_OVERRIDE"),
        "ground_budget_default": _assigned(tree, "_FX_GROUND_LEFT"),
        "ground_env_opt_out": "MYSTIC_FX_GROUND" in _source(path),
    }


def governor():
    tree = ast.parse(_source(PERF))
    return {
        "load_smooth": _assigned(tree, "_FX_LOAD_SMOOTH"),
        "base_heroes": _assigned(tree, "_FX_BASE_HEROES"),
        "load_min": _assigned(tree, "_FX_LOAD_MIN"),
        "load_exp": _assigned(tree, "_FX_LOAD_EXP"),
        "particle_cap": _assigned(tree, "_FX_PARTICLE_CAP"),
        "projectile_cap": _assigned(tree, "_FX_PROJ_CAP"),
        "skill_projectile_cap": _assigned(tree, "_FX_SKILL_PROJ_CAP"),
        "particle_floor": _reset_floor(tree, "_FX_PARTICLE_LEFT"),
        "projectile_floor": _reset_floor(tree, "_FX_PROJ_LEFT"),
        "skill_projectile_floor": _reset_floor(tree, "_FX_SKILL_PROJ_LEFT"),
        "particle_ratio": _preset(tree, "particle_ratio"),
        "skill_quant_floor": _preset(tree, "skill_quant_floor"),
        "atk_quant_floor": _preset(tree, "atk_quant_floor"),
        "ground_budget": _preset(tree, "fx_ground_budget"),
        "max_hero_render": _preset(tree, "max_hero_render"),
        "skill_projectile_gate": _assigned(tree, "_FX_SKILL_PROJ_CAP"),
        "tokens_gated": "_FX_TOKENS_ACTIVE" in _source(PERF),
    }


def fx_module(path):
    text = _source(path)
    tree = ast.parse(text)
    funcs = _top_functions(tree)
    classes = _top_classes(tree)
    consts = _top_constants(tree)
    caps = {k: v for k, v in consts.items() if CAP_NAME.search(k)}
    available = set(funcs) | set(classes) | set(consts)
    return {
        "lines": len(text.splitlines()),
        "defs": len(funcs),
        "classes": classes,
        "api": [name for name in FX_CONTRACT if name in available],
        "missing_api": [name for name in FX_CONTRACT if name not in available],
        "caps": caps,
    }


def v1_module(path):
    text = _source(path)
    tree = ast.parse(text)
    funcs = _top_functions(tree)
    installs = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "install":
            installs = ast.unparse(node.args)
    return {
        "lines": len(text.splitlines()),
        "functions": funcs,
        "install_args": installs,
        "subclasses_legacy": "legacy_cls" in text,
    }


def bundle():
    path = HEROES / "_bundle.py"
    text = _source(path)
    tree = ast.parse(text)
    namespaces = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("_NS_"):
            namespaces[node.name] = [
                item.name for item in node.body
                if isinstance(item, ast.FunctionDef) and item.name.startswith("draw_")
            ]
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("_NS_"):
                    namespaces.setdefault(target.id, [])
    installs = {}
    for line in text.splitlines():
        match = re.search(r"_NS_([a-z]+) = _install_([a-z]+)_v1\(_NS_([a-z]+)\)", line)
        if match:
            installs[match.group(1)] = {
                "module": "%s_v1" % match.group(2),
                "same_namespace": match.group(1) == match.group(3),
            }
    return {
        "lines": len(text.splitlines()),
        "namespaces": {name: namespaces[name] for name in sorted(namespaces)},
        "namespace_count": len(namespaces),
        "v1_installs": installs,
        "renderer_functions": sum(len(v) for v in namespaces.values()),
    }


def skill_quant_ladder():
    """`_skill_quant`'s busy-count ladder: thresholds and the quantum per step."""
    body = _function_source(HEROES / "__init__.py", "_skill_quant")
    thresholds = [int(x) for x in re.findall(r"if n <= (\d+)", body)]
    values = re.findall(r"q = (HERO_SKILL_QUANT|\d+)", body)
    return {"thresholds": thresholds, "values": values}


def combat_feel():
    path = HEROES / "combat_feel.py"
    tree = ast.parse(_source(path))
    consts = _top_constants(tree)
    hit_stop = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "HitStop":
            for item in node.body:
                if not isinstance(item, ast.Assign):
                    continue
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        hit_stop[target.id] = _eval(item.value, consts)
    consts["FIXED_DT"] = _eval(
        next(
            (
                node.value
                for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "FIXED_DT" for t in node.targets)
            ),
            ast.Constant(0.0),
        ),
        consts,
    )
    return {
        "lines": len(_source(path).splitlines()),
        "constants": {k: consts[k] for k in sorted(consts)},
        "hit_stop": {k: hit_stop[k] for k in sorted(hit_stop)},
        "functions": _top_functions(tree),
        "classes": _top_classes(tree),
    }


def aliases(tree):
    extra = _assigned(tree, "_EXTRA")
    if not isinstance(extra, dict):
        return {}
    return {name: len(syms) for name, syms in sorted(extra.items()) if isinstance(syms, list)}


def source_fixture():
    files = _modules()
    trees = {p.name: ast.parse(_source(p)) for p in files}
    init_tree = trees["__init__.py"]
    fx = {p.name: fx_module(p) for p in files if p.name.endswith("_fx.py")}
    v1 = {p.name: v1_module(p) for p in files if p.name.endswith("_v1.py")}
    paths = live_fx(init_tree)["paths"]
    return {
        "folder": {
            "files": len(files),
            "lines": sum(len(_source(p).splitlines()) for p in files),
            "fx_modules": len(fx),
            "v1_modules": len(v1),
            "per_file_lines": {p.name: len(_source(p).splitlines()) for p in files},
        },
        "live_fx": {
            "heroes": live_fx(init_tree)["heroes"],
            "heroes_kind": live_fx(init_tree)["heroes_kind"],
            "paths": {k: paths[k] for k in sorted(paths)},
            "contract": list(FX_CONTRACT),
            "bus_functions": [
                name
                for name in _top_functions(init_tree)
                if name in ("begin_fx_frame", "fx_frame", "count_busy_fx_heroes", "_fx_busy",
                            "_reset_fx_ground_budget", "_live_fx_pre", "_live_fx_post",
                            "_install_global_fx_caps", "_skill_quant", "_atk_quant")
            ],
        },
        "renderers": {
            "heroes": renderers(init_tree),
            "aliases": aliases(init_tree),
            "scale": scale_block(),
        },
        "governor": governor(),
        "skill_quant_ladder": skill_quant_ladder(),
        "fx": fx,
        "v1": v1,
        "bundle": bundle(),
        "combat_feel": combat_feel(),
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote %s" % FIXTURE)
        return 0
    if not FIXTURE.is_file():
        print("missing fixture: run with --write", file=sys.stderr)
        return 1
    on_disk = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if on_disk != fixture:
        print("heroes/ inventory drifted from the source folder", file=sys.stderr)
        return 1
    print("heroes/ inventory matches the source folder")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
