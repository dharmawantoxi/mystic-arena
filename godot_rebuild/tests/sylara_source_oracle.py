"""Execute actual Python Hero/SylaraSkills and Hero's ranged projectile loop.

Stub only inventory/audio/skill visual FX; never mirror skill arithmetic.
"""
import ast
import json
import math
import random
import sys
from pathlib import Path

from kaizen_source_oracle import build_hero_env
from structure_source_oracle import ROOT
from thorne_source_oracle import Enemy

FIXTURE = Path(__file__).parent / "fixtures/sylara_source.json"


class Target(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.attack_timer = 0


def setup():
    env = build_hero_env()
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Hero")
    for name in ("_spawn_projectile", "_spawn_skill_projectile"):
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                     "<source Hero." + name + ">", "exec"), env)
        setattr(env["SourceHero"], name, env[name])
    env.update(_HERO_PROJ_MAX=6, _HERO_PROJ_MAX_AGE=72,
               _HERO_PROJ_DEAD_AGE=36, _HERO_PROJ_MAX_DIST=380)
    # Extract the original Hero.update projectile loop and its cleanup,
    # rather than copying/reimplementing the homing arithmetic in tests.
    update = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "update")
    loop = next(n for n in update.body if isinstance(n, ast.For)
                and isinstance(n.iter, ast.Attribute) and n.iter.attr == "projectiles")
    cleanup = next(n for n in update.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Attribute) and t.attr == "projectiles"
                           for t in n.targets))
    function = ast.FunctionDef(name="tick_projectiles", args=ast.arguments(
        posonlyargs=[], args=[ast.arg(arg="self")], vararg=None, kwonlyargs=[],
        kw_defaults=[], kwarg=None, defaults=[]), body=[loop, cleanup], decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                 "<source Hero.update projectiles>", "exec"), env)
    return env


def state(hero, enemies):
    return dict(hp=hero.hp, speed=hero.speed, attack_cd=hero.attack_cooldown,
        q=hero.skill_timer, w=hero.w_cooldown, e=hero.e_cooldown, r=hero.r_cooldown,
        visual=hero.active_skill_timer, active=hero.active_skill or "",
        focus=hero._focus_fire_timer, windrun=hero._windrun_timer,
        shackle=hero._shackle_timer, bound=hero._shackle_target is not None,
        powershot=hero._powershot_timer,
        enemies=[dict(hp=e.hp, attack_timer=e.attack_timer) for e in enemies])


def source_fixture():
    env = setup()
    H = env["SourceHero"]
    fixture = dict(casts=[], ticks={}, windrun=[], projectiles=[])
    positions = {
        "q": [(620, 340), (650, 340), (679, 340), (680, 340),
              (600, 354), (600, 355), (400, 340)],
        "w": [(620, 340)],
        "e": [(700, 340)],
        "r": [(620, 340), (760, 340), (790, 340), (800, 340),
              (650, 365), (650, 375), (400, 340)],
    }
    for key, coords in positions.items():
        for populated in (False, True):
            hero = H("sylara", "red", 500, 340)
            hero.hp = 500
            enemies = [Target(*point) for point in coords] if populated else []
            if populated:
                hero.target = enemies[0]  # source preserves valid current target
            success = getattr(hero.skills, "cast_" + key)(enemies, [], [])
            repeat = getattr(hero.skills, "cast_" + key)(enemies, [], [])
            fixture["casts"].append(dict(key=key, populated=populated,
                positions=[list(p) for p in coords], success=success, repeat=repeat,
                state=state(hero, enemies)))
    for radius in (199, 200, 201, 206, 208):
        hero = H("sylara", "red", 500, 340)
        enemy = Target(500 + radius, 340)
        success = hero.skills.cast_e([enemy], [], [])
        fixture["casts"].append(dict(key="e_boundary", radius=radius,
            success=success, state=state(hero, [enemy])))
    for key, ticks, moments in (("q", 180, (1, 179, 180)),
                                ("w", 180, (1, 179, 180)),
                                ("e", 150, (1, 15, 16, 150)),
                                ("r", 60, (1, 59, 60))):
        hero = H("sylara", "red", 500, 340)
        enemies = [Target(620, 340), Target(760, 340), Target(650, 365)]
        hero.target = enemies[0]
        assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
        records = []
        for tick in range(1, ticks + 1):
            hero.skills.update_timers(enemies, [], [])
            if tick in moments:
                records.append(dict(tick=tick, state=state(hero, enemies)))
        fixture["ticks"][key] = records
    for school in ("physical", "magic"):
        for roll in (0.0, 0.7499, 0.75, 0.99):
            hero = H("sylara", "red", 500, 340)
            hero.hp = 500
            assert hero.skills.cast_w([], [], [])
            old = random.random
            random.random = lambda: roll
            try:
                hero.take_damage(80, "blue", source=Target(560, 340), school=school)
            finally:
                random.random = old
            fixture["windrun"].append(dict(school=school, roll=roll, hp=hero.hp))
    # Actual Hero._do_attack creates a homing basic arrow. The original
    # Hero.update projectile AST segment advances it; move target in flight.
    hero = H("sylara", "red", 500, 340)
    enemy = Target(620, 340)
    hero.target = enemy
    hero._do_attack()
    assert hero.projectiles and enemy.hp == 10000
    for tick in range(0, 17):
        if tick == 2:
            enemy.y = 360
        if tick:
            env["tick_projectiles"](hero)
        if tick in (0, 1, 2, 12, 13, 14, 16):
            fixture["projectiles"].append(dict(tick=tick, hp=enemy.hp,
                count=len(hero.projectiles), positions=[[p["x"], p["y"]]
                                                     for p in hero.projectiles]))
    return fixture


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        assert result == json.loads(FIXTURE.read_text(encoding="utf-8")), "Sylara source drift"
    print("PASS: source Sylara Q/W/E/R, windrun evasion and real homing arrows")
