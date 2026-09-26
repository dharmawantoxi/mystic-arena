"""Oracle nexus: metode sumber Castle/Minion/wave, tanpa pygame.

Mengeksekusi metode numerik asli dari _core.py/_entity.py (AST), bukan
menyalin angka dari implementasi Godot. Presentasi/audio di-stub.
"""
import ast
import json
import math
from pathlib import Path
from types import SimpleNamespace

from structure_source_oracle import ROOT, namespace

FIXTURE = Path(__file__).parent / "fixtures/nexus_source.json"


def _compile(node, env):
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<source nexus method>", "exec"), env)
    return env[node.name]


def _entity_tree():
    return ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))


def _core_tree():
    return ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))


def source_fixture():
    env = namespace()
    env["math"] = math
    # MINION_TYPES memakai nama warna (GOBLIN_COLOR, ...) sehingga tidak
    # literal; bangun ulang dengan warna dummy agar __init__ asli jalan.
    _core = _core_tree()
    _table = next(
        node.value for node in _core.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "MINION_TYPES" for t in node.targets)
    )
    _minions = {}
    for _k, _v in zip(_table.keys, _table.values):
        _name = ast.literal_eval(_k)
        _entry = {}
        for _fk, _fv in zip(_v.keys, _v.values):
            _field = ast.literal_eval(_fk)
            try:
                _entry[_field] = ast.literal_eval(_fv)
            except (ValueError, TypeError):
                if _field == "color":
                    _entry[_field] = (255, 255, 255)
                else:
                    raise
        _minions[_name] = _entry
    env["MINION_TYPES"] = _minions

    class _StubMixin:
        def _init_tower_debuffs(self):
            self.slow_amount = 0.0
            self.slow_timer = 0
            self.atk_slow_amount = 0.0
            self.atk_slow_timer = 0
            self.skill_down_amount = 0.0
            self.skill_down_timer = 0
            self.anti_heal_amount = 0.0
            self.anti_heal_timer = 0
            self.burn_dps = 0.0
            self.burn_timer = 0
            self.burn_accum = 0.0
            self.burn_tick_cd = 0
            self.burn_team = None
            self.stun_timer = 0
            self.armor_shred_amount = 0.0
            self.armor_shred_timer = 0
            self.dmg_amp_amount = 0.0
            self.dmg_amp_timer = 0
            self.heal_amp_amount = 0.0
            self.heal_amp_timer = 0
            self.blind_amount = 0.0
            self.blind_timer = 0

    env["TowerDebuffMixin"] = _StubMixin

    entity = _entity_tree()
    castle_ast = next(n for n in entity.body if isinstance(n, ast.ClassDef) and n.name == "Castle")
    castle_methods = {n.name: n for n in castle_ast.body if isinstance(n, ast.FunctionDef)}
    wanted_castle = ["__init__", "_apply_level_stats", "upgrade", "upgrade_cost",
                     "set_wave", "get_minion_composition"]
    castle_cls = ast.ClassDef(name="SourceCastle", bases=[], keywords=[],
                              body=[castle_methods[n] for n in wanted_castle],
                              decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[castle_cls], type_ignores=[])),
                 "<source castle>", "exec"), env)
    SourceCastle = env["SourceCastle"]

    minion_ast = next(n for n in entity.body if isinstance(n, ast.ClassDef) and n.name == "Minion")
    minion_methods = {n.name: n for n in minion_ast.body if isinstance(n, ast.FunctionDef)}
    minion_cls = ast.ClassDef(name="SourceMinion", bases=[ast.Name(id="TowerDebuffMixin", ctx=ast.Load())],
                              keywords=[],
                              body=[minion_methods[n] for n in ("__init__", "_find_target_smart", "_distance_to")],
                              decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[minion_cls], type_ignores=[])),
                 "<source minion>", "exec"), env)
    SourceMinion = env["SourceMinion"]
    # isinstance(e, Minion) di sumber harus mengenali minion uji.
    env["Minion"] = SourceMinion

    core = _core_tree()
    game_ast = next(n for n in core.body if isinstance(n, ast.ClassDef) and n.name == "Game")
    game_methods = {n.name: n for n in game_ast.body if isinstance(n, ast.FunctionDef)}
    comp_fn = _compile(game_methods["_get_wave_composition"], dict(env))

    result = {"nexus_levels": [], "hp_cases": [], "shield_waves": [],
              "minion_scaling": [], "composition": {}, "ai_cases": []}

    # --- Tier nexus dari metode asli (level, stat, harga, scale/AI) ---
    probe = SourceCastle(100, 620, "blue")
    for level in range(1, 6):
        if level > 1:
            price = probe.upgrade_cost()
            assert probe.upgrade()
        else:
            price = 0
        data = env["NEXUS_LEVELS"][level]
        result["nexus_levels"].append({
            "level": level,
            "price": price,
            "hp": probe.max_hp,
            "damage": probe.damage,
            "range": probe.range,
            "cooldown": probe.attack_cooldown,
            "scale": data["minion_scale"],
            "ai": data["minion_ai_level"],
            "upgrade_cost": data["upgrade_cost"],
            "shield_capacity": int(probe.max_hp * env["CASTLE_SHIELD_HP_RATIO"]),
            "next_price": probe.upgrade_cost(),
        })
    assert not probe.upgrade()

    # --- Formula HP/shield upgrade: eksekusi _apply_level_stats asli ---
    # old_hp pecahan dipilih untuk menguji trunc int() dan bonus 500 + cap.
    for old_level in range(1, 5):
        new_max = env["NEXUS_LEVELS"][old_level + 1]["hp"]
        old_max = env["NEXUS_LEVELS"][old_level]["hp"]
        for old_hp in (1, 100, old_max // 2, old_max - 1, old_max):
            for purchased in (False, True):
                for shield_ratio in (0.0, 0.5, 1.0):
                    castle = SourceCastle(100, 620, "blue")
                    while castle.level < old_level:
                        castle.upgrade()
                    # Siapkan shield_max realistis: tanpa pembelian tetap 4000,
                    # dengan pembelian mengikuti tier lama.
                    if purchased:
                        castle.castle_shield_purchased = True
                        castle.shield_max = int(old_max * env["CASTLE_SHIELD_HP_RATIO"])
                    else:
                        castle.castle_shield_purchased = False
                        castle.shield_max = int(env["NEXUS_LEVELS"][1]["hp"] * env["CASTLE_SHIELD_HP_RATIO"])
                    castle.hp = old_hp
                    castle.shield = int(castle.shield_max * shield_ratio)
                    castle.timer = 7
                    castle.shield_no_damage_timer = 11
                    cost = castle.upgrade_cost()
                    assert castle.upgrade()
                    result["hp_cases"].append({
                        "from": old_level, "to": old_level + 1,
                        "old_hp": old_hp, "old_max": old_max, "new_max": new_max,
                        "cost": cost,
                        "purchased": purchased, "shield_ratio": shield_ratio,
                        "new_hp": castle.hp,
                        "new_shield": castle.shield,
                        "new_shield_max": castle.shield_max,
                        "timer": castle.timer,
                        "shield_clock": castle.shield_no_damage_timer,
                        "shield_active": castle.shield_active,
                    })

    # --- set_wave asli: gratis sampai wave 10, purchased vs tidak ---
    for purchased in (False, True):
        for wave in (0, 1, 9, 10, 11, 13):
            for before in (0, 2000, 4000):
                castle = SourceCastle(100, 620, "blue")
                castle.castle_shield_purchased = purchased
                castle.shield_max = int(castle.max_hp * env["CASTLE_SHIELD_HP_RATIO"])
                castle.shield = before
                castle.shield_active = True
                castle.free_shield_active = True
                castle.set_wave(wave)
                result["shield_waves"].append({
                    "purchased": purchased, "wave": wave, "before": before,
                    "after": castle.shield,
                    "active": castle.shield_active,
                    "free": castle.free_shield_active,
                })

    # --- Scaling minion: eksekusi Minion.__init__ asli ---
    for kind in ("goblin", "orc", "troll", "undead", "dark_rider"):
        for nexus_level in range(1, 6):
            unit = SourceMinion(kind, "blue", "mid", nexus_level, [(0, 0), (10, 10)])
            result["minion_scaling"].append({
                "kind": kind, "nexus": nexus_level,
                "max_hp": unit.max_hp, "damage": unit.damage,
                "speed": unit.speed, "range": unit.range,
                "cooldown": unit.attack_cooldown,
                "gold": unit.gold_reward, "regen": unit.regen,
                "armor": unit.armor, "magic_resist": unit.magic_resist,
                "ai": unit.ai_level,
            })

    # --- Komposisi wave: castle tier x nomor wave (metode asli) ---
    for castle_level in range(1, 6):
        key = str(castle_level)
        result["composition"][key] = {}
        for wave in (1, 3, 4, 6, 7, 9, 10, 12, 13, 20):
            fake = SimpleNamespace(
                blue_base=SimpleNamespace(level=castle_level),
                red_base=SimpleNamespace(level=castle_level),
                wave_number=wave,
            )
            result["composition"][key][str(wave)] = comp_fn(fake, "blue")
            # Red memakai level red_base; pastikan simetris bila level sama.
            assert comp_fn(fake, "red") == result["composition"][key][str(wave)]
        # Base tanpa scaling wave untuk verifikasi queue.
        assert SourceCastle(0, 0, "blue").get_minion_composition() == env["NEXUS_WAVE_COMPOSITION"][1]

    # --- AI tier: eksekusi _find_target_smart asli ---
    # Urutan enemies disengaja tidak terurut agar tie/order teruji.
    def _enemy(eid, x, y, hp, lane, max_hp, is_minion, tower_kind=False):
        if is_minion:
            e = SourceMinion("goblin", "red", lane, 1, [(0, 0)])
            e.id = eid
            e.x, e.y, e.hp, e.max_hp = float(x), float(y), hp, max_hp
            e.lane = lane
            e.alive = True
            return e
        e = SimpleNamespace(id=eid, x=float(x), y=float(y), hp=hp,
                            max_hp=max_hp, lane=lane, alive=True)
        if tower_kind:
            e.tower_kind = "outer"
        return e

    scenarios = []
    # S0: tiga minion dalam range, jarak/hp/lane berbeda + tower + nexus.
    # Self di (100,100) range 30 (goblin tier1): in-range <=30.
    base_enemies = [
        _enemy(11, 120, 100, 40, "mid", 45, True),    # jarak 20, hp 40, lane sama
        _enemy(12, 110, 100, 10, "top", 45, True),    # jarak 10 (terdekat), hp 10, lane beda
        _enemy(13, 125, 100, 5, "mid", 45, True),     # jarak 25, hp 5 (terendah), lane sama
        _enemy(21, 115, 100, 2000, "mid", 2000, False),  # tower, jarak 15, max>=1500
        _enemy(22, 118, 100, 4000, "mid", 4000, False),  # nexus, jarak 18
        _enemy(31, 200, 100, 45, "mid", 45, True),    # luar range, dalam range+30 (jarak 100? tidak) -> luar
        _enemy(32, 125, 100, 45, "mid", 45, True),    # jarak 25 duplikat untuk tie
    ]
    # Jarak 100 untuk eid31 sebenarnya di luar range+30 (60) -> tidak dipilih fallback.
    # Tambahkan kandidat fallback dalam 30<dist<=60:
    base_enemies.append(_enemy(33, 150, 100, 45, "mid", 45, True))  # jarak 50 fallback
    scenarios.append(("mixed", base_enemies))
    # S1: hanya tower/nexus dalam range (tanpa minion) untuk AI4.
    scenarios.append(("structures_only", [
        _enemy(21, 115, 100, 2000, "mid", 2000, False),
        _enemy(22, 110, 100, 4000, "mid", 4000, False),
    ]))
    # S2: tidak ada in-range, dua kandidat fallback jarak 40/50.
    scenarios.append(("fallback", [
        _enemy(41, 140, 100, 45, "mid", 45, True),
        _enemy(42, 150, 100, 5, "top", 45, True),
    ]))
    # S3: tie jarak persis untuk AI1 (dua target jarak 10).
    scenarios.append(("tie", [
        _enemy(51, 110, 100, 40, "mid", 45, True),
        _enemy(52, 90, 100, 10, "mid", 45, True),
    ]))

    for name, enemies in scenarios:
        for ai in range(1, 6):
            me = SourceMinion("goblin", "blue", "mid", 1, [(0, 0)])
            me.x, me.y = 100.0, 100.0
            me.range = 30
            me.ai_level = ai
            me.lane = "mid"
            target = me._find_target_smart(list(enemies))
            result["ai_cases"].append({
                "scenario": name, "ai": ai,
                "target": getattr(target, "id", None),
            })

    return result


def main():
    assert source_fixture() == json.loads(FIXTURE.read_text(encoding="utf-8")), "Nexus source contract drift"
    print("PASS: original nexus levels/HP/shield, minion scaling, composition and AI tiers.")


if __name__ == "__main__":
    main()
