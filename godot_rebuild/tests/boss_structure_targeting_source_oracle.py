"""Read-only source oracle for boss visibility to tower/nexus targeting.

Executes the real `Tower._find_target` and `Castle._find_target` from
`_entity.py` against source-shaped entities, with the enemy list built exactly
like the source call sites do. `Tower.update` queries the spatial grid and then
appends any living enemy boss inside `self.range` from an explicit `all_units`
scan; `Castle.update` builds `enemies` straight from `all_units`, whose last
element is the live boss. `_find_target` keeps the later candidate on an exact
tie, so an in-range boss wins tied distances.

The fixture also pins the source structures that make the boss a candidate at
all: the boss scan inside `Tower.update`, `Castle.update` reading `all_units`,
and `Game.update` adding `active_boss` to both `all_units` and the hero list
that feeds `update_spatial_grid`. Eight scenarios are recorded per boss type (four
distances for a tower and for the castle), each with the winner when the boss is
present and the winner when the boss is omitted - the second column is what the
native port used to return before layer 8m. `--write` rewrites the fixture.
"""
import ast
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/boss_structure_targeting_source.json"

STRUCTURE_RANGES = (("tower", "ARCHER_LEVELS"), ("castle", "NEXUS_LEVELS"))

# (label, unit distance expression, boss distance expression). Both are
# functions of `range` so the inclusive boundary and the tie are locked.
SCENARIOS = (
    ("boss_at_range_unit_out_of_range", lambda r: r + 40.0, lambda r: r),
    ("boss_out_of_range_unit_in_range", lambda r: r - 20.0, lambda r: r + 1.0),
    ("boss_ties_nearest_unit", lambda r: r / 2.0, lambda r: r / 2.0),
    ("boss_farther_than_unit", lambda r: r / 4.0, lambda r: r / 2.0),
)

EXPECTED = {
    "boss_at_range_unit_out_of_range": "boss",
    "boss_out_of_range_unit_in_range": "unit",
    "boss_ties_nearest_unit": "boss",
    "boss_farther_than_unit": "unit",
}


def target_class():
    """Exec the original Tower/Castle `_find_target` methods read-only."""
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    body = []
    for class_name in ("Tower", "Castle"):
        original = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name
        )
        method = next(
            node
            for node in original.body
            if isinstance(node, ast.FunctionDef) and node.name == "_find_target"
        )
        method = ast.parse(ast.unparse(method)).body[0]
        method.name = "tower_find_target" if class_name == "Tower" else "castle_find_target"
        body.append(method)
    cls = ast.ClassDef(
        name="SourceStructureTargeting", bases=[], keywords=[], body=body, decorator_list=[]
    )
    env = {"math": math}
    exec(  # noqa: S102 - executing the original source methods
        compile(
            ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
            "<source boss structure targeting>",
            "exec",
        ),
        env,
    )
    return env["SourceStructureTargeting"]


def method_node(class_name, method_name, source_file="_entity.py"):
    tree = ast.parse((ROOT / source_file).read_text(encoding="utf-8"))
    original = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def boss_scan_present(class_name):
    """Source shape of the `all_units` boss scan inside update()."""
    for node in ast.walk(method_node(class_name, "update")):
        if not isinstance(node, ast.For):
            continue
        text = ast.unparse(node)
        if "all_units" in text and "boss_type" in text and "append" in text and "range" in text:
            return True
    return False


def update_text():
    return ast.unparse(method_node("Game", "update", "_core.py"))


def grid_includes_boss():
    """`Game.update` appends the live boss to the list indexed by the grid."""
    text = update_text()
    return "spatial_heroes" in text and "active_boss" in text and "update_spatial_grid" in text


def all_units_includes_boss():
    """`Game.update` appends the live boss to `all_units` (the castle's list)."""
    text = update_text()
    return "all_units" in text and "active_boss" in text


def castle_uses_all_units():
    """`Castle.update` builds `enemies` from `all_units`, so the boss is listed."""
    text = ast.unparse(method_node("Castle", "update"))
    return "all_units" in text and "enemies = [u for u in all_units" in text


def cell(value):
    if value is None:
        return "none"
    return value


def source_tables():
    """Literal level-1 range table for each structure kind, straight from `_core.py`."""
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    tables = {}
    for _structure_kind, name in STRUCTURE_RANGES:
        node = next(
            item
            for item in core.body
            if isinstance(item, ast.Assign)
            and any(getattr(target, "id", "") == name for target in item.targets)
        )
        tables[name] = ast.literal_eval(node.value)
    return tables


def structure_targeting_cases(target_cls, boss_cls, lane_path):
    from bosses.boss_data import get_all_boss_types

    tables = source_tables()
    cases = []
    for kind in sorted(get_all_boss_types()):
        for structure_kind, source_table in STRUCTURE_RANGES:
            attack_range = float(tables[source_table][1]["range"])
            for label, unit_expr, boss_expr in SCENARIOS:
                distance_unit = unit_expr(attack_range)
                distance_boss = boss_expr(attack_range)
                structure = SimpleNamespace(x=0.0, y=0.0, team="blue", range=attack_range)
                unit = SimpleNamespace(x=distance_unit, y=0.0, alive=True, team="red")
                boss = boss_cls(kind, lane_path)
                boss.x = distance_boss
                boss.y = 0.0
                # Tower.update: grid results first, then the explicit in-range
                # boss scan. Castle.update: `enemies` is all_units (the live boss
                # is its last element). An out-of-range placeholder can never win
                # `_find_target`, so both lists record the same source winner.
                if structure_kind == "tower":
                    enemies = [unit]
                    if math.hypot(boss.x, boss.y) <= attack_range:
                        enemies.append(boss)
                else:
                    enemies = [unit, boss]
                finder = getattr(
                    target_cls, "tower_find_target" if structure_kind == "tower" else "castle_find_target"
                )
                winner = finder(structure, enemies)
                winner_without_boss = finder(structure, [unit])
                tag = "boss" if winner is boss else ("unit" if winner is unit else None)
                tag_without_boss = (
                    "boss"
                    if winner_without_boss is boss
                    else ("unit" if winner_without_boss is unit else None)
                )
                assert tag == EXPECTED[label], "%s source targeting drifted for %s" % (
                    label,
                    structure_kind,
                )
                assert tag_without_boss != "boss", "boss omission case must not pick the boss"
                cases.append(
                    {
                        "boss_type": kind,
                        "structure_kind": structure_kind,
                        "label": label,
                        "range": attack_range,
                        "unit_distance": distance_unit,
                        "boss_distance": distance_boss,
                        "boss_in_range": distance_boss <= attack_range,
                        "expected": cell(tag),
                        "expected_without_boss": cell(tag_without_boss),
                    }
                )
    return cases


def source_fixture():
    from boss_core_source_oracle import boss_class as core_boss_class
    from boss_core_source_oracle import namespace as core_namespace
    from check_source_contract import source_lanes

    env = core_namespace()
    boss_cls = core_boss_class(env)
    target_cls = target_class()
    lane_path = source_lanes()["mid"]
    return {
        "source": {
            "tower_boss_scan": boss_scan_present("Tower"),
            "castle_uses_all_units": castle_uses_all_units(),
            "all_units_includes_boss": all_units_includes_boss(),
            "grid_includes_boss": grid_includes_boss(),
            "tower_range": float(source_tables()["ARCHER_LEVELS"][1]["range"]),
            "castle_range": float(source_tables()["NEXUS_LEVELS"][1]["range"]),
        },
        "cases": structure_targeting_cases(target_cls, boss_cls, lane_path),
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s (%d cases)" % (FIXTURE, len(actual["cases"])))
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Boss structure targeting source drift"
        )
        print(
            "PASS: Boss structure targeting — %d cases across %d boss types"
            % (len(actual["cases"]), len({row["boss_type"] for row in actual["cases"]}))
        )


if __name__ == "__main__":
    main()
