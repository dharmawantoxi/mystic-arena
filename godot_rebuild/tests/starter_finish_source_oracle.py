"""Read-only actual Vex/Zephyr skills, Hero attacks, timer statements and respawn.

Uses the established empty-inventory/audio harness. Dummy opponents record hits,
slows and attack clocks. No source skill arithmetic is replicated here.
"""
import ast
import json
import sys
from pathlib import Path

from sylara_source_oracle import setup, Target
from structure_source_oracle import ROOT

FIXTURE = Path(__file__).parent / "fixtures/starter_finish_source.json"
FIELDS = {
    "hp": "hp", "damage": "damage", "skill_value": "skill_damage",
    "max_hp": "max_hp", "level": "level", "attack_timer": "attack_timer",
    "skill_timer": "skill_timer", "w_cooldown": "w_cooldown",
    "e_cooldown": "e_cooldown", "r_cooldown": "r_cooldown",
    "active_skill_timer": "active_skill_timer",
    "eclipse_timer": "_sanity_eclipse_timer", "prison_timer": "_astral_prison_timer",
    "essence_timer": "_essence_flux_timer", "bramble_timer": "_bramble_timer",
    "shadow_realm_timer": "_shadow_realm_timer", "curse_timer": "_curse_timer",
    "bedlam_timer": "_bedlam_timer",
}


def source_env():
    env = setup()
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    minion = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Minion")
    slow = next(n for n in minion.body if isinstance(n, ast.FunctionDef) and n.name == "apply_slow")
    exec(compile(ast.fix_missing_locations(ast.Module(body=[slow], type_ignores=[])),
                 "<source Minion.apply_slow>", "exec"), env)
    Target.apply_slow = env["apply_slow"]
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Hero")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "respawn")
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 "<source Hero.respawn>", "exec"), env)
    update = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "update")
    clocks = {"attack_timer", "skill_timer", "w_cooldown", "e_cooldown",
              "r_cooldown", "active_skill_timer"}
    body = [n for n in update.body if isinstance(n, ast.If)
            and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Attribute)
            and n.test.left.attr in clocks]
    assert len(body) == 6, "Re-audit Hero.update clocks"
    fn = ast.FunctionDef(name="tick_clocks", args=ast.arguments(posonlyargs=[],
        args=[ast.arg(arg="self")], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=body, decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                 "<source Hero.update clocks>", "exec"), env)
    return env


def state(hero, enemies):
    result = {native: getattr(hero, source) for native, source in FIELDS.items()
              if hasattr(hero, source)}
    result["active_skill"] = hero.active_skill or ""
    result["position"] = [hero.x, hero.y]
    result["enemies"] = [dict(hp=e.hp, slow_amount=e.slow_amount, slow_timer=e.slow_timer,
                              cooldown_ticks=e.attack_timer) for e in enemies]
    for native, source in (("prison_target_id", "_astral_prison_target"),
                           ("curse_target_id", "_curse_target")):
        if hasattr(hero, source):
            target = getattr(hero, source)
            result[native] = enemies.index(target) if target in enemies else -1
    if hasattr(hero, "_bramble_origin"):
        result["bramble_origin"] = list(hero._bramble_origin or (0, 0))
    return result


def source_fixture():
    env = source_env()
    H = env["SourceHero"]
    result = dict(casts=[], traces=[], defense=[], attacks=[], respawn=[])
    for kind in ("vex", "zephyr"):
        for key in "qwer":
            # Cast/no target, target retention, exact radial/ring/line edges.
            for populated in (False, True):
                coords = [(620, 340), (530, 340), (531, 340), (540, 340),
                          (541, 340), (555, 340), (556, 340), (560, 340),
                          (561, 340), (580, 340), (581, 340), (680, 340),
                          (681, 340), (550, 357), (550, 358), (500, 340)]
                h = H(kind, "red", 500, 340)
                h.hp = 500
                enemies = [Target(*p) for p in coords] if populated else []
                if enemies:
                    h.target = enemies[0]
                ok = getattr(h.skills, "cast_" + key)(enemies, [], [])
                repeat = getattr(h.skills, "cast_" + key)(enemies, [], [])
                result["casts"].append(dict(hero=kind, key=key, positions=coords if populated else [],
                    target=0 if enemies else -1, ok=ok, repeat=repeat, state=state(h, enemies)))
            for radius in (172, 173, 199, 200, 201, 206, 207, 208):
                h = H(kind, "red", 500, 340)
                h.hp = 500
                enemies = [Target(500 + radius, 340)]
                ok = getattr(h.skills, "cast_" + key)(enemies, [], [])
                repeat = getattr(h.skills, "cast_" + key)(enemies, [], [])
                result["casts"].append(dict(hero=kind, key=key, positions=[[500+radius, 340]],
                    target=-1, ok=ok, repeat=repeat, state=state(h, enemies)))
            for mode in ("normal", "move_upgrade", "target_dies"):
                h = H(kind, "red", 500, 340)
                h.hp = 500
                coords = [(550, 340), (600, 340), (590, 340), (610, 340), (580, 340)]
                enemies = [Target(*p) for p in coords]
                h.target = enemies[0]
                enemies[0].attack_timer = 90  # prison must not shorten this
                assert getattr(h.skills, "cast_" + key)(enemies, [], [])
                rows = []
                for tick in range(1, 242):
                    if tick == 2 and mode == "move_upgrade":
                        h.x += 100
                        enemies[0].x += 200
                        assert h.upgrade()
                    if tick == 2 and mode == "target_dies":
                        enemies[0].alive = False
                    env["tick_clocks"](h)
                    h.skills.update_timers(enemies, [], [])
                    if tick in (1, 2, 9, 10, 14, 15, 19, 20, 59, 60, 149, 150, 179, 180, 239, 240, 241):
                        rows.append(dict(tick=tick, state=state(h, enemies)))
                result["traces"].append(dict(hero=kind, key=key, mode=mode, positions=coords, rows=rows))
        # The same source ranged attack and original projectile loop used by Sylara.
        h = H(kind, "red", 500, 340)
        enemy = Target(620, 340)
        h.target = enemy
        h._do_attack()
        rows = []
        for tick in range(18):
            if tick:
                env["tick_projectiles"](h)
                env["tick_clocks"](h)
            rows.append(dict(tick=tick, hp=enemy.hp, attack_timer=h.attack_timer,
                positions=[[p['x'], p['y']] for p in h.projectiles]))
        result["attacks"].append(dict(hero=kind, rows=rows))
        # Source respawn deliberately retains kit timers and W/E/R, even after death.
        h = H(kind, "red", 500, 340)
        enemies = [Target(550, 340)]
        for key in "qwer":
            assert getattr(h.skills, "cast_" + key)(enemies, [], [])
        h.attack_timer = 17
        h.hp, h.alive = 0, False
        env["respawn"](h)
        result["respawn"].append(dict(hero=kind, state=state(h, enemies)))
    for school in ("physical", "magic"):
        for tick in (0, 179, 180):
            h = H("zephyr", "red", 500, 340)
            h.hp = 300
            h.skills.cast_w([], [], [])
            for _ in range(tick):
                h.skills.update_timers([], [], [])
            before = h.hp
            h.take_damage(100, "blue", school=school)
            result["defense"].append(dict(school=school, tick=tick, before=before, hp=h.hp))
    return json.loads(json.dumps(result))


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        assert result == json.loads(FIXTURE.read_text()), "Vex/Zephyr source drift"
    print("PASS: Vex/Zephyr actual skills, bounds, timers, upgrades, ranged attacks, realm, respawn")
