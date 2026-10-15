"""Source oracle for layer 9ao: the boss ability screen-shake site table.

The source Boss fires `_shake_screen(N)` from 128 call sites across 113
methods of `bosses/base_boss.py`. `_shake_screen` itself is presentation-only
(it routes to `game_instance.effects.shake_screen` under a try/except) and the
native rebuild already ports the ScreenShake physics (`scripts/ui/screen_shake.gd`,
its own oracle + suite) plus the EffectManager route and the boss DEATH shake
(`prototype_battle._queue_boss_death_presentation`).

This oracle records the authoritative site table so the ability-shake wiring
can proceed in stages, and pins the wired sites:

* 9ao: the one-shot enrage/frenzy shakes inside `Boss.update` (25 true class
  at `:624`, 15 mini at `:639`), carried by `BossState.enrage_fx_shake` and
  consumed by `prototype_battle._present_boss_enrage_shake` through the same
  gate as the death shake.
* 9ao-2: all 30 cast sites of the six audited families (alchemist, xirthalis,
  nyxarath, thalgryn, syrentha, kunkka), wired through the `BossAI._shake`
  helper - including the whiff-guard branches (nyxarath/thalgryn/syrentha Q,
  xirthalis E) and the zero-distance guard the native Q port folds into a
  dedicated branch. The pin is the intensity MULTISET: every wired source
  site must exist in `boss_ai.gd` with the same intensity.

The remaining 96 cast sites across 89 methods stay a documented roadmap
(later sub-slices wire them family by family against this table).

Run: python godot_rebuild/tests/boss_shake_sites_source_oracle.py
"""
import ast
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOSS_SRC = ROOT / "bosses" / "base_boss.py"
BOSS_STATE = ROOT / "godot_rebuild" / "scripts" / "match" / "boss_state.gd"
BOSS_AI = ROOT / "godot_rebuild" / "scripts" / "match" / "boss_ai.gd"
PROTOTYPE = ROOT / "godot_rebuild" / "scripts" / "match" / "prototype_battle.gd"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_shake_sites_source.json"

# 9ao-2 wired families: every cast shake site of these methods is routed
# through BossAI._shake in the matching native recipe arm.
FAMILY_METHODS = frozenset({
    "_cast_q_acid_spray", "_cast_w_unstable_concoction", "_cast_e_chemical_rage",
    "_cast_r_greevils_greed",
    "_xirthalis_q", "_xirthalis_w", "_xirthalis_e", "_xirthalis_r",
    "_nyxarath_q", "_nyxarath_w", "_nyxarath_e", "_nyxarath_r",
    "_thalgryn_q", "_thalgryn_w", "_thalgryn_e", "_thalgryn_r",
    "_syrentha_q", "_syrentha_w", "_syrentha_e", "_syrentha_r",
    "_cast_w_x_marks", "_cast_e_ghost_ship", "_cast_r_torrent",
})

EXPECTED_TOTAL = 128
EXPECTED_METHODS = 113
EXPECTED_CAST_SITES = 126
EXPECTED_HISTOGRAM = {
    "5": 1, "6": 1, "8": 10, "10": 22, "12": 27, "14": 15, "15": 12,
    "16": 5, "18": 7, "20": 8, "22": 5, "24": 2, "25": 8, "26": 1,
    "28": 2, "30": 2,
}


def _sites():
    source = BOSS_SRC.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    rows = []
    for func in cls.body:
        if not isinstance(func, ast.FunctionDef):
            continue
        for node in ast.walk(func):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "_shake_screen"):
                assert len(node.args) == 1 and isinstance(node.args[0], ast.Constant), \
                    "every shake site passes one constant intensity"
                intensity = int(node.args[0].value)
                klass = "cast"
                if func.name == "update":
                    prev = lines[node.lineno - 2]
                    if "max(18" in prev:
                        klass = "enrage_true"
                    elif "max(20" in prev:
                        klass = "enrage_mini"
                    else:
                        raise AssertionError("unclassified update shake at %d" % node.lineno)
                rows.append({
                    "method": func.name,
                    "line": node.lineno,
                    "intensity": intensity,
                    "class": klass,
                    "wired": klass != "cast" or func.name in FAMILY_METHODS,
                })
    rows.sort(key=lambda row: row["line"])
    return rows


def _native_wiring():
    state = BOSS_STATE.read_text(encoding="utf-8")
    proto = PROTOTYPE.read_text(encoding="utf-8")
    ai = BOSS_AI.read_text(encoding="utf-8")
    wiring = {
        "state_field": "var enrage_fx_shake := 0" in state,
        "true_branch": ("maxi(18, int(float(attack_cooldown) * 0.75))\n"
                        "\t\t\tenrage_fx_shake = 25") in state,
        "mini_branch": ("maxi(20, int(float(attack_cooldown) * 0.80))\n"
                        "\t\t\tenrage_fx_shake = 15") in state,
        "step_hook": ("if boss.enrage_fx_shake > 0:\n"
                      "\t\t_present_boss_enrage_shake(boss)") in proto,
        "presenter": "func _present_boss_enrage_shake(boss: BossState) -> void:" in proto,
        "one_shot_clear": "boss.enrage_fx_shake = 0" in proto,
        "shake_routes": proto.count("effects.shake_screen(shake)") == 2,
        "shake_helper": "static func _shake(world, intensity: float) -> void:" in ai,
    }
    wiring["native_cast_multiset"] = sorted(
        int(value) for value in re.findall(r"_shake\(world, (\d+)\)", ai))
    return wiring


def source_fixture():
    rows = _sites()
    assert len(rows) == EXPECTED_TOTAL, len(rows)
    methods = sorted(set(row["method"] for row in rows))
    histogram = Counter(str(row["intensity"]) for row in rows)
    enrage_rows = [row for row in rows if row["class"] != "cast"]
    cast_rows = [row for row in rows if row["class"] == "cast"]
    assert len(enrage_rows) == 2 and len(cast_rows) == EXPECTED_CAST_SITES
    assert [(row["class"], row["intensity"]) for row in enrage_rows] == [
        ("enrage_true", 25), ("enrage_mini", 15)], enrage_rows
    assert dict(histogram) == EXPECTED_HISTOGRAM, dict(histogram)
    wiring = _native_wiring()
    assert all(value for key, value in wiring.items() if key != "native_cast_multiset"), wiring
    cast_wired = sorted(row["intensity"] for row in rows
                        if row["class"] == "cast" and row["wired"])
    assert len(cast_wired) == 30, len(cast_wired)
    assert wiring["native_cast_multiset"] == cast_wired, (
        wiring["native_cast_multiset"], cast_wired)
    shape = {
        "total_sites": len(rows),
        "method_count": len(methods),
        "cast_sites_total": len(cast_rows),
        "cast_method_count": len(set(row["method"] for row in cast_rows)),
        "cast_sites_wired": sum(1 for row in cast_rows if row["wired"]),
        "cast_sites_remaining": sum(1 for row in cast_rows if not row["wired"]),
        "intensity_histogram": dict(sorted(histogram.items(), key=lambda kv: int(kv[0]))),
        "enrage_sites": [
            {"class": row["class"], "intensity": row["intensity"], "line": row["line"]}
            for row in enrage_rows
        ],
        "native_wiring": wiring,
    }
    assert shape["cast_sites_wired"] == 30 and shape["cast_sites_remaining"] == 96, shape
    return {
        "source": "bosses/base_boss.py::Boss._shake_screen call sites",
        "shape": shape,
        "rows": rows,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    shape = fixture["shape"]
    print("boss_shake_sites: %d sites / %d methods (enrage wired: %d, cast wired: %d, "
          "cast roadmap: %d / %d methods)"
          % (shape["total_sites"], shape["method_count"],
             len(shape["enrage_sites"]), shape["cast_sites_wired"],
             shape["cast_sites_remaining"], shape["cast_method_count"]))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
