"""Read-only AST oracle for the source hero-before-boss match tick phase.

The authoritative Game.update loop and its speed-multiplier path both update
living heroes before the active Boss. A hero can therefore wound/kill the boss
or change its position before Boss.update selects a target and acts. The native
prototype had the boss phase before `_step_hero_act`, reversing those outcomes.

The 4 cases per boss model the source phase order against the source Boss
alive/target/attack gates; the native suite replays each case through the real
HeroState and BossState match helpers. No Python source is modified.
"""
import ast
import json
from pathlib import Path

from boss_motion_source_oracle import source_boss_types

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/boss_phase_order_source.json"
BOSS_RANGE = 80.0

SCENARIOS = (
    {
        "label": "hero_lethal_hit_precedes_boss",
        "hero_action": "lethal_hit",
        "hero_start_dx": 0.0,
        "hero_end_dx": 0.0,
        "hero_speed": 0.0,
        "hero_damage": 100000,
        "hero_attack_timer": 0,
        "boss_hp_mode": "one",
    },
    {
        "label": "hero_wound_precedes_boss_attack",
        "hero_action": "nonlethal_hit",
        "hero_start_dx": 0.0,
        "hero_end_dx": 0.0,
        "hero_speed": 0.0,
        "hero_damage": 100,
        "hero_attack_timer": 0,
        "boss_hp_mode": "full",
    },
    {
        "label": "hero_enters_attack_range_before_boss",
        "hero_action": "move_in",
        "hero_start_dx": BOSS_RANGE + 250.0,
        "hero_end_dx": BOSS_RANGE - 20.0,
        "hero_speed": 400.0,
        "hero_damage": 0,
        "hero_attack_timer": 1,
        "boss_hp_mode": "full",
    },
    {
        "label": "hero_exits_target_radius_before_boss",
        "hero_action": "move_out",
        "hero_start_dx": BOSS_RANGE - 20.0,
        "hero_end_dx": BOSS_RANGE + 220.0,
        "hero_speed": 400.0,
        "hero_damage": 0,
        "hero_attack_timer": 1,
        "boss_hp_mode": "full",
    },
)


def _method(source_file: str, class_name: str, method_name: str) -> ast.FunctionDef:
    tree = ast.parse((ROOT / source_file).read_text(encoding="utf-8"))
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def _calls_method(node: ast.AST, receiver: str, name: str) -> bool:
    return any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == name
        and ast.unparse(call.func.value) == receiver
        for call in ast.walk(node)
    )


def _phase_order(method: ast.FunctionDef) -> list[str]:
    hero_loop = next(
        node for node in ast.walk(method)
        if isinstance(node, ast.For)
        and ast.unparse(node.iter) == "all_heroes"
        and isinstance(node.target, ast.Name)
        and _calls_method(node, node.target.id, "update")
    )
    boss_guard = next(
        node for node in ast.walk(method)
        if isinstance(node, ast.If)
        and _calls_method(node, "self.active_boss", "update")
    )
    phases = [(hero_loop.lineno, "heroes"), (boss_guard.lineno, "boss")]
    phases.sort()
    return [phase for _line, phase in phases]


def _has_source_boss_guards(boss_update: ast.FunctionDef) -> tuple[bool, bool, bool]:
    dead_guard = any(
        isinstance(node, ast.If)
        and ast.unparse(node.test) == "not self.alive"
        and any(isinstance(child, ast.Return) for child in node.body)
        for node in boss_update.body[:2]
    )
    target_radius = any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "best_dist" for target in node.targets)
        and ast.unparse(node.value) == "self.range + 100"
        for node in ast.walk(boss_update)
    )
    target_and_attack_edges = {
        ast.unparse(node.test)
        for node in ast.walk(boss_update)
        if isinstance(node, ast.If)
    }
    strict_target_edge = "dist < best_dist" in target_and_attack_edges
    inclusive_attack_edge = "dist <= self.range" in target_and_attack_edges
    return dead_guard, target_radius and strict_target_edge, inclusive_attack_edge


def _simulate_source_case(scenario: dict, hero_before_boss: bool) -> dict:
    boss_hp = 1.0 if scenario["boss_hp_mode"] == "one" else 1000.0
    hero_x = float(scenario["hero_start_dx"])
    boss_alive = True
    target = "none"
    boss_action = "not_ticked"
    attacks = 0
    phases = ["heroes", "boss"] if hero_before_boss else ["boss", "heroes"]

    for phase in phases:
        if phase == "heroes":
            if scenario["hero_action"] in ("lethal_hit", "nonlethal_hit"):
                boss_hp -= float(scenario["hero_damage"])
                boss_alive = boss_hp > 0.0
            elif scenario["hero_action"] in ("move_in", "move_out"):
                hero_x = float(scenario["hero_end_dx"])
        elif not boss_alive:
            boss_action = "skip_dead"
        else:
            distance = abs(hero_x)
            if distance < BOSS_RANGE + 100.0:
                target = "hero"
                if distance <= BOSS_RANGE:
                    boss_action = "attack"
                    attacks += 1
                else:
                    boss_action = "chase"
            else:
                boss_action = "no_target"

    return {
        **scenario,
        "boss_range": BOSS_RANGE,
        "expected_boss_alive": boss_alive,
        "expected_boss_action": boss_action,
        "expected_boss_attacks": attacks,
        "expected_target": target,
        "expected_hero_dx_after_update": hero_x,
    }


def source_fixture() -> dict:
    game_update = _method("_core.py", "Game", "update")
    gameplay_update = _method("_core.py", "Game", "_update_gameplay")
    boss_update = _method("bosses/base_boss.py", "Boss", "update")
    game_order = _phase_order(game_update)
    gameplay_order = _phase_order(gameplay_update)
    dead_guard, strict_target_edge, inclusive_attack_edge = _has_source_boss_guards(boss_update)
    source = {
        "game_update_order": game_order,
        "speed_multiplier_update_order": gameplay_order,
        "boss_update_skips_dead": dead_guard,
        "boss_target_radius_add": 100.0 if strict_target_edge else -1.0,
        "boss_target_radius_is_strict": strict_target_edge,
        "boss_attack_range_is_inclusive": inclusive_attack_edge,
    }
    assert game_order == ["heroes", "boss"], "Game.update phase order changed; re-audit boss tick oracle"
    assert gameplay_order == ["heroes", "boss"], "Game._update_gameplay order changed; re-audit boss tick oracle"
    assert dead_guard and strict_target_edge and inclusive_attack_edge, "Boss.update gates changed; re-audit cases"

    types = sorted(source_boss_types())
    assert len(types) == 216, f"Expected all source boss types, found {len(types)}"
    cases = [
        {"boss_type": boss_type, **_simulate_source_case(scenario, True)}
        for boss_type in types
        for scenario in SCENARIOS
    ]
    assert len(cases) == 864 and all(
        sum(case["boss_type"] == boss_type for case in cases) == 4 for boss_type in types
    )
    return {"source": source, "cases": cases}


def main() -> None:
    fixture = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(fixture['cases'])} phase-order cases across 216 boss types")


if __name__ == "__main__":
    main()
