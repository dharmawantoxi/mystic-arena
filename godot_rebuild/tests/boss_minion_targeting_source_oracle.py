"""Read-only source oracle for boss visibility to minion targeting.

Executes the real `Minion._get_enemies` and `Minion._find_target_smart` from
`_entity.py` on top of the real `SpatialGrid` / `update_spatial_grid` /
`query_enemies_in_range` from `_system.py`, with the indexed lists built exactly
like the source call site: `Game.update` inserts `self.minions` plus
`spatial_heroes`, and `spatial_heroes` gains the live boss as its LAST element
(`spatial_heroes = spatial_heroes + [self.active_boss]`). Towers and bases are
never indexed - `_get_enemies` appends them after the grid results, inside
`self.range + 30`.

That ordering is what the fixture pins:

* the boss is a candidate at all (the native registry never holds it),
* the inclusive grid radius `range + 30` and the strict `< range + 30` fallback
  agree at the edge,
* `_find_target_smart` groups filter with `isinstance(e, Minion)`, so the boss is
  never part of the lane/lowest-hp minion groups,
* the siege group (`max_hp >= 1500`) returns the first match in enemy order, and
  the boss - a grid result - precedes every appended tower.

Four scenarios are recorded per boss type, each with the winner when the boss is
indexed and the winner when it is omitted; the second column is what the native
port returned before layer 8n. `--write` rewrites the fixture.
"""
import ast
import json
import math
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/boss_minion_targeting_source.json"

MINION_KIND = "goblin"
QUERIER = (600.0, 300.0)

# (label, ai_level, boss distance, unit distance, tower distance, boss hp).
# Distances are functions of the source minion `range` so the inclusive attack
# boundary, the inclusive grid radius and the strict fallback all stay locked.
SCENARIOS = (
    ("boss_at_attack_range_edge", 1, lambda r: r, lambda r: r + 10.0, None, None),
    ("boss_at_grid_radius_edge", 1, lambda r: r + 30.0, lambda r: r + 10.0, None, None),
    ("boss_outside_minion_group", 4, lambda r: r * 0.6, lambda r: r * 0.9, None, 1.0),
    ("boss_precedes_siege_tower", 5, lambda r: r * 0.6, lambda r: r * 0.2, lambda r: r * 0.4, None),
)

EXPECTED = {
    "boss_at_attack_range_edge": "boss",
    "boss_at_grid_radius_edge": "unit",
    "boss_outside_minion_group": "unit",
    "boss_precedes_siege_tower": "boss",
}


def _module(*nodes):
    return compile(
        ast.fix_missing_locations(ast.Module(body=list(nodes), type_ignores=[])),
        "<source minion targeting>",
        "exec",
    )


def _nodes(source_file):
    return ast.parse((ROOT / source_file).read_text(encoding="utf-8")).body


def _method_node(class_name, method_name, source_file="_entity.py"):
    original = next(
        node for node in _nodes(source_file) if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def grid_cell_size():
    """Literal cell size of the module-level `_grid = SpatialGrid(cell_size=60)`."""
    node = next(
        item
        for item in _nodes("_system.py")
        if isinstance(item, ast.Assign)
        and any(getattr(target, "id", "") == "_grid" for target in item.targets)
    )
    return int(ast.literal_eval(node.value.keywords[0].value))


def grid_namespace():
    """Exec the real spatial grid read-only; no pygame import is triggered."""
    wanted = {"SpatialGrid", "update_spatial_grid", "query_enemies_in_range"}
    body = [
        node
        for node in _nodes("_system.py")
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in wanted
    ]
    assert len(body) == 3, "Re-audit the spatial grid before trusting this oracle"
    env = {"math": math}
    exec(_module(*body), env)  # noqa: S102 - executing the original source grid
    env["_grid"] = env["SpatialGrid"](cell_size=grid_cell_size())
    stub = sys.modules.setdefault("_system", ModuleType("_system"))
    stub.query_enemies_in_range = env["query_enemies_in_range"]
    stub.update_spatial_grid = env["update_spatial_grid"]
    return env


def minion_class(grid_env):
    """Exec the real Minion lookup/selection methods into a class named Minion.

    The name matters: `_find_target_smart` groups filter with
    `isinstance(e, Minion)`, so the source-shaped minions built here are group
    members while the real Boss (TowerDebuffMixin) is not.
    """
    wanted = ("_get_enemies", "_find_target_smart", "_distance_to")
    body = [ast.parse(ast.unparse(_method_node("Minion", name))).body[0] for name in wanted]
    cls = ast.ClassDef(name="Minion", bases=[], keywords=[], body=body, decorator_list=[])
    env = dict(grid_env)
    exec(_module(cls), env)  # noqa: S102 - executing the original source methods
    return env["Minion"], env


def make_minion(cls, x, y, team, attack_range, hp, ai_level=1, lane=0):
    unit = cls.__new__(cls)
    unit.x = float(x)
    unit.y = float(y)
    unit.team = team
    unit.range = float(attack_range)
    unit.hp = float(hp)
    unit.max_hp = float(hp)
    unit.ai_level = ai_level
    unit.lane = lane
    unit.alive = True
    return unit


def make_tower(x, y, team, hp):
    """Source-shaped Tower: no `tower_kind` attribute is ever stored."""
    from types import SimpleNamespace

    return SimpleNamespace(x=float(x), y=float(y), team=team, alive=True, hp=float(hp), max_hp=float(hp))


class _Literalize(ast.NodeTransformer):
    """Blank out the colour names inside the stat tables; only numbers matter."""

    def visit_Name(self, node):  # noqa: N802 - ast visitor naming
        return ast.copy_location(ast.Constant(value=None), node)


def _core_literal(name):
    node = next(
        item
        for item in _nodes("_core.py")
        if isinstance(item, ast.Assign)
        and any(getattr(target, "id", "") == name for target in item.targets)
    )
    return ast.literal_eval(_Literalize().visit(node.value))


def minion_stats():
    """Literal goblin row straight from `_core.MINION_TYPES`."""
    table = _core_literal("MINION_TYPES")[MINION_KIND]
    return float(table["range"]), float(table["hp"])


def tower_stats():
    """Source `Tower._apply_level_stats` for a level-1 archer: max_hp and range."""
    base = _core_literal("ARCHER_LEVELS")[1]
    return int(base["hp"] * _core_literal("TOWER_HP_MULTIPLIER")), float(base["range"])


def get_enemies_text():
    return ast.unparse(_method_node("Minion", "_get_enemies"))


def smart_text():
    return ast.unparse(_method_node("Minion", "_find_target_smart"))


def update_text():
    return ast.unparse(_method_node("Minion", "update"))


def game_update_text():
    return ast.unparse(_method_node("Game", "update", "_core.py"))


def grid_index_text():
    return ast.unparse(
        next(
            node
            for node in _nodes("_system.py")
            if isinstance(node, ast.FunctionDef) and node.name == "update_spatial_grid"
        )
    )


def selection_order():
    """`Minion.update` looks enemies up first, then selects from that list."""
    text = update_text()
    return (
        "_get_enemies(all_units, all_towers, all_bases)" in text
        and "_find_target_smart(enemies)" in text
        and text.index("_get_enemies") < text.index("_find_target_smart")
    )


def query_radius_source():
    text = get_enemies_text()
    return (
        "query_enemies_in_range(self.x, self.y, radius, self.team)" in text
        and "radius = self.range + 30" in text
    )


def grid_indexes_boss():
    """`Game.update` hands the live boss to `update_spatial_grid` as a hero."""
    text = game_update_text()
    return (
        "spatial_heroes = spatial_heroes + [self.active_boss]" in text
        and "update_spatial_grid(self.minions, spatial_heroes)" in text
    )


def grid_inserts_heroes():
    text = grid_index_text()
    return "for m in minions" in text and "for h in heroes" in text and "_grid.insert(h)" in text


def minion_groups_exclude_boss():
    """The lane/minion groups test `isinstance(e, Minion)`; Boss is not one."""
    return smart_text().count("isinstance(e, Minion)") == 3


def siege_group_uses_max_hp():
    return "hasattr(e, 'max_hp') and e.max_hp >= 1500" in smart_text()


def resolve(env, minion_cls, querier, red_unit, boss, tower):
    """Run the real lookup + selection over a source-shaped world."""
    minions = [querier, red_unit]
    heroes = [] if boss is None else [boss]
    env["update_spatial_grid"](minions, heroes)
    towers = [] if tower is None else [tower]
    enemies = minion_cls._get_enemies(querier, minions + heroes, towers, [])
    return minion_cls._find_target_smart(querier, enemies)


def tag_of(winner, boss, red_unit, tower):
    if winner is boss:
        return "boss"
    if winner is red_unit:
        return "unit"
    if winner is tower:
        return "tower"
    return "none"


def targeting_cases(boss_cls, minion_cls, env, lane_path):
    from bosses.boss_data import get_all_boss_types

    attack_range, minion_hp = minion_stats()
    tower_hp, _tower_range = tower_stats()
    cases = []
    for kind in sorted(get_all_boss_types()):
        for label, ai_level, boss_expr, unit_expr, tower_expr, boss_hp in SCENARIOS:
            boss_distance = boss_expr(attack_range)
            unit_distance = unit_expr(attack_range)
            querier = make_minion(
                minion_cls, QUERIER[0], QUERIER[1], "blue", attack_range, minion_hp, ai_level
            )
            red_unit = make_minion(
                minion_cls,
                QUERIER[0] + unit_distance,
                QUERIER[1],
                "red",
                attack_range,
                minion_hp,
            )
            boss = boss_cls(kind, lane_path)
            boss.x = QUERIER[0] + boss_distance
            boss.y = QUERIER[1]
            if boss_hp is not None:
                boss.hp = boss_hp
            tower = None
            if tower_expr is not None:
                tower = make_tower(
                    QUERIER[0] + tower_expr(attack_range), QUERIER[1], "red", float(tower_hp)
                )
            winner = resolve(env, minion_cls, querier, red_unit, boss, tower)
            without = resolve(env, minion_cls, querier, red_unit, None, tower)
            tag = tag_of(winner, boss, red_unit, tower)
            tag_without_boss = tag_of(without, boss, red_unit, tower)
            assert tag == EXPECTED[label], "%s source targeting drifted" % label
            assert tag_without_boss != "boss", "boss omission case must not pick the boss"
            cases.append(
                {
                    "boss_type": kind,
                    "label": label,
                    "ai_level": ai_level,
                    "range": attack_range,
                    "grid_radius": attack_range + 30.0,
                    "unit_distance": unit_distance,
                    "boss_distance": boss_distance,
                    "tower_distance": None if tower is None else tower_expr(attack_range),
                    "boss_hp": boss_hp if boss_hp is None else float(boss_hp),
                    "unit_hp": minion_hp,
                    "expected": tag,
                    "expected_without_boss": tag_without_boss,
                }
            )
    return cases


def source_fixture():
    from boss_core_source_oracle import boss_class as core_boss_class
    from boss_core_source_oracle import namespace as core_namespace
    from check_source_contract import source_lanes

    env = core_namespace()
    boss_cls = core_boss_class(env)
    grid_env = grid_namespace()
    minion_cls, env = minion_class(grid_env)
    attack_range, minion_hp = minion_stats()
    tower_hp, tower_range = tower_stats()
    return {
        "source": {
            "minion_range": attack_range,
            "minion_hp": minion_hp,
            "tower_max_hp": float(tower_hp),
            "tower_range": tower_range,
            "grid_cell_size": grid_cell_size(),
            "grid_radius": attack_range + 30.0,
            "query_radius_source": query_radius_source(),
            "grid_indexes_boss": grid_indexes_boss(),
            "grid_inserts_heroes": grid_inserts_heroes(),
            "selection_order": selection_order(),
            "minion_groups_exclude_boss": minion_groups_exclude_boss(),
            "siege_group_uses_max_hp": siege_group_uses_max_hp(),
        },
        "cases": targeting_cases(boss_cls, minion_cls, env, source_lanes()["mid"]),
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s (%d cases)" % (FIXTURE, len(actual["cases"])))
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Boss minion targeting source drift"
        )
        print(
            "PASS: Boss minion targeting — %d cases across %d boss types"
            % (len(actual["cases"]), len({row["boss_type"] for row in actual["cases"]}))
        )


if __name__ == "__main__":
    main()
