"""Source oracle for layer 9ao: the boss ability screen-shake site table.

The source Boss fires `_shake_screen(N)` from 128 call sites across 113
methods of `bosses/base_boss.py`. `_shake_screen` itself is presentation-only
(it routes to `game_instance.effects.shake_screen` under a try/except) and the
native rebuild already ports the ScreenShake physics (`scripts/ui/screen_shake.gd`,
its own oracle + suite) plus the EffectManager route and the boss DEATH shake
(`prototype_battle._queue_boss_death_presentation`).

This oracle records the authoritative site table so the ability-shake wiring
can proceed in stages, and pins the first wired sites: the one-shot
enrage/frenzy shakes inside `Boss.update` (25 true class at `:624`, 15 mini at
`:639`), now carried by `BossState.enrage_fx_shake` and consumed by
`prototype_battle._present_boss_enrage_shake` through the same gate as the
death shake. The remaining 126 cast sites across 112 methods stay a documented
roadmap (sub-slices 9ao-2+ wire them family by family against this table).

Run: python godot_rebuild/tests/boss_shake_sites_source_oracle.py
"""
import ast
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOSS_SRC = ROOT / "bosses" / "base_boss.py"
BOSS_STATE = ROOT / "godot_rebuild" / "scripts" / "match" / "boss_state.gd"
PROTOTYPE = ROOT / "godot_rebuild" / "scripts" / "match" / "prototype_battle.gd"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_shake_sites_source.json"

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
                    "wired": klass != "cast",
                })
    rows.sort(key=lambda row: row["line"])
    return rows


def _native_wiring():
    state = BOSS_STATE.read_text(encoding="utf-8")
    proto = PROTOTYPE.read_text(encoding="utf-8")
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
    }
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
    assert all(wiring.values()), wiring
    shape = {
        "total_sites": len(rows),
        "method_count": len(methods),
        "cast_sites_total": len(cast_rows),
        "cast_method_count": len(set(row["method"] for row in cast_rows)),
        "intensity_histogram": dict(sorted(histogram.items(), key=lambda kv: int(kv[0]))),
        "enrage_sites": [
            {"class": row["class"], "intensity": row["intensity"], "line": row["line"]}
            for row in enrage_rows
        ],
        "native_wiring": wiring,
    }
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
    print("boss_shake_sites: %d sites / %d methods (enrage wired: %d, cast roadmap: %d / %d)"
          % (shape["total_sites"], shape["method_count"],
             len(shape["enrage_sites"]), shape["cast_sites_total"],
             shape["cast_method_count"]))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
