"""Source-AST oracle for level-2 Boss smart AI."""
import ast
import json
import sys
from pathlib import Path

from boss_core_source_oracle import ROOT, _module, namespace

FIXTURE = Path(__file__).parent / "fixtures/boss_level_two_ai_source.json"
KINDS = ("razak", "khalros", "gorath", "alchemist")
METHODS = {"__init__", "speed", "ability_damage", "_get_boss_stats", "_shake_screen"}
for kind in KINDS:
    METHODS.add("_smart_ai_" + kind)
METHODS.update({
    "_razak_q", "_razak_w", "_razak_e", "_razak_r",
    "_khalros_q", "_khalros_w", "_khalros_e", "_khalros_r",
    "_gorath_q", "_gorath_w", "_gorath_e", "_gorath_r",
    "_cast_q_acid_spray", "_cast_w_unstable_concoction",
    "_cast_e_chemical_rage", "_cast_r_greevils_greed",
})


def source_boss_class(env):
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Boss")
    body = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in METHODS]
    assert len(body) == 27, "Re-audit level-2 smart Boss methods"
    cls = ast.ClassDef(name="LevelTwoBoss", bases=[ast.Name(id="BossBase", ctx=ast.Load())],
                       keywords=[], body=body, decorator_list=[])
    exec(_module(cls), env)  # noqa: S102 - original source methods
    return env["LevelTwoBoss"]


class Target:
    serial = 0

    def __init__(self, x, y, hp=2000):
        Target.serial += 1
        self.id = Target.serial
        self.x, self.y = float(x), float(y)
        self.team, self.alive = "blue", True
        self.hp, self.max_hp = hp, hp
        self.attack_timer = 0
        self.slow_amount, self.slow_timer = 0.0, 0
        self.hits = []

    def take_damage(self, damage, team, *args, **kwargs):
        self.hits.append(int(damage))
        self.hp = max(0, self.hp - int(damage))
        self.alive = self.hp > 0

    def apply_slow(self, amount, duration):
        self.slow_amount, self.slow_timer = amount, duration


def run_case(cls, kind, mode):
    boss = cls(kind, [(0, 0)])
    boss.x = boss.y = 0.0
    distance = 50.0
    targets = [Target(distance, 0)]
    if mode == "cluster":
        targets += [Target(60, 0), Target(70, 0)]
    elif mode == "far":
        distance = 130.0
        targets[0].x = distance
    elif mode == "low":
        boss.hp = int(boss.max_hp * 0.5)
    elif mode == "critical_cluster":
        boss.hp = int(boss.max_hp * 0.25)
        targets += [Target(60, 0, 200), Target(70, 0, 200)]
    elif mode == "execute":
        targets[0].hp = int(targets[0].max_hp * 0.2)
    elif mode == "q_only":
        boss.q_timer = 0
        boss.w_timer = boss.e_timer = boss.r_timer = 2
        boss.active_skill = None
        boss.active_skill_timer = 0
    boss.target = targets[0]
    getattr(boss, "_smart_ai_" + kind)(targets, distance)
    return {
        "skill": getattr(boss, "active_skill", None),
        "timers": [getattr(boss, key, 0) for key in ("q_timer", "w_timer", "e_timer", "r_timer")],
        "active_timer": getattr(boss, "active_skill_timer", 0),
        "hp": boss.hp,
        "damage": boss.damage,
        "speed": boss.speed,
        "position": [boss.x, boss.y],
        "rage": [getattr(boss, "rage_active", False), getattr(boss, "rage_timer", 0)],
        "targets": [{"hits": t.hits, "hp": t.hp, "attack_timer": t.attack_timer,
                     "slow": [t.slow_amount, t.slow_timer]} for t in targets],
    }


def source_fixture():
    cls = source_boss_class(namespace())
    plan = {
        "razak": ("cluster", "far", "normal", "q_only"),
        "khalros": ("cluster", "low", "far", "normal"),
        "gorath": ("execute", "low", "cluster", "far"),
        "alchemist": ("critical_cluster", "low", "cluster", "normal"),
    }
    return {"cases": {kind + ":" + mode: run_case(cls, kind, mode)
                      for kind, modes in plan.items() for mode in modes}}


def main():
    data = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("wrote", FIXTURE)
        return
    assert data == json.loads(FIXTURE.read_text(encoding="utf-8")), "Boss level-2 AI drift"
    print("PASS: source level-2 Boss smart AI")


if __name__ == "__main__":
    main()
