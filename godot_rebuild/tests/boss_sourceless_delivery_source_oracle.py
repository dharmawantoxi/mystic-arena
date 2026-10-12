"""9ac: `Boss.take_damage(damage, from_team)` with no source, recorded read-only.

The source signature is

    def take_damage(self, damage, from_team, damage_type='normal',
                    source=None, school=None)

and `from_team` is accepted but never read: unlike `Hero.take_damage`,
`Boss.take_damage` has no team filter - the caller decides - and the blind block
only runs when `source is not None` (`bosses/base_boss.py:5978-5991`). A
source-free hit therefore

* consumes no blind draw at all (a source-free hit can never miss),
* is credited to nobody (`credit_hero_damage(None, ...)` is a no-op),
* leaves `_killed_by = None` on a lethal blow, and
* keeps the caller's `school` as the only armour switch: `school=None` skips the
  armour cut even on an armoured boss, while an explicit `"physical"` applies it.

Rows execute the real `Boss.take_damage` from the `boss_core_source_oracle`
harness with a counting `random.random` wrapper, so the blind-draw column and
the credit hook come from the source algorithm. `--write` rewrites the fixture.
"""

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from boss_core_source_oracle import boss_class, namespace  # noqa: E402
from boss_kill_credit_source_oracle import RecordingEffects  # noqa: E402
from check_source_contract import source_lanes  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_sourceless_delivery_source.json"
BOSS_SOURCE = ROOT / "bosses" / "base_boss.py"
MINI = "gornak"
TRUE_BOSS = "abaddon"
ARMORED_RAW = 200

_ENV = None
BOSS_CLS = None
LANE = None
_ENV_RANDOM = None


def _harness():
    global _ENV, BOSS_CLS, LANE, _ENV_RANDOM
    if _ENV is None:
        _ENV = namespace()
        BOSS_CLS = boss_class(_ENV)
        LANE = source_lanes()["mid"]
        _ENV_RANDOM = _ENV["random"]
    return BOSS_CLS


def _signature_shape() -> dict:
    import ast

    tree = ast.parse(BOSS_SOURCE.read_text(encoding="utf-8"))
    holder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    method = next(
        node for node in holder.body if isinstance(node, ast.FunctionDef) and node.name == "take_damage"
    )
    args = [arg.arg for arg in method.args.args]
    defaults = [ast.unparse(value) for value in method.args.defaults]
    text = ast.unparse(method)
    blind = next(
        node
        for node in ast.walk(method)
        if isinstance(node, ast.If) and "source is not None" in ast.unparse(node.test)
    )
    blind_text = ast.unparse(blind)
    comparisons = [
        ast.unparse(node)
        for node in ast.walk(method)
        if isinstance(node, ast.Compare)
        and any(
            part in ast.unparse(node) for part in ("self.team", "from_team")
        )
    ]
    return {
        "signature": args,
        "defaults": defaults,
        "from_team_reads": text.count("from_team") - 1,
        "blind_needs_source": "source is not None" in blind_text,
        "blind_is_normal_only": "damage_type == 'normal'" in blind_text,
        "blind_draws_inside_guard": "random.random()" in blind_text,
        "team_comparisons": comparisons,
        "credits_source": "credit_hero_damage(source, effective_damage)" in text,
        "killed_by_is_source": "self._killed_by = source" in text,
    }


def _run(
    kind,
    raw,
    from_team="blue",
    damage_type="normal",
    school=None,
    hp=None,
    blind=None,
    true_strike=False,
):
    cls = _harness()
    boss = cls(kind, LANE)
    if hp is not None:
        boss.hp = float(hp)
    source = None
    if blind is not None:
        source = SimpleNamespace(
            team="blue",
            alive=True,
            blind_timer=10,
            blind_amount=float(blind),
            items=SimpleNamespace(has_true_strike=lambda: bool(true_strike)),
        )
    effects = RecordingEffects()
    main_module = sys.modules["__main__"]
    previous_game = getattr(main_module, "game_instance", None)
    main_module.game_instance = SimpleNamespace(effects=effects)
    entity_stub = sys.modules["_entity"]
    real_credit = entity_stub.credit_hero_damage
    credits = []
    entity_stub.credit_hero_damage = lambda src, amount: credits.append(
        {"source": src, "amount": int(amount)}
    )
    draws = []
    real_random = _ENV_RANDOM.random

    def counting_random():
        draws.append(1.0)
        return real_random()

    _ENV_RANDOM.random = counting_random
    try:
        before = int(boss.hp)
        boss.take_damage(raw, from_team, damage_type=damage_type, source=source, school=school)
    finally:
        _ENV_RANDOM.random = real_random
        entity_stub.credit_hero_damage = real_credit
        if previous_game is None:
            del main_module.game_instance
        else:
            main_module.game_instance = previous_game
    return {
        "hp_loss": before - int(boss.hp),
        "blind_draws": len(draws),
        "credit_calls": len(credits),
        "credited": sum(row["amount"] for row in credits if row["source"] is not None),
        "killed_by": getattr(boss, "_killed_by", None),
        "alive": bool(boss.alive),
        "defeated": bool(boss.defeated),
        "hurt_flash_timer": int(boss.hurt_flash_timer),
    }


def _row(name, expected, note, **columns):
    return {"name": name, "note": note, "expected": expected, "columns": columns}


def source_fixture():
    cls = _harness()
    mini = cls(MINI, LANE)
    true_boss = cls(TRUE_BOSS, LANE)
    plain = _run(MINI, ARMORED_RAW)
    teams = [
        _run(MINI, ARMORED_RAW, from_team=team)["hp_loss"] for team in ("blue", "red", None)
    ]
    blinded = _run(MINI, ARMORED_RAW, blind=1.0)
    pierced = _run(MINI, ARMORED_RAW, blind=1.0, true_strike=True)
    lethal = _run(MINI, ARMORED_RAW, hp=50.0)
    armored_neutral = _run(TRUE_BOSS, ARMORED_RAW, school=None)
    armored_physical = _run(TRUE_BOSS, ARMORED_RAW, school="physical")
    armored_magic = _run(TRUE_BOSS, ARMORED_RAW, school="magic")
    fire_neutral = _run(TRUE_BOSS, ARMORED_RAW, damage_type="fire", school=None)
    fire_physical = _run(TRUE_BOSS, ARMORED_RAW, damage_type="fire", school="physical")
    cases = [
        _row(
            "sourceless_normal_hit",
            plain,
            "no source, no school: resilience only, no blind draw, no credit",
        ),
        _row(
            "team_variants",
            {"hp_losses": teams, "blind_draws": 0},
            "from_team is never read, so blue/red/None land the identical hit",
            **{"blue": teams[0], "red": teams[1], "none": teams[2]}
        ),
        _row(
            "blinded_attacker_control",
            blinded,
            "control: a real source with blind 1.0 consumes one draw and misses",
        ),
        _row(
            "true_strike_control",
            pierced,
            "control: the same blind is pierced by an item true strike",
        ),
        _row(
            "sourceless_lethal_hit",
            lethal,
            "lethal source-free hit: _killed_by stays None and the boss retires",
        ),
        _row(
            "armored_school_columns",
            {"neutral": armored_neutral["hp_loss"], "physical": armored_physical["hp_loss"],
             "magic": armored_magic["hp_loss"]},
            "Abaddon armour 32: only an explicit physical school cuts the hit",
        ),
        _row(
            "fire_school_columns",
            {"neutral": fire_neutral["hp_loss"], "physical": fire_physical["hp_loss"]},
            "the caller's school is the armour switch even for fire damage",
        ),
    ]
    return {
        "source": "`bosses/base_boss.py::Boss.take_damage` executed with the real class",
        "callsite": "godot_rebuild/scripts/match/prototype_battle.gd::_deliver_hit (BossState branch)",
        "signature_shape": _signature_shape(),
        "live_stats": {
            "raw": ARMORED_RAW,
            "mini": {"kind": MINI, "max_hp": int(mini.max_hp), "armor": int(mini.armor),
                     "damage_reduction": float(mini.damage_reduction)},
            "true_boss": {"kind": TRUE_BOSS, "max_hp": int(true_boss.max_hp),
                          "armor": int(true_boss.armor),
                          "damage_reduction": float(true_boss.damage_reduction)},
        },
        "cases": cases,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["signature_shape"]
    if shape["signature"] != ["self", "damage", "from_team", "damage_type", "source", "school"]:
        problems.append("Boss.take_damage signature drifted")
    if shape["from_team_reads"] != 0:
        problems.append("from_team is now read, re-audit the boss damage path")
    if not (
        shape["blind_needs_source"]
        and shape["blind_is_normal_only"]
        and shape["blind_draws_inside_guard"]
    ):
        problems.append("the source blind guard drifted")
    if shape["team_comparisons"]:
        problems.append("Boss.take_damage now compares teams: %s" % shape["team_comparisons"])
    if not (shape["credits_source"] and shape["killed_by_is_source"]):
        problems.append("the source attribution tail drifted")
    rows = {row["name"]: row["expected"] for row in fixture["cases"]}
    teams = rows["team_variants"]["hp_losses"]
    if len(set(teams)) != 1 or teams[0] <= 0:
        problems.append("team variants must land the identical hit")
    if rows["sourceless_normal_hit"]["blind_draws"] != 0:
        problems.append("a source-free hit must consume no blind draw")
    if rows["blinded_attacker_control"]["blind_draws"] != 1:
        problems.append("a blinded attacker must consume exactly one draw")
    if rows["blinded_attacker_control"]["hp_loss"] != 0:
        problems.append("blind 1.0 must miss")
    if rows["true_strike_control"]["hp_loss"] <= 0:
        problems.append("true strike must pierce the blind")
    lethal = rows["sourceless_lethal_hit"]
    if lethal["killed_by"] is not None or lethal["alive"] or not lethal["defeated"]:
        problems.append("a lethal source-free hit must leave _killed_by None and retire the boss")
    if rows["sourceless_normal_hit"]["credited"] != 0:
        problems.append("a source-free hit must credit nobody")
    columns = rows["armored_school_columns"]
    if not columns["physical"] < columns["neutral"]:
        problems.append("explicit physical school must cut the armoured hit")
    if columns["magic"] >= columns["neutral"]:
        problems.append("magic_resist must cut the armoured true boss")
    fire = rows["fire_school_columns"]
    if fire["neutral"] != columns["neutral"] or fire["physical"] != columns["physical"]:
        problems.append("fire rows must follow the caller school, not the damage type")
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print("boss sourceless delivery oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not (args.self_test or args.write):
        parser.error("one of the arguments --self-test --write is required")
    fixture = source_fixture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
        print("wrote %s (%d cases)" % (FIXTURE.name, len(fixture["cases"])))
        return 0
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture != committed:
        print("FAIL: fixture drift vs %s" % FIXTURE.name)
        return 1
    return _self_test(fixture)


if __name__ == "__main__":
    raise SystemExit(main())
