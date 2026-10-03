"""Source AST oracle for boss lane motion, ranged kiting and AI range gating.

Only original Boss methods are executed: _face, _advance_waypoint,
_lane_target, _move_forward, _get_boss_stats and update. The motion trace
supplies source-shaped entities and stubs smart abilities; the dispatch trace
records the source's inclusive attack-range gate.
"""
import ast
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIXTURE = Path(__file__).parent / "fixtures/boss_motion_source.json"
RANGED_BOSSES = (
    "ancient_apparition",
    "morgath",
    "razak",
    "varkul",
    "xerathis",
    "nyzrak",
    "syrentha",
    "thalgryn",
    "nyxarath",
    "malzareth",
    "akashari",
    "vorenmarr",
)


class Target:
    def __init__(self, x, y, team=0, hp=1000):
        self.x = float(x)
        self.y = float(y)
        self.team = team
        self.alive = True
        self.hp = hp
        self.hits = []
        self.damage_calls = []

    def take_damage(self, damage, *args, **kwargs):
        self.hits.append(int(damage))
        self.damage_calls.append({"damage": int(damage), "args": args, "kwargs": kwargs})
        self.hp -= int(damage)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False


def smart_ai_boss_types():
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    names = sorted(
        node.name[len("_smart_ai_") :]
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_smart_ai_")
    )
    assert len(names) == 79, "Boss smart-AI roster drifted"
    return tuple(names)


def source_boss_types():
    from bosses.boss_data import get_all_boss_types

    names = tuple(sorted(get_all_boss_types()))
    assert len(names) == 216, "Boss type roster drifted"
    return names


def source_class():
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    wanted = {"_face", "_advance_waypoint", "_lane_target", "_move_forward", "_get_boss_stats", "update"}
    body = [node for node in original.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    assert {node.name for node in body} == wanted, "Boss motion methods drifted"
    cls = ast.ClassDef(name="SourceBossMotion", bases=[], keywords=[], body=body, decorator_list=[])
    env = {"math": math}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "<source boss motion>", "exec"), env)
    result = env["SourceBossMotion"]
    result._tick_tower_debuffs = lambda self: None
    result._eff_attack_cd = lambda self, base_cd: base_cd
    result._use_ability = lambda self, enemies: None
    return result


def base_boss(cls, x=20.0, y=0.0):
    boss = cls()
    boss.boss_type = "unknown"
    boss.boss_class = "mini"
    boss.team = 1
    boss.x = x
    boss.y = y
    boss._prev_x = x
    boss._prev_y = y
    boss.speed = 3.0
    boss.range = 80.0
    boss.damage = 100
    boss.attack_cooldown = 30
    boss.cleave_radius = 80.0
    boss.cleave_ratio = 0.40
    boss.max_hp = 10000
    boss.hp = boss.max_hp
    boss.alive = True
    boss.timer = 0
    boss.ability_timer = 999
    boss.ability2_timer = 999
    boss.ability_active_timer = 0
    boss.ability_active = False
    boss.ability_cooldown_max = 100
    boss.ability_damage = 1
    boss.ability_range = 1
    boss.stun_timer = 0
    boss.hurt_flash_timer = 0
    boss.entrance_timer = 0
    boss.enrage_triggered = False
    boss.is_enraged = False
    boss.enrage_pulse = 0.0
    boss.anim_time = 0
    boss.pulse = 0
    boss.direction = -1
    boss._attack_facing = None
    boss._attack_lock_timer = 0
    boss._kite_mode = "hold"
    boss.lane_path = []
    boss.waypoint_index = -1
    boss.is_moving = False
    boss._moving_cached = False
    boss.target = None
    return boss


def ranged_kiting_cases(cls):
    from bosses.boss_data import get_all_boss_types

    cases = []
    for boss_type in RANGED_BOSSES:
        stats = get_all_boss_types()[boss_type]
        min_distance = float(stats.get("min_distance", 200))
        prefer_distance = float(stats.get("prefer_distance", 280))
        hold_distance = (min_distance + prefer_distance) / 2.0
        scenarios = (
            ("back_entry", "hold", ((min_distance - 1.0, min_distance - 2.0),)),
            (
                "back_hysteresis_exit",
                "back",
                (
                    (min_distance + 6.0, min_distance + 5.0),
                    (hold_distance, hold_distance - 1.0),
                ),
            ),
            ("in_entry", "hold", ((prefer_distance + 10.0, prefer_distance + 5.0),)),
            (
                "in_hysteresis_exit",
                "in",
                (
                    (prefer_distance - 6.0, prefer_distance - 7.0),
                    (hold_distance, hold_distance - 1.0),
                ),
            ),
        )
        for label, initial_mode, inputs in scenarios:
            boss = base_boss(cls, 0.0, 0.0)
            boss.boss_type = boss_type
            boss.speed = 3.0
            boss._kite_mode = initial_mode
            steps = []
            for distance, attack_range in inputs:
                boss.range = attack_range
                target = Target(boss.x + distance, boss.y)
                boss.update([target], [], [])
                steps.append(
                    {
                        "distance": distance,
                        "attack_range": attack_range,
                        "expected": {
                            "x": boss.x,
                            "y": boss.y,
                            "kite_mode": boss._kite_mode,
                            "direction": boss.direction,
                        },
                    }
                )
            cases.append(
                {
                    "boss_type": boss_type,
                    "label": label,
                    "min_distance": min_distance,
                    "prefer_distance": prefer_distance,
                    "speed": 3.0,
                    "kite_mode": initial_mode,
                    "steps": steps,
                }
            )
    return cases


def smart_ai_dispatch_cases(cls):
    from bosses.boss_data import get_all_boss_types

    cases = []
    all_bosses = get_all_boss_types()
    for boss_type in smart_ai_boss_types():
        attack_range = float(all_bosses[boss_type].get("range", 40))
        scenarios = (
            ("attack_range_inclusive", attack_range),
            ("one_pixel_outside_attack_range", attack_range + 1.0),
            ("inside_target_acquisition_only", attack_range + 99.0),
            ("strict_target_acquisition_edge", attack_range + 100.0),
        )
        for label, distance in scenarios:
            boss = base_boss(cls, 0.0, 0.0)
            boss.boss_type = boss_type
            boss.range = attack_range
            boss.timer = 999
            boss._move_forward = lambda: None
            calls = []
            setattr(
                boss,
                "_smart_ai_" + boss_type,
                lambda _enemies, target_distance: calls.append(float(target_distance)),
            )
            target = Target(distance, 0.0)
            boss.update([target], [], [])
            cases.append(
                {
                    "boss_type": boss_type,
                    "label": label,
                    "attack_range": attack_range,
                    "distance": distance,
                    "expected": {
                        "target_selected": boss.target is not None,
                        "smart_ai_call_count": len(calls),
                        "smart_ai_dispatched": bool(calls),
                    },
                }
            )
    return cases


def _damage_call_rows(target, boss):
    rows = []
    for call in target.damage_calls:
        kwargs = call["kwargs"]
        args = call["args"]
        rows.append(
            {
                "damage": call["damage"],
                "from_team": args[0] if args else None,
                "school": kwargs.get("school"),
                "source_is_boss": kwargs.get("source") is boss,
                "source_supplied": "source" in kwargs,
            }
        )
    return rows


def basic_attack_source_cases(cls):
    from bosses.boss_data import get_all_boss_types

    all_bosses = get_all_boss_types()
    smart_types = set(smart_ai_boss_types())
    cases = []
    for boss_type in source_boss_types():
        stats = all_bosses[boss_type]
        attack_range = float(stats.get("range", 40))
        scenarios = (
            ("ready_basic_hit", 10.0, 0, True),
            ("cooldown_blocks_basic_hit", 10.0, 2, False),
            ("outside_attack_range", attack_range + 1.0, 0, False),
            ("strict_target_acquisition_edge", attack_range + 100.0, 0, False),
        )
        for label, distance, initial_timer, include_cleave in scenarios:
            boss = base_boss(cls, 0.0, 0.0)
            boss.boss_type = boss_type
            boss.boss_class = str(stats.get("boss_class", "mini"))
            boss.range = attack_range
            boss.damage = int(stats.get("damage", 100))
            boss.attack_cooldown = int(stats.get("attack_cooldown", 30))
            boss.timer = initial_timer
            boss.ability_timer = 999
            boss.ability2_timer = 999
            boss._move_forward = lambda: None
            if boss_type in smart_types:
                setattr(
                    boss,
                    "_smart_ai_" + boss_type,
                    lambda _enemies, _target_distance: None,
                )
            target = Target(distance, 0.0)
            enemies = [target]
            cleave = Target(20.0, 0.0) if include_cleave else None
            if cleave is not None:
                enemies.append(cleave)
            boss.update(enemies, [], [])
            cases.append(
                {
                    "boss_type": boss_type,
                    "label": label,
                    "attack_range": attack_range,
                    "distance": distance,
                    "initial_timer": initial_timer,
                    "expected": {
                        "target_selected": boss.target is target,
                        "basic_attack_seq": int(getattr(boss, "_basic_attack_seq", 0)),
                        "timer": boss.timer,
                        "target_calls": _damage_call_rows(target, boss),
                        "cleave_calls": _damage_call_rows(cleave, boss) if cleave else [],
                    },
                }
            )
    return cases


def source_fixture():
    cls = source_class()

    forward = base_boss(cls)
    forward.lane_path = [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)]
    forward.waypoint_index = 2
    forward._move_forward()
    forward_first = [forward.x, forward.y, forward.waypoint_index, forward.direction]
    forward._move_forward()
    forward_second = [forward.x, forward.y, forward.waypoint_index, forward.direction]

    facing = base_boss(cls)
    facing._face(1.0, 0.0)
    horizontal = facing.direction
    facing._attack_facing = -1
    facing._attack_lock_timer = 3
    facing._face(1.0, 0.0)
    locked = facing.direction
    facing._attack_lock_timer = 0
    facing._face(0.01, 2.0)
    near_vertical = facing.direction

    target = Target(10, 0, hp=1000)
    near = Target(20, 0, hp=1000)
    attack = base_boss(cls, 0.0, 0.0)
    attack.update([target, near], [], [])
    attack_row = {
        "target_hits": target.hits,
        "near_hits": near.hits,
        "target_hp": target.hp,
        "near_hp": near.hp,
        "timer": attack.timer,
        "basic_attack_seq": int(getattr(attack, "_basic_attack_seq", 0)),
        "direction": attack.direction,
    }

    chase_target = Target(150, 0, hp=1000)
    chase = base_boss(cls, 0.0, 0.0)
    chase.update([chase_target], [], [])
    chase_row = {"x": chase.x, "y": chase.y, "direction": chase.direction}

    return {
        "forward": {"first": forward_first, "second": forward_second},
        "facing": {"horizontal": horizontal, "locked": locked, "near_vertical": near_vertical},
        "attack": attack_row,
        "chase": chase_row,
        "ranged_kiting": ranged_kiting_cases(cls),
        "smart_ai_dispatch": smart_ai_dispatch_cases(cls),
        "basic_attack_source": basic_attack_source_cases(cls),
    }


def main():
    actual = source_fixture()
    if "--write" in __import__("sys").argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s" % FIXTURE)
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "Boss motion source drift"
        print("PASS: Boss motion — waypoint/facing/chase, 48 kiting, 316 smart-AI gates and 864 source-attributed basic hits")


if __name__ == "__main__":
    main()
