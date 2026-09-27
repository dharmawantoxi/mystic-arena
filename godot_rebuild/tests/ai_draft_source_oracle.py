"""Read-only AIPlayer recruitment oracle; execute source AST, not a mirror.

Real final catalog (both _core definitions, real boss_data/hero_balance) and
real levels are used. Hero construction is a receipt probe only: this does NOT
prove hero kits or scene integration. Random choice is injected and records the
exact candidate order/weights; random.choices itself is Python's implementation.
"""
import ast
import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from kaizen_source_oracle import _exec_catalog
from structure_source_oracle import namespace

ROOT = Path(__file__).resolve().parents[2]
METADATA = ROOT / "godot_rebuild/data/ai/recruitment.json"
FIXTURE = Path(__file__).parent / "fixtures/ai_draft_source.json"
sys.path.insert(0, str(ROOT))


class ChoiceProbe:
    def __init__(self, draw):
        self.draw = draw
        self.calls = []
        self.rng = random.Random(0)
        self.rng.random = lambda: self.draw

    def choice(self, options):
        self.calls.append({"kind": "uniform", "options": list(options), "weights": []})
        return options[min(len(options) - 1, int(self.draw * len(options)))]

    def choices(self, options, weights, k=1):
        self.calls.append({"kind": "weighted", "options": list(options), "weights": list(weights)})
        return self.rng.choices(options, weights=weights, k=k)


def build_source():
    env = namespace()
    catalog = _exec_catalog(env)()
    from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES
    from levels import ALL_LEVELS
    # The source catalog catches import errors. Do not let a silently incomplete
    # catalog be blessed as a new fixture by this oracle.
    expected_bosses = {key for table in (MINI_BOSS_TYPES, TRUE_BOSS_TYPES)
                       for key, value in table.items() if value.get("hero_unlock")}
    assert {key for key, value in catalog.items() if value.get("is_boss_hero")} == expected_bosses
    assert set(env["AI_HERO_PREFERENCES"]) <= catalog.keys()
    metadata = {
        "starters": env["AI_HERO_PREFERENCES"],
        "catalog": {key: {"cost": int(value.get("cost", 400)),
                           "is_boss_hero": bool(value.get("is_boss_hero"))}
                    for key, value in catalog.items()},
        "fallback": {key: {"cost": int(value.get("cost", 400))}
                     for key, value in env["HERO_TYPES"].items()},
        "levels": {str(cfg["level_number"]): {"bosses": [
            *cfg.get("mini_bosses", {}).values(),
            *([cfg["true_boss"]] if cfg.get("true_boss") else [])]}
            for cfg in ALL_LEVELS},
        "spawn_origin": [env["RED_BASE_X"] - 60, env["RED_BASE_Y"] + 30],
    }
    source = next(n for n in ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8")).body
                  if isinstance(n, ast.ClassDef) and n.name == "AIPlayer")
    names = {"__init__", "_get_hero_pool", "_choose_hero_purchase_target", "_try_buy_hero", "_ai_reserve"}
    methods = [n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in methods} == names
    cls = ast.ClassDef(name="AIPlayer", bases=[], keywords=[], decorator_list=[], body=methods)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "<original AIPlayer recruitment>", "exec"), env)
    env["get_all_hero_types"] = lambda: catalog
    return env, metadata


def configure(env, metadata):
    env["get_all_hero_types"] = lambda: metadata["catalog"]
    env["HERO_TYPES"] = metadata["fallback"]
    configs = {int(key): {"mini_bosses": dict(enumerate(value["bosses"]))}
               for key, value in metadata["levels"].items()}
    # Used only for synthetic missing/duplicate/misclassified entries. Real
    # production cases call the actual levels.get_level_config unchanged.
    return SimpleNamespace(get_level_config=configs.get)


def purchase_case(env, level, owned, steps, initial=350, draw=0.0):
    ai = env["AIPlayer"](level_number=level)
    ai.gold = initial
    ai.heroes = [SimpleNamespace(hero_type=key, alive=False) for key in owned]
    receipts = []
    def hero(kind, team, x, y):
        receipts.append({"hero_type": kind, "team": team, "position": [x, y]})
        return SimpleNamespace(hero_type=kind, alive=True)
    env["Hero"] = hero
    probe = ChoiceProbe(draw)
    env["random"] = probe
    case = dict(level=level, owned=owned, initial_gold=initial, draw=draw, steps=[])
    for instruction in steps:
        if "level" in instruction:
            ai.level_number = instruction["level"]
        if "own" in instruction:
            ai.heroes.extend(SimpleNamespace(hero_type=key, alive=False) for key in instruction["own"])
        if instruction.get("own_target"):
            ai.heroes.append(SimpleNamespace(hero_type=ai._hero_purchase_target, alive=False))
        if instruction.get("own_pool"):
            ai.heroes = [SimpleNamespace(hero_type=key, alive=False) for key in ai._get_hero_pool()]
        ai.gold += instruction.get("credit", 0)
        probe.calls.clear()
        receipts.clear()
        success = ai._try_buy_hero()
        case["steps"].append({"input": instruction, "success": success, "gold": ai.gold,
            "owned": [h.hero_type for h in ai.heroes], "target": ai._hero_purchase_target or "",
            "cost": ai._hero_purchase_target_cost, "reserve": ai._ai_reserve(),
            "total": ai.total_heroes_bought, "calls": list(probe.calls), "receipts": list(receipts)})
    return case


def source_fixture():
    env, metadata = build_source()
    result = {"pools": [], "choices": [], "purchases": [], "reserves": [], "sampling": []}
    for level in (-3, 0, *range(1, 56), 80):
        ai = env["AIPlayer"](level_number=level)
        result["pools"].append(dict(level=level, pool=ai._get_hero_pool(), sources=ai._hero_source_levels))
    for level in (1, 2, 7, 20, 54, 55):
        ai = env["AIPlayer"](level_number=level)
        pool = ai._get_hero_pool()
        bosses = [key for key in pool if metadata["catalog"][key]["is_boss_hero"]]
        rosters = [[], ["kaizen"], metadata["starters"], pool]
        if bosses:
            rosters += [["kaizen", bosses[0]], bosses, [bosses[-1]]]
        for owned in rosters:
            ai.heroes = [SimpleNamespace(hero_type=key, alive=False) for key in owned]
            available = [key for key in pool if key not in owned]
            for draw in (0.0, 0.5, 0.999999):
                env["random"] = probe = ChoiceProbe(draw)
                chosen = ai._choose_hero_purchase_target(available, metadata["catalog"])
                result["choices"].append(dict(level=level, owned=owned, draw=draw,
                    chosen=chosen or "", calls=probe.calls))
    for level in (1, 2, 7, 54):
        # Starter wait -> exact payment -> newest boss wait -> saved boss purchase.
        result["purchases"].append(purchase_case(env, level, [], [
            {}, {}, {"credit": 49}, {"credit": 1}, {}, {}, {"credit": 100000}, {}, {}]))
        result["purchases"].append(purchase_case(env, level, ["kaizen"], [
            {}, {}, {"own_target": True}, {}, {"credit": 100000}, {"own_pool": True}], initial=0, draw=0.5))
    result["purchases"].append(purchase_case(env, 7, ["kaizen"], [
        {}, {"level": 1}, {}, {"credit": 400}, {"own_pool": True}], initial=0))
    # Source's permissive method itself has no roster-cap check: policy owns that.
    result["purchases"].append(purchase_case(env, 7, metadata["starters"][:5], [
        {}, {}], initial=100000, draw=0.999999))
    for target in (None, "", "kaizen"):
        for cost in (-10, 0, 400, 5000):
            ai = env["AIPlayer"]()
            ai._hero_purchase_target, ai._hero_purchase_target_cost = target, cost
            reserve = ai._ai_reserve()
            result["reserves"].append(dict(target=target or "", cost=cost, reserve=reserve))
    options, weights = ["a", "b", "c"], [1, 2, 1]
    for draw in (0, 0.249999, 0.25, 0.749999, 0.75, 0.999999):
        chosen = ChoiceProbe(draw).choices(options, weights)[0]
        result["sampling"].append(dict(options=options, weights=weights, draw=draw, chosen=chosen))
    synthetic = {
        "starters": ["starter", "fallback", "missing"],
        "catalog": {"starter": {"cost": 400, "is_boss_hero": False},
                    "old": {"cost": 900, "is_boss_hero": True},
                    "new": {"cost": 1900, "is_boss_hero": True},
                    "not_boss": {"cost": 1, "is_boss_hero": False}},
        "fallback": {"fallback": {"cost": 777}},
        "levels": {"1": {"bosses": ["old", "old", "starter", "absent", "not_boss"]},
                   "3": {"bosses": ["old", "new", "new"]}},
        "spawn_origin": metadata["spawn_origin"],
    }
    levels = configure(env, synthetic)
    with patch.dict(sys.modules, {"levels": levels}):
        ai = env["AIPlayer"](level_number=4)
        result["synthetic"] = dict(metadata=synthetic, pool=ai._get_hero_pool(), sources=ai._hero_source_levels,
            purchases=[purchase_case(env, 4, ["starter", "old", "new"], [{}, {"credit": 1}, {}], initial=776),
                       purchase_case(env, 4, ["starter", "old", "new", "fallback"], [{}, {"credit": 1}], initial=399)])
    return metadata, result


def encoded(value):
    # One scenario per line rather than ten thousand scalar lines.
    sections = []
    for key, section in value.items():
        if isinstance(section, list):
            text = "[\n" + ",\n".join("    " + json.dumps(row, separators=(",", ":"))
                                        for row in section) + "\n  ]"
        else:
            text = json.dumps(section, indent=2)
        sections.append("  " + json.dumps(key) + ": " + text)
    return "{\n" + ",\n".join(sections) + "\n}\n"



if __name__ == "__main__":
    metadata, fixture = source_fixture()
    if "--write" in sys.argv:
        METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        FIXTURE.write_text(encoded(fixture), encoding="utf-8")
    else:
        assert metadata == json.loads(METADATA.read_text(encoding="utf-8")), "Recruitment metadata drift"
        assert fixture == json.loads(FIXTURE.read_text(encoding="utf-8")), "AI draft fixture drift"
    print(f"PASS: AI draft oracle — {len(metadata['catalog'])} catalog entries, "
          f"{len(metadata['levels'])} levels; metadata/pool/draft/reserve, NOT playable kits")
