"""Oracle for the level-1 subset: original source scheduler, economy, slot, build/sell methods.
Only presentation, bosses, random spawn jitter and AI auto-upgrades are stubbed.
No pygame/game import and no previous migration converter is used.
"""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from check_source_contract import source_lanes
from structure_source_oracle import namespace, source_classes

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/match_source.json"
LEVEL_DATA = ROOT / "godot_rebuild/data/levels/level_1.json"
BOSS_DATA = ROOT / "godot_rebuild/data/levels/level_1_bosses.json"


def compile_method(node, env):
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<source match method>", "exec"), env)
    return env[node.name]


def source_fixture():
    env = namespace()
    tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    game_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Game")
    methods = {n.name: n for n in game_class.body if isinstance(n, ast.FunctionDef)}
    selected = [methods[n] for n in ("update_waves", "_get_wave_composition", "_generate_build_slots_from_lanes", "try_build_tower")]
    cls = ast.ClassDef(name="SourceGame", bases=[], keywords=[], body=selected, decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])), "<source match subset>", "exec"), env)
    for name in ("compute_starting_gold", "compute_gold_per_second"):
        compile_method(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name), env)
    path_data = source_lanes()
    lane_ids = {"top": 0, "mid": 1, "bot": 2}
    noop = lambda *args, **kwargs: None
    env["Minion"] = lambda kind, team, lane, level, path: SimpleNamespace(kind=kind, team=team, lane=lane, alive=True)

    def game():
        g = env["SourceGame"]()
        g.wave_number, g.wave_timer = 0, 300
        g.spawn_queue_blue, g.spawn_queue_red = [], []
        g.spawn_timer_blue, g.spawn_timer_red = 0, 0
        g.blue_base = SimpleNamespace(level=1, set_wave=noop)
        g.red_base = SimpleNamespace(level=1, set_wave=noop)
        g.minions = []
        g.map_renderer = SimpleNamespace(get_lane_path=lambda lane: path_data[lane])
        g.level_config = {"mini_bosses": {}}
        g.effects = SimpleNamespace(announce_wave=noop, show_path_preview=noop)
        g._try_spawn_pending_mini_boss = noop
        g._auto_scale_ai_castle = noop
        return g

    result = {"traces": [], "composition": {}, "slots": [], "economy": []}
    for blocked_until in (0, 2050):
        g = game()
        trace = {"blocked_until": blocked_until, "spawns": [], "starts": [], "snapshots": []}
        for tick in range(1, 3801):
            g.minions = [SimpleNamespace(alive=True)] if 301 < tick < blocked_until else []
            previous_wave = g.wave_number
            g.update_waves()
            if g.wave_number != previous_wave:
                trace["starts"].append([tick, g.wave_number])
            for unit in g.minions:
                if hasattr(unit, "kind"):
                    trace["spawns"].append([tick, 0 if unit.team == "blue" else 1, unit.kind, lane_ids[unit.lane]])
            if tick in (300, 301, 320, 321, 461, 1801, 1802, 2049, 2050, 3303, 3800):
                trace["snapshots"].append([tick, g.wave_number, g.wave_timer, len(g.spawn_queue_blue), len(g.spawn_queue_red)])
        result["traces"].append(trace)
    g = game()
    for wave in (1, 3, 4, 6, 7, 9, 10, 12, 13, 30):
        g.wave_number = wave
        result["composition"][str(wave)] = g._get_wave_composition("blue")
    g._generate_build_slots_from_lanes()
    for team, slots in enumerate((g.build_slots_blue, g.build_slots_red)):
        result["slots"].extend({"team": team, "lane": lane_ids[s["lane"]], "position": [s["x"], s["y"]]} for s in slots)

    # Execute the original income statements unchanged, without the rest of Game.update.
    body = methods["update"].body
    income_start = next(i for i, n in enumerate(body) if isinstance(n, ast.AugAssign)
                        and isinstance(n.target, ast.Attribute) and n.target.attr == "gold_timer")
    income = ast.FunctionDef(name="income", args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="self")],
        kwonlyargs=[], kw_defaults=[], defaults=[]), body=body[income_start:income_start + 2], decorator_list=[])
    income = ast.fix_missing_locations(income)
    tick_income = compile_method(income, env)
    level_one = level_config("LEVEL_1")
    result["normal_start"] = env["compute_starting_gold"](level_one, 1, "normal")
    result["ai_start"] = env["STARTING_GOLD"]
    for level in (1, 4, 20):
        for difficulty in ("easy", "normal", "hard", "unknown"):
            starting = env["compute_starting_gold"](level_one, level, difficulty)
            rate = env["compute_gold_per_second"](level, difficulty)
            account = SimpleNamespace(gold=starting, ai=SimpleNamespace(gold=env["STARTING_GOLD"]),
                gold_timer=0, _gold_income_milli=0, gold_per_second=rate, wave_number=0)
            sample = {"level": level, "difficulty": difficulty, "starting": starting, "rate": rate, "pulses": []}
            for tick in range(1, 481):
                account.wave_number = (tick - 1) // 180
                tick_income(account)
                if tick % 60 == 0:
                    sample["pulses"].append([account.gold, account.ai.gold, account._gold_income_milli])
            result["economy"].append(sample)
    # Complete level-1 build -> UI sale, including the source's 50G fallback.
    tower_class = source_classes(env)["Tower"]
    entities = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    tower_ast = next(n for n in entities.body if isinstance(n, ast.ClassDef) and n.name == "Tower")
    sell = next(n for n in tower_ast.body if isinstance(n, ast.FunctionDef) and n.name == "sell_value")
    tower_class.sell_value = compile_method(sell, env)
    env["Tower"] = tower_class
    g.gold, g.towers = 1000, []
    g.build_popup_slot = g.build_slots_blue[0]
    g.close_build_popup = lambda: setattr(g, "build_popup_slot", None)
    g.close_popup = noop
    g.try_build_tower("archer")
    result["build_cost"] = 1000 - g.gold
    before = g.gold
    g.selected_tower = g.towers[0]
    input_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "InputHandler")
    sell_ui = next(n for n in input_class.body if isinstance(n, ast.FunctionDef) and n.name == "_try_sell_tower")
    compile_method(sell_ui, env)(SimpleNamespace(game=g))
    result["sell_refund"] = g.gold - before
    result["castle_auto_scale"] = castle_auto_scale(env)
    result["minion_spawn_offsets"] = minion_spawn_offsets(env)
    result["enemy_scaling"] = enemy_scaling(env)
    result["level_one"] = level_config("LEVEL_1")
    result["boss_spawn"] = boss_spawn(env)
    return result


def minion_spawn_offsets(env):
    """Real Minion.__init__ spread statements, exec'd verbatim.

    `_entity.py` places a new minion on its lane path, adds uniform(-8, 8) to
    both axes, then adds the per-lane Y offset. The extracted slice is the
    source's own AST, so the constants and the order of operations are taken
    from the game, not from a hand-written copy. Rows are recorded twice with
    the same seed (mid lane = jitter only, the row's lane = jitter + spread) so
    the fixture proves the lane offset is applied after the jitter without
    changing it.
    """
    import random as _random

    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    minion = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Minion")
    init = next(n for n in minion.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    start = next(i for i, n in enumerate(init.body)
                 if isinstance(n, ast.Import) and any(a.name == "random" for a in n.names))
    body = init.body[start:start + 5]
    assert [type(n).__name__ for n in body] == ["Import", "AugAssign", "AugAssign", "Assign", "AugAssign"], \
        "minion spawn offset slice drifted"
    lane_names = {0: "top", 1: "mid", 2: "bot"}
    fn = ast.fix_missing_locations(ast.FunctionDef(
        name="spawn_offset", args=ast.arguments(
            posonlyargs=[], args=[ast.arg(arg="self")], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=body, decorator_list=[]))
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<source minion spawn offset>", "exec"), env)
    spawn_offset = env["spawn_offset"]

    def place(lane, seed):
        node = SimpleNamespace(x=1000.0, y=200.0, lane=lane_names[lane])
        _random.seed(seed)
        spawn_offset(node)
        return node

    rows = []
    for lane in (0, 1, 2):
        for step in range(3):
            seed = 900 + lane * 10 + step
            mid = place(1, seed)
            placed = place(lane, seed)
            offset_x = mid.x - 1000.0
            offset_y = mid.y - 200.0
            assert -8.0 <= offset_x <= 8.0 and -8.0 <= offset_y <= 8.0, "jitter out of source range"
            assert abs(placed.x - mid.x) < 1e-9, "lane offset must not change x"
            rows.append({
                "base": [1000.0, 200.0],
                "lane": lane,
                "offset_x": offset_x,
                "offset_y": offset_y,
                "lane_offset": placed.y - mid.y,
                "final_y": placed.y,
            })
    return {"jitter": 8.0, "lane_offsets": [-20, 0, 20], "rows": rows}


def castle_auto_scale(env):
    """Real Game._auto_scale_ai_castle against the real Castle level methods.

    The castle class is exec'd straight from `_entity.py` (upgrade +
    _apply_level_stats), so the recorded level/HP/damage/range come from the
    source, not from a hand-written stub.
    """
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    castle = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Castle")
    body = [n for n in castle.body
            if isinstance(n, ast.FunctionDef)
            and n.name in ("upgrade", "_apply_level_stats")]
    assert {n.name for n in body} == {"upgrade", "_apply_level_stats"}, "castle methods missing"
    stub = ast.parse("class SourceCastle:\n    pass").body[0]
    stub.body = body
    exec(compile(ast.fix_missing_locations(ast.Module(body=[stub], type_ignores=[])),
                 "<source castle levels>", "exec"), env)
    castle_type = env["SourceCastle"]

    core_tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    game_class = next(n for n in core_tree.body
                      if isinstance(n, ast.ClassDef) and n.name == "Game")
    scale_fn = next(n for n in game_class.body
                    if isinstance(n, ast.FunctionDef) and n.name == "_auto_scale_ai_castle")
    game_stub = ast.parse("class SourceCastleScale:\n    pass").body[0]
    game_stub.body = [scale_fn]
    exec(compile(ast.fix_missing_locations(ast.Module(body=[game_stub], type_ignores=[])),
                 "<source castle auto scale>", "exec"), env)
    scale_type = env["SourceCastleScale"]

    rows = []
    for wave in range(1, 31):
        game = scale_type()
        game.wave_number = wave
        base = castle_type()
        opening = env["NEXUS_LEVELS"][1]
        base.level = 1
        base.max_hp = opening["hp"]
        base.hp = base.max_hp
        base.damage = opening["damage"]
        base.range = opening["range"]
        base.attack_cooldown = opening["attack_cooldown"]
        base.castle_shield_purchased = False
        game.red_base = base
        game._auto_scale_ai_castle()
        rows.append({
            "wave": wave,
            "level": base.level,
            "max_hp": base.max_hp,
            "damage": base.damage,
            "range": base.range,
        })
    # A castle whose shield was already bought keeps its shield percentage.
    game = scale_type()
    game.wave_number = 30
    shielded = castle_type()
    opened = env["NEXUS_LEVELS"][2]
    shielded.level = 2
    shielded.max_hp = opened["hp"]
    shielded.hp = shielded.max_hp
    shielded.damage = opened["damage"]
    shielded.range = opened["range"]
    shielded.attack_cooldown = opened["attack_cooldown"]
    shielded.castle_shield_purchased = True
    shielded.shield_max = int(shielded.max_hp * env["CASTLE_SHIELD_HP_RATIO"])
    shielded.shield = int(shielded.shield_max * 0.5)
    game.red_base = shielded
    game._auto_scale_ai_castle()
    rows.append({
        "wave": 30,
        "level": shielded.level,
        "max_hp": shielded.max_hp,
        "damage": shielded.damage,
        "range": shielded.range,
        "shield_max": shielded.shield_max,
        "shield": shielded.shield,
    })
    return rows


def level_config(name):
    """`LEVEL_n` from levels/level_data.py as a plain dict (source literal)."""
    module = ast.parse((ROOT / "levels/level_data.py").read_text(encoding="utf-8"))
    return ast.literal_eval(next(n.value for n in module.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)))


def source_minion(env):
    """Real `Minion.__init__` (AST) plus a stub TowerDebuffMixin, no pygame."""
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    table = next(node.value for node in core.body if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "MINION_TYPES" for t in node.targets))
    minions = {}
    for key, value in zip(table.keys, table.values):
        entry = {}
        for field_key, field_value in zip(value.keys, value.values):
            field = ast.literal_eval(field_key)
            try:
                entry[field] = ast.literal_eval(field_value)
            except (ValueError, TypeError):
                assert field == "color", "unexpected non-literal minion field"
                entry[field] = (255, 255, 255)
        minions[ast.literal_eval(key)] = entry
    env["MINION_TYPES"] = minions

    class StubMixin:
        def _init_tower_debuffs(self):
            for name in ("slow_amount", "slow_timer", "atk_slow_amount", "atk_slow_timer",
                         "skill_down_amount", "skill_down_timer", "anti_heal_amount",
                         "anti_heal_timer", "burn_dps", "burn_timer", "burn_accum",
                         "burn_tick_cd", "stun_timer", "armor_shred_amount", "armor_shred_timer",
                         "dmg_amp_amount", "dmg_amp_timer", "heal_amp_amount", "heal_amp_timer",
                         "blind_amount", "blind_timer"):
                setattr(self, name, 0)
            self.burn_team = None

    env["TowerDebuffMixin"] = StubMixin
    entity = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    minion_ast = next(n for n in entity.body if isinstance(n, ast.ClassDef) and n.name == "Minion")
    init = next(n for n in minion_ast.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    cls = ast.ClassDef(name="SourceMinion", bases=[ast.Name(id="TowerDebuffMixin", ctx=ast.Load())],
                       keywords=[], body=[init], decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "<source minion>", "exec"), env)
    return env["SourceMinion"]


def enemy_scaling(env):
    """Real difficulty/enemy scaling statements plus the real Minion stats.

    Slices are the source AST itself: the `enemy_scaling_enabled` assignment and
    multiplier if/else from `Game.reset`, the red-minion block from
    `Game.update_waves`, and the three castle-start statements from `Game.reset`.
    The minion stats come from the real `Minion.__init__`.
    """
    source_type = source_minion(env)
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    game = next(n for n in core.body if isinstance(n, ast.ClassDef) and n.name == "Game")
    methods = {n.name: n for n in game.body if isinstance(n, ast.FunctionDef)}
    reset_body = methods["reset"].body

    def compile_fn(name, body, args):
        fn = ast.fix_missing_locations(ast.FunctionDef(
            name=name, args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=a) for a in args],
                                          kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=body, decorator_list=[]))
        exec(compile(ast.Module(body=[fn], type_ignores=[]), "<source " + name + ">", "exec"), env)
        return env[name]

    setup_index = next(i for i, n in enumerate(reset_body)
                       if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Attribute)
                       and n.targets[0].attr == "enemy_scaling_enabled")
    scaling_if_index = next(i for i, n in enumerate(reset_body) if i > setup_index
                            and isinstance(n, ast.If)
                            and ast.unparse(n.test) == "self.enemy_scaling_enabled")
    apply_difficulty = compile_fn(
        "apply_difficulty",
        [reset_body[setup_index], reset_body[scaling_if_index]], ("self", "cfg"))

    scale_if = next(
        n for n in ast.walk(methods["update_waves"])
        if isinstance(n, ast.If)
        and any(isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Attribute)
                and s.targets[0].attr == "max_hp" and isinstance(s.targets[0].value, ast.Name)
                and s.targets[0].value.id == "m" for s in n.body))
    scale_minion = compile_fn("scale_minion", [scale_if], ("self", "m"))

    start_index = next(i for i, n in enumerate(reset_body)
                       if isinstance(n, ast.While) and "starting_castle_level" in ast.unparse(n.test))
    start_slice = reset_body[start_index:start_index + 3]
    assert [type(n).__name__ for n in start_slice] == ["While", "Assign", "While"], \
        "castle start slice drifted"
    apply_start_levels = compile_fn("apply_start_levels", start_slice, ("self", "cfg"))

    one = level_config("LEVEL_1")
    rows = []
    for difficulty in ("easy", "normal", "hard", "unknown"):
        game_stub = SimpleNamespace(difficulty=difficulty)
        apply_difficulty(game_stub, one)
        assert game_stub.enemy_scaling_enabled == (difficulty == "hard")
        for nexus_level in (1, 4):
            unit = source_type("goblin", "blue", "mid", nexus_level, [(0, 0), (10, 10)])
            before = {"max_hp": unit.max_hp, "damage": unit.damage, "speed": unit.speed}
            scale_minion(game_stub, unit)
            rows.append({
                "difficulty": difficulty,
                "enabled": game_stub.enemy_scaling_enabled,
                "hp_mult": game_stub.enemy_hp_mult,
                "damage_mult": game_stub.enemy_damage_mult,
                "speed_mult": game_stub.enemy_speed_mult,
                "nexus": nexus_level,
                "before": before,
                "max_hp": unit.max_hp,
                "hp": unit.hp,
                "damage": unit.damage,
                "speed": unit.speed,
                "base_speed": unit.base_speed,
            })

    class StubCastle:
        def __init__(self):
            self.level = 1

        def upgrade(self):
            self.level += 1

    synthetic = {"starting_castle_level": 3, "castle_start_level": 2}
    castle_rows = []
    for scaling in (False, True):
        for cfg in (one, synthetic):
            stub = SimpleNamespace(blue_base=StubCastle(), red_base=StubCastle(),
                                   enemy_scaling_enabled=scaling)
            apply_start_levels(stub, cfg)
            castle_rows.append({
                "scaling": scaling,
                "starting_castle_level": cfg["starting_castle_level"],
                "castle_start_level": cfg["castle_start_level"],
                "blue_level": stub.blue_base.level,
                "red_level": stub.red_base.level,
            })
    return {"rows": rows, "castles": castle_rows}




def source_boss(env):
    """Real Boss.__init__, apply_scaling, apply_slow, apply_debuff, speed and
    ability_damage from bosses/base_boss.py + TowerDebuffMixin from _core.py +
    bosses/boss_data.py + hero_archetypes.py, without importing pygame.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import hero_archetypes

    boss_data_ns = {}
    exec((ROOT / "bosses/boss_data.py").read_text(encoding="utf-8"), boss_data_ns)
    env["get_all_boss_types"] = boss_data_ns["get_all_boss_types"]

    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    debuff_mixin = next(n for n in core.body if isinstance(n, ast.ClassDef) and n.name == "TowerDebuffMixin")
    exec(compile(ast.fix_missing_locations(ast.Module(body=[debuff_mixin], type_ignores=[])),
                 "<source tower debuff mixin>", "exec"), env)

    boss_tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    boss_cls = next(n for n in boss_tree.body if isinstance(n, ast.ClassDef) and n.name == "Boss")
    keep_names = ("speed", "ability_damage", "__init__", "apply_scaling", "apply_slow", "apply_debuff")
    keep = [n for n in boss_cls.body if isinstance(n, ast.FunctionDef) and n.name in keep_names]
    cls = ast.ClassDef(
        name="SourceBoss",
        bases=[ast.Name(id="TowerDebuffMixin", ctx=ast.Load())],
        keywords=[],
        body=keep,
        decorator_list=[],
    )
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "<source boss>", "exec"), env)
    return env["SourceBoss"], env["get_all_boss_types"](), hero_archetypes


def boss_spawn(env):
    """Real mini-boss schedule, pending spawn queue, red_towers_destroyed counter,
    true-boss spawn gate, and Boss.__init__ / apply_scaling / tenacity debuffs.
    """
    import random as _random
    import types as _types

    boss_cls, all_bosses, archetypes = source_boss(env)
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    game = next(n for n in core.body if isinstance(n, ast.ClassDef) and n.name == "Game")
    methods = {n.name: n for n in game.body if isinstance(n, ast.FunctionDef)}

    env["print"] = lambda *args, **kwargs: None
    boss_mod = _types.ModuleType("bosses.base_boss")
    boss_mod.Boss = boss_cls
    sys.modules["bosses.base_boss"] = boss_mod
    render_mod = _types.ModuleType("_render")
    render_mod.BossIntroCinematic = lambda *args, **kwargs: SimpleNamespace(boss=args[0] if args else None)
    sys.modules["_render"] = render_mod

    roll_fn = compile_method(methods["_roll_mini_boss_schedule"], env)
    try_spawn_fn = compile_method(methods["_try_spawn_pending_mini_boss"], env)

    field_clear_if = next(
        n for n in ast.walk(methods["update_waves"])
        if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == "field_clear"
    )
    mb_start = next(
        i for i, s in enumerate(field_clear_if.body)
        if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name)
        and s.targets[0].id == "mini_bosses"
    )
    mb_slice = field_clear_if.body[mb_start:mb_start + 4]
    assert [type(s).__name__ for s in mb_slice] == ["Assign", "If", "If", "Expr"],         "mini boss wave slice drifted"
    wave_push_fn = compile_method(ast.fix_missing_locations(ast.FunctionDef(
        name="_wave_boss_step",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="self")], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=mb_slice,
        decorator_list=[],
    )), env)

    update_body = methods["update"].body
    true_boss_if = next(
        s for s in update_body
        if isinstance(s, ast.If) and "red_towers_destroyed" in ast.unparse(s.test)
    )
    true_boss_fn = compile_method(ast.fix_missing_locations(ast.FunctionDef(
        name="_true_boss_step",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="self")], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[true_boss_if],
        decorator_list=[],
    )), env)

    tower_for = next(
        s for s in update_body
        if isinstance(s, ast.For) and isinstance(s.iter, ast.Attribute) and s.iter.attr == "towers"
        and "red_towers_destroyed" in ast.unparse(s)
    )
    tower_death_fn = compile_method(ast.fix_missing_locations(ast.FunctionDef(
        name="_tower_death_step",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="self")], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[tower_for],
        decorator_list=[],
    )), env)

    one = level_config("LEVEL_1")
    mid_path = source_lanes()["mid"]
    level_one_ids = list(one["mini_bosses"].values()) + [one["true_boss"]]
    catalog = {}
    boss_rows = []
    for boss_type in level_one_ids:
        raw = all_bosses[boss_type]
        boss_class = raw.get("boss_class", "mini")
        armor, mr = archetypes.get_boss_resistances(boss_type, boss_class)
        profile = raw.get("resist_profile") or archetypes.BOSS_RESISTANCES.get(boss_type, {}).get("profile", "balanced")
        catalog[boss_type] = {
            "name": raw["name"],
            "title": raw["title"],
            "boss_class": boss_class,
            "hp": int(raw["hp"]),
            "damage": int(raw["damage"]),
            "speed": float(raw["speed"]),
            "range": int(raw["range"]),
            "attack_cooldown": int(raw["attack_cooldown"]),
            "radius": int(raw["radius"]),
            "gold_reward": int(raw["gold_reward"]),
            "color": list(raw["color"]),
            "color_dark": list(raw["color_dark"]),
            "ability_cooldown": int(raw["ability_cooldown"]),
            "ability_damage": int(raw["ability_damage"]),
            "ability_range": int(raw["ability_range"]),
            "entrance_text": raw["entrance_text"],
            "entrance_color": list(raw["entrance_color"]),
            "ability2_cooldown": int(raw.get("ability2_cooldown", 0)),
            "ability2_heal_pct": float(raw.get("ability2_heal_pct", 0.0)),
            "armor": int(raw.get("armor", armor)),
            "magic_resist": float(raw.get("magic_resist", mr)),
            "resist_profile": profile,
        }
        for scaled, mults in ((False, (1.0, 1.0, 1.0)), (True, (1.15, 1.10, 1.0))):
            inst = boss_cls(boss_type, mid_path)
            if scaled:
                inst.apply_scaling(*mults)
            boss_rows.append({
                "boss_type": boss_type,
                "scaled": scaled,
                "mults": list(mults),
                "name": inst.name,
                "title": inst.title,
                "boss_class": inst.boss_class,
                "max_hp": inst.max_hp,
                "hp": inst.hp,
                "damage": inst.damage,
                "base_damage": inst.base_damage,
                "speed": inst.speed,
                "base_speed": getattr(inst, "base_speed", inst.speed),
                "range": inst.range,
                "attack_cooldown": inst.attack_cooldown,
                "radius": inst.radius,
                "gold_reward": inst.gold_reward,
                "ability_cooldown_max": inst.ability_cooldown_max,
                "ability_damage": inst.ability_damage,
                "ability_range": inst.ability_range,
                "ability2_cooldown_max": inst.ability2_cooldown_max,
                "ability2_heal_pct": inst.ability2_heal_pct,
                "position": [inst.x, inst.y],
                "waypoint_index": inst.waypoint_index,
                "direction": inst.direction,
                "damage_reduction": inst.damage_reduction,
                "tenacity": inst.tenacity,
                "max_damage_per_hit": inst.max_damage_per_hit,
                "armor": inst.armor,
                "magic_resist": inst.magic_resist,
                "resist_profile": inst.resist_profile,
                "entrance_timer": inst.entrance_timer,
            })

    fallback_inst = boss_cls("gornak", [])
    debuff_inst = boss_cls("abaddon", mid_path)
    debuff_inst.apply_debuff("slow", 0.80, 90)
    debuff_inst.apply_debuff("atk_slow", 0.60, 80)
    debuff_inst.apply_debuff("skill_down", 0.25, 60)
    debuff_inst.apply_stun(60)
    debuff_check = {
        "fallback_pos": [fallback_inst.x, fallback_inst.y],
        "slow_amount": debuff_inst.slow_amount,
        "slow_timer": debuff_inst.slow_timer,
        "slowed_speed": debuff_inst.speed,
        "atk_slow_amount": debuff_inst.atk_slow_amount,
        "atk_slow_timer": debuff_inst.atk_slow_timer,
        "skill_down_amount": debuff_inst.skill_down_amount,
        "skill_down_timer": debuff_inst.skill_down_timer,
        "reduced_ability_damage": debuff_inst.ability_damage,
        "stun_timer": debuff_inst.stun_timer,
    }

    schedules = []
    for difficulty in ("easy", "normal", "hard", "unknown"):
        for seed in (101, 202, 303):
            _random.seed(seed)
            stub = SimpleNamespace(level_config=one, difficulty=difficulty)
            rolled = roll_fn(stub)
            waves = list(rolled.keys())
            values = list(rolled.values())
            low, high = (20, 40) if difficulty == "easy" else (11, 30)
            assert waves == sorted(waves) and len(set(waves)) == len(waves)
            assert all(low <= w <= high for w in waves)
            assert values == list(one["mini_bosses"].values())
            schedules.append({
                "difficulty": difficulty,
                "seed": seed,
                "low": low,
                "high": high,
                "waves": waves,
                "bosses": values,
            })

    empty_roll = roll_fn(SimpleNamespace(level_config={"mini_bosses": {}}, difficulty="normal"))
    assert empty_roll == {}

    # Spawn & queue trace executing the real wave push, _try_spawn_pending_mini_boss,
    # tower death loop, and true boss check.
    state = SimpleNamespace(
        level_number=1,
        level_config=one,
        _mini_boss_schedule={12: "gornak", 16: "morgath", 24: "drakar"},
        pending_mini_bosses=[],
        active_boss=None,
        true_boss_spawned=False,
        red_towers_destroyed=0,
        enemy_scaling_enabled=True,
        enemy_hp_mult=1.15,
        enemy_damage_mult=1.10,
        enemy_speed_mult=1.0,
        map_renderer=SimpleNamespace(get_lane_path=lambda lane: mid_path),
        gold=1000,
        score=0,
        ai=SimpleNamespace(gold=350),
        towers=[],
        wave_number=0,
    )
    state._try_spawn_pending_mini_boss = lambda: try_spawn_fn(state)

    events = []

    def snap(tag):
        events.append({
            "tag": tag,
            "wave": state.wave_number,
            "active": state.active_boss.boss_type if state.active_boss else None,
            "active_max_hp": state.active_boss.max_hp if state.active_boss else 0,
            "pending": [list(item) for item in state.pending_mini_bosses],
            "red_towers_destroyed": state.red_towers_destroyed,
            "true_boss_spawned": state.true_boss_spawned,
        })

    # Wave 12 starts -> gornak spawns immediately.
    state.wave_number = 12
    wave_push_fn(state)
    snap("wave_12_spawn")

    # Wave 16 starts while gornak is still alive -> morgath stays pending.
    state.wave_number = 16
    wave_push_fn(state)
    snap("wave_16_queued")

    # 5 red towers + 2 blue towers die -> red_towers_destroyed == 5, no true boss yet.
    state.towers = [
        SimpleNamespace(alive=False, team="red", gold_reward=100) for _ in range(5)
    ] + [
        SimpleNamespace(alive=False, team="blue", gold_reward=100) for _ in range(2)
    ]
    tower_death_fn(state)
    true_boss_fn(state)
    snap("five_red_towers")

    # 6th red tower dies while gornak is still alive -> true boss blocked by active_boss.
    state.towers.append(SimpleNamespace(alive=False, team="red", gold_reward=100))
    tower_death_fn(state)
    true_boss_fn(state)
    snap("six_red_towers_blocked")

    # Active boss cleared -> true boss spawns when active_boss is None.
    state.active_boss = None
    true_boss_fn(state)
    snap("true_boss_spawned")

    # Wave 24 starts while true boss is alive -> drakar queues behind morgath.
    state.wave_number = 24
    wave_push_fn(state)
    snap("wave_24_queued_behind_true_boss")

    # True boss dies -> _try_spawn_pending_mini_boss pops morgath, then drakar.
    state.active_boss.alive = False
    state._try_spawn_pending_mini_boss()
    true_boss_fn(state)
    snap("morgath_popped_after_true_boss")

    state.active_boss.alive = False
    state._try_spawn_pending_mini_boss()
    snap("drakar_popped_last")

    return {
        "catalog": catalog,
        "boss_rows": boss_rows,
        "debuff_check": debuff_check,
        "schedules": schedules,
        "events": events,
    }


def main():
    if "--write" in sys.argv:
        data = source_fixture()
        FIXTURE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        LEVEL_DATA.parent.mkdir(parents=True, exist_ok=True)
        LEVEL_DATA.write_text(json.dumps(data["level_one"], indent=2) + "\n", encoding="utf-8")
        BOSS_DATA.write_text(json.dumps(data["boss_spawn"]["catalog"], indent=2) + "\n", encoding="utf-8")
        print("wrote %s, %s and %s" % (FIXTURE, LEVEL_DATA, BOSS_DATA))
        return
    # Round-trip through JSON so int-keyed source dicts (mini_bosses) compare
    # against their serialized form.
    data = json.loads(json.dumps(source_fixture()))
    assert data["level_one"] == json.loads(LEVEL_DATA.read_text(encoding="utf-8")), \
        "level 1 data drifted from source"
    assert data["boss_spawn"]["catalog"] == json.loads(BOSS_DATA.read_text(encoding="utf-8")), \
        "level 1 boss catalog drifted from source"
    assert data == json.loads(FIXTURE.read_text(encoding="utf-8")), "Match source contract drift"
    print("PASS: original wave traces, composition, 18 slots, income ledger and build/sell prices.")


if __name__ == "__main__":
    main()
