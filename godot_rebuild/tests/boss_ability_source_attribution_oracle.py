"""Read-only source oracle for uncredited `source=None` boss ability and skill hits.

Executes the real `Boss._use_ability` and all 79 `_smart_ai_*` skill methods from
`bosses/base_boss.py`, together with the real `_is_physical_hit`,
`resolve_damage_school` and `Hero.take_damage` from `_entity.py` and the real
`HeroItemInventory` (`notify_damage_taken`, `get_armor`, `get_evasion`,
`get_block`, `get_reflect_pct`, `has_true_strike`, `is_veiled`, `clear_on_death`)
from `hero_items.py`.

In `bosses/base_boss.py`:
* Only the primary basic attack in `Boss.update` (`bosses/base_boss.py:707-709`)
  passes `source=self` (`self.target.take_damage(self.damage, self.team,
  school='physical', source=self)`).
* Cleave (`bosses/base_boss.py:724`), generic ability `Boss._use_ability`
  (`bosses/base_boss.py:1079`), and all 176 skill / persistent-tick `take_damage`
  calls across the 79 `_smart_ai_*` recipes (`bosses/base_boss.py:1168-8485`)
  call `target.take_damage(damage, self.team)` with two positional arguments and
  no `source=` keyword (`source=None`).

In `Hero.take_damage` (`_entity.py:4525-4732`) and
`HeroItemInventory.notify_damage_taken` (`hero_items.py:2439-2472`), `source=None`
on an ability/skill hit has four direct gameplay consequences:
1. Attacker blind (`_entity.py:4608-4609`) checks `if source is not None and
   getattr(source, 'blind_timer', 0) > 0:`; a blinded boss's ability/skill hits
   do not miss from `boss.blind_amount`.
2. Thorne's Bristleback (`_entity.py:4684-4706`) still reduces incoming physical
   damage by 30% (`0.70`), but its 25% reflect checks `if ... and source is not
   None and source is not self:` and therefore does not reflect onto the boss.
3. `HeroItemInventory.notify_damage_taken` (`hero_items.py:2445-2472`) still
   resets Leviathan Heart's `last_damage_timer = 300`, but Razor Carapace
   Thornmail reflect checks `if refl > 0 and damage > 0 and source is not None`
   and therefore does not reflect onto the boss.
4. Lethal hits (`_entity.py:4731-4732`) check `if source is not None and source
   is not self: self._killed_by = source` and therefore leave `_killed_by` as
   `None` (`killed_by == -1`).

Before layer 8u, `BossAI._hit` (`godot_rebuild/scripts/match/boss_ai.gd:3699`)
passed `boss.id` instead of `-1` to `world._deliver_hit(...)`.

Four scenarios are recorded for each of the 216 boss types (864 cases total),
each carrying `expected` (source `source=None` / native `source_id=-1`) and
`expected_with_boss_source` (the pre-layer `source=boss` / `boss.id` behavior).
`--write` rewrites the fixture.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_item_source_oracle import (  # noqa: E402
    _core_module,
    inventory_type,
    source_namespace,
)
from boss_ability_source_oracle import (  # noqa: E402
    SOURCE_STATS,
    make_boss,
    source_class as boss_ability_class,
)

FIXTURE = Path(__file__).parent / "fixtures/boss_ability_source_attribution.json"

SCENARIOS = (
    "blind_boss_ability_lands",
    "bristleback_mitigates_without_reflect",
    "razor_carapace_combat_timer_without_reflect",
    "lethal_ability_preserves_uncredited_killed_by",
)


class _DeterministicRandom:
    def random(self):
        return 0.10


def _nodes(source_file):
    return ast.parse((ROOT / source_file).read_text(encoding="utf-8")).body


def _method_node(class_name, method_name, source_file):
    original = next(
        node
        for node in _nodes(source_file)
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def _method_text(class_name, method_name, source_file):
    return ast.unparse(_method_node(class_name, method_name, source_file))


def _boss_take_damage_calls():
    original = next(
        node
        for node in _nodes("bosses/base_boss.py")
        if isinstance(node, ast.ClassDef) and node.name == "Boss"
    )
    calls = []
    for method in original.body:
        if not isinstance(method, ast.FunctionDef):
            continue
        for node in ast.walk(method):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "take_damage"
            ):
                calls.append(
                    (
                        method.name,
                        node.lineno,
                        len(node.args),
                        tuple(sorted(k.arg for k in node.keywords if k.arg)),
                    )
                )
    return calls


def _build_hero_class():
    entity_nodes = _nodes("_entity.py")
    helper_nodes = [
        node
        for node in entity_nodes
        if isinstance(node, ast.FunctionDef)
        and node.name in ("_is_physical_hit", "resolve_damage_school")
    ]
    assert {n.name for n in helper_nodes} == {
        "_is_physical_hit",
        "resolve_damage_school",
    }, "Missing damage-school helpers in _entity.py"
    take_damage_node = _method_node("Hero", "take_damage", "_entity.py")
    env = {
        "_ACTIVE_HERO": [None],
        "credit_hero_damage": lambda *_args, **_kwargs: None,
        "random": _DeterministicRandom(),
        "round": round,
        "int": int,
        "max": max,
        "min": min,
        "getattr": getattr,
        "hasattr": hasattr,
    }
    hero_cls = ast.ClassDef(
        name="SourceHero",
        bases=[],
        keywords=[],
        body=[take_damage_node],
        decorator_list=[],
    )
    module = ast.Module(body=helper_nodes + [hero_cls], type_ignores=[])
    exec(
        compile(ast.fix_missing_locations(module), "<source Hero.take_damage>", "exec"),
        env,
    )
    return env["SourceHero"]


def _run_single(boss_cls, hero_cls, inv_cls, boss_type, scenario, inject_boss_source):
    boss = make_boss(boss_cls, boss_type, 1.0, None)
    boss.alive = True
    boss.blind_timer = 30 if scenario == "blind_boss_ability_lands" else 0
    boss.blind_amount = 1.0 if scenario == "blind_boss_ability_lands" else 0.0
    boss.reflect_hits = []

    def boss_take_damage(dmg, _from_team, *_args, **_kwargs):
        boss.reflect_hits.append(int(dmg))

    boss.take_damage = boss_take_damage
    attributed_hits = []

    def make_hero(x, y, hp, name):
        hero = hero_cls()
        hero.name = name
        hero.role = "Bruiser"
        hero.level = 1
        hero.x = float(x)
        hero.y = float(y)
        hero.radius = 16.0
        hero.team = "blue"
        hero.alive = True
        hero.max_hp = 10000
        hero.hp = int(hp)
        hero.base_hp = 10000
        hero.damage = 41
        hero.base_damage = 41
        hero.range = 70
        hero.speed = 1.0
        hero.is_melee_hero = True
        hero.deaths = 0
        hero._killed_by = None
        hero.attack_timer = 0
        hero._bristleback_active = (
            scenario == "bristleback_mitigates_without_reflect" and name == "target"
        )
        hero.clear_tower_debuffs = lambda: None
        hero.apply_heal_amp = lambda _amount, _duration: None
        inv = inv_cls(hero)
        if (
            scenario == "razor_carapace_combat_timer_without_reflect"
            and name == "target"
        ):
            assert inv.add("razor_carapace")
            assert inv.add("leviathan_heart")
            inv.thorn_timer = 180
            inv.last_damage_timer = 0
        hero.max_hp = 10000
        hero.hp = int(hp)
        hero.items = inv
        orig_take_damage = hero.take_damage

        def wrapped_take_damage(
            dmg, from_team, damage_type="normal", source=None, school=None
        ):
            eff_source = boss if (inject_boss_source and source is None) else source
            if name == "target" and int(dmg) > 0:
                attributed_hits.append(eff_source is boss)
            return orig_take_damage(
                dmg,
                from_team,
                damage_type=damage_type,
                source=eff_source,
                school=school,
            )

        hero.take_damage = wrapped_take_damage
        hero.apply_slow = lambda _amount, _duration: None
        return hero

    start_hp = (
        1 if scenario == "lethal_ability_preserves_uncredited_killed_by" else 10000
    )
    target = make_hero(20.0, 0.0, start_hp, "target")
    ally = make_hero(30.0, 0.0, 10000, "ally")
    boss.target = target
    steps = 2 if boss_type in ("kunkka", "xerathis", "solvarin") else 1
    smart_fn = getattr(boss, f"_smart_ai_{boss_type}", None)
    for _ in range(steps):
        if smart_fn is not None:
            smart_fn([target, ally], 20.0)
        else:
            boss._use_ability([target, ally])
    return {
        "steps": int(steps),
        "skill": getattr(boss, "active_skill", None) or "",
        "target_hp": int(target.hp),
        "target_alive": bool(target.alive),
        "target_deaths": int(target.deaths),
        "damage_taken": int(start_hp - target.hp),
        "boss_hp": int(boss.hp),
        "last_damage_timer": int(target.items.last_damage_timer),
        "killed_by_boss": bool(target._killed_by is boss),
        "hit_source_attributed": bool(any(attributed_hits)),
        "reflect_count": int(len(boss.reflect_hits)),
        "reflect_raw": int(sum(boss.reflect_hits)),
    }


def attribution_cases():
    hero_cls = _build_hero_class()
    item_env = source_namespace(with_inventory=True)
    item_env["_fx_notify"] = lambda *_args, **_kwargs: None
    boss_cls = boss_ability_class()
    rows = []
    with _core_module():
        inv_cls = inventory_type(item_env)
        for boss_type in SOURCE_STATS:
            is_smart = hasattr(boss_cls, f"_smart_ai_{boss_type}")
            for scenario in SCENARIOS:
                expected = _run_single(
                    boss_cls, hero_cls, inv_cls, boss_type, scenario, False
                )
                contrast = _run_single(
                    boss_cls, hero_cls, inv_cls, boss_type, scenario, True
                )
                assert expected != contrast, (
                    f"Attribution scenario must differ for {boss_type} {scenario}"
                )
                rows.append(
                    {
                        "boss_type": boss_type,
                        "boss_class": str(SOURCE_STATS[boss_type]["boss_class"]),
                        "dispatch": "smart" if is_smart else "generic",
                        "scenario": scenario,
                        "expected": expected,
                        "expected_with_boss_source": contrast,
                    }
                )
    return rows


SOURCE_FLAGS = {
    "basic_attack_passes_source_self": lambda: (
        "self.target.take_damage(self.damage, self.team, school='physical', source=self)"
        in _method_text("Boss", "update", "bosses/base_boss.py")
    ),
    "cleave_omits_source": lambda: (
        "near_e.take_damage(cleave_dmg, self.team)"
        in _method_text("Boss", "update", "bosses/base_boss.py")
    ),
    "generic_ability_omits_source": lambda: (
        "e.take_damage(self.ability_damage, self.team)"
        in _method_text("Boss", "_use_ability", "bosses/base_boss.py")
    ),
    "all_ability_take_damage_calls_omit_source": lambda: (
        [
            (m, line, argc, kw)
            for (m, line, argc, kw) in _boss_take_damage_calls()
            if not (m == "update" and kw == ("school", "source"))
        ]
        and all(
            argc == 2 and kw == ()
            for (m, _line, argc, kw) in _boss_take_damage_calls()
            if not (m == "update" and kw == ("school", "source"))
        )
    ),
    "hero_blind_requires_source": lambda: (
        "if source is not None and getattr(source, 'blind_timer', 0) > 0:"
        in _method_text("Hero", "take_damage", "_entity.py")
    ),
    "bristleback_reflect_requires_source": lambda: (
        "if getattr(self, '_bristleback_active', False) and damage > 0 and (source is not None) and (source is not self):"
        in _method_text("Hero", "take_damage", "_entity.py")
    ),
    "razor_carapace_reflect_requires_source": lambda: (
        "if refl > 0 and damage > 0 and (source is not None)"
        in _method_text(
            "HeroItemInventory", "notify_damage_taken", "hero_items.py"
        )
        and "self.last_damage_timer = p['combat_timeout']"
        in _method_text(
            "HeroItemInventory", "notify_damage_taken", "hero_items.py"
        )
    ),
    "hero_killed_by_requires_source": lambda: (
        "if source is not None and source is not self:\n            self._killed_by = source"
        in _method_text("Hero", "take_damage", "_entity.py")
    ),
}


def source_fixture():
    flags = {name: bool(check()) for name, check in SOURCE_FLAGS.items()}
    for name, value in flags.items():
        assert value, f"source shape drifted: {name}"
    non_basic_calls = [
        call
        for call in _boss_take_damage_calls()
        if not (call[0] == "update" and call[3] == ("school", "source"))
    ]
    return {
        "source": dict(
            flags,
            ability_take_damage_call_count=len(non_basic_calls) - 1,
            razor_carapace_armor=12,
            razor_carapace_reflect_pct=0.35,
            leviathan_combat_timeout=300,
        ),
        "cases": attribution_cases(),
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE: {FIXTURE} ({len(actual['cases'])} cases)")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Boss ability source attribution drift"
        )
        print(
            "PASS: Boss ability source attribution — %d cases across %d boss types"
            % (len(actual["cases"]), len({row["boss_type"] for row in actual["cases"]}))
        )


if __name__ == "__main__":
    main()
