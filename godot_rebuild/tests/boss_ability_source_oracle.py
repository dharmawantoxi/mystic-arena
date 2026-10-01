"""AST oracle for the active level-1 Boss smart abilities.

The fixture executes the original Boss smart-AI and cast methods from
bosses/base_boss.py. It covers the first smart-AI slice (Gornak, Morgath,
Drakar, Abaddon, Alchemist, Malzareth, Akashari, Vorenmarr, Nyxarath and
Thalgryn), plus the source generic _use_ability fallback.
It does not execute entrance/enrage or render hooks; those are separate
sub-layers.
"""
import ast
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIXTURE = Path(__file__).parent / "fixtures/boss_ability_source.json"

from bosses.boss_data import get_all_boss_types  # noqa: E402

SOURCE_STATS = get_all_boss_types()


class Target:
    def __init__(self, x, y, hp=10000, name="target", max_hp=None):
        self.x = float(x)
        self.y = float(y)
        self.hp = int(hp)
        self.max_hp = int(hp if max_hp is None else max_hp)
        self.name = name
        self.alive = True
        self.team = "blue"
        self.speed = 1.0
        self.attack_timer = 0
        self.hits = []
        self.slows = []

    def take_damage(self, damage, *_args, **_kwargs):
        damage = int(damage)
        self.hits.append(damage)
        self.hp = max(0, self.hp - damage)
        if self.hp <= 0:
            self.alive = False

    def apply_slow(self, amount, duration):
        self.slows.append([float(amount), int(duration)])


def source_class():
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    wanted = {
        "_use_ability",
        "_smart_ai_gornak",
        "_cast_q_mana_break",
        "_cast_w_blink",
        "_cast_e_counterspell",
        "_cast_r_mana_void",
        "_smart_ai_morgath",
        "_cast_q_spark_wraith",
        "_cast_w_flux",
        "_cast_e_magnetic_field",
        "_cast_r_tempest_double",
        "_smart_ai_drakar",
        "_cast_q_battle_hunger",
        "_cast_w_counter_helix",
        "_cast_e_berserkers_call",
        "_cast_r_culling_blade",
        "_smart_ai_abaddon",
        "_cast_q_mist_coil",
        "_smart_ai_alchemist",
        "_cast_q_acid_spray",
        "_cast_w_unstable_concoction",
        "_cast_e_chemical_rage",
        "_cast_r_greevils_greed",
        "_smart_ai_malzareth",
        "_malzareth_q",
        "_malzareth_w",
        "_malzareth_e",
        "_malzareth_r",
        "_smart_ai_akashari",
        "_akashari_q",
        "_akashari_w",
        "_akashari_e",
        "_akashari_r",
        "_smart_ai_vorenmarr",
        "_vorenmarr_q",
        "_vorenmarr_w",
        "_vorenmarr_e",
        "_vorenmarr_r",
        "_smart_ai_nyxarath",
        "_nyxarath_q",
        "_nyxarath_w",
        "_nyxarath_e",
        "_nyxarath_r",
        "_smart_ai_thalgryn",
        "_thalgryn_q",
        "_thalgryn_w",
        "_thalgryn_e",
        "_thalgryn_r",
        "_cast_w_aphotic_shield",
        "_cast_e_darkness_gale",
        "_cast_r_death_sever",
    }
    body = [node for node in original.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    assert {node.name for node in body} == wanted, "Boss ability methods drifted"
    cls = ast.ClassDef(name="SourceBossAbility", bases=[], keywords=[], body=body, decorator_list=[])
    env = {"math": math}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "<source boss abilities>", "exec"), env)
    result = env["SourceBossAbility"]

    def stats(self):
        return dict(SOURCE_STATS[self.boss_type])

    result._get_boss_stats = stats
    result._shake_screen = lambda self, _intensity: None
    return result


def make_boss(cls, kind, hp_ratio=1.0, target=None):
    boss = cls()
    source = SOURCE_STATS[kind]
    boss.boss_type = kind
    boss.boss_class = source["boss_class"]
    boss.team = "red"
    boss.x = 0.0
    boss.y = 0.0
    boss.max_hp = int(source["hp"])
    boss.hp = int(boss.max_hp * hp_ratio)
    boss.damage = int(source["damage"])
    boss.ability_cooldown_max = int(source.get("ability_cooldown", 0))
    boss.ability_damage = int(source.get("ability_damage", 0))
    boss.ability_range = int(source.get("ability_range", 0))
    boss.ability2_timer = 0
    boss.ability_timer = 0
    boss.ability_active = False
    boss.ability_active_timer = 0
    boss.target = target
    boss.is_enraged = False
    boss.dmg_scaling_mult = 1.0
    boss.skill_down_timer = 0
    boss.skill_down_amount = 0.0
    return boss


def row(boss, targets):
    return {
        "type": boss.boss_type,
        "skill": getattr(boss, "active_skill", None),
        "active_skill_timer": int(getattr(boss, "active_skill_timer", 0)),
        "q_timer": int(getattr(boss, "q_timer", 0)),
        "w_timer": int(getattr(boss, "w_timer", 0)),
        "e_timer": int(getattr(boss, "e_timer", 0)),
        "r_timer": int(getattr(boss, "r_timer", 0)),
        "ability_timer": int(getattr(boss, "ability_timer", 0)),
        "ability_active": bool(getattr(boss, "ability_active", False)),
        "hp": int(boss.hp),
        "damage": int(boss.damage),
        "x": float(boss.x),
        "y": float(boss.y),
        "rage_active": bool(getattr(boss, "rage_active", False)),
        "rage_timer": int(getattr(boss, "rage_timer", 0)),
        "necro_buff_active": bool(getattr(boss, "necro_buff_active", False)),
        "necro_buff_timer": int(getattr(boss, "necro_buff_timer", 0)),
        "presence_active": bool(getattr(boss, "presence_active", False)),
        "presence_timer": int(getattr(boss, "presence_timer", 0)),
        "morph_buff_active": bool(getattr(boss, "morph_buff_active", False)),
        "morph_buff_timer": int(getattr(boss, "morph_buff_timer", 0)),
        "defense_boost": bool(getattr(boss, "defense_boost", False)),
        "defense_timer": int(getattr(boss, "defense_timer", 0)),
        "flux_active_timer": int(getattr(boss, "flux_active_timer", 0)),
        "clones_active_timer": int(getattr(boss, "clones_active_timer", 0)),
        "targets": [
            {
                "name": target.name,
                "hp": int(target.hp),
                "alive": bool(target.alive),
                "hits": list(target.hits),
                "attack_timer": int(target.attack_timer),
                "slows": list(target.slows),
            }
            for target in targets
        ],
    }


def smart_case(cls, kind, label, hp_ratio, target_specs, distance, method):
    targets = [
        Target(*spec[:4], max_hp=(spec[4] if len(spec) > 4 else None))
        for spec in target_specs
    ]
    boss = make_boss(cls, kind, hp_ratio, targets[0] if targets else None)
    getattr(boss, method)(targets, distance)
    return {"label": label, "result": row(boss, targets)}


def persistent_morgath(cls):
    target = Target(400, 0, name="flux")
    boss = make_boss(cls, "morgath", target=target)
    boss.q_timer = 999
    boss.w_timer = 999
    boss.e_timer = 999
    boss.r_timer = 999
    boss.active_skill_timer = 0
    boss.flux_target = target
    boss.flux_active_timer = 31
    boss.clones_active_timer = 0
    boss._smart_ai_morgath([target], 400)
    return {"label": "morgath_flux_tick", "result": row(boss, [target])}


def generic_case(cls):
    targets = [Target(20, 0, name="near"), Target(100, 0, name="far")]
    boss = make_boss(cls, "abaddon", target=targets[0])
    boss.ability_cooldown_max = 180
    boss.ability_damage = 270
    boss.ability_range = 50
    boss.ability_timer = 0
    boss._use_ability(targets)
    return {"label": "generic_ability", "result": row(boss, targets)}


def source_fixture():
    cls = source_class()
    cases = [
        smart_case(cls, "gornak", "gornak_q", 1.0, [(80, 0, 10000, "target")], 80, "_smart_ai_gornak"),
        smart_case(cls, "gornak", "gornak_blink", 1.0, [(200, 0, 10000, "target")], 200, "_smart_ai_gornak"),
        smart_case(
            cls,
            "gornak",
            "gornak_counterspell",
            1.0,
            [(20, 0, 10000, "a"), (40, 0, 10000, "b"), (60, 0, 10000, "c")],
            20,
            "_smart_ai_gornak",
        ),
        smart_case(cls, "gornak", "gornak_mana_void", 0.3, [(20, 0, 10000, "target")], 20, "_smart_ai_gornak"),
        smart_case(cls, "morgath", "morgath_spark", 1.0, [(330, 0, 10000, "target")], 330, "_smart_ai_morgath"),
        smart_case(cls, "morgath", "morgath_flux", 1.0, [(100, 0, 10000, "target")], 100, "_smart_ai_morgath"),
        smart_case(
            cls,
            "morgath",
            "morgath_field",
            1.0,
            [(20, 0, 10000, "a"), (30, 0, 10000, "b")],
            20,
            "_smart_ai_morgath",
        ),
        smart_case(cls, "morgath", "morgath_clones", 0.4, [(20, 0, 10000, "target")], 20, "_smart_ai_morgath"),
        persistent_morgath(cls),
        smart_case(cls, "drakar", "drakar_rage", 0.3, [(200, 0, 10000, "target")], 200, "_smart_ai_drakar"),
        smart_case(
            cls,
            "drakar",
            "drakar_counter_helix",
            1.0,
            [(20, 0, 10000, "a"), (30, 0, 10000, "b")],
            20,
            "_smart_ai_drakar",
        ),
        smart_case(cls, "drakar", "drakar_call", 0.5, [(200, 0, 10000, "target")], 200, "_smart_ai_drakar"),
        smart_case(cls, "drakar", "drakar_culling", 1.0, [(50, 0, 1000, "target", 10000)], 50, "_smart_ai_drakar"),
        smart_case(cls, "abaddon", "abaddon_coil", 1.0, [(100, 0, 10000, "target")], 100, "_smart_ai_abaddon"),
        smart_case(cls, "abaddon", "abaddon_shield", 0.2, [(20, 0, 10000, "target")], 20, "_smart_ai_abaddon"),
        smart_case(cls, "abaddon", "abaddon_gale", 1.0, [(200, 0, 10000, "target")], 200, "_smart_ai_abaddon"),
        smart_case(
            cls,
            "abaddon",
            "abaddon_death_sever",
            1.0,
            [(20, 0, 10000, "a"), (30, 0, 10000, "b"), (40, 0, 10000, "c")],
            20,
            "_smart_ai_abaddon",
        ),
        smart_case(
            cls,
            "alchemist",
            "alchemist_greevils_greed",
            0.3,
            [(20, 0, 10000, "a"), (40, 0, 10000, "b"), (60, 0, 10000, "c")],
            20,
            "_smart_ai_alchemist",
        ),
        smart_case(
            cls,
            "alchemist",
            "alchemist_chemical_rage",
            0.5,
            [(300, 0, 10000, "target")],
            300,
            "_smart_ai_alchemist",
        ),
        smart_case(
            cls,
            "alchemist",
            "alchemist_unstable_concoction",
            1.0,
            [(100, 0, 10000, "a"), (150, 0, 10000, "b")],
            100,
            "_smart_ai_alchemist",
        ),
        smart_case(
            cls,
            "alchemist",
            "alchemist_acid_spray",
            1.0,
            [(100, 0, 10000, "target")],
            100,
            "_smart_ai_alchemist",
        ),
        smart_case(
            cls,
            "malzareth",
            "malzareth_death_pulse",
            0.3,
            [(20, 0, 10000, "a"), (40, 0, 10000, "b")],
            20,
            "_smart_ai_malzareth",
        ),
        smart_case(
            cls,
            "malzareth",
            "malzareth_shadow_word",
            1.0,
            [(100, 0, 10000, "target"), (140, 0, 10000, "splash")],
            100,
            "_smart_ai_malzareth",
        ),
        smart_case(
            cls,
            "malzareth",
            "malzareth_nether_blast",
            1.0,
            [(100, 0, 10000, "target")],
            100,
            "_smart_ai_malzareth",
        ),
        smart_case(
            cls,
            "malzareth",
            "malzareth_void",
            1.0,
            [(270, 0, 10000, "target")],
            270,
            "_smart_ai_malzareth",
        ),
        smart_case(
            cls,
            "akashari",
            "akashari_sonic_scream",
            0.3,
            [(20, 0, 10000, "a"), (40, 0, 10000, "b")],
            20,
            "_smart_ai_akashari",
        ),
        smart_case(
            cls,
            "akashari",
            "akashari_scream_of_pain",
            1.0,
            [(100, 0, 10000, "a"), (120, 0, 10000, "b"), (140, 0, 10000, "c")],
            100,
            "_smart_ai_akashari",
        ),
        smart_case(
            cls,
            "akashari",
            "akashari_shadow_strike",
            0.5,
            [(200, 0, 10000, "target"), (220, 0, 10000, "near")],
            200,
            "_smart_ai_akashari",
        ),
        smart_case(
            cls,
            "akashari",
            "akashari_scream",
            1.0,
            [(270, 0, 10000, "target")],
            270,
            "_smart_ai_akashari",
        ),
        smart_case(
            cls,
            "vorenmarr",
            "vorenmarr_chaos_storm",
            0.3,
            [(20, 0, 10000, "a"), (40, 0, 10000, "b")],
            20,
            "_smart_ai_vorenmarr",
        ),
        smart_case(
            cls,
            "vorenmarr",
            "vorenmarr_shadow_word",
            0.5,
            [(300, 0, 10000, "target")],
            300,
            "_smart_ai_vorenmarr",
        ),
        smart_case(
            cls,
            "vorenmarr",
            "vorenmarr_rain_of_fire",
            1.0,
            [(100, 0, 10000, "target"), (150, 0, 10000, "near")],
            100,
            "_smart_ai_vorenmarr",
        ),
        smart_case(
            cls,
            "vorenmarr",
            "vorenmarr_chaos_bolt",
            1.0,
            [(270, 0, 10000, "target")],
            270,
            "_smart_ai_vorenmarr",
        ),
        smart_case(
            cls,
            "nyxarath",
            "nyxarath_requiem",
            0.3,
            [(20, 0, 10000, "a"), (40, 0, 10000, "b")],
            20,
            "_smart_ai_nyxarath",
        ),
        smart_case(
            cls,
            "nyxarath",
            "nyxarath_presence",
            0.5,
            [(300, 0, 10000, "target")],
            300,
            "_smart_ai_nyxarath",
        ),
        smart_case(
            cls,
            "nyxarath",
            "nyxarath_necromastery",
            1.0,
            [(20, 0, 10000, "a"), (40, 0, 10000, "b")],
            20,
            "_smart_ai_nyxarath",
        ),
        smart_case(
            cls,
            "nyxarath",
            "nyxarath_shadowraze",
            1.0,
            [(100, 0, 10000, "target")],
            100,
            "_smart_ai_nyxarath",
        ),
        smart_case(
            cls,
            "thalgryn",
            "thalgryn_replicate",
            0.3,
            [(20, 0, 10000, "a"), (40, 0, 10000, "b")],
            20,
            "_smart_ai_thalgryn",
        ),
        smart_case(
            cls,
            "thalgryn",
            "thalgryn_morph",
            0.5,
            [(300, 0, 10000, "target")],
            300,
            "_smart_ai_thalgryn",
        ),
        smart_case(
            cls,
            "thalgryn",
            "thalgryn_waveform",
            1.0,
            [(300, 0, 10000, "target"), (100, 0, 10000, "path")],
            300,
            "_smart_ai_thalgryn",
        ),
        smart_case(
            cls,
            "thalgryn",
            "thalgryn_adaptive_strike",
            1.0,
            [(100, 0, 10000, "target"), (150, 0, 10000, "splash")],
            100,
            "_smart_ai_thalgryn",
        ),
        generic_case(cls),
    ]
    return {"cases": cases}


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %d source ability cases" % len(actual["cases"]))
    else:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        assert actual == expected, "Boss ability source drift"
        print("PASS: Boss ability — %d source cases" % len(actual["cases"]))


if __name__ == "__main__":
    main()
