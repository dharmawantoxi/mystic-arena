"""Execute original Ice upgrade/muzzle/volley/slow methods, without pygame.

Reuses the Cannon oracle environment (real Tower/Bullet/debuff/take_damage
methods) and adds the real _shoot_ice, ice muzzle helper, Minion.apply_slow,
_eff_attack_cd and _eff_speed. Victims use real damage + slow semantics.
"""
import ast
import json
import math
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from cannon_source_oracle import build_env, make_victim
from structure_source_oracle import ROOT

FIXTURE = Path(__file__).parent / "fixtures/ice_source.json"


def source_fixture():
    env = build_env()
    tower_type, bullet_type = env["SourceTower"], env["SourceBullet"]
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    tower_ast = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Tower")
    shoot_ice = next(n for n in tower_ast.body if isinstance(n, ast.FunctionDef)
                     and n.name == "_shoot_ice")
    exec(compile(ast.Module(body=[shoot_ice], type_ignores=[]),
                 "<original ice volley>", "exec"), env)
    tower_type._shoot_ice = env["_shoot_ice"]
    minion_ast = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Minion")
    minion_methods = {n.name: n for n in minion_ast.body if isinstance(n, ast.FunctionDef)}
    exec(compile(ast.Module(body=[minion_methods["apply_slow"]], type_ignores=[]),
                 "<original minion slow>", "exec"), env)
    env["SourceVictim"].apply_slow = env["apply_slow"]
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    mixin_ast = next(n for n in core.body if isinstance(n, ast.ClassDef)
                     and n.name == "TowerDebuffMixin")
    mixin_methods = {n.name: n for n in mixin_ast.body if isinstance(n, ast.FunctionDef)}
    for name in ("_eff_speed", "_eff_attack_cd"):
        exec(compile(ast.Module(body=[mixin_methods[name]], type_ignores=[]),
                     "<original effective stats>", "exec"), env)
        setattr(env["SourceVictim"], name, env[name])
    bundle = ast.parse((ROOT / "towers/_bundle.py").read_text(encoding="utf-8"))
    ice_ns = next(n for n in bundle.body if isinstance(n, ast.ClassDef)
                  and n.name == "_NS_ice_tower")
    config = next(n.value for n in ice_ns.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "LEVEL_CONFIGS" for t in n.targets))
    helper = next(n for n in ice_ns.body if isinstance(n, ast.FunctionDef)
                  and n.name == "get_ice_crystal_position")
    helper.decorator_list = []
    env["_NS_ice_tower"] = SimpleNamespace(LEVEL_CONFIGS=ast.literal_eval(config))
    env["ice_configs"] = ast.literal_eval(config)
    exec(compile(ast.Module(body=[helper], type_ignores=[]),
                 "<original ice crystal>", "exec"), env)
    crystal = env["get_ice_crystal_position"]
    stub = ModuleType("towers.ice_tower")
    stub.get_ice_crystal_position = crystal
    fixture = {"path_selection": {}, "levels": [], "muzzle": [], "volleys": [],
               "on_hit": [], "slow": []}
    with patch.dict(sys.modules, {"towers": ModuleType("towers"),
                                  "towers.ice_tower": stub}):
        fresh = tower_type(500, 340, "blue")
        fixture["path_selection"] = dict(
            ice_price=fresh.upgrade_cost("ice"),
            upgrade_none=fresh.upgrade(None),
            upgrade_bogus=fresh.upgrade("bogus"),
            still_level=fresh.level, still_type=fresh.tower_type)
        assert fresh.upgrade("ice")
        fixture["path_selection"].update(
            ice_level=fresh.level, ice_type=fresh.tower_type,
            ice_next_default=fresh.upgrade_cost())
        assert fresh.upgrade("archer")
        fixture["path_selection"].update(
            kept_type=fresh.tower_type, kept_level=fresh.level)
        obj = tower_type(500, 340, "blue")
        assert obj.upgrade("ice")
        for level in range(2, 7):
            if level > 2:
                price = obj.upgrade_cost()
                obj.hp, obj.shield, obj.timer, obj.no_damage_timer = 1, 0, 17, 9
                assert obj.upgrade()
            else:
                price = 175
            row = dict(level=level, price=price, hp=obj.hp, max_hp=obj.max_hp,
                       shield=obj.shield, damage=obj.damage, range=obj.range,
                       cooldown=obj.attack_cooldown, armor=obj.armor,
                       magic_resist=obj.magic_resist, slow=obj.slow,
                       slow_duration=obj.slow_duration, atk_slow=obj.atk_slow,
                       slow_aoe=obj.slow_aoe, chain=obj.chain,
                       refund=obj.sell_value() or 50,
                       next_price=obj.upgrade_cost(),
                       timer=obj.timer, no_damage_timer=obj.no_damage_timer)
            fixture["levels"].append(row)
            aims = {}
            for name, dx, dy in (("E", 60, 0), ("W", -60, 0), ("N", 0, -60),
                                 ("S", 0, 60), ("NE", 60, -60), ("SE", 60, 60),
                                 ("SW", -60, 60), ("NW", -60, -60)):
                angle = math.atan2(dy, dx)
                cx, cy = crystal(500, 340, level, 1 if dx > 0 else -1)
                aims[name] = dict(angle=angle,
                                  position=[cx + math.cos(angle) * 5,
                                            cy + math.sin(angle) * 5])
            fixture["muzzle"].append(dict(
                level=level, tower_h=env["ice_configs"][level]["tower_h"],
                crystal_tier=env["ice_configs"][level]["crystal_tier"],
                crystal_plus=list(crystal(500, 340, level, 1)),
                crystal_minus=list(crystal(500, 340, level, -1)),
                aims=aims))
            for side in (-1, 1):
                target = SimpleNamespace(id=7, x=500 + side * 60, y=340, alive=True)
                obj.target, obj.bullets = target, []
                obj.angle = math.atan2(target.y - obj.y, target.x - obj.x)
                shots = []
                env["Bullet"] = lambda x, y, tgt, dmg, team, kind, special=None: shots.append(
                    dict(position=[x, y], target=getattr(tgt, "id", None),
                         damage=dmg, kind=kind, special=special or {}))
                obj._shoot_ice()
                fixture["volleys"].append(dict(level=level, side=side, shots=shots,
                                               flash=obj.shoot_flash_timer))
        fixture["path_selection"]["ice_maxed"] = not obj.upgrade()
        fixture["path_selection"]["ice_max_price"] = obj.upgrade_cost()
        del env["Bullet"]
        for level in (2, 4, 6):
            tower = tower_type(500, 340, "blue")
            assert tower.upgrade("ice")
            while tower.level < level:
                assert tower.upgrade()
            main = make_victim(env, 1, 560, 340, hp=10000)
            others = []
            if tower.slow_aoe > 0:
                edge = make_victim(env, 2, 560 + tower.slow_aoe, 340, hp=10000)
                outside = make_victim(env, 3, 560 + tower.slow_aoe + 1.0, 340, hp=10000)
                ally = make_victim(env, 4, 570, 340, team="blue", hp=10000)
                dead = make_victim(env, 5, 570, 340, hp=10000)
                dead.alive = False
                others = [edge, outside, ally, dead]
            shot = bullet_type.__new__(bullet_type)
            shot.x, shot.y, shot.target, shot.damage, shot.team = 0.0, 0.0, main, tower.damage, "blue"
            shot.speed, shot.active, shot.bullet_type = 8, True, "ice"
            shot.special_data = {"slow": tower.slow, "slow_duration": tower.slow_duration}
            if tower.atk_slow > 0:
                shot.special_data["atk_slow"] = tower.atk_slow
            if tower.slow_aoe > 0:
                shot.special_data["slow_aoe"] = tower.slow_aoe
            target_list = [main] + others if level == 6 else None
            shot._on_hit(target_list)
            case = dict(level=level, damage=tower.damage, slow=tower.slow,
                        slow_duration=tower.slow_duration, atk_slow=tower.atk_slow,
                        slow_aoe=tower.slow_aoe, main_calls=main.calls,
                        main_slow=dict(amount=main.slow_amount, timer=main.slow_timer),
                        main_atk=dict(amount=main.atk_slow_amount,
                                      timer=main.atk_slow_timer),
                        victims=[])
            for victim in others:
                case["victims"].append(dict(
                    id=victim.id, calls=victim.calls,
                    slow=dict(amount=victim.slow_amount, timer=victim.slow_timer),
                    atk=dict(amount=victim.atk_slow_amount,
                             timer=victim.atk_slow_timer)))
            fixture["on_hit"].append(case)
        stacking = make_victim(env, 11, 0, 0, hp=10000)
        stacking.apply_slow(0.25, 90)
        first = dict(amount=stacking.slow_amount, timer=stacking.slow_timer)
        stacking.apply_slow(0.10, 10)
        weaker_shorter = dict(amount=stacking.slow_amount, timer=stacking.slow_timer)
        stacking.apply_slow(0.10, 200)
        weaker_longer = dict(amount=stacking.slow_amount, timer=stacking.slow_timer)
        stacking.apply_slow(0.65, 50)
        stronger = dict(amount=stacking.slow_amount, timer=stacking.slow_timer)
        victim = make_victim(env, 12, 0, 0, hp=10000)
        victim.apply_slow(0.5, 3)
        victim.apply_debuff("atk_slow", 0.4, 2)
        ticks = []
        for _ in range(5):
            victim._tick_tower_debuffs()
            ticks.append(dict(slow_amount=victim.slow_amount, slow_timer=victim.slow_timer,
                              atk_amount=victim.atk_slow_amount,
                              atk_timer=victim.atk_slow_timer))
        speeds = []
        for amount, duration in ((0.0, 0), (0.25, 90), (0.65, 150)):
            probe = make_victim(env, 13, 0, 0, hp=10000)
            probe.speed, probe.base_speed = 1.5, 1.5
            if duration:
                probe.apply_slow(amount, duration)
            speeds.append(dict(amount=amount, timer=probe.slow_timer,
                               eff=probe._eff_speed(),
                               inline=probe.base_speed * (1.0 - probe.slow_amount)
                               if probe.slow_timer > 0 else probe.base_speed))
        cooldowns = []
        for amount, duration in ((0.0, 0), (0.15, 90), (0.25, 110), (0.40, 150)):
            probe = make_victim(env, 14, 0, 0, hp=10000)
            if duration:
                probe.apply_debuff("atk_slow", amount, duration)
            cooldowns.append(dict(amount=amount, timer=probe.atk_slow_timer,
                                   eff45=probe._eff_attack_cd(45),
                                   eff22=probe._eff_attack_cd(22)))
        fixture["slow"].append(dict(case="stacking", first=first,
                                    weaker_shorter=weaker_shorter,
                                    weaker_longer=weaker_longer,
                                    stronger=stronger))
        fixture["slow"].append(dict(case="ticks", ticks=ticks))
        fixture["slow"].append(dict(case="speed", rows=speeds))
        fixture["slow"].append(dict(case="attack_cd", rows=cooldowns))
    return fixture


def main():
    assert source_fixture() == json.loads(FIXTURE.read_text(encoding="utf-8")), \
        "Ice upgrade/source contract drift"
    print("PASS: original Ice levels 2-6, path selection, muzzle, volley, slow and attack-slow.")


if __name__ == "__main__":
    main()
