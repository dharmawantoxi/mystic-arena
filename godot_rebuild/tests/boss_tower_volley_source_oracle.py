"""Read-only source oracle for boss visibility in tower multi-shot volleys and chains.

Executes the real `Tower._find_target`, `Tower._shoot`, `Tower._shoot_archer`
and `Tower._shoot_mage` from `_entity.py`, together with the boss-scan loop
inside `Tower.update` and the real `Boss` class from `boss_core_source_oracle`.

In `Tower.update` (`_entity.py:815-831`), any living enemy boss inside
`self.range` (inclusive) is appended to `enemies` after the spatial-grid unit
query, and that same `enemies` list is passed to both `self._find_target(enemies)`
and `self._shoot(enemies)`:

* `Tower._shoot_archer(enemies)` (`_entity.py:915-925`) builds
  `targets = [self.target]`, scans `enemies` for secondary living targets inside
  `self.range` (inclusive) up to `num_shots` (2 at level 5, 3 at level 6), and
  refills any still-missing slots with `self.target`.
* `Tower._shoot_mage(enemies)` (`_entity.py:1031-1049`) builds
  `targets = [self.target]`, scans `enemies` for secondary living targets inside
  `self.range` (inclusive) up to `self.chain` (2 at levels 2-3, 3 at levels 4-5,
  4 at level 6), and emits one `"mage"` bullet per target with no refill.

Before layer 8t, `SiegeBattle.fire_projectile` scanned only `units` (which never
contains `active_boss`), so whenever a closer unit was the primary target, an
archer volley refilled its extra arrow(s) onto the unit instead of shooting the
boss, and a mage tower dropped the chain bolt to the boss completely.

Four scenarios are recorded for each of the 216 boss types (864 cases total),
each carrying `expected` (with the live boss in `all_units`) and
`expected_without_boss` (the pre-layer `units`-only scan). `--write` rewrites
the fixture.
"""
import ast
import json
import math
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/boss_tower_volley_source.json"

TOWER_POS = (500.0, 340.0)

# (label, tower_path, level, unit_offsets, boss_offset)
SCENARIOS = (
    ("archer_l5_boss_at_range_edge", "archer", 5, (80.0,), 220.0),
    ("archer_l6_unit_fills_before_boss", "archer", 6, (60.0, 120.0), 180.0),
    ("mage_l2_boss_at_range_edge", "mage", 2, (60.0,), 180.0),
    ("mage_l6_boss_outside_range", "mage", 6, (60.0,), 231.0),
)


def _nodes(source_file):
    return ast.parse((ROOT / source_file).read_text(encoding="utf-8")).body


def _method_node(class_name, method_name, source_file="_entity.py"):
    original = next(
        node
        for node in _nodes(source_file)
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def _boss_scan_loop_node():
    """Extract the exact `for u in all_units:` boss scan from `Tower.update`."""
    update_node = _method_node("Tower", "update")
    for node in update_node.body:
        if not isinstance(node, ast.For):
            continue
        text = ast.unparse(node)
        if "all_units" in text and "boss_type" in text and "enemies.append(u)" in text:
            return node
    raise AssertionError("Tower.update boss scan loop not found")


def build_env():
    from cannon_source_oracle import build_env as cannon_env

    env = cannon_env()
    tower_type = env["SourceTower"]
    for name in ("_find_target", "_shoot", "_shoot_archer", "_shoot_mage"):
        node = _method_node("Tower", name)
        exec(  # noqa: S102 - executing the original source methods read-only
            compile(
                ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                "<source tower volley %s>" % name,
                "exec",
            ),
            env,
        )
        setattr(tower_type, name, env[name])

    scan_loop = _boss_scan_loop_node()
    scan_fn = ast.FunctionDef(
        name="_append_boss_scan",
        args=ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(arg="self"),
                ast.arg(arg="enemies"),
                ast.arg(arg="all_units"),
            ],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=[scan_loop],
        decorator_list=[],
    )
    exec(  # noqa: S102 - executing the original Tower.update boss scan read-only
        compile(
            ast.fix_missing_locations(ast.Module(body=[scan_fn], type_ignores=[])),
            "<source tower boss scan>",
            "exec",
        ),
        env,
    )
    tower_type._append_boss_scan = env["_append_boss_scan"]

    bundle = ast.parse((ROOT / "towers/_bundle.py").read_text(encoding="utf-8"))
    for ns_name, fn_name, mod_key in (
        ("_NS_archer_tower", "get_archer_bow_position", "archer_helper"),
        ("_NS_mage_tower", "get_mage_crystal_position", "mage_helper"),
    ):
        ns_node = next(
            node
            for node in bundle.body
            if isinstance(node, ast.ClassDef) and node.name == ns_name
        )
        config = next(
            node.value
            for node in ns_node.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "LEVEL_CONFIGS" for t in node.targets)
        )
        helper = next(
            node
            for node in ns_node.body
            if isinstance(node, ast.FunctionDef) and node.name == fn_name
        )
        helper.decorator_list = []
        env[ns_name] = SimpleNamespace(LEVEL_CONFIGS=ast.literal_eval(config))
        exec(  # noqa: S102 - executing the original tower muzzle helper read-only
            compile(
                ast.fix_missing_locations(ast.Module(body=[helper], type_ignores=[])),
                "<source %s>" % fn_name,
                "exec",
            ),
            env,
        )
        env[mod_key] = env[fn_name]
    return env


def boss_env():
    from boss_core_source_oracle import boss_class, namespace

    env = namespace()
    return env, boss_class(env)


def _make_tower(env, path, level):
    tower = env["SourceTower"](TOWER_POS[0], TOWER_POS[1], "blue")
    assert tower.upgrade(path)
    while tower.level < level:
        assert tower.upgrade(path if path == "archer" else None)
    return tower


def _tag_of(target, units, boss):
    if target is boss:
        return "boss"
    for idx, unit in enumerate(units):
        if target is unit:
            return "unit_%d" % (idx + 1)
    raise AssertionError("Unknown volley target: %r" % (target,))


def _run_shot(env, tower, units, boss, include_boss):
    # Spatial grid returns living enemy units inside tower.range in stable order;
    # Tower.update then runs its explicit boss scan over all_units.
    enemies = [
        u
        for u in units
        if u.alive
        and u.team != tower.team
        and math.hypot(u.x - tower.x, u.y - tower.y) <= tower.range
    ]
    all_units = list(units) + ([boss] if include_boss else [])
    tower._append_boss_scan(enemies, all_units)
    tower.target = tower._find_target(enemies)
    assert tower.target is units[0], "Primary target must be the nearest unit"
    tower.angle = math.atan2(tower.target.y - tower.y, tower.target.x - tower.x)
    shots = []
    env["Bullet"] = lambda x, y, tgt, dmg, team, kind="normal", special=None: shots.append(
        {
            "target": _tag_of(tgt, units, boss),
            "damage": int(dmg),
            "kind": str(kind),
            "special": dict(special or {}),
        }
    )
    tower.bullets = []
    tower._shoot(enemies)
    shot_targets = [row["target"] for row in shots]
    return {
        "primary": _tag_of(tower.target, units, boss),
        "shot_targets": shot_targets,
        "shot_count": len(shot_targets),
        "boss_shots": sum(tag == "boss" for tag in shot_targets),
    }


def volley_cases(env, boss_cls):
    from bosses.boss_data import get_all_boss_types

    archer_mod = ModuleType("towers.archer_tower")
    archer_mod.get_archer_bow_position = env["archer_helper"]
    mage_mod = ModuleType("towers.mage_tower")
    mage_mod.get_mage_crystal_position = env["mage_helper"]

    cases = []
    with patch.dict(
        sys.modules,
        {
            "towers": ModuleType("towers"),
            "towers.archer_tower": archer_mod,
            "towers.mage_tower": mage_mod,
        },
    ):
        towers = {
            (path, level): _make_tower(env, path, level)
            for _label, path, level, _units, _boss in SCENARIOS
        }
        for kind in sorted(get_all_boss_types()):
            for label, path, level, unit_offsets, boss_offset in SCENARIOS:
                tower = towers[(path, level)]
                units = [
                    SimpleNamespace(
                        id=idx + 1,
                        x=TOWER_POS[0] + float(offset),
                        y=TOWER_POS[1],
                        alive=True,
                        team="red",
                    )
                    for idx, offset in enumerate(unit_offsets)
                ]
                boss = boss_cls(kind, None)
                boss.x = TOWER_POS[0] + float(boss_offset)
                boss.y = TOWER_POS[1]
                expected = _run_shot(env, tower, units, boss, include_boss=True)
                without_boss = _run_shot(env, tower, units, boss, include_boss=False)
                if label != "mage_l6_boss_outside_range":
                    assert expected["boss_shots"] == 1, "%s must hit the boss once" % label
                    assert without_boss["boss_shots"] == 0, (
                        "%s without boss must never target the boss" % label
                    )
                else:
                    assert expected["boss_shots"] == 0 and without_boss["boss_shots"] == 0
                cases.append(
                    {
                        "boss_type": kind,
                        "label": label,
                        "tower_path": path,
                        "level": int(level),
                        "range": float(tower.range),
                        "slot_count": int(
                            tower.chain
                            if path == "mage"
                            else (2 if level == 5 else 3)
                        ),
                        "unit_distances": [float(offset) for offset in unit_offsets],
                        "boss_distance": float(boss_offset),
                        "boss_in_range": float(boss_offset) <= float(tower.range),
                        "expected": expected,
                        "expected_without_boss": without_boss,
                    }
                )
    return cases


def _update_text():
    return ast.unparse(_method_node("Tower", "update"))


def _shoot_text():
    return ast.unparse(_method_node("Tower", "_shoot"))


def _shoot_archer_text():
    return ast.unparse(_method_node("Tower", "_shoot_archer"))


def _shoot_mage_text():
    return ast.unparse(_method_node("Tower", "_shoot_mage"))


def _game_update_text():
    return ast.unparse(_method_node("Game", "update", "_core.py"))


SOURCE_FLAGS = {
    "tower_boss_scan_in_update": lambda: (
        "getattr(u, 'boss_type', None)" in _update_text()
        and "math.hypot(u.x - self.x, u.y - self.y) <= self.range" in _update_text()
        and "enemies.append(u)" in _update_text()
    ),
    "tower_update_passes_enemies_to_shoot": lambda: (
        "self.target = self._find_target(enemies)" in _update_text()
        and "self._shoot(enemies)" in _update_text()
    ),
    "shoot_dispatches_archer_and_mage": lambda: (
        "self._shoot_archer(enemies)" in _shoot_text()
        and "self._shoot_mage(enemies)" in _shoot_text()
    ),
    "archer_volley_scans_enemies_inclusive": lambda: (
        "for e in enemies:" in _shoot_archer_text()
        and "if len(targets) >= num_shots:" in _shoot_archer_text()
        and "if dist <= self.range:" in _shoot_archer_text()
    ),
    "archer_volley_refills_primary": lambda: (
        "while len(targets) < num_shots:" in _shoot_archer_text()
        and "targets.append(self.target)" in _shoot_archer_text()
    ),
    "mage_chain_scans_enemies_inclusive": lambda: (
        "for e in enemies:" in _shoot_mage_text()
        and "if len(targets) >= self.chain:" in _shoot_mage_text()
        and "if dist <= self.range:" in _shoot_mage_text()
    ),
    "mage_chain_has_no_refill": lambda: "while len(targets)" not in _shoot_mage_text(),
    "all_units_includes_boss": lambda: (
        "all_units = all_units + [self.active_boss]" in _game_update_text()
    ),
}


def source_fixture():
    env = build_env()
    _env, boss_cls = boss_env()
    flags = {name: bool(check()) for name, check in SOURCE_FLAGS.items()}
    for name, value in flags.items():
        assert value, "source shape drifted: %s" % name
    return {
        "source": dict(
            flags,
            **{
                "archer_l5": {
                    "range": float(env["ARCHER_LEVELS"][5]["range"]),
                    "damage": int(env["ARCHER_LEVELS"][5]["damage"]),
                    "volley_count": 2,
                },
                "archer_l6": {
                    "range": float(env["ARCHER_LEVELS"][6]["range"]),
                    "damage": int(env["ARCHER_LEVELS"][6]["damage"]),
                    "volley_count": 3,
                },
                "mage_l2": {
                    "range": float(env["MAGE_LEVELS"][2]["range"]),
                    "damage": int(env["MAGE_LEVELS"][2]["damage"]),
                    "chain": int(env["MAGE_LEVELS"][2]["chain"]),
                    "skill_down": float(env["MAGE_LEVELS"][2]["skill_down"]),
                    "anti_heal": float(env["MAGE_LEVELS"][2]["anti_heal"]),
                    "debuff_duration": int(env["MAGE_LEVELS"][2]["debuff_duration"]),
                },
                "mage_l6": {
                    "range": float(env["MAGE_LEVELS"][6]["range"]),
                    "damage": int(env["MAGE_LEVELS"][6]["damage"]),
                    "chain": int(env["MAGE_LEVELS"][6]["chain"]),
                    "skill_down": float(env["MAGE_LEVELS"][6]["skill_down"]),
                    "anti_heal": float(env["MAGE_LEVELS"][6]["anti_heal"]),
                    "debuff_duration": int(env["MAGE_LEVELS"][6]["debuff_duration"]),
                },
            },
        ),
        "cases": volley_cases(env, boss_cls),
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s (%d cases)" % (FIXTURE, len(actual["cases"])))
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Boss tower volley source drift"
        )
        print(
            "PASS: Boss tower volley — %d cases across %d boss types"
            % (len(actual["cases"]), len({row["boss_type"] for row in actual["cases"]}))
        )


if __name__ == "__main__":
    main()
