"""Read-only AST Hero + real GrimjawSkills oracle, empty inventory/audio only.

Uses simple enemy/allied receipts for effects; no pygame/Game imports. Q/R tick
at their actual source modulo intervals; E crit persists across basic attacks.
"""
import json
import sys
from pathlib import Path

from kaizen_source_oracle import build_hero_env
from thorne_source_oracle import Enemy

FIXTURE = Path(__file__).parent / "fixtures/grimjaw_source.json"


class Ally(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.team = "red"
        self.max_hp = 10000
        self.hp = 9990


def snapshot(hero, enemies):
    return dict(hp=hero.hp, damage=hero.damage, attack_timer=hero.attack_timer,
        q=hero.skill_timer, w=hero.w_cooldown, e=hero.e_cooldown, r=hero.r_cooldown,
        active=hero.active_skill or "", visual=hero.active_skill_timer,
        spin=hero._blade_fury_timer, ward=hero._heal_ward_timer,
        crit=hero._crit_buff_timer, slash=hero._omnislash_timer,
        locked=hero._omnislash_target is not None,
        enemies=[u.hp for u in enemies])


def source_fixture():
    env = build_hero_env()
    result = {"casts": [], "traces": {}, "crit_attacks": {}}
    for key, positions in (
        ("q", [(450, 340), (420, 340)]),
        ("w", [(450, 340)]),
        ("e", [(450, 340), (440, 340), (439, 340)]),
        ("r", [(450, 340), (600, 340)]),
    ):
        for with_enemies in (False, True):
            hero = env["SourceHero"]("grimjaw", "red", 500, 340)
            hero.hp = 900
            enemies = [Enemy(*p) for p in positions] if with_enemies else []
            success = getattr(hero.skills, "cast_" + key)(enemies, [], [])
            repeat = getattr(hero.skills, "cast_" + key)(enemies, [], [])
            result["casts"].append(dict(key=key, positions=[list(p) for p in positions],
                with_enemies=with_enemies, success=success, repeat=repeat,
                state=snapshot(hero, enemies)))
    # Exercise tick ordering at exact modulo boundaries, including final tick 0.
    for key, last, moments in (("q", 180, (1, 15, 16, 165, 180)),
                               ("r", 90, (1, 2, 8, 90))):
        hero = env["SourceHero"]("grimjaw", "red", 500, 340)
        enemies = [Enemy(450, 340), Enemy(600, 340)]
        assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
        states = []
        for tick in range(1, last + 1):
            hero.skills.update_timers(enemies, [], [])
            if tick in moments:
                states.append(dict(tick=tick, state=snapshot(hero, enemies)))
        result["traces"][key] = states
    # Ward is cast without an enemy, heals caster + allies at fixed ward point.
    hero = env["SourceHero"]("grimjaw", "red", 500, 340)
    hero.hp = 900
    near, far = Ally(540, 340), Ally(620, 340)
    assert hero.skills.cast_w([near, far], [], [])
    states = []
    for tick in range(1, 361):
        if tick == 2:
            hero.x = 610  # hero moves away; ward stays at cast point
        hero.skills.update_timers([near, far], [], [])
        if tick in (1, 2, 359, 360):
            states.append(dict(tick=tick, hp=hero.hp, near=near.hp, far=far.hp,
                               ward=hero._heal_ward_timer, ward_pos=list(hero._heal_ward_pos)))
    result["traces"]["w"] = states
    hero = env["SourceHero"]("grimjaw", "red", 500, 340)
    enemy = Enemy(450, 340)
    assert hero.skills.cast_e([enemy], [], [])
    hero.target = enemy
    before = snapshot(hero, [enemy])
    hero._do_attack()
    first = snapshot(hero, [enemy])
    hero.attack_timer = 0
    hero._do_attack()
    second = snapshot(hero, [enemy])
    for _ in range(300):
        hero.skills.update_timers([enemy], [], [])
    hero.attack_timer = 0
    hero._do_attack()
    after = snapshot(hero, [enemy])
    result["crit_attacks"] = dict(before=before, first=first, second=second, after=after)
    return result


if __name__ == "__main__":
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "Grimjaw source drift"
    print("PASS: source Grimjaw Q/W/E/R, timed spin/ward/slash and repeated crit")
