"""Execute original Kaizen/Hero init/level/attack/Q-combo methods, without pygame.

Fase Kaizen-1 = inti combat hero + kombo Q. Kode yang dieksekusi adalah
100% kode game asli (via AST dari berkas sumber, tanpa modifikasi):

- _core.get_all_hero_types (KEDUA definisi, sesuai urutan berkas) +
  _default_hero_unlock_cost + literal HERO_TYPES/HERO_LEVELS — katalog
  final pasca hero_balance.apply_to_catalog (angka yang dipakai game).
- Hero.__init__/skill_damage/attack_cooldown/_apply_level_stats/upgrade/
  upgrade_cost/_do_attack/take_damage/_eff_attack_cd/_eff_attack_range/
  _get_all_enemies (AST dari _entity.py).
- hero_skills ASLI (KaizenSkills + BaseSkill) — impor nyata dengan stub.
- Tower.take_damage + credit_hero_damage + _is_physical_hit (korban menara).

Stub (terdokumentasi; nilai ekuivalen inventory kosong — diverifikasi
terhadap hero_items.py: _sum_stat->0, timer->0, has()->False):
- hero_items.HeroItemInventory -> FakeInventory (cabang `inv is not None`
  tetap hidup dengan nilai kosong, persis seperti hero tanpa item).
- sound_manager.SoundManager -> play() no-op.
- settings -> HERO_TYPES/HERO_LEVELS literal nyata dari _core.py
  (di game, settings adalah alias runtime untuk global _core).

Cermin 2-baris (Hero.update TIDAK diport — bukan metode utuh):
attack_timer/skill_timer/w/e/r_cooldown/active_skill_timer semuanya
`if t > 0: t -= 1` (_entity.py:3809,3945-3959). Fase Kaizen-1 tidak
memport update/AI/gerakan/proyektil/W/E/R/item/shop/respawn.
"""
import ast
import json
import math
import random
import sys
from pathlib import Path
from types import ModuleType

from cannon_source_oracle import build_env, make_victim
from structure_source_oracle import ROOT

sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/kaizen_source.json"

CORE_LITERALS = (
    "HERO_TYPES", "HERO_LEVELS", "BLUE_BASE_X", "BLUE_BASE_Y",
    "RED_BASE_X", "RED_BASE_Y", "MAX_HERO_LEVEL",
    "STARTER_HERO_UNLOCK_COST", "MINI_BOSS_HERO_UNLOCK_COST",
    "TRUE_BOSS_HERO_UNLOCK_COST",
)

HERO_METHODS = {
    "__init__", "skill_damage", "attack_cooldown", "_recalc_item_stats",
    "_apply_level_stats", "upgrade", "upgrade_cost", "_do_attack",
    "take_damage", "_eff_attack_cd", "_eff_attack_range",
    "_get_all_enemies",
}


class FakeInventory:
    """Pengganti HeroItemInventory dengan nilai inventory kosong.

    Setiap nilai di bawah sama dengan yang dikembalikan inventory
    kosong asli (i.e. hero tanpa item): jumlah stat 0, timer 0,
    has() False, roll_crit (False, 1.0), AS mult 1.0.
    """

    def __init__(self, hero):
        self.hero = hero
        self.rend_target = None
        self.aura_guard_block = 0

    def get_max_hp(self):
        return self.hero.max_hp

    def get_bonus_damage(self):
        return 0

    def get_attack_speed_mult(self):
        return 1.0

    def get_range_bonus(self):
        return 0

    def get_rend_crit(self):
        return None

    def roll_crit(self, rng=None):
        return (False, 1.0)

    def is_veiled(self):
        return False

    def get_lifesteal_pct(self):
        return 0

    def get_cooldown_reduction(self):
        return 0

    def get_spell_vamp(self):
        return 0

    def get_skill_amp(self):
        return 0.0

    def get_move_speed_pct(self):
        return 0

    def get_evasion(self):
        return 0.0

    def get_armor(self):
        return 0

    def get_block(self):
        return None

    def has_true_strike(self):
        return False

    def clear_on_death(self):
        return False

    def has(self, item):
        return False

    def on_basic_attack_hit(self, target, damage, all_units=None):
        return None

    def on_ranged_attack_hit(self, target, damage, all_units=None):
        return None

    def notify_damage_taken(self, rng=None, damage=0, source=None):
        return None


class _FakeSoundManager:
    def play(self, *args, **kwargs):
        return None


def _install_stubs():
    """Pasang stub modul + kembalikan literal _core."""
    core = ast.parse((ROOT / "_core.py").read_text())
    literals = {}
    for node in core.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Name)
                        and target.id in CORE_LITERALS):
                    literals[target.id] = ast.literal_eval(node.value)
    missing = [k for k in CORE_LITERALS if k not in literals]
    assert not missing, f"literal _core hilang: {missing}"

    settings_mod = ModuleType("settings")
    settings_mod.HERO_TYPES = literals["HERO_TYPES"]
    settings_mod.HERO_LEVELS = literals["HERO_LEVELS"]
    sys.modules["settings"] = settings_mod

    sound_mod = ModuleType("sound_manager")
    sound_mod.SoundManager = _FakeSoundManager
    sys.modules["sound_manager"] = sound_mod

    items_mod = ModuleType("hero_items")
    items_mod.HeroItemInventory = FakeInventory
    sys.modules["hero_items"] = items_mod
    return literals


def _exec_catalog(literals):
    """Eksekusi get_all_hero_types asli (dua definisi + alias)."""
    core = ast.parse((ROOT / "_core.py").read_text())
    defs = [n for n in core.body
            if isinstance(n, ast.FunctionDef)
            and n.name == "get_all_hero_types"]
    assert len(defs) == 2, "harus ada 2 definisi get_all_hero_types"
    alias = [n for n in core.body
             if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name)
                     and t.id == "_original_get_all_hero_types_shop_prices"
                     for t in n.targets)]
    assert len(alias) == 1, "alias katalog tidak ketemu"
    cost_consts = [n for n in core.body
                   if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name)
                           and t.id in (
                               "STARTER_HERO_UNLOCK_COST",
                               "MINI_BOSS_HERO_UNLOCK_COST",
                               "TRUE_BOSS_HERO_UNLOCK_COST")
                           for t in n.targets)]
    assert len(cost_consts) == 3, "konstanta harga hero tidak lengkap"
    cost_fn = next(n for n in core.body
                   if isinstance(n, ast.FunctionDef)
                   and n.name == "_default_hero_unlock_cost")
    namespace = {"HERO_TYPES": literals["HERO_TYPES"]}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cost_fn], type_ignores=[])),
                 "_core", "exec"), namespace)
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[defs[0], alias[0]] + cost_consts + [defs[1]],
        type_ignores=[])), "_core", "exec"), namespace)
    return namespace["get_all_hero_types"]


def build_hero_env():
    """Lingkungan eksekusi: basis cannon + katalog + Hero + skill."""
    literals = _install_stubs()
    import hero_archetypes
    import hero_balance
    import hero_skills  # noqa: F401 — impor nyata, dipakai Hero.__init__

    env = build_env()
    env["math"] = math
    env["random"] = random
    env["get_all_hero_types"] = _exec_catalog(literals)
    env["hero_archetypes"] = hero_archetypes
    env["hero_balance"] = hero_balance
    for key in ("BLUE_BASE_X", "BLUE_BASE_Y", "RED_BASE_X", "RED_BASE_Y",
                "MAX_HERO_LEVEL", "HERO_LEVELS"):
        env[key] = literals[key]

    tree = ast.parse((ROOT / "_entity.py").read_text())
    hero_node = next(n for n in tree.body
                     if isinstance(n, ast.ClassDef) and n.name == "Hero")
    methods = [n for n in hero_node.body
               if isinstance(n, ast.FunctionDef) and n.name in HERO_METHODS]
    found = {n.name for n in methods}
    assert found == HERO_METHODS, f"metode Hero kurang: {HERO_METHODS - found}"
    cls = ast.ClassDef(name="SourceHero", bases=[
        ast.Name(id="SourceDebuffs", ctx=ast.Load())],
        keywords=[], body=methods, decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "_entity", "exec"), env)

    helpers = {}
    for name in ("credit_hero_damage", "_is_physical_hit"):
        node = next(n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                     "_entity", "exec"), helpers)
    env.update(helpers)

    tower_node = next(n for n in tree.body
                      if isinstance(n, ast.ClassDef) and n.name == "Tower")
    tower_take = next(n for n in tower_node.body
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "take_damage")
    take_ns = dict(env)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[tower_take], type_ignores=[])),
                 "_entity", "exec"), take_ns)
    env["SourceTower"].take_damage = take_ns["take_damage"]
    return env


def fresh_hero(env, x=500.0, y=340.0):
    hero = env["SourceHero"].__new__(env["SourceHero"])
    hero.__init__("kaizen", "blue")
    assert type(hero.skills).__name__ == "KaizenSkills", \
        f"handler salah: {type(hero.skills).__name__}"
    hero.x, hero.y = x, y
    return hero


def victim_summary(victim):
    return {
        "id": victim.id,
        "hp": victim.hp,
        "alive": victim.alive,
        "calls": [dict(damage=c["damage"], from_team=c["from_team"],
                       damage_type=c["damage_type"],
                       hp_before=c["hp_before"], hp_after=c["hp_after"],
                       alive_after=c["alive_after"])
                  for c in victim.calls],
    }


def source_fixture():
    env = build_hero_env()
    data = {}

    # ── Identitas pasca-__init__ ─────────────────────────────
    hero = fresh_hero(env)
    catalog = env["get_all_hero_types"]()["kaizen"]
    data["hero"] = {
        "hero_type": hero.hero_type,
        "name": hero.name,
        "title": hero.title,
        "role": hero.role,
        "catalog_cost": catalog["cost"],
        "catalog_unlock_cost": catalog["unlock_cost"],
        "level": hero.level,
        "hp": hero.hp,
        "max_hp": hero.max_hp,
        "damage": hero.damage,
        "speed": hero.speed,
        "range": hero.range,
        "attack_cd_base": hero._base_attack_cd,
        "attack_cd_prop": hero.attack_cooldown,
        "skill_damage": hero.skill_damage,
        "skill_cooldown_max": hero.skill_cooldown_max,
        "skill_range": hero.skill_data["skill_range"],
        "dmg_school": hero.dmg_school,
        "is_melee_hero": hero.is_melee_hero,
        "hunt_range": hero.hunt_range,
        "aggro_range": hero.aggro_range,
        "radius": hero.radius,
        "facing": hero.facing,
        "spawn": [hero.x if hero.x == 500.0 else hero.x, hero.y],
        "skills_handler": type(hero.skills).__module__ + "." +
                          type(hero.skills).__name__,
        "q_state": [hero._q_stack, hero._q_reset_timer, hero._is_dashing,
                    hero._dash_timer, hero._wind_wall_timer,
                    hero._ulti_active, hero._ulti_timer],
    }
    spawned = env["SourceHero"].__new__(env["SourceHero"])
    spawned.__init__("kaizen", "blue")
    data["hero"]["spawn_default"] = [spawned.x, spawned.y]

    # ── Level 1..15 via upgrade() asli ───────────────────────
    lv = fresh_hero(env)
    lv.hp = 1  # kunci perilaku HP saat naik level (tidak heal)
    levels = []
    for expected in range(1, 16):
        assert lv.level == expected
        row = {"level": lv.level, "damage": lv.damage,
               "skill_damage": lv.skill_damage, "max_hp": lv.max_hp,
               "hp": lv.hp, "upgrade_cost": lv.upgrade_cost()}
        if expected < 15:
            assert lv.upgrade() is True
            row["accepted"] = True
            row["hp_after"] = lv.hp
        else:
            assert lv.upgrade() is False
            row["accepted"] = False
        levels.append(row)
    data["levels"] = levels

    # ── Property skill_damage + skill_down ───────────────────
    # Sumber memakai field gaya minion (skill_down_amount/timer);
    # TIDAK ada API apply (Hero.take_damage tidak menerapkan skill_down).
    sk = fresh_hero(env)
    base_skill = sk.skill_damage
    skill_cases = {"none": base_skill}
    for amount in (0.2, 0.5, 1.0):
        sk2 = fresh_hero(env)
        sk2.skill_down_amount = amount
        sk2.skill_down_timer = 60
        skill_cases[str(amount)] = sk2.skill_damage
    data["skill_prop"] = {"base": base_skill, "cases": skill_cases}

    # ── Cooldown/range efektif ───────────────────────────────
    ef = fresh_hero(env)
    eff_cases = {"none": ef._eff_attack_cd(ef._base_attack_cd)}
    for amount in (0.15, 0.4, 1.0):
        ef2 = fresh_hero(env)
        ef2.apply_debuff("atk_slow", amount, 60)
        assert ef2.atk_slow_amount == amount
        eff_cases[f"slow_{amount}"] = ef2._eff_attack_cd(
            ef2._base_attack_cd)
    ef3 = fresh_hero(env)
    ef3.stun_timer = 30
    eff_cases["stunned"] = ef3._eff_attack_cd(ef3._base_attack_cd)
    data["eff"] = {"attack_cd": eff_cases,
                   "attack_range": ef._eff_attack_range()}

    # ── Basic attack melee (_do_attack memakai self.target) ──
    atk = fresh_hero(env)
    target = make_victim(env, "t1", 560.0, 340.0, hp=100000)
    # magic_resist 0.5: damage penuh => sekolah physical (kunci perilaku).
    target.magic_resist = 0.5
    atk.target = target
    atk._do_attack()
    basic = {"hit": victim_summary(target),
             "attack_timer": atk.attack_timer,
             "facing": atk.facing,
             "seq": atk._basic_attack_seq,
             "attack_facing": atk._attack_facing}
    atk._do_attack()  # timer aktif -> no-op
    basic["blocked_calls"] = len(target.calls)
    basic["blocked_timer"] = atk.attack_timer
    far = fresh_hero(env)
    oob = make_victim(env, "t2", 571.0, 340.0, hp=100000)
    far.target = oob
    far._do_attack()
    basic["out_of_range_calls"] = len(oob.calls)
    basic["out_of_range_timer"] = far.attack_timer
    dead_t = make_victim(env, "t3", 560.0, 340.0, hp=100000)
    dead_t.alive = False
    far.target = dead_t
    far._do_attack()
    basic["dead_target_calls"] = len(dead_t.calls)
    left = fresh_hero(env)
    vl = make_victim(env, "t4", 440.0, 340.0, hp=100000)
    left.target = vl
    left._do_attack()
    basic["facing_left"] = left.facing
    basic["facing_left_calls"] = len(vl.calls)
    above = fresh_hero(env)
    va = make_victim(env, "t5", 500.0, 300.0, hp=100000)
    above.target = va
    above._do_attack()
    basic["facing_above"] = above.facing  # dx==0 -> facing tidak berubah
    basic["facing_above_calls"] = len(va.calls)
    data["basic"] = basic

    # ── Q1 Steel Wind ────────────────────────────────────────
    def q_lineup(hp=100000):
        units = [
            make_victim(env, "e1", 560.0, 340.0, hp=hp),
            make_victim(env, "e2", 600.0, 340.0, hp=hp),
            make_victim(env, "e3", 610.0, 340.0, hp=hp),
            make_victim(env, "e4", 616.0, 340.0, hp=hp),
        ]
        dead = make_victim(env, "dead", 540.0, 340.0, hp=hp)
        dead.alive = False
        units.append(dead)
        ally = make_victim(env, "ally", 560.0, 300.0, team="blue", hp=hp)
        units.append(ally)
        tower = env["SourceTower"](560.0, 400.0, "red")
        return units, tower

    q1 = fresh_hero(env)
    units, tower = q_lineup()
    tower_pre = {"hp": tower.hp, "shield": tower.shield,
                 "armor": tower.armor, "magic_resist": tower.magic_resist}
    assert q1.skills.cast_q(units, [tower], []) is True
    data["q1"] = {
        "result": True,
        "skill_timer": q1.skill_timer,
        "q_stack": q1._q_stack,
        "q_reset_timer": q1._q_reset_timer,
        "active_skill": q1.active_skill,
        "active_skill_timer": q1.active_skill_timer,
        "target_id": q1.target.id if q1.target else None,
        "pos": [q1.x, q1.y],
        "tower_pre": tower_pre,
        "tower_hp": tower.hp,
        "tower_shield": tower.shield,
        "victims": [victim_summary(v) for v in units],
    }
    weak_units, _weak_tower = q_lineup()
    weak = make_victim(env, "weak", 550.0, 340.0, hp=30)
    weak_units.append(weak)
    q1b = fresh_hero(env)
    assert q1b.skills.cast_q(weak_units, [], []) is True
    data["q1_kill"] = {"alive": weak.alive, "hp": weak.hp,
                       "calls": len(weak.calls)}

    # ── Q1 gagal: tanpa target ───────────────────────────────
    fz = fresh_hero(env)
    far_only = [make_victim(env, "far", 616.0, 340.0, hp=100000)]
    assert fz.skills.cast_q(far_only, [], []) is False
    data["q1_fizzle"] = {"result": False, "skill_timer": fz.skill_timer,
                         "q_stack": fz._q_stack, "calls": len(far_only[0].calls)}

    # ── Q1 gagal: cooldown aktif ─────────────────────────────
    cd = fresh_hero(env)
    cd.skill_timer = 10
    cdu = [make_victim(env, "c1", 560.0, 340.0, hp=100000)]
    assert cd.skills.cast_q(cdu, [], []) is False
    data["q1_cooldown"] = {"result": False, "skill_timer": cd.skill_timer,
                           "calls": len(cdu[0].calls)}

    # ── Q2 Dash Strike (status diatur: stack 1 + cooldown siap) ──
    q2 = fresh_hero(env)
    units2, tower2 = q_lineup()
    assert q2.skills.cast_q(units2, [tower2], []) is True
    assert q2._q_stack == 1
    q2.skill_timer = 0  # ekuivalen CDR: cooldown siap dalam jendela kombo
    assert q2.skills.cast_q(units2, [tower2], []) is True
    data["q2"] = {
        "result": True,
        "pos": [q2.x, q2.y],
        "is_dashing": q2._is_dashing,
        "dash_timer": q2._dash_timer,
        "q_stack": q2._q_stack,
        "q_reset_timer": q2._q_reset_timer,
        "skill_timer": q2.skill_timer,
        "target_id": q2.target.id if q2.target else None,
        "active_skill": q2.active_skill,
        "active_skill_timer": q2.active_skill_timer,
        "tower_hp": tower2.hp,
        "victims": [victim_summary(v) for v in units2],
    }

    # ── Quirk kombo: reset 180 < cooldown 300 ────────────────
    qk = fresh_hero(env)
    unitsk, _tk = q_lineup()
    assert qk.skills.cast_q(unitsk, [], []) is True
    for _ in range(180):
        qk.skills.update_timers([], [], [])
    data["quirk"] = {"stack_after_180": qk._q_stack,
                     "reset_after_180": qk._q_reset_timer,
                     "skill_timer_after_180": qk.skill_timer}

    # ── Timer Q2: dash 15 lalu reset kombo ───────────────────
    qt = fresh_hero(env)
    unitsq, _tq = q_lineup()
    assert qt.skills.cast_q(unitsq, [], []) is True
    qt.skill_timer = 0
    assert qt.skills.cast_q(unitsq, [], []) is True
    for _ in range(15):
        qt.skills.update_timers([], [], [])
    dash_mid = {"is_dashing": qt._is_dashing,
                "dash_timer": qt._dash_timer,
                "q_stack": qt._q_stack,
                "q_reset_timer": qt._q_reset_timer}
    for _ in range(165):
        qt.skills.update_timers([], [], [])
    dash_mid["stack_after_180"] = qt._q_stack
    dash_mid["reset_after_180"] = qt._q_reset_timer
    data["qtimers"] = dash_mid

    # ── Hero sebagai korban ──────────────────────────────────
    hv = fresh_hero(env)
    src = make_victim(env, "src", 600.0, 340.0, hp=100000)
    pre_hp = hv.hp
    hv.take_damage(100, "red", source=src)
    take = {"hp_before": pre_hp, "hp_after": hv.hp,
            "dealt": src.damage_dealt, "alive": hv.alive}
    dying = fresh_hero(env)
    dying.hp = 10
    # apply_slow tidak ikut diekstrak di env cannon (ada resist item);
    # slow di sini hanya untuk membuktikan clear saat mati.
    dying.slow_amount = 0.3
    dying.slow_timer = 60
    src2 = make_victim(env, "src2", 600.0, 340.0, hp=100000)
    dying.take_damage(100, "red", source=src2)
    take["death"] = {"alive": dying.alive, "hp": dying.hp,
                     "deaths": dying.deaths,
                     "killed_by_src2": dying._killed_by is src2,
                     "slow_cleared": dying.slow_amount == 0,
                     "dealt": src2.damage_dealt}
    over = fresh_hero(env)
    over.take_damage(999999, "red", source=src)
    take["overkill_hp"] = over.hp
    take["overkill_alive"] = over.alive
    data["take"] = take

    data["meta"] = {
        "skills_source": "hero_skills (impor nyata + stub)",
        "timer_mirror": "attack/skill/w/e/r/active 2-baris decrement",
    }
    return data


def main():
    data = source_fixture()
    FIXTURE.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"wrote {FIXTURE} ({len(json.dumps(data))} bytes)")


if __name__ == "__main__":
    main()
