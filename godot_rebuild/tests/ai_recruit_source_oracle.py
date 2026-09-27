"""Read-only source oracle for an actual Hero purchase, not a receipt.

This first phase exercises the *real* AIPlayer._try_buy_hero and Hero.__init__
for Kaizen with the existing empty-inventory/audio stubs. It does NOT prove
other 221 kits; those cannot be constructed using native Kaizen skills.
"""
import ast
import json
import sys
from pathlib import Path

from ai_upgrade_source_oracle import compile_subset
from kaizen_source_oracle import build_hero_env
from structure_source_oracle import ROOT

FIXTURE = Path(__file__).parent / "fixtures/ai_recruit_source.json"
STATS = ROOT / "godot_rebuild/data/ai/hero_combat_stats.json"


def source_fixture():
    env = build_hero_env()
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    ai_type = compile_subset(tree, "AIPlayer", ("__init__", "_ai_reserve", "_try_buy_hero"), env)
    env["Hero"] = env["SourceHero"]
    stats = {}
    catalog = env["get_all_hero_types"]()
    assert len(catalog) == 222, "Re-audit roster rather than silently dropping kits"
    for hero_type, entry in catalog.items():
        hero = env["SourceHero"](hero_type, "red", 1120, 90)
        assert hero.skills is not None, f"Missing source handler: {hero_type}"
        stats[hero_type] = dict(
            name=hero.name, role=hero.role, cost=entry["cost"],
            is_boss_hero=entry["is_boss_hero"],
            base_hp=hero.base_hp, base_damage=hero.base_damage,
            max_hp=hero.max_hp, damage=hero.damage,
            speed=hero.speed, range=hero.range,
            attack_cooldown=hero.attack_cooldown,
            skill_base=hero.skill_damage_base, skill_damage=hero.skill_damage,
            skill_cooldown=hero.skill_cooldown_max, skill_range=hero.skill_range,
            dmg_school=hero.dmg_school, is_melee=hero.is_melee_hero)
    result = []
    for initial in (399, 400, 401):
        player = ai_type()
        player.gold = initial
        player._get_hero_pool = lambda: ["kaizen"]
        player._hero_purchase_target = "kaizen"
        player._hero_purchase_target_cost = 400
        first = player._try_buy_hero()
        hero = player.heroes[0] if first else None
        result.append(dict(initial=initial, success=first, balance=player.gold,
            count=player.total_heroes_bought, reserve=player._ai_reserve(),
            target=player._hero_purchase_target or "",
            hero=(dict(hero_type=hero.hero_type, team=hero.team, x=hero.x, y=hero.y,
                       max_hp=hero.max_hp, hp=hero.hp, damage=hero.damage,
                       skill_damage=hero.skill_damage, level=hero.level,
                       auto_cast=hero.auto_cast_enabled) if hero else None)))
    return result, stats


if __name__ == "__main__":
    purchases, stats = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(purchases, indent=2) + "\n", encoding="utf-8")
        STATS.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    else:
        assert purchases == json.loads(FIXTURE.read_text(encoding="utf-8")), "AI real recruit drift"
        assert stats == json.loads(STATS.read_text(encoding="utf-8")), "Hero combat stat drift"
    print(f"PASS: {len(stats)} source Hero numeric baselines, {len(purchases)} Kaizen purchases "
          "(other kits still pending)")
