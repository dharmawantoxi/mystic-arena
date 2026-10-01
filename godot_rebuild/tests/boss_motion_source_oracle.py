"""Source AST oracle for Boss lane motion and basic attack/cleave.

Only the original Boss methods are executed: _face, _advance_waypoint,
_lane_target, _move_forward and update. The update test supplies source-shaped
entities and disables the later smart-ability dispatch with a no-op method;
that keeps this fixture on the movement/attack sub-layer.
"""
import ast
import json
import math
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/boss_motion_source.json"


class Target:
    def __init__(self, x, y, team=0, hp=1000):
        self.x = float(x)
        self.y = float(y)
        self.team = team
        self.alive = True
        self.hp = hp
        self.hits = []

    def take_damage(self, damage, *args, **kwargs):
        self.hits.append(int(damage))
        self.hp -= int(damage)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False


def source_class():
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    wanted = {"_face", "_advance_waypoint", "_lane_target", "_move_forward", "update"}
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
    }


def main():
    actual = source_fixture()
    if "--write" in __import__("sys").argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s" % FIXTURE)
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "Boss motion source drift"
        print("PASS: Boss motion — waypoint budget, facing lock, chase and cleave")


if __name__ == "__main__":
    main()
