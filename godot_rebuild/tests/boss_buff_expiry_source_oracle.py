"""Source oracle for layer 9am: boss self-buff stat lifecycles.

Two divergences found by auditing the `_tick_smart_clocks` expiry effects
against the source recipes:

* `_smart_ai_alchemist` (`bosses/base_boss.py:1257-1260`) expires Chemical
  Rage by clearing `rage_active` ONLY. The cast (`_cast_e_chemical_rage`,
  `:1341`) writes `self.damage = int(self.damage * 1.5)` against the CURRENT
  damage, so the source boost persists after expiry and COMPOUNDS on every
  recast (1.5x, 2.25x, ...). The pre-9am native expiry reset the damage to
  `_source_damage`, a native invention that erased the compounding.
* `_xirthalis_q` (`:2248-2261`) writes `self.speed = base_speed * 1.8` with
  `base_speed = stats.get("speed", 1.15)` - the RAW catalog speed, because
  `_get_boss_stats` scales only *damage* keys. The expiry
  (`_smart_ai_xirthalis`, `:2211-2216`) restores that raw catalog speed, so
  difficulty/enrage speed scaling is deliberately lost after one Shukuchi
  cycle. The pre-9am native port set the flag without ANY speed write and
  expired it without restoring anything.

The oracle pins both facts two ways without pygame:

1. AST shape checks over `bosses/base_boss.py`: the exact write sets of the
   two expiry blocks and the exact source segments of the two cast writes.
2. Numeric rows executing the REAL source methods (`_smart_ai_alchemist`,
   `_smart_ai_xirthalis`, `_cast_e_chemical_rage`, `_xirthalis_q`,
   `_get_boss_stats`, `_shake_screen`) on stub bosses carrying the real
   `bosses/boss_data.py` catalog numbers. Every row records `expected`
   (source) and `native_old` (the pre-9am port) columns with their own inputs
   and outputs, the house 9ag/9ah style.

Run: python godot_rebuild/tests/boss_buff_expiry_source_oracle.py
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
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_buff_expiry_source.json"

HARD_SPD_MULT = 1.15
HARD_DMG_MULT = 1.1

METHODS = (
    "_get_boss_stats",
    "_shake_screen",
    "_smart_ai_alchemist",
    "_cast_e_chemical_rage",
    "_smart_ai_xirthalis",
    "_xirthalis_q",
)


def _install_boss_data():
    """Register `bosses.boss_data` by file path so its package `__init__`
    (and every heavy sibling) never executes - it is pure data."""
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


def _stub(namespace, boss_type, **attrs):
    stub = _Stub()
    stub.boss_type = boss_type
    stub.x = 0.0
    stub.y = 0.0
    stub.active_skill = None
    stub.active_skill_timer = 0
    stub.q_timer = 0
    stub.w_timer = 0
    stub.e_timer = 0
    stub.r_timer = 0
    stub.skill_down_timer = 0
    stub.skill_down_amount = 0.0
    stub.dmg_scaling_mult = 1.0
    stub.is_enraged = False
    for key, value in attrs.items():
        setattr(stub, key, value)
    for name in METHODS:
        setattr(stub, name, types.MethodType(namespace[name], stub))
    return stub


def _expiry_writes(func_name, timer_attr):
    """AST: the write targets of `if self.<timer_attr> <= 0:` inside a recipe,
    plus the source segment of every assigned value."""
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


def _cast_segments(func_name):
    source = BOSS_SRC.read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    func = next(n for n in cls.body
                if isinstance(n, ast.FunctionDef) and n.name == func_name)
    out = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    out.append((target.attr,
                                ast.get_source_segment(source, node.value),
                                ast.get_source_segment(source, node)))
                elif isinstance(target, ast.Name):
                    out.append((target.id,
                                ast.get_source_segment(source, node.value),
                                ast.get_source_segment(source, node)))
    return out


def source_fixture():
    catalog = _install_boss_data()
    namespace = _exec_methods()
    xir = catalog["xirthalis"]
    alc = catalog["alchemist"]
    s0 = float(xir["speed"])
    d0 = int(int(alc["damage"]) * HARD_DMG_MULT)
    xir_hp = float(xir["hp"])
    alc_hp = float(alc["hp"])

    # ── AST shape pins ──
    rage_writes = _expiry_writes("_smart_ai_alchemist", "rage_timer")
    shukuchi_writes = _expiry_writes("_smart_ai_xirthalis", "shukuchi_timer")
    q_cast = dict((attr, seg) for attr, seg, _ in _cast_segments("_xirthalis_q"))
    rage_cast = dict((attr, seg) for attr, seg, _ in _cast_segments("_cast_e_chemical_rage"))
    shape = {
        "rage_expiry_writes": sorted(attr for attr, _ in rage_writes),
        "rage_expiry_has_damage_write": any(attr == "damage" for attr, _ in rage_writes),
        "shukuchi_expiry_writes": sorted(attr for attr, _ in shukuchi_writes),
        "shukuchi_expiry_speed_segment": dict(shukuchi_writes).get("speed"),
        "q_cast_base_speed_segment": q_cast.get("base_speed"),
        "q_cast_speed_segment": q_cast.get("speed"),
        "rage_cast_damage_segment": rage_cast.get("damage"),
        "catalog_speed_xirthalis": s0,
        "catalog_damage_alchemist": alc["damage"],
    }
    assert shape["rage_expiry_writes"] == ["rage_active"], shape
    assert not shape["rage_expiry_has_damage_write"]
    assert shape["shukuchi_expiry_writes"] == ["shukuchi_active", "speed"], shape
    assert shape["shukuchi_expiry_speed_segment"] == 'stats.get("speed", 1.15)'
    assert shape["q_cast_base_speed_segment"] == 'stats.get("speed", 1.15)'
    assert shape["q_cast_speed_segment"] == "base_speed * 1.8"
    assert shape["rage_cast_damage_segment"] == "int(self.damage * 1.5)"

    # ── Numeric rows: execute the real source methods ──
    rows = []

    # 1. Xirthalis Shukuchi cast on hard-scaled speed.
    stub = _stub(
        namespace, "xirthalis",
        hp=0.6 * xir_hp, max_hp=xir_hp, speed=s0 * HARD_SPD_MULT,
        shukuchi_active=False, shukuchi_timer=0,
        timelapse_mark_timer=0, timelapse_hp_mark=0.0,
        w_timer=999, e_timer=999, r_timer=999,
    )
    stub._smart_ai_xirthalis([], 999.0)
    assert stub.shukuchi_active and stub.shukuchi_timer == 180
    rows.append({
        "name": "xirthalis_shukuchi_cast",
        "boss": "xirthalis",
        "arm": "recipe",
        "divergent": True,
        "expected": {
            "input": {"hp": 0.6 * xir_hp, "max_hp": xir_hp,
                      "speed": s0 * HARD_SPD_MULT, "base_speed": s0 * HARD_SPD_MULT,
                      "q_timer": 0, "w_timer": 999, "e_timer": 999, "r_timer": 999,
                      "shukuchi_active": False, "shukuchi_timer": 0,
                      "target_distance": 999.0},
            "output": {"speed": stub.speed, "shukuchi_active": True,
                       "shukuchi_timer": 180, "q_timer": stub.q_timer},
        },
        "native_old": {
            "input": {"hp": 0.6 * xir_hp, "max_hp": xir_hp,
                      "speed": s0 * HARD_SPD_MULT, "base_speed": s0 * HARD_SPD_MULT,
                      "q_timer": 0, "w_timer": 999, "e_timer": 999, "r_timer": 999,
                      "shukuchi_active": False, "shukuchi_timer": 0,
                      "target_distance": 999.0},
            # Pre-9am the flag arm never wrote speed.
            "output": {"speed": s0 * HARD_SPD_MULT, "shukuchi_active": True,
                       "shukuchi_timer": 180, "q_timer": stub.q_timer},
        },
    })
    assert stub.speed == s0 * 1.8

    # 2. Shukuchi expiry restores the RAW catalog speed (scaling lost, source-faithful).
    stub = _stub(
        namespace, "xirthalis",
        hp=xir_hp, max_hp=xir_hp, speed=s0 * 1.8,
        shukuchi_active=True, shukuchi_timer=1, q_timer=180,
        timelapse_mark_timer=0, timelapse_hp_mark=0.0,
        w_timer=999, e_timer=999, r_timer=999,
    )
    stub._smart_ai_xirthalis([], 999.0)
    assert not stub.shukuchi_active
    rows.append({
        "name": "xirthalis_shukuchi_expiry",
        "boss": "xirthalis",
        "arm": "clocks",
        "divergent": True,
        "expected": {
            "input": {"hp": xir_hp, "max_hp": xir_hp,
                      "speed": s0 * 1.8, "base_speed": s0 * HARD_SPD_MULT,
                      "q_timer": 180, "w_timer": 999, "e_timer": 999, "r_timer": 999,
                      "shukuchi_active": True, "shukuchi_timer": 1,
                      "target_distance": 999.0},
            "output": {"speed": stub.speed, "shukuchi_active": False,
                       "shukuchi_timer": 0},
        },
        "native_old": {
            "input": {"hp": xir_hp, "max_hp": xir_hp,
                      "speed": s0 * HARD_SPD_MULT, "base_speed": s0 * HARD_SPD_MULT,
                      "q_timer": 180, "w_timer": 999, "e_timer": 999, "r_timer": 999,
                      "shukuchi_active": True, "shukuchi_timer": 1,
                      "target_distance": 999.0},
            # Pre-9am expiry only cleared the flag; speed kept its input value.
            "output": {"speed": s0 * HARD_SPD_MULT, "shukuchi_active": False,
                       "shukuchi_timer": 0},
        },
    })
    assert stub.speed == s0

    # 3. Alchemist Chemical Rage cast 1 (parity control: both columns agree).
    stub = _stub(
        namespace, "alchemist",
        hp=0.5 * alc_hp, max_hp=alc_hp, damage=d0, base_damage=d0,
        rage_active=False, rage_timer=0,
        w_timer=999, r_timer=999,
    )
    stub._smart_ai_alchemist([], 999.0)
    assert stub.rage_active and stub.rage_timer == 360 and stub.e_timer == 480
    cast1 = stub.damage
    assert cast1 == int(d0 * 1.5)
    cast_input = {"hp": 0.5 * alc_hp, "max_hp": alc_hp, "damage": d0,
                  "base_damage": d0, "q_timer": 0, "w_timer": 999, "e_timer": 0,
                  "r_timer": 999, "rage_active": False, "rage_timer": 0,
                  "target_distance": 999.0}
    cast_output = {"damage": cast1, "hp": stub.hp, "rage_active": True,
                   "rage_timer": 360, "e_timer": 480}
    rows.append({
        "name": "alchemist_rage_cast_1",
        "boss": "alchemist",
        "arm": "recipe",
        "divergent": False,
        "expected": {"input": dict(cast_input), "output": dict(cast_output)},
        "native_old": {"input": dict(cast_input), "output": dict(cast_output)},
    })

    # 4. Rage expiry: source keeps the boost; pre-9am native reset to base_damage.
    stub = _stub(
        namespace, "alchemist",
        hp=0.5 * alc_hp, max_hp=alc_hp, damage=cast1, base_damage=d0,
        rage_active=True, rage_timer=1, e_timer=480,
        w_timer=999, r_timer=999,
    )
    stub._smart_ai_alchemist([], 999.0)
    assert not stub.rage_active and stub.damage == cast1
    rows.append({
        "name": "alchemist_rage_expiry",
        "boss": "alchemist",
        "arm": "clocks",
        "divergent": True,
        "expected": {
            "input": {"hp": 0.5 * alc_hp, "max_hp": alc_hp, "damage": cast1,
                      "base_damage": d0, "q_timer": 0, "w_timer": 999,
                      "e_timer": 480, "r_timer": 999,
                      "rage_active": True, "rage_timer": 1,
                      "target_distance": 999.0},
            "output": {"damage": stub.damage, "rage_active": False,
                       "rage_timer": 0},
        },
        "native_old": {
            "input": {"hp": 0.5 * alc_hp, "max_hp": alc_hp, "damage": cast1,
                      "base_damage": d0, "q_timer": 0, "w_timer": 999,
                      "e_timer": 480, "r_timer": 999,
                      "rage_active": True, "rage_timer": 1,
                      "target_distance": 999.0},
            # Pre-9am expiry wrote damage = _source_damage(boss) = base_damage.
            "output": {"damage": d0, "rage_active": False, "rage_timer": 0},
        },
    })

    # 5. Rage recast compounds on the persisted boost (pre-9am: reset first).
    stub = _stub(
        namespace, "alchemist",
        hp=0.5 * alc_hp, max_hp=alc_hp, damage=cast1, base_damage=d0,
        rage_active=False, rage_timer=0, e_timer=0,
        w_timer=999, r_timer=999,
    )
    stub._smart_ai_alchemist([], 999.0)
    assert stub.rage_active and stub.damage == int(cast1 * 1.5)
    rows.append({
        "name": "alchemist_rage_cast_2",
        "boss": "alchemist",
        "arm": "recipe",
        "divergent": True,
        "expected": {
            "input": {"hp": 0.5 * alc_hp, "max_hp": alc_hp, "damage": cast1,
                      "base_damage": d0, "q_timer": 0, "w_timer": 999,
                      "e_timer": 0, "r_timer": 999,
                      "rage_active": False, "rage_timer": 0,
                      "target_distance": 999.0},
            "output": {"damage": stub.damage, "rage_active": True,
                       "rage_timer": 360, "e_timer": 480},
        },
        "native_old": {
            "input": {"hp": 0.5 * alc_hp, "max_hp": alc_hp, "damage": d0,
                      "base_damage": d0, "q_timer": 0, "w_timer": 999,
                      "e_timer": 0, "r_timer": 999,
                      "rage_active": False, "rage_timer": 0,
                      "target_distance": 999.0},
            "output": {"damage": int(d0 * 1.5), "rage_active": True,
                       "rage_timer": 360, "e_timer": 480},
        },
    })
    assert stub.damage == int(int(d0 * 1.5) * 1.5)

    return {
        "source": "bosses/base_boss.py::(_smart_ai_alchemist, _smart_ai_xirthalis)",
        "shape": shape,
        "rows": rows,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("boss_buff_expiry: %d shape pins, %d rows (%d divergent)"
          % (len(fixture["shape"]), len(fixture["rows"]),
             sum(1 for row in fixture["rows"] if row["divergent"])))
    for row in fixture["rows"]:
        print("  %-28s expected=%s native_old=%s"
              % (row["name"],
                 {k: v for k, v in row["expected"]["output"].items()
                  if k in ("speed", "damage")},
                 {k: v for k, v in row["native_old"]["output"].items()
                  if k in ("speed", "damage")}))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
