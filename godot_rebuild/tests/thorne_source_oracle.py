"""Execute original Hero + ThorneSkills Q/W/E/R/timers/damage, read-only.

World opponents are simple damage/slow receipts; Hero, catalog and skill handler
methods are real source. This does not claim item/forge or presentation parity.
"""
import ast
import json
import sys
from pathlib import Path

from kaizen_source_oracle import build_hero_env
from structure_source_oracle import ROOT

FIXTURE = Path(__file__).parent / "fixtures/thorne_source.json"


class Enemy:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.team, self.alive = "blue", True
        self.hp = 10000
        self.slow_amount = 0.0
        self.slow_timer = 0

    def take_damage(self, damage, _team, **_kwargs):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False

    def apply_slow(self, amount, duration):
        self.slow_amount, self.slow_timer = amount, duration


def source_fixture():
    env = build_hero_env()
    result = {"skills": [], "timers": [], "reflect": [], "respawn": {}}
    for skill, positions in (
        ("q", [(450, 340), (550, 340), (460, 380), (390, 340)]),
        ("w", [(450, 340), (600, 340)]),
        ("e", [(410, 340), (400, 340), (399, 340)]),
        ("r", [(386, 340), (380, 340), (379, 340)]),
    ):
        for with_enemies in (False, True):
            hero = env["SourceHero"]("thorne", "red", 500, 340)
            hero.hp = 1000
            enemies = [Enemy(*pos) for pos in positions] if with_enemies else []
            success = getattr(hero.skills, "cast_" + skill)(enemies, [], [])
            repeat = getattr(hero.skills, "cast_" + skill)(enemies, [], [])
            result["skills"].append(dict(skill=skill, with_enemies=with_enemies,
                positions=[list(p) for p in positions], success=success, repeat=repeat,
                hp=hero.hp, damage=hero.damage, attack_cd=hero.attack_cooldown,
                skill_timer=hero.skill_timer, w_cooldown=hero.w_cooldown,
                e_cooldown=hero.e_cooldown, r_cooldown=hero.r_cooldown,
                active_skill=hero.active_skill or "", active_timer=hero.active_skill_timer,
                viscous=hero._viscous_nose_timer, bristleback=hero._bristleback_timer,
                quill=hero._spray_timer, warpath=hero._warpath_timer,
                enemies=[dict(hp=e.hp, slow=e.slow_amount, slow_timer=e.slow_timer)
                         for e in enemies]))
    for school in ("physical", "magic"):
        for active in (False, True):
            hero = env["SourceHero"]("thorne", "red", 500, 340)
            hero.hp = 1000
            enemy = Enemy(450, 340)
            if active:
                assert hero.skills.cast_w([enemy], [], [])
            before = hero.hp
            hero.take_damage(100, "blue", source=enemy, school=school)
            result["reflect"].append(dict(school=school, active=active,
                before=before, hp=hero.hp, attacker_hp=enemy.hp,
                bristleback=hero._bristleback_timer))
    for mode in ("w", "r", "r_upgrade"):
        hero = env["SourceHero"]("thorne", "red", 500, 340)
        enemy = Enemy(450, 340)
        assert getattr(hero.skills, "cast_" + mode[0])([enemy], [], [])
        total = 240 if mode == "w" else 300
        if mode == "r_upgrade":
            for _ in range(120):
                hero.skills.update_timers([], [], [])
            assert hero.upgrade()
            remaining = total - 120
        else:
            remaining = total
        for _ in range(remaining - 1):
            hero.skills.update_timers([], [], [])
        before = dict(bristleback=hero._bristleback_timer, warpath=hero._warpath_timer,
                      damage=hero.damage, attack_cd=hero.attack_cooldown, level=hero.level)
        hero.skills.update_timers([], [], [])
        result["timers"].append(dict(mode=mode, before=before,
            after=dict(bristleback=hero._bristleback_timer, warpath=hero._warpath_timer,
                       damage=hero.damage, attack_cd=hero.attack_cooldown, level=hero.level)))
    # The actual Hero.respawn source method is not among the Kaizen oracle's
    # compiled subset; attach exactly that method to the source Hero class.
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    hero_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Hero")
    method = next(n for n in hero_class.body if isinstance(n, ast.FunctionDef) and n.name == "respawn")
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 "<source Hero.respawn>", "exec"), env)
    hero = env["SourceHero"]("thorne", "red", 500, 340)
    hero.alive, hero.hp = False, 0
    hero.w_cooldown, hero.e_cooldown, hero.r_cooldown = 123, 77, 321
    hero.skill_timer = 88
    hero.active_skill, hero.active_skill_timer = "r", 60
    env["respawn"](hero)
    result["respawn"] = dict(x=hero.x, y=hero.y, hp=hero.hp, alive=hero.alive,
        w=hero.w_cooldown, e=hero.e_cooldown, r=hero.r_cooldown,
        q=hero.skill_timer, active=hero.active_skill or "", visual=hero.active_skill_timer)
    return result


if __name__ == "__main__":
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "Thorne source drift"
    print("PASS: Thorne source Hero+skills Q/W/E/R, physical/magic reflect and timed upgrade")
