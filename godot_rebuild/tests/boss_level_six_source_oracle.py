"""Execute the actual level-6 boss recipes from hero_skills/_bundle.py.

Batch 8: Kunkka (L6 True Boss), Gravewake / Syrentha / Thalgryn (L6 mini bosses).
All four own registry recipes, so none of them may join the 150-ID
`_fallback_cast` group. Read-only harness shared with boss_level_one/three/four/
five (real SourceHero, real Hero.update clocks, real homing projectile loop, real
respawn, real 1.6x boss upgrade prices).

Recorded per ID, from the source itself:
* line geometry (0 < proj < max, |perp| < width) with exact edges,
* radial geometry centered on the TARGET (Kunkka W/R, Gravewake W) versus on the
  HERO (Gravewake R, Syrentha W/R, Thalgryn R),
* Thalgryn splash around the target and its Waveform dash (min(dist, 200)),
* the dist == 0 early returns (no damage, and Kunkka E skips its own heal),
* rage / defense flags: damage = int(catalog * mult), catalog reset on expiry and
  NO invented mitigation for defense_boost,
* self heals through the source hp property (cap first, then anti-heal),
* gate reach max(skill_range, 140), recast ticks, attacks, respawn, levels 1-15.
"""
import json
import sys
from pathlib import Path

from starter_finish_source_oracle import source_env
from boss_level_one_source_oracle import state, targets, _cast_case

FIXTURE = Path(__file__).parent / "fixtures/boss_level_six_source.json"
IDS = ("kunkka", "gravewake", "syrentha", "thalgryn")
# Explicit target for geometry cases; the gate keeps a valid in-reach target.
AIM = (700, 340)
# Per-slot probe coordinates, each straddling one exact source boundary.
GEOMETRY = {
    "kunkka": {
        # Q line 0<proj<250, |perp|<70, x1.8
        "q": [(700, 340), (500, 340), (501, 340), (400, 340), (749, 340), (750, 340),
              (751, 340), (560, 409), (560, 410), (560, 411), (560, 271), (560, 270)],
        # W target-centered <=120, x1.5 + attack clock 60
        "w": [(700, 340), (500, 340), (579, 340), (580, 340), (581, 340), (819, 340),
              (820, 340), (821, 340), (700, 459), (700, 460), (700, 461)],
        # E line 0<proj<300, |perp|<80, x2.2 + clock 90 + heal 15%
        "e": [(700, 340), (500, 340), (501, 340), (400, 340), (799, 340), (800, 340),
              (801, 340), (560, 419), (560, 420), (560, 421), (560, 281), (560, 280)],
        # R target-centered (else hero) <=200, x3.0 + clock 120 + heal 20%
        "r": [(700, 340), (500, 340), (499, 340), (501, 340), (899, 340), (900, 340),
              (901, 340), (700, 539), (700, 540), (700, 541)],
    },
    "gravewake": {
        # Q line 0<proj<200, |perp|<60, x1.4 + slow 0.5/180
        "q": [(700, 340), (500, 340), (501, 340), (400, 340), (699, 340), (700, 341),
              (701, 340), (560, 399), (560, 400), (560, 401), (560, 281), (560, 280)],
        # W target-centered (else hero) <=120, x1.3 + clock 60
        "w": [(700, 340), (500, 340), (579, 340), (580, 340), (581, 340), (819, 340),
              (820, 340), (821, 340), (700, 459), (700, 460), (700, 461)],
        # E self: defense flag 300 + heal 12%
        "e": [(550, 340), (700, 340)],
        # R radial hero <=200, x2.0 + slow 0.5/180 + heal 10%
        "r": [(550, 340), (699, 340), (700, 340), (701, 340), (301, 340), (300, 340),
              (299, 340), (500, 539), (500, 540), (500, 541)],
    },
    "syrentha": {
        # Q line 0<proj<250, |perp|<70, x1.3 + slow 0.5/180
        "q": [(700, 340), (500, 340), (501, 340), (400, 340), (749, 340), (750, 340),
              (751, 340), (560, 409), (560, 410), (560, 411), (560, 271), (560, 270)],
        # W radial hero <=150, x1.0 + clock 120 + slow 0.7/240
        "w": [(550, 340), (649, 340), (650, 340), (651, 340), (351, 340), (350, 340),
              (349, 340), (500, 489), (500, 490), (500, 491)],
        # E self: rage 360 + damage int(catalog*1.4) + heal 12%
        "e": [(550, 340), (700, 340)],
        # R radial hero <=220, x2.2 + clock 150 + heal 10%
        "r": [(550, 340), (719, 340), (720, 340), (721, 340), (281, 340), (280, 340),
              (279, 340), (500, 559), (500, 560), (500, 561)],
    },
    "thalgryn": {
        # Q line 0<proj<250, |perp|<50, x1.6 then dash min(dist,200)
        "q": [(700, 340), (500, 340), (501, 340), (400, 340), (749, 340), (750, 340),
              (751, 340), (560, 389), (560, 390), (560, 391), (560, 291), (560, 290)],
        # W target x2.0 + splash <=60 around the TARGET x0.7
        "w": [(700, 340), (500, 340), (759, 340), (760, 340), (761, 340), (641, 340),
              (640, 340), (639, 340), (700, 399), (700, 400), (700, 401)],
        # E self: rage 300 + damage int(catalog*1.35) + heal 14%
        "e": [(550, 340), (700, 340)],
        # R radial hero <=200, x2.0 + slow 0.4/180 + heal 10%
        "r": [(550, 340), (699, 340), (700, 340), (701, 340), (301, 340), (300, 340),
              (299, 340), (500, 539), (500, 540), (500, 541)],
    },
}
# Slots whose recipe heals the caster, and the source value the heal derives from.
HEALS = {
    "kunkka": {"e": "max_hp", "r": "max_hp"},
    "gravewake": {"e": "max_hp", "r": "max_hp"},
    "syrentha": {"e": "max_hp", "r": "max_hp"},
    "thalgryn": {"e": "max_hp", "r": "max_hp"},
}
# Slots that set rage_active (damage buff + catalog reset) or defense_boost.
RAGE = {"syrentha": {"e": 360}, "thalgryn": {"e": 300}}
DEFENSE = {"gravewake": {"e": 300}}
# Thalgryn Waveform dash distance cap.
DASH = {"thalgryn": {"q": 200}}
# Target offsets used for the dash cases (axis aligned plus one 3-4-5 diagonal).
DASH_OFFSETS = [(50, 0), (150, 0), (199, 0), (200, 0), (201, 0), (259, 0), (260, 0),
                (120, 90), (0, 150), (0, 0)]
ANTI_HEAL = (0.0, 0.5, 1.0)
HP_MODES = ("partial", "full", "one")
TRACE_TICKS = (1, 2, 29, 30, 59, 60, 89, 90, 119, 120, 149, 150, 179, 180,
               239, 240, 241, 299, 300, 301, 359, 360, 361, 419, 420, 421,
               479, 480, 481)


def _cooldowns(hero):
    return {"q": hero.skill_cooldown_max, "w": hero.w_cooldown_max,
            "e": hero.e_cooldown_max, "r": hero.r_cooldown_max}


def _dash_case(result, env, H, kind, key, offset):
    hero = H(kind, "red", 500, 340)
    hero.hp = 500
    point = (500 + offset[0], 340 + offset[1])
    enemies = targets([point])
    hero.target = enemies[0]
    ok = getattr(hero.skills, "cast_" + key)(enemies, [], [])
    result["dash"].append(dict(hero=kind, key=key, offset=list(offset), ok=ok,
        state=state(hero, enemies)))


def _dead_target_case(result, H, kind, key, coords, dead):
    hero = H(kind, "red", 500, 340)
    hero.hp = 500
    enemies = targets(coords)
    hero.target = enemies[dead]
    enemies[dead].alive = False
    ok = getattr(hero.skills, "cast_" + key)(enemies, [], [])
    repeat = getattr(hero.skills, "cast_" + key)(enemies, [], [])
    result["casts"].append(dict(hero=kind, key=key, positions=coords, target=dead,
        dead=True, ok=ok, repeat=repeat, state=state(hero, enemies)))


def source_fixture(ids=IDS):
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    result = dict(casts=[], traces=[], recasts=[], heals=[], defense=[], dash=[],
                  attacks=[], buffed_attacks=[], respawn=[], catalog={}, levels={})
    for kind in ids:
        h = H(kind, "red", 500, 340)
        recipe = h.skills._SKILL_REGISTRY[kind]
        assert len(recipe) == 4 and all(hasattr(h.skills, m) for m in recipe.values())
        catalog = env["get_all_hero_types"]()[kind]
        result["catalog"][kind] = dict(
            recipe=recipe, damage=catalog["damage"], cost=catalog["cost"],
            visual={key: h.skills._get_visual_duration(key) for key in "qwer"},
            cooldowns=_cooldowns(h), school=h.dmg_school, melee=bool(h.is_melee_hero),
            skill_range=h.skill_range, attack_range=h.range,
            attack_cooldown=h.attack_cooldown, max_hp=h.max_hp,
            skill_damage=h.skill_damage, rage=RAGE.get(kind, {}),
            defense=DEFENSE.get(kind, {}))
        for key in "qwer":
            coords = GEOMETRY[kind][key]
            # Gate + geometry: no enemy, auto-target, explicit target, dead target,
            # retained far target and the exact reach boundary.
            for case, selected in [([], -1), (coords, -1), (coords, 0),
                                   ([(450, 340), (550, 340)], -1),
                                   ([(450, 340), (550, 340)], 1),
                                   ([(900, 340), (550, 340)], 0)]:
                _cast_case(result, H, kind, key, case, selected)
            _dead_target_case(result, H, kind, key, [(540, 340), (600, 340)], 0)
            reach = max(int(h.skill_range), 140)
            for radius in (reach - 1, reach, reach + 1):
                _cast_case(result, H, kind, key, [(500 + radius, 340)], -1)
            # The zero-distance target: source returns early, cooldown still burns.
            zero = H(kind, "red", 500, 340)
            zero.hp = 500
            opponents = targets([(500, 340), (560, 340)])
            zero.target = opponents[0]
            zero_ok = getattr(zero.skills, "cast_" + key)(opponents, [], [])
            zero_repeat = getattr(zero.skills, "cast_" + key)(opponents, [], [])
            result["casts"].append(dict(hero=kind, key=key,
                positions=[[500, 340], [560, 340]], target=0, zero_distance=True,
                ok=zero_ok, repeat=zero_repeat, state=state(zero, opponents)))
            for mode in ("normal", "move_upgrade", "target_dies", "retarget"):
                hero = H(kind, "red", 500, 340)
                hero.hp = 500
                trace_coords = [(550, 340), (600, 340), (590, 340), (610, 340),
                                (580, 340)]
                enemies = targets(trace_coords)
                hero.target = enemies[0]
                enemies[0].attack_timer = 90
                assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
                rows = []
                for tick in range(1, 482):
                    if tick == 2 and mode == "move_upgrade":
                        hero.x += 100
                        enemies[0].x += 200
                        assert hero.upgrade()
                    if tick == 2 and mode == "target_dies":
                        enemies[0].alive = False
                    if tick == 2 and mode == "retarget":
                        hero.target = enemies[1]
                    env["tick_clocks"](hero)
                    hero.skills.update_timers(enemies, [], [])
                    if tick in TRACE_TICKS:
                        rows.append(dict(tick=tick, state=state(hero, enemies)))
                result["traces"].append(dict(hero=kind, key=key, mode=mode,
                    positions=trace_coords, length=481, rows=rows))
            hero = H(kind, "red", 500, 340)
            hero.hp = 500
            enemies = targets([(550, 340)])
            cooldown = _cooldowns(hero)[key]
            assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
            rows = []
            for tick in range(1, cooldown + 3):
                env["tick_clocks"](hero)
                if tick >= cooldown - 1:
                    ok = getattr(hero.skills, "cast_" + key)(enemies, [], [])
                    rows.append(dict(tick=tick, ok=ok, state=state(hero, enemies)))
            result["recasts"].append(dict(hero=kind, key=key, cooldown=cooldown,
                length=cooldown + 2, rows=rows))
        for offset in DASH_OFFSETS:
            for key in sorted(DASH.get(kind, {})):
                _dash_case(result, env, H, kind, key, offset)
        for key in sorted(HEALS[kind]):
            for hp_mode in HP_MODES:
                for anti in ANTI_HEAL:
                    hero = H(kind, "red", 500, 340)
                    enemies = targets([(550, 340)])
                    if hp_mode == "partial":
                        hero.hp = 500
                    elif hp_mode == "full":
                        hero.hp = hero.max_hp
                    else:
                        hero.hp = 1
                    if anti:
                        hero.apply_debuff("anti_heal", anti, 600)
                    before = hero.hp
                    assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
                    result["heals"].append(dict(hero=kind, key=key, hp_mode=hp_mode,
                        anti_heal=anti, source=HEALS[kind][key], before=before,
                        hp=hero.hp, max_hp=hero.max_hp, enemy_hp=enemies[0].hp,
                        damage=hero.damage,
                        anti_heal_amount=hero.anti_heal_amount,
                        anti_heal_timer=hero.anti_heal_timer))
        # No invented mitigation: E flags never reduce incoming damage.
        for school in ("physical", "magic"):
            hero = H(kind, "red", 500, 340)
            hero.hp = 500
            enemies = targets([(550, 340)])
            assert getattr(hero.skills, "cast_e")(enemies, [], [])
            before = hero.hp
            hero.take_damage(100, "blue", school=school)
            result["defense"].append(dict(hero=kind, school=school, before=before,
                hp=hero.hp, damage=hero.damage))
        # Basic attacks: raw catalog path and, for rage heroes, the buffed damage.
        for point in ([560, 340], [620, 340]):
            hero = H(kind, "red", 500, 340)
            enemy = targets([tuple(point)])[0]
            hero.target = enemy
            hero._do_attack()
            # Melee Kunkka/Gravewake (range 70) cannot reach 120px: _do_attack
            # leaves the clock at 0 and nothing is delivered.
            attacked = hero.attack_timer > 0
            rows = []
            for tick in range(24):
                if tick:
                    env["tick_projectiles"](hero)
                    env["tick_clocks"](hero)
                rows.append(dict(tick=tick, hp=enemy.hp, attack_timer=hero.attack_timer,
                    positions=[[p['x'], p['y']] for p in hero.projectiles]))
            result["attacks"].append(dict(hero=kind, target_position=point,
                attacked=attacked, rows=rows))
        for key in sorted(RAGE.get(kind, {})):
            hero = H(kind, "red", 500, 340)
            enemy = targets([(560, 340)])[0]
            assert getattr(hero.skills, "cast_" + key)([enemy], [], [])
            buffed = hero.damage
            hero.target = enemy
            hero._do_attack()
            attacked = hero.attack_timer > 0
            rows = []
            for tick in range(24):
                if tick:
                    env["tick_projectiles"](hero)
                    env["tick_clocks"](hero)
                rows.append(dict(tick=tick, hp=enemy.hp, attack_timer=hero.attack_timer,
                    positions=[[p['x'], p['y']] for p in hero.projectiles]))
            result["buffed_attacks"].append(dict(hero=kind, key=key, damage=buffed,
                target_position=[560, 340], attacked=attacked, rows=rows))
        hero = H(kind, "red", 500, 340)
        enemies = targets([(550, 340)])
        for key in "qwer":
            assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
        hero.attack_timer = 17
        hero.hp, hero.alive = 0, False
        env["respawn"](hero)
        result["respawn"].append(dict(hero=kind, state=state(hero, enemies)))
        sample = H(kind, "red", 500, 340)
        sample.hp = 1
        result["levels"][kind] = []
        for level in range(1, 16):
            result["levels"][kind].append(dict(level=level, hp=sample.hp,
                damage=sample.damage, max_hp=sample.max_hp,
                skill_value=sample.skill_damage, price=sample.upgrade_cost()))
            assert sample.upgrade() == (level < 15)
    return json.loads(json.dumps(result))


if __name__ == "__main__":
    data = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(data, separators=(",", ":")) + "\n")
        print(f"WROTE {FIXTURE} {len(json.dumps(data))} bytes PASS: level-6 real recipes, "
              "line/radial edges, dash, flags, heals, attacks, respawn")
    else:
        assert data == json.loads(FIXTURE.read_text()), "Level-six boss source drift"
        print("PASS: Kunkka/Gravewake/Syrentha/Thalgryn real recipes, line+radial edges, "
              "dash, rage/defense flags, heals, attacks, respawn")
