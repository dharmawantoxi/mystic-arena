"""Source oracle for layer 9an: buff damage writes read the SCALED catalog.

Four self-buff pairs wrote damage off the difficulty-BAKED `base_damage`
snapshot in the native port while the source reads `_get_boss_stats()`
(catalog damage x skill_down x dmg_scaling_mult x enrage, `int(round(v*mult))`
- rounded ONCE from the raw catalog value):

* nyxarath Necromastery: cast `int(base_damage * 1.4)` off
  `stats.get("damage", 130)`; expiry resets to `stats.get("damage", 130)`.
* thalgryn Morph: `int(base_damage * 1.35)` off `stats.get("damage", 92)`.
* syrentha Mirror Image: `int(base_damage * 1.4)` off `stats.get("damage", 98)`.
* kunkka Rum: `int(base_damage * 1.3)` off `stats.get("damage", 125)`.

The pre-9an native used `boss.base_damage` (int-truncated bake) in all eight
places, double-rounding and dropping the runtime multipliers - e.g. hard +
enraged nyxarath: source casts int(round(175*1.1*1.25)*1.4) = 337, the old
native int(int(175*1.1)*1.4) = 268.

The xerathis Arcane pair is the OPPOSITE class and stays verbatim: the source
itself multiplies the attribute `self.base_damage` (cast `int(self.base_damage
* 1.3)`, expiry `self.damage = self.base_damage`), and the source attribute is
the same difficulty-baked snapshot the native keeps - pinned here so the two
classes never get conflated.

The oracle pins both classes with AST shape checks and records numeric rows
executing the REAL source methods on stubs with real `bosses/boss_data.py`
numbers: cast rows under hard scaling + enrage, expiry rows under hard scaling
+ skill-down. Every row carries `expected` (source) and `native_old` (pre-9an)
columns with their own inputs and outputs, the house 9ag/9ah/9am style.

Run: python godot_rebuild/tests/boss_buff_scaling_source_oracle.py
"""
import ast
import importlib.util
import json
import math
import random
import sys
import textwrap
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOSS_SRC = ROOT / "bosses" / "base_boss.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_buff_scaling_source.json"

HARD_DMG_MULT = 1.1
SKILL_DOWN_AMOUNT = 0.3

# buff: (smart_ai func, cast func, timer attr, flag attr, expiry fallback, mult)
BUFFS = {
    "nyxarath": ("_smart_ai_nyxarath", "_nyxarath_w", "necro_buff_timer",
                 "necro_buff_active", 130, 1.4),
    "thalgryn": ("_smart_ai_thalgryn", "_thalgryn_e", "morph_buff_timer",
                 "morph_buff_active", 92, 1.35),
    "syrentha": ("_smart_ai_syrentha", "_syrentha_e", "mirror_buff_timer",
                 "mirror_buff_active", 98, 1.4),
    "kunkka": ("_smart_ai_kunkka", "_cast_e_ghost_ship", "rum_buff_timer",
               "rum_buff_active", 125, 1.3),
}

METHODS = (
    "_get_boss_stats",
    "_shake_screen",
    "_smart_ai_nyxarath",
    "_nyxarath_w",
    "_smart_ai_thalgryn",
    "_thalgryn_e",
    "_smart_ai_syrentha",
    "_syrentha_e",
    "_smart_ai_kunkka",
    "_cast_e_ghost_ship",
)


def _install_boss_data():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    pkg = types.ModuleType("bosses")
    pkg.__path__ = [str(ROOT / "bosses")]
    sys.modules["bosses"] = pkg
    spec = importlib.util.spec_from_file_location(
        "bosses.boss_data", ROOT / "bosses" / "boss_data.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["bosses.boss_data"] = module
    spec.loader.exec_module(module)
    return module.get_all_boss_types()


def _method_block(name):
    lines = BOSS_SRC.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.startswith("    def %s(" % name))
    end = next(i for i, line in enumerate(lines)
               if i > start and (line.startswith("    def ")
                                 or line.startswith("class ")
                                 or (line[:1].strip() and not line.startswith((" ", "\t", "#")))))
    return textwrap.dedent("\n".join(lines[start:end]))


def _exec_methods():
    namespace = {"math": math, "random": random}
    for name in METHODS:
        block = _method_block(name)
        exec(compile(block, "base_boss.py::%s" % name, "exec"), namespace)
    return namespace


class _Stub:
    pass


class _EnemyStub:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True
        self.team = 1
        self.attack_timer = 0
        self.hits = []

    def take_damage(self, amount, from_team=None, **kwargs):
        self.hits.append(amount)
        return amount


def _stub(namespace, boss_type, **attrs):
    stub = _Stub()
    stub.boss_type = boss_type
    stub.x = 0.0
    stub.y = 0.0
    stub.team = 2
    stub.target = None
    stub.active_skill = None
    stub.active_skill_timer = 0
    stub.q_timer = 999
    stub.w_timer = 999
    stub.e_timer = 999
    stub.r_timer = 999
    stub.skill_down_timer = 0
    stub.skill_down_amount = 0.0
    stub.dmg_scaling_mult = 1.0
    stub.is_enraged = False
    stub.necro_buff_active = False
    stub.necro_buff_timer = 0
    stub.presence_active = False
    stub.presence_timer = 0
    stub.morph_buff_active = False
    stub.morph_buff_timer = 0
    stub.mirror_buff_active = False
    stub.mirror_buff_timer = 0
    stub.rum_buff_active = False
    stub.rum_buff_timer = 0
    stub.x_mark_timer = 0
    stub.x_mark_target = None
    for key, value in attrs.items():
        setattr(stub, key, value)
    for name in METHODS:
        setattr(stub, name, types.MethodType(namespace[name], stub))
    return stub


def _expiry_writes(func_name, timer_attr):
    source = BOSS_SRC.read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    func = next(n for n in cls.body
                if isinstance(n, ast.FunctionDef) and n.name == func_name)
    hits = []
    for node in ast.walk(func):
        if (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Attribute)
                and node.test.left.attr == timer_attr
                and isinstance(node.test.ops[0], ast.LtE)):
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute):
                            hits.append((target.attr,
                                         ast.get_source_segment(source, stmt.value)))
    return hits


def _assign_segments(func_name):
    source = BOSS_SRC.read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    func = next(n for n in cls.body
                if isinstance(n, ast.FunctionDef) and n.name == func_name)
    out = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, (ast.Attribute, ast.Name)):
                    key = target.attr if isinstance(target, ast.Attribute) else target.id
                    out.append((key, ast.get_source_segment(source, node.value)))
    return out


def source_fixture():
    catalog = _install_boss_data()
    namespace = _exec_methods()
    source_text = BOSS_SRC.read_text(encoding="utf-8")

    # ── AST shape pins ──
    shape = {
        "stats_scale_segment": "int(round(v * mult))" in source_text,
        "base_damage_bake_writes": source_text.count("self.base_damage = self.damage"),
        "buffs": {},
    }
    assert shape["stats_scale_segment"]
    assert shape["base_damage_bake_writes"] == 2

    for boss, (smart, cast, timer_attr, flag_attr, fallback, mult) in BUFFS.items():
        expiry = dict(_expiry_writes(smart, timer_attr))
        cast_segments = dict(_assign_segments(cast))
        pin = {
            "expiry_writes": sorted(expiry),
            "expiry_damage_segment": expiry.get("damage"),
            "cast_base_segment": cast_segments.get("base_damage"),
            "cast_damage_segment": cast_segments.get("damage"),
        }
        assert pin["expiry_writes"] == sorted([flag_attr, "damage"]), (boss, pin)
        assert pin["expiry_damage_segment"] == 'stats.get("damage", %d)' % fallback, pin
        assert pin["cast_base_segment"] == 'stats.get("damage", %d)' % fallback, pin
        assert pin["cast_damage_segment"] == "int(base_damage * %s)" % mult, pin
        shape["buffs"][boss] = pin

    # xerathis verbatim class: the attribute path, NOT the stats read.
    arcane_expiry = dict(_expiry_writes("_smart_ai_xerathis", "arcane_buff_timer"))
    xerathis_cast = dict(_assign_segments("_xerathis_e"))
    shape["xerathis"] = {
        "expiry_writes": sorted(arcane_expiry),
        "expiry_damage_segment": arcane_expiry.get("damage"),
        "cast_damage_segment": xerathis_cast.get("damage"),
    }
    assert shape["xerathis"]["expiry_writes"] == ["arcane_buff_active", "damage"]
    assert shape["xerathis"]["expiry_damage_segment"] == "self.base_damage"
    assert shape["xerathis"]["cast_damage_segment"] == "int(self.base_damage * 1.3)"

    for boss in BUFFS:
        shape["bosses"] = shape.get("bosses", {})
        shape["bosses"][boss] = {
            "damage": catalog[boss]["damage"],
            "hp": catalog[boss]["hp"],
        }

    rows = []
    for boss, (smart, cast_name, timer_attr, flag_attr, fallback, mult) in BUFFS.items():
        cat = catalog[boss]
        cat_damage = int(cat["damage"])
        cat_hp = float(cat["hp"])
        baked = int(cat_damage * HARD_DMG_MULT)  # int-truncated, like both ports
        enrage_mult = HARD_DMG_MULT * 1.25
        down_mult = (1.0 - SKILL_DOWN_AMOUNT) * HARD_DMG_MULT

        # ── cast row: hard scaling + enrage ──
        cast_attrs = {
            "hp": 0.7 * cat_hp if boss == "nyxarath" else 0.5 * cat_hp,
            "max_hp": cat_hp,
            "damage": baked,
            "base_damage": baked,
            "dmg_scaling_mult": HARD_DMG_MULT,
            "is_enraged": True,
        }
        enemies = []
        if boss == "nyxarath":
            cast_attrs["w_timer"] = 0
            enemies = [_EnemyStub(10.0, 0.0), _EnemyStub(-10.0, 0.0)]
        else:
            cast_attrs["e_timer"] = 0
        if boss == "kunkka":
            cast_attrs["target"] = _EnemyStub(300.0, 0.0)
            enemies = [_EnemyStub(100.0, 0.0)]
        stub = _stub(namespace, boss, **cast_attrs)
        getattr(stub, smart)(enemies, 999.0 if boss != "kunkka" else 300.0)
        assert getattr(stub, flag_attr), (boss, "cast must fire")
        scaled = int(round(cat_damage * enrage_mult))
        assert stub.damage == int(scaled * mult), (boss, stub.damage)
        buffed = stub.damage
        cast_input = {
            "hp": cast_attrs["hp"], "max_hp": cat_hp, "damage": baked,
            "base_damage": baked, "dmg_scaling_mult": HARD_DMG_MULT,
            "is_enraged": True, "skill_down_timer": 0, "skill_down_amount": 0.0,
            "q_timer": 999, "w_timer": cast_attrs.get("w_timer", 999),
            "e_timer": cast_attrs.get("e_timer", 999), "r_timer": 999,
            flag_attr: False, timer_attr: 0,
            "enemy_count": len(enemies), "has_target": boss == "kunkka",
            "target_distance": 300.0 if boss == "kunkka" else 999.0,
        }
        cast_output = {
            "damage": buffed, "hp": stub.hp, flag_attr: True,
            timer_attr: getattr(stub, timer_attr),
            "w_timer" if boss == "nyxarath" else "e_timer":
                stub.w_timer if boss == "nyxarath" else stub.e_timer,
        }
        old_output = dict(cast_output)
        old_output["damage"] = int(baked * mult)
        assert old_output["damage"] != buffed, (boss, "cast row must diverge")
        rows.append({
            "name": "%s_buff_cast" % boss,
            "boss": boss,
            "divergent": True,
            "expected": {"input": dict(cast_input), "output": cast_output},
            "native_old": {"input": dict(cast_input), "output": old_output},
        })

        # ── expiry row: hard scaling + skill-down, no enrage ──
        expiry_attrs = {
            "hp": 0.7 * cat_hp,
            "max_hp": cat_hp,
            "damage": buffed,
            "base_damage": baked,
            "dmg_scaling_mult": HARD_DMG_MULT,
            "skill_down_timer": 100,
            "skill_down_amount": SKILL_DOWN_AMOUNT,
            flag_attr: True,
            timer_attr: 1,
        }
        stub = _stub(namespace, boss, **expiry_attrs)
        getattr(stub, smart)([], 999.0)
        assert not getattr(stub, flag_attr), (boss, "expiry must fire")
        restored = int(round(cat_damage * down_mult))
        assert stub.damage == restored, (boss, stub.damage)
        expiry_input = {
            "hp": 0.7 * cat_hp, "max_hp": cat_hp, "damage": buffed,
            "base_damage": baked, "dmg_scaling_mult": HARD_DMG_MULT,
            "is_enraged": False, "skill_down_timer": 100,
            "skill_down_amount": SKILL_DOWN_AMOUNT,
            "q_timer": 999, "w_timer": 999, "e_timer": 999, "r_timer": 999,
            flag_attr: True, timer_attr: 1,
            "enemy_count": 0, "has_target": False, "target_distance": 999.0,
        }
        expiry_output = {"damage": restored, flag_attr: False, timer_attr: 0}
        old_expiry = dict(expiry_output)
        old_expiry["damage"] = baked
        assert old_expiry["damage"] != restored, (boss, "expiry row must diverge")
        rows.append({
            "name": "%s_buff_expiry" % boss,
            "boss": boss,
            "divergent": True,
            "expected": {"input": dict(expiry_input), "output": expiry_output},
            "native_old": {"input": dict(expiry_input), "output": old_expiry},
        })

    return {
        "source": "bosses/base_boss.py::(_smart_ai_nyxarath, _smart_ai_thalgryn,"
                  " _smart_ai_syrentha, _smart_ai_kunkka)",
        "shape": shape,
        "rows": rows,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("boss_buff_scaling: %d rows (%d divergent)"
          % (len(fixture["rows"]),
             sum(1 for row in fixture["rows"] if row["divergent"])))
    for row in fixture["rows"]:
        print("  %-24s expected.damage=%s native_old.damage=%s"
              % (row["name"], row["expected"]["output"]["damage"],
                 row["native_old"]["output"]["damage"]))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
