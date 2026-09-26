"""Execute original Cannon upgrade/muzzle/volley/splash/burn methods, without pygame.

Runs the real Tower/Cannon numeric methods, the real Bullet._on_hit cannon
branch, and the real TowerDebuffMixin burn methods (AST-extracted). Fake units
use the REAL Minion.take_damage + REAL resolve_damage_school so burn/splash
death semantics (alive guard, clear_tower_debuffs, reward flag) are locked.
"""
import ast
import json
import math
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from structure_source_oracle import ROOT, namespace

FIXTURE = Path(__file__).parent / "fixtures/cannon_source.json"


def _entity_tree():
    return ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))


def _exec(node, env, label):
    exec(compile(ast.Module(body=[node], type_ignores=[]), label, "exec"), env)
    return env.get(getattr(node, "name", ""))


def build_env():
    env = namespace()
    env["math"] = math
    # _entity.py sets this inside a pygame import guard; audio is out of scope.
    env["SOUND_ENABLED"] = False
    # Full upgrade paths: the shared namespace keeps archer only.
    env["TOWER_UPGRADE_PATHS"] = {
        name: env[name] for name in ("ARCHER_LEVELS", "CANNON_LEVELS", "ICE_LEVELS", "MAGE_LEVELS")
    }
    env["TOWER_UPGRADE_PATHS"] = {
        key.lower().replace("_levels", ""): value for key, value in env["TOWER_UPGRADE_PATHS"].items()
    }
    # Real damage-school resolution: tower/burn hits must stay school-free.
    tree = _entity_tree()
    hero_slot = next(n for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "_ACTIVE_HERO" for t in n.targets))
    _exec(hero_slot, env, "<source hero slot>")
    resolve = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                   and n.name == "resolve_damage_school")
    env["resolve_damage_school"] = _exec(resolve, env, "<source resolve_damage_school>")
    tower_ast = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Tower")
    methods = {n.name: n for n in tower_ast.body if isinstance(n, ast.FunctionDef)}
    wanted = ["__init__", "_apply_level_stats", "can_upgrade", "upgrade_cost",
              "upgrade", "sell_value", "_shoot_cannon"]
    tower_cls = ast.ClassDef(name="SourceTower", bases=[], keywords=[],
                             body=[methods[n] for n in wanted], decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[tower_cls], type_ignores=[])),
                 "<source tower>", "exec"), env)
    bullet_ast = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Bullet")
    bullet_methods = {n.name: n for n in bullet_ast.body if isinstance(n, ast.FunctionDef)}
    bullet_cls = ast.ClassDef(name="SourceBullet", bases=[], keywords=[],
                              body=[bullet_methods[n] for n in ("__init__", "_on_hit")],
                              decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[bullet_cls], type_ignores=[])),
                 "<source bullet>", "exec"), env)
    # Real debuff mixin (burn apply/tick/clear) + real Minion.take_damage.
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    mixin_ast = next(n for n in core.body if isinstance(n, ast.ClassDef)
                     and n.name == "TowerDebuffMixin")
    mixin_methods = {n.name: n for n in mixin_ast.body if isinstance(n, ast.FunctionDef)}
    mixin_cls = ast.ClassDef(name="SourceDebuffs", bases=[], keywords=[],
                             body=[mixin_methods[n] for n in (
                                 "_init_tower_debuffs", "apply_debuff",
                                 "clear_tower_debuffs", "_tick_tower_debuffs")],
                             decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[mixin_cls], type_ignores=[])),
                 "<source debuffs>", "exec"), env)
    minion_ast = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Minion")
    take_damage = next(n for n in minion_ast.body if isinstance(n, ast.FunctionDef)
                       and n.name == "take_damage")
    victim_cls = ast.ClassDef(
        name="SourceVictim", bases=[ast.Name(id="SourceDebuffs", ctx=ast.Load())],
        keywords=[], body=[take_damage], decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[victim_cls], type_ignores=[])),
                 "<source victim>", "exec"), env)
    # Muzzle helper + per-level render config, unchanged.
    bundle = ast.parse((ROOT / "towers/_bundle.py").read_text(encoding="utf-8"))
    cannon_ns = next(n for n in bundle.body if isinstance(n, ast.ClassDef)
                     and n.name == "_NS_cannon_tower")
    config = next(n.value for n in cannon_ns.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "LEVEL_CONFIGS" for t in n.targets))
    helper = next(n for n in cannon_ns.body if isinstance(n, ast.FunctionDef)
                  and n.name == "get_cannon_muzzle_position")
    helper.decorator_list = []
    env["_NS_cannon_tower"] = SimpleNamespace(LEVEL_CONFIGS=ast.literal_eval(config))
    env["cannon_configs"] = ast.literal_eval(config)
    _exec(helper, env, "<source cannon muzzle>")
    return env


def make_victim(env, unit_id, x, y, team="red", hp=1000):
    victim = env["SourceVictim"].__new__(env["SourceVictim"])
    victim._init_tower_debuffs()
    victim.id, victim.x, victim.y, victim.team = unit_id, x, y, team
    victim.max_hp, victim.radius, victim.gold_reward = 1000, 9, 8
    victim.armor, victim.magic_resist = 0.0, 0.0
    victim.hp, victim.alive, victim.calls = hp, True, []
    real_take = env["SourceVictim"].take_damage.__get__(victim, env["SourceVictim"])
    original_hp = victim.hp

    def recording_take_damage(damage, from_team, damage_type="normal", source=None, school=None):
        victim.calls.append(dict(damage=damage, from_team=from_team,
                                 damage_type=damage_type, hp_before=victim.hp))
        real_take(damage, from_team, damage_type, source, school)
        victim.calls[-1].update(hp_after=victim.hp, alive_after=victim.alive)

    victim.take_damage = recording_take_damage
    assert victim.hp == original_hp
    return victim


def source_fixture():
    env = build_env()
    tower_type, bullet_type = env["SourceTower"], env["SourceBullet"]
    muzzle = env["get_cannon_muzzle_position"]
    stub = ModuleType("towers.cannon_tower")
    stub.get_cannon_muzzle_position = muzzle
    fixture = {"path_selection": {}, "levels": [], "muzzle": [], "volleys": [],
               "splash": [], "burn": []}
    with patch.dict(sys.modules, {"towers": ModuleType("towers"),
                                  "towers.cannon_tower": stub}):
        fresh = tower_type(500, 340, "blue")
        fixture["path_selection"] = dict(
            level=fresh.level, tower_type=fresh.tower_type,
            archer_price=fresh.upgrade_cost("archer"),
            cannon_price=fresh.upgrade_cost("cannon"),
            ice_price=fresh.upgrade_cost("ice"),
            mage_price=fresh.upgrade_cost("mage"),
            default_price=fresh.upgrade_cost(),
            upgrade_none=fresh.upgrade(None),
            upgrade_bogus=fresh.upgrade("bogus"),
            still_level=fresh.level, still_type=fresh.tower_type)
        # Same-tier costs are identical across all four paths at level 2.
        assert fresh.upgrade("cannon")
        fixture["path_selection"].update(
            cannon_level=fresh.level, cannon_type=fresh.tower_type,
            cannon_next_default=fresh.upgrade_cost(),
            cannon_next_archer_arg=fresh.upgrade_cost("archer"))
        # Past level 1 the target argument is ignored: the path sticks.
        assert fresh.upgrade("archer")
        fixture["path_selection"].update(
            kept_type=fresh.tower_type, kept_level=fresh.level)
        obj = tower_type(500, 340, "blue")
        assert obj.upgrade("cannon")
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
                       magic_resist=obj.magic_resist, splash=obj.splash,
                       burn_dps=obj.burn_dps, burn_duration=obj.burn_duration,
                       chain=obj.chain, double_shot=obj.double_shot,
                       refund=obj.sell_value() or 50,
                       next_price=obj.upgrade_cost(),
                       timer=obj.timer, no_damage_timer=obj.no_damage_timer)
            fixture["levels"].append(row)
            # At fire time timer == 0, so the recoil branch never triggers:
            # 0 > cooldown - 8 is false for every cannon cooldown.
            fixture["muzzle"].append(dict(
                level=level, cooldown=obj.attack_cooldown,
                recoil_at_fire=0 if not (0 > obj.attack_cooldown - 8) else -1,
                tower_h=env["cannon_configs"][level]["tower_h"],
                cannon_tier=env["cannon_configs"][level]["cannon_tier"],
                faces={str(face): list(muzzle(500, 340, level, face, 0))
                       for face in (-1, 1)}))
            for side in (-1, 1):
                target = SimpleNamespace(id=7, x=500 + side * 60, y=340, alive=True)
                obj.target, obj.bullets, obj.timer = target, [], 0
                shots = []
                env["Bullet"] = lambda x, y, tgt, dmg, team, kind, special=None: shots.append(
                    dict(position=[x, y], target=getattr(tgt, "id", None),
                         damage=dmg, kind=kind, special=special or {}))
                obj._shoot_cannon()
                fixture["volleys"].append(dict(level=level, side=side, shots=shots,
                                               flash=obj.shoot_flash_timer))
        fixture["path_selection"]["cannon_maxed"] = not obj.upgrade()
        fixture["path_selection"]["cannon_max_price"] = obj.upgrade_cost()
        del env["Bullet"]
        # Splash: real _on_hit against real victim semantics.
        for level in (2, 4, 6):
            tower = tower_type(500, 340, "blue")
            assert tower.upgrade("cannon")
            while tower.level < level:
                assert tower.upgrade()
            main = make_victim(env, 1, 560, 340, hp=10000)
            splash_radius = tower.splash
            others = [
                make_victim(env, 2, 560 + splash_radius, 340, hp=10000),  # boundary: included
                make_victim(env, 3, 560 + splash_radius + 1.0, 340, hp=10000),  # outside
                make_victim(env, 4, 560 + 10, 340, hp=5),  # splash kill: no burn after death
                make_victim(env, 5, 560 + 10, 340, team="blue", hp=10000),  # ally: skipped
            ]
            dead = make_victim(env, 6, 560 + 10, 340, hp=10000)
            dead.alive = False
            others.append(dead)
            structure_like = SimpleNamespace(id=7, x=560 + 10, y=340, team="red",
                                             alive=True, calls=[],
                                             take_damage=lambda *a, **k: structure_like.calls.append(a))
            others.append(structure_like)
            shot = bullet_type.__new__(bullet_type)
            shot.x, shot.y, shot.target, shot.damage, shot.team = 0.0, 0.0, main, tower.damage, "blue"
            shot.speed, shot.active, shot.bullet_type = 8, True, "cannon"
            shot.special_data = {"splash": tower.splash, "burn_dps": tower.burn_dps,
                                 "burn_duration": tower.burn_duration}
            shot._on_hit([main] + others)
            case = dict(level=level, damage=tower.damage, splash=splash_radius,
                        splash_damage=int(tower.damage * 0.6),
                        main_calls=main.calls,
                        main_burn=dict(dps=main.burn_dps, timer=main.burn_timer,
                                       team=main.burn_team),
                        victims=[])
            for victim in others:
                if isinstance(victim, SimpleNamespace):
                    case["victims"].append(dict(id=victim.id, calls=[list(map(str, c)) for c in victim.calls],
                                               burn=None))
                else:
                    case["victims"].append(dict(id=victim.id, calls=victim.calls,
                                               burn=dict(dps=victim.burn_dps, timer=victim.burn_timer,
                                                         team=victim.burn_team)))
            fixture["splash"].append(case)
        # Burn stacking + tick damage, real mixin methods.
        stacking = make_victim(env, 11, 0, 0, hp=10000)
        stacking.apply_debuff("burn", 8, 120, source_team="blue")
        first = dict(dps=stacking.burn_dps, timer=stacking.burn_timer,
                     accum=stacking.burn_accum, tick_cd=stacking.burn_tick_cd,
                     team=stacking.burn_team)
        stacking.apply_debuff("burn", 5, 200, source_team="red")
        weaker = dict(dps=stacking.burn_dps, timer=stacking.burn_timer,
                      team=stacking.burn_team)
        stacking.apply_debuff("burn", 30, 60, source_team="red")
        stronger = dict(dps=stacking.burn_dps, timer=stacking.burn_timer,
                        team=stacking.burn_team)
        fixture["burn"].append(dict(case="stacking", first=first, weaker=weaker,
                                    stronger=stronger))
        for dps, duration in ((8, 120), (30, 180)):
            victim = make_victim(env, 12, 0, 0, hp=10000)
            victim.apply_debuff("burn", dps, duration, source_team="blue")
            events = []
            for tick in range(1, duration + 5):
                before = len(victim.calls)
                victim._tick_tower_debuffs()
                for call in victim.calls[before:]:
                    events.append(dict(tick=tick, damage=call["damage"],
                                       from_team=call["from_team"],
                                       damage_type=call["damage_type"]))
            fixture["burn"].append(dict(case="ticks", dps=dps, duration=duration,
                                        events=events, hp=victim.hp,
                                        timer=victim.burn_timer, dps_after=victim.burn_dps,
                                        accum=victim.burn_accum))
        # Burn applied without a source team falls back to the victim team.
        fallback = make_victim(env, 13, 0, 0, hp=10000)
        fallback.apply_debuff("burn", 60, 30)
        for _ in range(30):
            fallback._tick_tower_debuffs()
        fixture["burn"].append(dict(case="fallback_team",
                                    from_team=fallback.calls[0]["from_team"],
                                    damage=fallback.calls[0]["damage"]))
        # Death clears burn: no further ticks once take_damage kills.
        dying = make_victim(env, 14, 0, 0, hp=3)
        dying.apply_debuff("burn", 60, 180, source_team="blue")
        for _ in range(60):
            dying._tick_tower_debuffs()
        fixture["burn"].append(dict(case="death", calls=dying.calls,
                                    alive=dying.alive, timer=dying.burn_timer,
                                    dps=dying.burn_dps, accum=dying.burn_accum))
        dead_tick = make_victim(env, 15, 0, 0, hp=10000)
        dead_tick.apply_debuff("burn", 60, 180, source_team="blue")
        dead_tick.alive = False
        for _ in range(35):
            dead_tick._tick_tower_debuffs()
        fixture["burn"].append(dict(case="already_dead", calls=dead_tick.calls,
                                    timer=dead_tick.burn_timer,
                                    tick_cd=dead_tick.burn_tick_cd))
    return fixture


def main():
    assert source_fixture() == json.loads(FIXTURE.read_text(encoding="utf-8")), \
        "Cannon upgrade/source contract drift"
    print("PASS: original Cannon levels 2-6, path selection, muzzle, splash and burn.")


if __name__ == "__main__":
    main()
