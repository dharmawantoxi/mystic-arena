"""Closed group of bosses that execute the SAME actual source fallback method.

This is NOT permission to substitute generic kits for registry recipes. Eligibility
is derived from the live source handler and an absent source recipe, then compared
to the explicit native ID list. Every eligible hero executes its own real Hero and
BossHeroSkills QWER, cooldown, attack, level and respawn tests.
"""
import json
import re
import sys
from pathlib import Path

from starter_finish_source_oracle import source_env
from boss_level_one_source_oracle import state, targets as boss_targets
from structure_source_oracle import ROOT

NATIVE = ROOT / "godot_rebuild"
FIXTURE = Path(__file__).parent / "fixtures/source_shared_boss.json"
IDS_FILE = NATIVE / "scripts/data/source_shared_boss_ids.gd"


def eligible_ids(env):
    from hero_skills.boss_hero_skills import BossHeroSkills
    from hero_skills import SKILL_HANDLERS
    return sorted(kind for kind, data in env["get_all_hero_types"]().items()
        if data["is_boss_hero"] and SKILL_HANDLERS.get(kind) is BossHeroSkills
        and kind not in BossHeroSkills._SKILL_REGISTRY)


def targets(coords):
    enemies = boss_targets(coords)
    for enemy in enemies:
        enemy.hp = enemy.max_hp = 100000
    return enemies


def source_fixture():
    env = source_env()
    H = env["SourceHero"]
    ids = eligible_ids(env)
    assert len(ids) == 150, "Source membership changed: re-audit, do not auto-enable kits"
    result = dict(ids=ids, heroes={})
    for kind in ids:
        result["heroes"][kind] = hero_fixture(env, H, kind)
    return json.loads(json.dumps(result))


def hero_fixture(env, H, kind):
    result = dict(casts=[], clocks=[], attacks=[], respawn=[], levels=[])
    sample = H(kind, "red", 500, 340)
    assert type(sample.skills).__name__ == "BossHeroSkills"
    assert sample.skills._SKILL_REGISTRY.get(kind) is None
    for key in "qwer":
        reach = max(int(sample.skill_range), 140)
        cases = [([], -1), ([(550, 340), (649, 340), (650, 340), (651, 340),
                  (699, 340), (700, 340), (701, 340), (450, 340)], 0),
                 ([(450, 340), (550, 340)], -1), ([(450, 340), (550, 340)], 1),
                 ([(1000, 340), (550, 340)], 0),
                 ([(500+reach, 340)], -1), ([(501+reach, 340)], -1)]
        for coords, selected in cases:
            h = H(kind, "red", 500, 340)
            h.hp = 500
            enemies = targets(coords)
            if selected >= 0:
                h.target = enemies[selected]
            # Record the ACTUAL dispatch path and still execute the original method.
            called = []
            original = h.skills._fallback_cast
            def tracked(hero, opponents, slot):
                called.append(slot)
                return original(hero, opponents, slot)
            h.skills._fallback_cast = tracked
            ok = getattr(h.skills, "cast_"+key)(enemies, [], [])
            repeat = getattr(h.skills, "cast_"+key)(enemies, [], [])
            assert called == ([key] if ok else []), (kind, key, "wrong source handler")
            result["casts"].append(dict(hero=kind, key=key, positions=coords, target=selected,
                ok=ok, repeat=repeat, state=state(h, enemies)))
        h = H(kind, "red", 500, 340)
        enemies = targets([(550, 340)])
        assert getattr(h.skills, "cast_"+key)(enemies, [], [])
        timer = {"q": "skill_timer", "w": "w_cooldown", "e": "e_cooldown", "r": "r_cooldown"}[key]
        duration = getattr(h, timer)
        rows = []
        for tick in range(1, duration+1):
            env["tick_clocks"](h)
            h.skills.update_timers(enemies, [], [])
            if tick in (1, duration-1, duration):
                rows.append(dict(tick=tick, state=state(h, enemies)))
        assert getattr(h.skills, "cast_"+key)(enemies, [], [])
        result["clocks"].append(dict(key=key, duration=duration, rows=rows,
            recast=state(h, enemies)))
    # Real source attack: no substitution of melee for ranged or instant for homing.
    h = H(kind, "red", 500, 340)
    enemy = boss_targets([(560, 340)])[0]
    h.target = enemy
    h._do_attack()
    rows = []
    for tick in range(18):
        if tick:
            env["tick_projectiles"](h)
            env["tick_clocks"](h)
        rows.append(dict(tick=tick, hp=enemy.hp, attack_timer=h.attack_timer,
            positions=[[p['x'], p['y']] for p in h.projectiles]))
    result["attacks"].append(dict(hero=kind, target_position=[560, 340], rows=rows))
    h = H(kind, "red", 500, 340)
    enemies = targets([(550, 340)])
    for key in "qwer":
        assert getattr(h.skills, "cast_"+key)(enemies, [], [])
    h.attack_timer = 17
    h.hp, h.alive = 0, False
    env["respawn"](h)
    result["respawn"].append(dict(hero=kind, state=state(h, enemies)))
    h = H(kind, "red", 500, 340)
    h.hp = 1
    for level in range(1, 16):
        result["levels"].append(dict(level=level, hp=h.hp, damage=h.damage,
            max_hp=h.max_hp, skill_value=h.skill_damage, price=h.upgrade_cost()))
        assert h.upgrade() == (level < 15)
    return result


def write_native_definitions(env, ids):
    """Only folds original constructor data into explicit native .tres assets."""
    stats = json.loads((NATIVE / "data/ai/hero_combat_stats.json").read_text())
    catalog = env["get_all_hero_types"]()
    for kind in ids:
        data = stats[kind]
        source = catalog[kind]
        fields = dict(id=kind, display_name=data['name'], title=source.get('title', data['name']),
            role=data['role'], cost=data['cost'], max_hp=data['base_hp'], damage=data['base_damage'],
            speed_px_per_tick=data['speed'], attack_range_px=data['range'],
            attack_cooldown_ticks=data['attack_cooldown'], base_skill=data['skill_base'],
            skill_cooldown_max=data['skill_cooldown'], skill_range_px=data['skill_range'],
            dmg_school=data['dmg_school'], is_melee=data['is_melee'], catalog_damage=source['damage'])
        text = (NATIVE / "data/heroes/vex.tres").read_text()
        for key, value in fields.items():
            line = key + " = " + json.dumps(value, ensure_ascii=False)
            if re.search(r'^'+key+r' = ', text, flags=re.M):
                text = re.sub(r'^'+key+r' = .*$', lambda _: line, text, flags=re.M)
            else:
                text += line + "\n"
        (NATIVE / f"data/heroes/{kind}.tres").write_text(text)
    IDS_FILE.write_text('extends RefCounted\n## Audited original source shared-kit membership; no runtime fallback.\nconst IDS := '+json.dumps(ids)+'\n')


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":"))+"\n")
        write_native_definitions(source_env(), result["ids"])
    else:
        assert result == json.loads(FIXTURE.read_text()), "Shared source boss behavior drift"
    print(f"PASS: {len(result['ids'])} real source shared kits, each with QWER/attack/clocks/levels/respawn")
