"""Read-only source oracle: selected original methods, no pygame/game imports.

Presentation callbacks are stubbed; numeric stat, shield, regen and damage methods
are executed unchanged. This is test infrastructure, NOT a runtime converter.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/structures_source.json"


class SilentSound:
    def play(self, *args, **kwargs):
        pass


def namespace():
    result = {}
    for node in ast.parse((ROOT / "_core.py").read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign):
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = value
    result["TOWER_UPGRADE_PATHS"] = {"archer": result["ARCHER_LEVELS"]}
    result["SoundManager"] = SilentSound
    result["credit_hero_damage"] = lambda *args: None
    result["resolve_damage_school"] = lambda damage_type, source, school, **kwargs: school or "physical"
    return result


def source_classes(env):
    module = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    classes = {}
    for name, extra in (("Tower", "_update_regen"), ("Castle", "_update_castle_shield")):
        original = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == name)
        names = {"__init__", "_apply_level_stats", "take_damage", extra}
        if name == "Castle":
            names.add("set_wave")
        methods = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in names]
        cls = ast.ClassDef(name=name, bases=[], keywords=[], body=methods, decorator_list=[])
        code = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
        exec(compile(code, f"<source {name} numeric methods>", "exec"), env)
        classes[name] = env[name]
    return classes


def source_fixture():
    env = namespace()
    classes = source_classes(env)
    result = {"stats": {}, "damage": [], "regen": {}, "muzzle": []}
    mapping = {"max_hp": "max_hp", "damage": "damage", "range": "attack_range_px",
               "attack_cooldown": "attack_cooldown_ticks", "shield_max": "shield_capacity"}
    for kind, cls_name in (("tower", "Tower"), ("nexus", "Castle")):
        obj = classes[cls_name](100, 200, "blue")
        data = {dest: getattr(obj, src) for src, dest in mapping.items()}
        if kind == "tower":
            data.update(armor=obj.armor, magic_resist=obj.magic_resist,
                        regen_per_tick=env["TOWER_HP_REGEN_RATE"],
                        hp_regen_delay_ticks=env["TOWER_HP_REGEN_DELAY"],
                        gold_reward=obj.gold_reward, shield_regen_enabled=obj.regen_shield_active,
                        shield_regen_delay_ticks=env["TOWER_REGEN_SHIELD_DELAY"],
                        shield_regen_per_tick=env["TOWER_REGEN_SHIELD_RATE"])
        else:
            data.update(shield_regen_delay_ticks=env["CASTLE_SHIELD_REGEN_DELAY"],
                        shield_regen_per_tick=env["CASTLE_SHIELD_REGEN_RATE"],
                        shield_damage_reduction=env["CASTLE_SHIELD_DAMAGE_REDUCTION"],
                        free_shield_waves=env["CASTLE_SHIELD_FREE_WAVES"])
        data.update(projectile_speed_px_per_tick=env["BULLET_SPEED"],
                    projectile_hit_radius_px=env["BULLET_RADIUS"])
        result["stats"][kind] = data
        for school in ("physical", "magic"):
            for shield in (0, 3, 100):
                for amount in (1, 5, 20, 100, 10000):
                    target = classes[cls_name](100, 200, "red")
                    target.hp, target.shield = 1000, shield
                    target.take_damage(amount, "blue", school=school)
                    result["damage"].append(dict(kind=kind, school=school, shield=shield,
                        amount=amount, hp=target.hp, shield_after=target.shield))
    tower = classes["Tower"](0, 0, "blue")
    tower.hp, tower.shield, tower.no_damage_timer = 1999.9, 0, 298
    tower._update_regen()
    result["regen"]["tower_before"] = tower.hp
    tower._update_regen()
    result["regen"]["tower_at"] = tower.hp
    result["regen"]["tower_shield"] = tower.shield
    nexus = classes["Castle"](0, 0, "blue")
    nexus.shield, nexus.shield_no_damage_timer = 3998, 118
    nexus._update_castle_shield()
    result["regen"]["nexus_before"] = nexus.shield
    nexus._update_castle_shield()
    result["regen"]["nexus_at"] = nexus.shield
    result["positions"] = {
        "blue": [list(env["BLUE_TOWERS"][i][:2]) for i in (2, 5, 8)],
        "red": [list(env["RED_TOWERS"][i][:2]) for i in (2, 5, 8)],
    }
    # Red bot selected index 8 is 1090,550; red mid index 5 is 780,400.
    module = ast.parse((ROOT / "towers/_bundle.py").read_text(encoding="utf-8"))
    cls = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == "_NS_archer_tower")
    config = next(n.value for n in cls.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "LEVEL_CONFIGS" for t in n.targets))
    helper = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "get_archer_bow_position")
    helper.decorator_list = []
    env["_NS_archer_tower"] = SimpleNamespace(LEVEL_CONFIGS=ast.literal_eval(config))
    exec(compile(ast.Module(body=[helper], type_ignores=[]), "<source muzzle helper>", "exec"), env)
    for x, y in ((100, 200), (500, 340), (1090, 550)):
        for face in (-1, 1):
            result["muzzle"].append(dict(at=[x, y], face=face,
                expected=list(env["get_archer_bow_position"](x, y, 1, face))))
    return result


def main():
    assert source_fixture() == json.loads(FIXTURE.read_text(encoding="utf-8")), "Structure fixture drift: re-audit original methods"
    print("PASS: original tower/nexus methods — stat, 60 damage cases, regen, positions and muzzle fixtures.")


if __name__ == "__main__":
    main()
