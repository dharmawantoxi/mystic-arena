"""Execute original Mage upgrade/muzzle/volley/debuff methods, without pygame.

Reuses the Cannon oracle environment (real Tower/Bullet/debuff/take_damage
methods) and adds the real _shoot_mage chain volley, mage crystal helper,
the real anti-heal hp property setter, and skill_down/anti_heal stacking.
Victims use real damage + debuff semantics.
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

FIXTURE = Path(__file__).parent / "fixtures/mage_source.json"


def source_fixture():
    env = build_env()
    tower_type, bullet_type = env["SourceTower"], env["SourceBullet"]
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    tower_ast = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Tower")
    shoot_mage = next(n for n in tower_ast.body if isinstance(n, ast.FunctionDef)
                      and n.name == "_shoot_mage")
    exec(compile(ast.Module(body=[shoot_mage], type_ignores=[]),
                 "<original mage volley>", "exec"), env)
    tower_type._shoot_mage = env["_shoot_mage"]
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    mixin_ast = next(n for n in core.body if isinstance(n, ast.ClassDef)
                     and n.name == "TowerDebuffMixin")
    hp_nodes = [n for n in mixin_ast.body if isinstance(n, ast.FunctionDef) and n.name == "hp"]
    assert len(hp_nodes) == 2 and not hp_nodes[0].decorator_list[0].id != "property"
    hp_nodes[0].decorator_list, hp_nodes[1].decorator_list = [], []
    hp_nodes[0].name, hp_nodes[1].name = "_hp_get", "_hp_set"
    exec(compile(ast.Module(body=hp_nodes, type_ignores=[]),
                 "<original anti-heal hp property>", "exec"), env)
    env["SourceVictim"].hp = property(env["_hp_get"], env["_hp_set"])
    bundle = ast.parse((ROOT / "towers/_bundle.py").read_text(encoding="utf-8"))
    mage_ns = next(n for n in bundle.body if isinstance(n, ast.ClassDef)
                   and n.name == "_NS_mage_tower")
    config = next(n.value for n in mage_ns.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "LEVEL_CONFIGS" for t in n.targets))
    helper = next(n for n in mage_ns.body if isinstance(n, ast.FunctionDef)
                  and n.name == "get_mage_crystal_position")
    helper.decorator_list = []
    env["_NS_mage_tower"] = SimpleNamespace(LEVEL_CONFIGS=ast.literal_eval(config))
    env["mage_configs"] = ast.literal_eval(config)
    exec(compile(ast.Module(body=[helper], type_ignores=[]),
                 "<original mage crystal>", "exec"), env)
    crystal = env["get_mage_crystal_position"]
    stub = ModuleType("towers.mage_tower")
    stub.get_mage_crystal_position = crystal
    fixture = {"path_selection": {}, "levels": [], "muzzle": [], "volleys": [],
               "on_hit": [], "debuff": []}
    with patch.dict(sys.modules, {"towers": ModuleType("towers"),
                                  "towers.mage_tower": stub}):
        fresh = tower_type(500, 340, "blue")
        fixture["path_selection"] = dict(
            mage_price=fresh.upgrade_cost("mage"),
            upgrade_none=fresh.upgrade(None),
            upgrade_bogus=fresh.upgrade("bogus"),
            still_level=fresh.level, still_type=fresh.tower_type)
        assert fresh.upgrade("mage")
        fixture["path_selection"].update(
            mage_level=fresh.level, mage_type=fresh.tower_type,
            mage_next_default=fresh.upgrade_cost())
        assert fresh.upgrade("archer")
        fixture["path_selection"].update(
            kept_type=fresh.tower_type, kept_level=fresh.level)
        obj = tower_type(500, 340, "blue")
        assert obj.upgrade("mage")
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
                       magic_resist=obj.magic_resist, skill_down=obj.skill_down,
                       anti_heal=obj.anti_heal, debuff_duration=obj.debuff_duration,
                       chain=obj.chain, refund=obj.sell_value() or 50,
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
                level=level, tower_h=env["mage_configs"][level]["tower_h"],
                crystal_tier=env["mage_configs"][level]["crystal_tier"],
                crystal_plus=list(crystal(500, 340, level, 1)),
                crystal_minus=list(crystal(500, 340, level, -1)),
                aims=aims))
            for side in (-1, 1):
                target = SimpleNamespace(id=7, x=500 + side * 60, y=340, alive=True)
                obj.target, obj.bullets = target, []
                obj.angle = math.atan2(target.y - obj.y, target.x - obj.x)
                entries = [target]
                for slot in range(obj.chain - 2):
                    entries.append(make_victim(env, 20 + slot, 560 + slot * 12, 340,
                                               hp=10000))
                entries.append(make_victim(env, 30, 500 + obj.range, 340, hp=10000))
                entries.append(make_victim(env, 31, 500 + obj.range + 1.0, 340, hp=10000))
                entries.append(make_victim(env, 32, 570, 340, hp=10000))
                entries[-1].alive = False
                entries.append(make_victim(env, 33, 575, 340, hp=10000))
                shots = []
                env["Bullet"] = lambda x, y, tgt, dmg, team, kind, special=None: shots.append(
                    dict(position=[x, y], target=getattr(tgt, "id", None),
                         damage=dmg, kind=kind, special=special or {}))
                obj._shoot_mage(entries)
                fixture["volleys"].append(dict(level=level, side=side, mode="full",
                                               shots=shots, flash=obj.shoot_flash_timer))
            target = SimpleNamespace(id=7, x=560, y=340, alive=True)
            obj.target, obj.bullets = target, []
            obj.angle = math.atan2(target.y - obj.y, target.x - obj.x)
            shots = []
            env["Bullet"] = lambda x, y, tgt, dmg, team, kind, special=None: shots.append(
                dict(position=[x, y], target=getattr(tgt, "id", None),
                     damage=dmg, kind=kind, special=special or {}))
            obj._shoot_mage([target])
            fixture["volleys"].append(dict(level=level, side=1, mode="solo",
                                           shots=shots, flash=obj.shoot_flash_timer))
        fixture["path_selection"]["mage_maxed"] = not obj.upgrade()
        fixture["path_selection"]["mage_max_price"] = obj.upgrade_cost()
        del env["Bullet"]
        for level in (2, 4, 6):
            tower = tower_type(500, 340, "blue")
            assert tower.upgrade("mage")
            while tower.level < level:
                assert tower.upgrade()
            main = make_victim(env, 1, 560, 340, hp=10000)
            frail = make_victim(env, 2, 560, 340, hp=5)
            for victim in (main, frail):
                shot = bullet_type.__new__(bullet_type)
                shot.x, shot.y, shot.target, shot.damage, shot.team = \
                    0.0, 0.0, victim, tower.damage, "blue"
                shot.speed, shot.active, shot.bullet_type = 8, True, "mage"
                shot.special_data = {}
                if tower.skill_down > 0:
                    shot.special_data["skill_down"] = tower.skill_down
                if tower.anti_heal > 0:
                    shot.special_data["anti_heal"] = tower.anti_heal
                if shot.special_data:
                    shot.special_data["debuff_duration"] = tower.debuff_duration
                shot._on_hit(None)
            fixture["on_hit"].append(dict(
                level=level, damage=tower.damage, skill_down=tower.skill_down,
                anti_heal=tower.anti_heal, debuff_duration=tower.debuff_duration,
                main_calls=main.calls, main_alive=main.alive,
                main_skill=dict(amount=main.skill_down_amount, timer=main.skill_down_timer),
                main_anti=dict(amount=main.anti_heal_amount, timer=main.anti_heal_timer),
                frail_calls=frail.calls, frail_alive=frail.alive,
                frail_skill=dict(amount=frail.skill_down_amount,
                                 timer=frail.skill_down_timer),
                frail_anti=dict(amount=frail.anti_heal_amount,
                                timer=frail.anti_heal_timer)))
        for kind, first in (("skill_down", (0.20, 120)), ("anti_heal", (0.40, 120))):
            stacking = make_victim(env, 11, 0, 0, hp=10000)
            stacking.apply_debuff(kind, *first)
            before = dict(amount=getattr(stacking, f"{kind}_amount"),
                          timer=getattr(stacking, f"{kind}_timer"))
            stacking.apply_debuff(kind, 0.10, 10)
            weaker_shorter = dict(amount=getattr(stacking, f"{kind}_amount"),
                                  timer=getattr(stacking, f"{kind}_timer"))
            stacking.apply_debuff(kind, 0.10, 200)
            weaker_longer = dict(amount=getattr(stacking, f"{kind}_amount"),
                                 timer=getattr(stacking, f"{kind}_timer"))
            stacking.apply_debuff(kind, 0.50 if kind == "skill_down" else 0.75, 50)
            stronger = dict(amount=getattr(stacking, f"{kind}_amount"),
                            timer=getattr(stacking, f"{kind}_timer"))
            fixture["debuff"].append(dict(case=f"stacking_{kind}", first=before,
                                          weaker_shorter=weaker_shorter,
                                          weaker_longer=weaker_longer,
                                          stronger=stronger))
        victim = make_victim(env, 12, 0, 0, hp=10000)
        victim.apply_debuff("skill_down", 0.5, 3)
        victim.apply_debuff("anti_heal", 0.75, 2)
        ticks = []
        for _ in range(5):
            victim._tick_tower_debuffs()
            ticks.append(dict(skill_amount=victim.skill_down_amount,
                              skill_timer=victim.skill_down_timer,
                              anti_amount=victim.anti_heal_amount,
                              anti_timer=victim.anti_heal_timer))
        fixture["debuff"].append(dict(case="ticks", ticks=ticks))
        regen_rows = []
        for max_hp, regen, hp_before, amount, duration in (
                (45, 0.6, 40.0, 0.0, 0), (45, 0.6, 40.0, 0.40, 120),
                (45, 0.6, 40.0, 1.00, 180), (45, 0.6, 44.8, 0.50, 130),
                (45, 0.6, 45.0, 0.50, 130), (45, 0.6, 44.0, 0.75, 150)):
            probe = make_victim(env, 13, 0, 0, hp=10000)
            probe.max_hp = max_hp
            probe.hp = hp_before
            if duration:
                probe.apply_debuff("anti_heal", amount, duration)
            probe.hp = min(probe.max_hp, probe.hp + regen)
            regen_rows.append(dict(max_hp=max_hp, regen=regen, hp_before=hp_before,
                                   amount=amount, timer=probe.anti_heal_timer,
                                   hp_after=probe.hp))
        fixture["debuff"].append(dict(case="regen", rows=regen_rows))
    return fixture


def main():
    assert source_fixture() == json.loads(FIXTURE.read_text(encoding="utf-8")), \
        "Mage upgrade/source contract drift"
    print("PASS: original Mage levels 2-6, path selection, muzzle, chain volley, "
          "on-hit debuffs, stacking, ticks and anti-heal regen.")


if __name__ == "__main__":
    main()
