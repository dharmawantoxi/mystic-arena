"""Oracle for the level-1 subset: original source scheduler, economy, slot, build/sell methods.
Only presentation, bosses, random spawn jitter and AI auto-upgrades are stubbed.
No pygame/game import and no previous migration converter is used.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

from check_source_contract import source_lanes
from structure_source_oracle import namespace, source_classes

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/match_source.json"


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
    level_module = ast.parse((ROOT / "levels/level_data.py").read_text(encoding="utf-8"))
    level_one = ast.literal_eval(next(n.value for n in level_module.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "LEVEL_1" for t in n.targets)))
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
    return result


def main():
    assert source_fixture() == json.loads(FIXTURE.read_text(encoding="utf-8")), "Match source contract drift"
    print("PASS: original wave traces, composition, 18 slots, income ledger and build/sell prices.")


if __name__ == "__main__":
    main()
