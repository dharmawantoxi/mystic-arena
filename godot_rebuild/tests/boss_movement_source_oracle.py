"""Source-executed oracle for Boss movement, basic attack and cleave."""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from boss_core_source_oracle import ROOT, _module, namespace

FIXTURE = Path(__file__).parent / "fixtures/boss_movement_source.json"


def source_boss_class(env):
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Boss")
    wanted = {"__init__", "speed", "ability_damage", "update", "_face", "_lane_target",
              "_advance_waypoint", "_move_forward", "_get_boss_stats"}
    body = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    assert len(body) == 11, "Re-audit Boss movement methods"
    cls = ast.ClassDef(name="MovementBoss", bases=[ast.Name(id="BossBase", ctx=ast.Load())],
                       keywords=[], body=body, decorator_list=[])
    exec(_module(cls), env)  # noqa: S102 - original Boss AST
    return env["MovementBoss"]


class Target:
    def __init__(self, x, y, name):
        self.x, self.y, self.name = float(x), float(y), name
        self.team, self.alive = "blue", True
        self.hits = []

    def take_damage(self, damage, team, *args, **kwargs):
        self.hits.append({"damage": int(damage), "team": team,
                          "school": kwargs.get("school", "neutral")})


def snapshot(boss):
    return {"position": [boss.x, boss.y], "waypoint": boss.waypoint_index,
            "direction": boss.direction, "timer": boss.timer,
            "attack_seq": getattr(boss, "_basic_attack_seq", 0),
            "lock": boss._attack_lock_timer, "kite": boss._kite_mode}


def ready(boss):
    boss.entrance_timer = 0
    boss.ability_timer = 999
    boss.ability2_timer = 999
    boss.boss_type = "oracle_plain"
    return boss


def source_fixture():
    env = namespace()
    boss_cls = source_boss_class(env)
    lane = [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)]

    walker = ready(boss_cls("gornak", lane))
    walk = []
    for _ in range(4):
        walker.update([], [], [])
        walk.append(snapshot(walker))

    chaser = ready(boss_cls("gornak", lane))
    quarry = Target(chaser.x - chaser.range - 40, chaser.y, "quarry")
    chaser.update([quarry], [], [])
    chase = snapshot(chaser)

    attacker = ready(boss_cls("gornak", lane))
    main = Target(attacker.x - 10, attacker.y, "main")
    splash = Target(attacker.x - 20, attacker.y, "splash")
    far = Target(attacker.x - 100, attacker.y, "far")
    attacker.update([main, splash, far], [], [])
    attack = {"boss": snapshot(attacker), "main": main.hits,
              "splash": splash.hits, "far": far.hits}

    slowed = ready(boss_cls("gornak", lane))
    slowed.atk_slow_amount, slowed.atk_slow_timer = 0.25, 10
    slow_target = Target(slowed.x - 10, slowed.y, "slow")
    slowed.update([slow_target], [], [])
    attack_slow_timer = slowed.timer

    kiter = boss_cls("morgath", lane)
    kiter.entrance_timer, kiter.ability_timer, kiter.ability2_timer = 0, 999, 999
    kite_target = Target(kiter.x - 200, kiter.y, "kite")
    kiter.update([kite_target], [], [])
    kite = snapshot(kiter)

    tie = ready(boss_cls("gornak", lane))
    first = Target(tie.x - 20, tie.y, "first")
    second = Target(tie.x + 20, tie.y, "second")
    tie.update([first, second], [], [])
    tied = {"first": first.hits, "second": second.hits}

    return {"walk": walk, "chase": chase, "attack": attack,
            "attack_slow_timer": attack_slow_timer, "kite": kite, "tie": tied}


def main():
    data = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("wrote", FIXTURE)
        return
    assert data == json.loads(FIXTURE.read_text(encoding="utf-8")), "Boss movement source drift"
    print("PASS: source Boss movement, attack cooldown and cleave")


if __name__ == "__main__":
    main()
