"""Source-AST oracle for generic Boss ability and level-1 smart AI."""
import ast
import json
import sys
from pathlib import Path

from boss_core_source_oracle import ROOT, _module, namespace

FIXTURE = Path(__file__).parent / "fixtures/boss_level_one_ai_source.json"
SMART = {
    "_smart_ai_gornak", "_cast_q_mana_break", "_cast_w_blink",
    "_cast_e_counterspell", "_cast_r_mana_void",
    "_smart_ai_morgath", "_cast_q_spark_wraith", "_cast_w_flux",
    "_cast_e_magnetic_field", "_cast_r_tempest_double",
    "_smart_ai_drakar", "_cast_q_battle_hunger", "_cast_w_counter_helix",
    "_cast_e_berserkers_call", "_cast_r_culling_blade",
    "_smart_ai_abaddon", "_cast_q_mist_coil", "_cast_w_aphotic_shield",
    "_cast_e_darkness_gale", "_cast_r_death_sever",
    "_get_boss_stats", "_use_ability", "_use_heal_ability", "_shake_screen",
    "__init__", "speed", "ability_damage",
}


def source_boss_class(env):
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Boss")
    body = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in SMART]
    assert len(body) == 29, "Re-audit level-1 smart Boss methods"
    cls = ast.ClassDef(name="SmartBoss", bases=[ast.Name(id="BossBase", ctx=ast.Load())],
                       keywords=[], body=body, decorator_list=[])
    exec(_module(cls), env)  # noqa: S102 - original source methods
    return env["SmartBoss"]


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
        if self.hp <= 0:
            self.alive = False

    def apply_slow(self, amount, duration):
        self.slow_amount, self.slow_timer = amount, duration


def snapshot(boss, targets):
    return {
        "skill": getattr(boss, "active_skill", None),
        "timers": [getattr(boss, key, 0) for key in ("q_timer", "w_timer", "e_timer", "r_timer")],
        "active_timer": getattr(boss, "active_skill_timer", 0),
        "hp": boss.hp,
        "damage": boss.damage,
        "position": [boss.x, boss.y],
        "flux_timer": getattr(boss, "flux_active_timer", 0),
        "clones_timer": getattr(boss, "clones_active_timer", 0),
        "rage_timer": getattr(boss, "rage_timer", 0),
        "defense_timer": getattr(boss, "defense_timer", 0),
        "targets": [{"hits": t.hits, "attack_timer": t.attack_timer,
                     "slow": [t.slow_amount, t.slow_timer], "hp": t.hp} for t in targets],
    }


def run_case(cls, kind, mode):
    boss = cls(kind, [(0, 0)])
    boss.x = boss.y = 0.0
    distance = 50.0
    targets = [Target(distance, 0)]
    if mode == "low":
        boss.hp = int(boss.max_hp * 0.25)
    elif mode == "cluster":
        targets += [Target(60, 0), Target(70, 0)]
    elif mode == "far":
        distance = 130.0
        targets[0].x = distance
    elif mode == "execute":
        targets[0].hp = int(targets[0].max_hp * 0.2)
    elif mode == "mid_hp":
        boss.hp = int(boss.max_hp * 0.5)
    elif mode == "q_only":
        boss.q_timer = 0
        boss.w_timer = boss.e_timer = boss.r_timer = 2
        boss.active_skill = None
        boss.active_skill_timer = 0
        boss.flux_target = None
        boss.flux_active_timer = 0
        boss.clones_active_timer = 0
        boss.clones_positions = []
    boss.target = targets[0]
    getattr(boss, "_smart_ai_" + kind)(targets, distance)
    return snapshot(boss, targets)


def source_fixture():
    env = namespace()
    cls = source_boss_class(env)
    cases = {}
    for kind, modes in {
        "gornak": ("normal", "low", "cluster", "far"),
        "morgath": ("normal", "low", "cluster", "q_only"),
        "drakar": ("cluster", "low", "execute", "mid_hp"),
        "abaddon": ("normal", "low", "cluster", "far"),
    }.items():
        for mode in modes:
            cases[kind + ":" + mode] = run_case(cls, kind, mode)

    generic = cls("krobellus", [(0, 0)])
    generic.x = generic.y = 0.0
    inside, outside = Target(50, 0), Target(generic.ability_range + 1, 0)
    generic._use_ability([inside, outside])
    generic_row = snapshot(generic, [inside, outside])
    generic_row["ability"] = [generic.ability_timer, generic.ability_active,
                              generic.ability_active_timer]

    healer = cls("abaddon", [(0, 0)])
    healer.hp = int(healer.max_hp * 0.2)
    healer._use_heal_ability()
    heal = {"hp": healer.hp, "timer": healer.ability2_timer}
    return {"cases": cases, "generic": generic_row, "heal": heal}


def main():
    data = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("wrote", FIXTURE)
        return
    assert data == json.loads(FIXTURE.read_text(encoding="utf-8")), "Boss level-1 AI drift"
    print("PASS: source generic Boss ability and level-1 smart AI")


if __name__ == "__main__":
    main()
