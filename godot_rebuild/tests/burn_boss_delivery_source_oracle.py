"""9ab: the boss burn tick is a source-free fire hit with the boss damage number.

`_core.py::TowerDebuffMixin._tick_tower_debuffs` fires once per
`TOWER_DEBUFF_BURN_TICK` (30) frames with

    self.burn_accum -= dmg
    self.take_damage(dmg, self.burn_team or self.team, "fire")

- three positional arguments, no `source=` and no `school=`. The boss therefore
runs the real `Boss.take_damage` ladder at `damage_type='fire'`, `source=None`:

* the Soul Rend amp applies (`bosses/base_boss.py:6003-6007`),
* the Corroder shred is skipped because `damage_type != 'fire'` is false,
* the school stays unresolved - fire never consults armour (native `"neutral"`),
* inherent resilience (0.20 mini / 0.30 true, 0.45 with `defense_boost`) applies,
* the anti-burst cap clamps the hit, and a lethal tick leaves `_killed_by = None`
  while clearing every tower debuff and queueing the source death snapshot,
* the presentation tail is

    game.effects.add_damage_number(
        self.x, self.y - self.radius - 10, effective_damage,
        is_critical=(effective_damage > self.max_hp * 0.03),
        damage_type=damage_type)
    game.effects.add_hit_particles(self.x, self.y, team=self.team, count=6)

Native already delivers the payload through `BossState.take_damage` (layer 8g),
so no `expected` number moves in this layer. What moved is the presentation:
the flat `dealt > 100` crit rule painted a 210 damage burn tick on Abaddon
(max_hp 36000, source threshold 1080) gold, while the source shows a plain
number. Every row therefore records the executed source ladder plus the
pre-9ab presentation model as the `native_old` column.

The rows execute the real `Boss.take_damage` and the real mixin tick through the
`boss_core_source_oracle` harness, with a recording wrapper around `take_damage`
so the tick payload and the `burn_team or team` fallback are visible.

`--self-test` verifies the executed rows and the AST shapes; `--write` is the
only fixture writer.
"""

import argparse
import ast
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from boss_core_source_oracle import boss_class, namespace  # noqa: E402
from boss_debuff_clock_source_oracle import source_class as mixin_class  # noqa: E402
from boss_kill_credit_source_oracle import RecordingEffects  # noqa: E402
from burn_tick_delivery_source_oracle import _burn_shape  # noqa: E402
from check_source_contract import source_lanes  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "burn_boss_delivery_source.json"
BOSS_SOURCE = ROOT / "bosses" / "base_boss.py"
MINI = "gornak"
TRUE_BOSS = "abaddon"
# One tick of a 60 dps burn: 60 / 60 fps * 30 frames. `burn_accum` is primed so
# the tick lands exactly 30 (30.5 -> int 30) and 0.5 stays accumulated.
DPS = 60.0
TICK_FRAMES = 30
PRIMED_ACCUM = 29.5
CRIT_PCT = 0.03
# Presentation model replaced by this layer: `dealt > 100`.
OLD_CRIT_THRESHOLD = 100

_ENV = None
BOSS_CLS = None
MIXIN = None
LANE = None


def _harness():
    global _ENV, BOSS_CLS, MIXIN, LANE
    if _ENV is None:
        _ENV = namespace()
        BOSS_CLS = boss_class(_ENV)
        MIXIN = mixin_class()
        LANE = source_lanes()["mid"]
    return BOSS_CLS


def _boss_number_shape() -> dict:
    tree = ast.parse(BOSS_SOURCE.read_text(encoding="utf-8"))
    holder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    method = next(
        node for node in holder.body if isinstance(node, ast.FunctionDef) and node.name == "take_damage"
    )
    calls = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_damage_number"
    ]
    call = calls[0]
    crit = next(keyword for keyword in call.keywords if keyword.arg == "is_critical")
    particles = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_hit_particles"
    ]
    return {
        "damage_numbers_calls": len(calls),
        "x_is_self_x": ast.unparse(call.args[0]) == "self.x",
        "y_is_self_y_radius_minus_10": ast.unparse(call.args[1]) == "self.y - self.radius - 10",
        "damage_is_effective": ast.unparse(call.args[2]) == "effective_damage",
        "crit_is_hp_pct": ast.unparse(crit.value) == "effective_damage > self.max_hp * 0.03",
        "damage_type_kwarg": any(
            keyword.arg == "damage_type" and ast.unparse(keyword.value) == "damage_type"
            for keyword in call.keywords
        ),
        "particles_count": int(particles[0].keywords[-1].value.value) if particles else 0,
        "killed_by_is_source": "self._killed_by = source" in ast.unparse(method),
        "clears_debuffs_on_death": "self.clear_tower_debuffs()" in ast.unparse(method),
    }


def _run_ticks(kind, state, ticks=1):
    cls = _harness()
    boss = cls(kind, LANE)
    boss._tick_tower_debuffs = types.MethodType(MIXIN._tick_tower_debuffs, boss)
    for field, value in state.items():
        setattr(boss, field, value)
    calls = []
    credits = []
    real_take = boss.take_damage

    def take(damage, from_team, damage_type="normal", source=None, school=None):
        calls.append(
            {"damage": int(damage), "from_team": from_team, "damage_type": damage_type}
        )
        return real_take(damage, from_team, damage_type=damage_type, source=source, school=school)

    boss.take_damage = take
    effects = RecordingEffects()
    main_module = sys.modules["__main__"]
    previous_game = getattr(main_module, "game_instance", None)
    main_module.game_instance = SimpleNamespace(effects=effects)
    entity_stub = sys.modules["_entity"]
    real_credit = entity_stub.credit_hero_damage
    entity_stub.credit_hero_damage = lambda source, amount: credits.append(
        {"source": source, "amount": int(amount)}
    )
    try:
        hp_before = int(boss.hp)
        for _ in range(ticks):
            boss._tick_tower_debuffs()
    finally:
        entity_stub.credit_hero_damage = real_credit
        if previous_game is None:
            del main_module.game_instance
        else:
            main_module.game_instance = previous_game
    return {
        "hp_loss": hp_before - int(boss.hp),
        "damage_calls": calls,
        "credits": credits,
        "killed_by": getattr(boss, "_killed_by", None),
        "alive": bool(boss.alive),
        "defeated": bool(boss.defeated),
        "burn_timer": int(boss.burn_timer),
        "burn_accum": round(float(boss.burn_accum), 4),
        "burn_tick_cd": int(boss.burn_tick_cd),
        "damage_numbers": effects.damage_numbers,
    }


def _columns(result, max_hp):
    loss = int(result["hp_loss"])
    numbers = result["damage_numbers"]
    number = numbers[-1] if numbers else {}
    return {
        "hp_loss": loss,
        "damage_calls": result["damage_calls"],
        "credits": len([row for row in result["credits"] if row["source"] is not None]),
        "credit_calls": len(result["credits"]),
        "killed_by": result["killed_by"],
        "alive": result["alive"],
        "defeated": result["defeated"],
        "damage_number_y": round(float(number.get("y", 0.0)), 4),
        "damage_number_type": str(number.get("damage_type", "")),
        "is_critical": bool(number.get("is_critical", False)),
        "burn_timer": result["burn_timer"],
        "burn_accum": result["burn_accum"],
        "burn_tick_cd": result["burn_tick_cd"],
        "source_crit_threshold": round(float(max_hp) * CRIT_PCT, 4),
    }


def _native_old(result, max_hp):
    # Pre-9ab native model: `dealt > 100` for the crit badge and
    # `position.y - radius` (no `- 10`) for the number anchor.
    number = result["damage_numbers"][-1] if result["damage_numbers"] else {}
    return {
        "hp_loss": int(result["hp_loss"]),
        "is_critical": int(result["hp_loss"]) > OLD_CRIT_THRESHOLD,
        "damage_number_y": round(float(number.get("y", 0.0)) + 10.0, 4),
        "source_crit_threshold": round(float(max_hp) * CRIT_PCT, 4),
    }


def _case(name, kind, state, note, ticks=1):
    cls = _harness()
    stats = cls(kind, LANE)
    max_hp = float(stats.max_hp)
    result = _run_ticks(kind, state, ticks)
    return {
        "name": name,
        "kind": kind,
        "note": note,
        "input": dict(state, **{"ticks": ticks}),
        "expected": _columns(result, max_hp),
        "native_old": _native_old(result, max_hp),
    }


def _refresh_case(name, kind, state, note):
    cls = _harness()
    boss = cls(kind, LANE)
    refresh_dps = float(state.get("refresh_dps", DPS))
    refresh_duration = int(state.get("refresh_duration", 120))
    refresh_team = state.get("refresh_team")
    for field, value in state.items():
        if field in ("refresh_dps", "refresh_duration", "refresh_team"):
            continue
        setattr(boss, field, value)
    boss.apply_debuff("burn", refresh_dps, refresh_duration, source_team=refresh_team)
    return {
        "name": name,
        "kind": kind,
        "note": note,
        "input": dict(state),
        "result": {
            "burn_dps": round(float(boss.burn_dps), 4),
            "burn_timer": int(boss.burn_timer),
            "burn_accum": round(float(boss.burn_accum), 4),
            "burn_tick_cd": int(boss.burn_tick_cd),
            "burn_team": boss.burn_team,
        },
    }


def source_fixture():
    cls = _harness()
    mini = cls(MINI, LANE)
    true_boss = cls(TRUE_BOSS, LANE)
    base = {"burn_dps": DPS, "burn_accum": PRIMED_ACCUM, "burn_tick_cd": 1, "burn_timer": 120}
    cases = [
        _case(
            "mini_boss_burn_tick",
            MINI,
            dict(base, burn_team="blue"),
            "plain 60 dps tick on a mini boss: 30 -> 0.20 resilience -> 24, crit is false on both columns",
        ),
        _case(
            "true_boss_burn_tick_big_payload",
            TRUE_BOSS,
            dict(base, burn_dps=18000.0, burn_accum=0.0, burn_team="blue"),
            "300 fire damage on a true boss: 210 dealt stays under the 1080 source threshold but the flat 100 rule painted it gold",
        ),
        _case(
            "mini_boss_burn_tick_big_payload",
            MINI,
            dict(base, burn_dps=18000.0, burn_accum=0.0, burn_team="blue"),
            "same payload on a mini boss: 240 dealt clears both thresholds (control row)",
        ),
        _case(
            "burn_tick_team_fallback",
            MINI,
            dict(base),
            "burn_team None falls back to the boss team in the tick payload",
        ),
        _case(
            "amped_burn_tick",
            MINI,
            dict(base, burn_team="blue", dmg_amp_amount=0.5, dmg_amp_timer=120),
            "Soul Rend amp runs before the fire branch: 30 -> 45 -> 0.20 resilience -> 36",
        ),
        _case(
            "shred_burn_tick",
            MINI,
            dict(base, burn_team="blue", armor_shred_amount=5.0, armor_shred_timer=120),
            "Corroder shred is skipped for fire, so the payload stays 24",
        ),
        _case(
            "armored_true_boss_burn_tick",
            TRUE_BOSS,
            dict(base, burn_team="blue", burn_dps=18000.0, burn_accum=0.0),
            "armour 32 on Abaddon never cuts a fire tick: the school stays unresolved",
        ),
        _case(
            "defense_boost_burn_tick",
            MINI,
            dict(base, burn_team="blue", defense_boost=True),
            "defense_boost lifts resilience to 0.45: 30 -> 16",
        ),
        _case(
            "capped_burn_tick",
            MINI,
            dict(base, burn_dps=200000.0, burn_accum=0.0, burn_team="blue"),
            "anti-burst cap clamps the tick to max_damage_per_hit 900 (control row)",
        ),
        _case(
            "lethal_burn_tick",
            MINI,
            dict(base, burn_team="blue", hp=20.0),
            "lethal tick: killed_by stays None, debts clear and the death snapshot becomes eligible",
        ),
    ]
    refreshes = [
        _refresh_case(
            "expired_burn_refresh",
            MINI,
            dict(burn_dps=0.0, burn_timer=0, burn_accum=9.9, burn_tick_cd=3, refresh_team="blue"),
            "an expired burn resets accum and the tick clock to the 30 frame interval",
        ),
        _refresh_case(
            "live_burn_refresh",
            MINI,
            dict(
                burn_dps=12.0,
                burn_timer=40,
                burn_accum=1.5,
                burn_tick_cd=7,
                refresh_team="red",
                refresh_dps=20.0,
                refresh_duration=10,
            ),
            "a live burn keeps the strongest dps, refreshes the longer duration and follows the new team",
        ),
    ]
    return {
        "source": "`_core.py::TowerDebuffMixin._tick_tower_debuffs` burn branch through the real `Boss.take_damage`",
        "callsite": "godot_rebuild/scripts/match/prototype_battle.gd::_step_active_boss + _boss_damage_number",
        "burn_shape": _burn_shape(),
        "boss_number_shape": _boss_number_shape(),
        "live_stats": {
            "dps": DPS,
            "tick_frames": TICK_FRAMES,
            "primed_accum": PRIMED_ACCUM,
            "crit_pct": CRIT_PCT,
            "old_crit_threshold": OLD_CRIT_THRESHOLD,
            "mini": {
                "kind": MINI,
                "max_hp": int(mini.max_hp),
                "radius": int(mini.radius),
                "damage_reduction": float(mini.damage_reduction),
                "max_damage_per_hit": int(mini.max_damage_per_hit),
            },
            "true_boss": {
                "kind": TRUE_BOSS,
                "max_hp": int(true_boss.max_hp),
                "radius": int(true_boss.radius),
                "damage_reduction": float(true_boss.damage_reduction),
                "max_damage_per_hit": int(true_boss.max_damage_per_hit),
            },
        },
        "cases": cases,
        "refreshes": refreshes,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["burn_shape"]
    if not (
        shape["take_damage_calls"] == 1
        and shape["three_positional_args"]
        and shape["third_arg_is_fire"]
        and shape["team_is_burn_team_or_team"]
        and shape["no_source_keyword"]
        and shape["no_school_keyword"]
        and shape["accum_drained_before"]
    ):
        problems.append("the source burn call shape drifted")
    if shape["burn_tick_interval"] != TICK_FRAMES or shape["burn_fps"] != 60.0:
        problems.append("the source burn interval constants drifted")
    number_shape = fixture["boss_number_shape"]
    if number_shape["damage_numbers_calls"] != 1 or not (
        number_shape["x_is_self_x"]
        and number_shape["y_is_self_y_radius_minus_10"]
        and number_shape["damage_is_effective"]
        and number_shape["crit_is_hp_pct"]
        and number_shape["damage_type_kwarg"]
        and number_shape["particles_count"] == 6
    ):
        problems.append("the source boss damage number shape drifted")
    if not (number_shape["killed_by_is_source"] and number_shape["clears_debuffs_on_death"]):
        problems.append("the source boss death tail drifted")
    live = fixture["live_stats"]
    for side in ("mini", "true_boss"):
        if live[side]["max_damage_per_hit"] != int(live[side]["max_hp"] * (0.12 if side == "mini" else 0.08)):
            problems.append("%s anti-burst cap drifted" % side)
    divergence = False
    for row in fixture["cases"]:
        expected = row["expected"]
        old = row["native_old"]
        label = row["name"]
        if not expected["damage_calls"]:
            problems.append("%s never fired a tick" % label)
            continue
        call = expected["damage_calls"][0]
        if call["damage_type"] != "fire" or call["from_team"] not in ("blue", "red", None):
            problems.append("%s tick payload drifted" % label)
        if expected["hp_loss"] <= 0:
            problems.append("%s must land damage" % label)
        if expected["is_critical"] != (expected["hp_loss"] > expected["source_crit_threshold"]):
            problems.append("%s crit column no longer follows the 3%% hp rule" % label)
        if expected["is_critical"] != old["is_critical"]:
            divergence = True
        if expected["credits"] != 0 or expected["killed_by"] is not None:
            problems.append("%s must stay unattributed" % label)
        if expected["credit_calls"] == 0:
            problems.append("%s never reached the credit hook" % label)
        if label == "burn_tick_team_fallback" and call["from_team"] != "red":
            problems.append("%s must fall back to the boss team" % label)
        if label == "lethal_burn_tick" and not (expected["defeated"] and not expected["alive"]):
            problems.append("%s must defeat the boss" % label)
        if label == "lethal_burn_tick" and not (
            expected["burn_timer"] == 0 and expected["burn_accum"] == 0.0
        ):
            problems.append("%s must clear the debuff store" % label)
        if label == "defense_boost_burn_tick" and expected["hp_loss"] != 16:
            problems.append("%s must record the 0.45 resilience" % label)
    if not divergence:
        problems.append("no row shows the presentation divergence this layer fixed")
    for row in fixture["refreshes"]:
        result = row["result"]
        if row["name"] == "expired_burn_refresh":
            if result["burn_tick_cd"] != TICK_FRAMES or result["burn_accum"] != 0.0:
                problems.append("expired refresh must reset the tick clock and accumulator")
            if result["burn_team"] != "blue":
                problems.append("expired refresh must adopt the source team")
        if row["name"] == "live_burn_refresh":
            if result["burn_dps"] != 20.0 or result["burn_timer"] != 40:
                problems.append("live refresh must keep the strongest dps and the longer duration")
            if result["burn_team"] != "red":
                problems.append("live refresh must follow the new team")
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print(
        "burn boss delivery oracle self-test passed: %d cases, %d refreshes"
        % (len(fixture["cases"]), len(fixture["refreshes"]))
    )
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
