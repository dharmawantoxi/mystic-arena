"""Execute the real Hero target selection used by boss-hero auto-cast AI.

Only skill readiness/casting are stubbed; `_get_all_enemies` and
`_try_auto_cast` come unchanged from the read-only `_entity.py` source.
"""
import ast
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_entity.py"
FIXTURE = Path(__file__).parent / "fixtures/boss_hero_ai_source.json"

CASES = [
    {
        "label": "nearest_living_enemy",
        "hero": {"id": 1, "team": "red", "x": 500.0, "y": 380.0,
                 "skill_range": 100.0, "initial_target_id": None},
        "units": [
            {"id": 11, "team": "blue", "alive": True, "x": 560.0, "y": 380.0},
            {"id": 12, "team": "blue", "alive": True, "x": 520.0, "y": 408.0},
            {"id": 13, "team": "red", "alive": True, "x": 501.0, "y": 380.0},
            {"id": 14, "team": "blue", "alive": False, "x": 502.0, "y": 380.0},
        ],
        "active_boss": None,
        "towers": [],
        "bases": [],
    },
    {
        "label": "stable_tie_keeps_first_unit",
        "hero": {"id": 2, "team": "red", "x": 0.0, "y": 0.0,
                 "skill_range": 100.0, "initial_target_id": None},
        "units": [
            {"id": 21, "team": "blue", "alive": True, "x": 25.0, "y": 0.0},
            {"id": 22, "team": "blue", "alive": True, "x": 0.0, "y": 25.0},
        ],
        "active_boss": {"id": 23, "team": "blue", "alive": True, "x": -25.0, "y": 0.0},
        "towers": [],
        "bases": [],
    },
    {
        "label": "nearest_base_beats_unit_boss_and_tower",
        "hero": {"id": 3, "team": "red", "x": 0.0, "y": 0.0,
                 "skill_range": 100.0, "initial_target_id": None},
        "units": [
            {"id": 31, "team": "blue", "alive": True, "x": 75.0, "y": 0.0},
        ],
        "active_boss": {"id": 32, "team": "blue", "alive": True, "x": 10.0, "y": 0.0},
        "towers": [
            {"id": 33, "team": "blue", "alive": True, "x": 20.0, "y": 0.0},
        ],
        "bases": [
            {"id": 34, "team": "blue", "alive": True, "x": 5.0, "y": 0.0},
        ],
    },
    {
        "label": "inclusive_skill_range_boundary",
        "hero": {"id": 4, "team": "red", "x": 0.0, "y": 0.0,
                 "skill_range": 100.0, "initial_target_id": None},
        "units": [
            {"id": 41, "team": "blue", "alive": True, "x": 100.0, "y": 0.0},
        ],
        "active_boss": None,
        "towers": [],
        "bases": [],
    },
    {
        "label": "no_nearby_enemy_preserves_existing_target",
        "hero": {"id": 5, "team": "red", "x": 0.0, "y": 0.0,
                 "skill_range": 100.0, "initial_target_id": 99},
        "units": [
            {"id": 51, "team": "red", "alive": True, "x": 1.0, "y": 0.0},
            {"id": 52, "team": "blue", "alive": False, "x": 2.0, "y": 0.0},
            {"id": 53, "team": "blue", "alive": True, "x": 101.0, "y": 0.0},
        ],
        "active_boss": None,
        "towers": [],
        "bases": [],
    },
    {
        "label": "no_skill_range_target_allows_lane_assignment",
        "hero": {"id": 6, "team": "red", "x": 500.0, "y": 380.0,
                 "skill_range": 100.0, "initial_target_id": None},
        "units": [
            {"id": 61, "team": "blue", "alive": True, "lane": 1,
             "x": 1000.0, "y": 380.0},
        ],
        "active_boss": None,
        "towers": [
            {"id": 62, "team": "blue", "alive": True, "x": 1100.0, "y": 380.0},
        ],
        "bases": [],
    },
]


def source_class():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    hero = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Hero"
    )
    wanted = {"_get_all_enemies", "_try_auto_cast"}
    methods = [
        node for node in hero.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    assert {node.name for node in methods} == wanted, "Re-audit Hero auto-cast target source"
    cls = ast.ClassDef(
        name="SourceBossHeroAutoCast",
        bases=[],
        keywords=[],
        body=methods,
        decorator_list=[],
    )
    env = {"math": math}
    exec(
        compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                "<source boss hero auto-cast>", "exec"),
        env,
    )
    return env["SourceBossHeroAutoCast"]


class _Target:
    def __init__(self, row):
        self.id = int(row["id"])
        self.team = row["team"]
        self.alive = bool(row["alive"])
        self.x = float(row["x"])
        self.y = float(row["y"])


def run_case(cls, row):
    hero_spec = row["hero"]
    hero = cls()
    hero.id = int(hero_spec["id"])
    hero.team = hero_spec["team"]
    hero.x = float(hero_spec["x"])
    hero.y = float(hero_spec["y"])
    hero.skill_range = float(hero_spec["skill_range"])
    hero.hp = 100.0
    hero.max_hp = 100.0
    initial_target_id = hero_spec["initial_target_id"]
    hero.target = None if initial_target_id is None else _Target({
        "id": initial_target_id,
        "team": "blue",
        "alive": True,
        "x": 0.0,
        "y": 0.0,
    })
    units = [_Target(target) for target in row["units"]]
    active_boss = row["active_boss"]
    if active_boss is not None:
        units.append(_Target(active_boss))
    towers = [_Target(target) for target in row["towers"]]
    bases = [_Target(target) for target in row["bases"]]
    hero.is_skill_ready = lambda _skill: False
    hero.cast_skill = lambda *_args: (_ for _ in ()).throw(
        AssertionError("all skill cooldowns are held in target-only oracle cases")
    )
    hero._try_auto_cast(units, towers, bases)
    return {
        "label": row["label"],
        "input": row,
        "target_id": None if hero.target is None else hero.target.id,
    }


def source_fixture():
    cls = source_class()
    cases = []
    for original in CASES:
        row = dict(original)
        row["expects_lane_assignment"] = row["label"] == "no_skill_range_target_allows_lane_assignment"
        cases.append(run_case(cls, row))
    return {"boss_type": "gornak", "cases": cases}


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %d Boss Hero auto-cast target cases" % len(actual["cases"]))
    else:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        assert actual == expected, "Boss Hero auto-cast source drift"
        print("PASS: Boss Hero auto-cast nearest-target handoff (6 cases)")


if __name__ == "__main__":
    main()
