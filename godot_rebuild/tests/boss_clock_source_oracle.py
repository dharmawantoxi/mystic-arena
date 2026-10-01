"""AST oracle for the source Boss entrance/enrage gameplay clock.

The fixture executes the original Boss.update method with an empty battlefield
and stubs only movement, tower-debuff ticking and presentation helpers. It
covers the entrance gate, mini/true enrage thresholds, one-shot transition and
the source even-tick cooldown acceleration.
"""
import ast
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIXTURE = Path(__file__).parent / "fixtures/boss_clock_source.json"


class SourceBossClock:
    pass


def source_class():
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    speed_nodes = [
        node for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name == "speed"
    ]
    update = next(node for node in original.body if isinstance(node, ast.FunctionDef) and node.name == "update")
    assert len(speed_nodes) == 2, "Re-audit Boss.speed before trusting this oracle"
    cls = ast.ClassDef(
        name="SourceBossClock",
        bases=[],
        keywords=[],
        body=speed_nodes + [update],
        decorator_list=[],
    )
    env = {"math": math}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "<source boss clock>", "exec"), env)
    result = env["SourceBossClock"]
    result._tick_tower_debuffs = lambda self: None
    result._move_forward = lambda self: None
    result._shake_screen = lambda self, _intensity: None
    result._use_heal_ability = lambda self: None
    return result


def make_boss(cls, boss_class="mini"):
    boss = cls()
    boss.boss_type = "clock_probe"
    boss.boss_class = boss_class
    boss.alive = True
    boss.x = 0.0
    boss.y = 0.0
    boss._prev_x = 0.0
    boss._prev_y = 0.0
    boss.anim_time = 0
    boss.pulse = 0.0
    boss.is_moving = False
    boss._moving_cached = False
    boss._attack_lock_timer = 0
    boss._attack_facing = None
    boss.stun_timer = 0
    boss.hurt_flash_timer = 2
    boss.entrance_timer = 0
    boss.max_hp = 10000
    boss.hp = 10000
    boss.enrage_triggered = False
    boss.is_enraged = False
    boss.enrage_pulse = 0.0
    boss._speed_value = 10.0
    boss.slow_amount = 0.0
    boss.slow_timer = 0
    boss.speed = 10.0
    boss.damage = 100
    boss.attack_cooldown = 30
    boss.timer = 5
    boss.ability_timer = 7
    boss.ability2_timer = 9
    boss.ability_active = True
    boss.ability_active_timer = 4
    boss.target = None
    boss.entrance_text = ""
    boss.radius = 30
    boss.range = 50
    boss._move_forward = lambda: None
    return boss


def row(boss):
    return {
        "anim_time": int(boss.anim_time),
        "pulse": float(boss.pulse),
        "entrance_timer": int(boss.entrance_timer),
        "hurt_flash_timer": int(boss.hurt_flash_timer),
        "timer": int(boss.timer),
        "ability_timer": int(boss.ability_timer),
        "ability2_timer": int(boss.ability2_timer),
        "ability_active": bool(boss.ability_active),
        "ability_active_timer": int(boss.ability_active_timer),
        "speed": float(boss.speed),
        "damage": int(boss.damage),
        "attack_cooldown": int(boss.attack_cooldown),
        "enrage_triggered": bool(boss.enrage_triggered),
        "is_enraged": bool(boss.is_enraged),
        "enrage_pulse": float(boss.enrage_pulse),
    }


def run_case(cls, label, boss_class, hp, entrance_timer, anim_time=0, slow_amount=0.0):
    boss = make_boss(cls, boss_class)
    boss.hp = hp
    boss.entrance_timer = entrance_timer
    boss.anim_time = anim_time
    boss.slow_amount = slow_amount
    boss.slow_timer = 1 if slow_amount > 0.0 else 0
    boss.update([], [], [])
    return {"label": label, "result": row(boss)}


def source_fixture():
    cls = source_class()
    cases = [
        run_case(cls, "mini_entrance", "mini", 10000, 2),
        run_case(cls, "mini_entrance_release", "mini", 10000, 1),
        run_case(cls, "mini_enrage_odd", "mini", 4000, 0, 0),
        run_case(cls, "mini_enrage_slow", "mini", 4000, 0, 0, 0.50),
        run_case(cls, "true_enrage_even", "true", 5000, 0, 1),
    ]
    boss = make_boss(cls, "mini")
    boss.hp = 4000
    boss.update([], [], [])
    boss.update([], [], [])
    cases.append({"label": "mini_enrage_once", "result": row(boss)})
    return {"cases": cases}


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %d source clock cases" % len(actual["cases"]))
    else:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        assert actual == expected, "Boss clock source drift"
        print("PASS: Boss clock — entrance gate, enrage thresholds and cooldown clock")


if __name__ == "__main__":
    main()
