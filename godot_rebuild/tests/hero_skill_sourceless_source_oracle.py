"""9m: source oracle for the sourceless delivery of Thorne's Viscous Nose (Q).

`hero_skills/_bundle.py::_NS_thorne_skills.cast_q` (`:4563-4609`) sprays a 60 px
cone (half angle 30 degrees) in front of the hero and, for every enemy inside
it, runs

    e.take_damage(int(h.skill_damage * 0.8), h.team)   # :4601
    self._apply_slow(e, 0.4, 180)                      # :4603

Two positional arguments and nothing else: no `source=`, no school, no
`damage_type`, so `Hero.take_damage` runs with `source=None` and
`_school = resolve_damage_school('normal', None, None, target_is_hero=False)
= None`, and a Tower/Castle victim resolves `_sch = None` too. Consequences the
native arm got wrong before this layer (it passed `hero.id` + `hero.dmg_school`):

* **no credit** - `credit_hero_damage(None, damage)` returns immediately, so the
  hit never lands in `hero.damage_dealt` (the ATTACK DAMAGE DEALER picker);
* **sourceless evasion** - the victim's evasion still applies, but the
  attacker's true strike / blind is not consulted (`source is None`);
* **no school mitigation on non-hero victims** - a `Tower.take_damage` with
  `_sch = None` applies neither armor nor magic resist.

This oracle executes the real `cast_q` method (AST extraction; the Q gate,
target check and cooldown triggers are stubbed) against recording victims, and
computes both columns of the victim ladder by executing the real
`Hero.take_damage` (via the 9j harness) and the real `Tower.take_damage`:
`expected` follows the recorded sourceless call, `native_old` re-runs the same
victim with `source=<attacker hero>` and the attacker school, which is what the
native arm did before this layer.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""
import argparse
import ast
import json
import math
import textwrap
from pathlib import Path

from hero_veil_immunity_source_oracle import (
    _case,
    _run_case,
    _take_damage_callable,
)

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "hero_skills" / "_bundle.py"
ENTITY = ROOT / "_entity.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_skill_sourceless_source.json"
# Thorne's kit in the source catalog: skill_base 70 -> int(70 * 0.8) = 56.
THORNE_SKILL_BASE = 70
MULTIPLIER = 0.8
CONE_LENGTH = 60.0
CONE_HALF_ANGLE = math.pi / 6.0
SLOW = [0.4, 180]
# Tower armour the tower rows pin (the tower rows only prove the school gate;
# the arm itself never sends a school).
TOWER_ARMOR = 6.0


class _RecordingVictim:
    """Unit/structure the executed source arm hits."""

    def __init__(self, name, x, y, team="red"):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.team = team
        self.alive = True
        self.calls = []

    def take_damage(self, damage, from_team, damage_type="normal", source=None, school=None):
        self.calls.append(
            {
                "damage": int(damage),
                "from_team": from_team,
                "damage_type": damage_type,
                "source": source is not None,
                "school": school,
            }
        )


class _StubSkill:
    """`self` for the extracted `cast_q`; every helper is a recorded stub."""

    def __init__(self, hero, enemies):
        self.hero = hero
        self.enemies = list(enemies)
        self.slows = []
        self.triggered = 0
        self.viscous_timer = 0

    def _check_q_cooldown(self):
        return True

    def _has_target(self, *_args):
        return bool(self.enemies)

    def _get_enemies(self, *_args):
        return list(self.enemies)

    def _apply_slow(self, target, amount, duration):
        self.slows.append([target.name, float(amount), int(duration)])

    def _trigger_q_cooldown(self, shake_amount=0):
        self.triggered += 1
        self.shake = shake_amount
        return True


class _StubHero:
    def __init__(self, x=0.0, y=0.0, facing=1, team="blue", skill_damage=THORNE_SKILL_BASE):
        self.x = float(x)
        self.y = float(y)
        self.facing = facing
        self.team = team
        self.skill_damage = skill_damage
        self.hp = 1000.0
        self.max_hp = 1000.0
        self._viscous_nose_active = False
        self._viscous_nose_timer = 0


def _cast_q_callable():
    """Compile the real `_NS_thorne_skills.cast_q` into a plain callable."""
    text = BUNDLE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    holder = next(
        node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "_NS_thorne_skills"
    )
    method = next(
        node
        for node in ast.walk(holder)
        if isinstance(node, ast.FunctionDef)
        and node.name == "cast_q"
        and "Viscous Nose" in (ast.get_source_segment(text, node) or "")
    )
    namespace = {"math": math}
    exec(compile(textwrap.dedent(ast.get_source_segment(text, method)), "<thorne-q>", "exec"), namespace)
    return namespace["cast_q"], text, method


def _run_source_arm():
    """Run the executed arm against the recording cone layout."""
    cast_q, _text, _method = _cast_q_callable()
    hero = _StubHero()
    inside = _RecordingVictim("unit_in_cone", 40.0, 0.0)
    behind = _RecordingVictim("unit_behind", -40.0, 0.0)
    outside_angle = _RecordingVictim("unit_outside_cone", 40.0, 40.0)
    too_far = _RecordingVictim("unit_too_far", 90.0, 0.0)
    structure = _RecordingVictim("structure_in_cone", 30.0, 0.0)
    skill = _StubSkill(hero, [inside, behind, outside_angle, too_far, structure])
    result = cast_q(skill, [], [], [])
    return {
        "result": bool(result),
        "skill": skill,
        "victims": {
            "unit_in_cone": inside,
            "unit_behind": behind,
            "unit_outside_cone": outside_angle,
            "unit_too_far": too_far,
            "structure_in_cone": structure,
        },
        "hero": hero,
    }


def _hero_ladder(take_damage, raw, *, sourced, armor=0):
    case = _case(
        "ladder",
        damage=raw,
        damage_type="normal",
        school="physical" if sourced else None,
        source_school="physical" if sourced else None,
        armor=armor,
        draws=[0.90],
    )
    return _run_case(take_damage, case)


def _tower_take_damage():
    """Compile the real `Tower.take_damage` into a plain callable (stub tower)."""
    text = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(text)
    holder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Tower")
    method = next(
        node for node in holder.body if isinstance(node, ast.FunctionDef) and node.name == "take_damage"
    )
    helper = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "resolve_damage_school":
            helper = node
            break
    credits = []
    namespace = {
        "credit_hero_damage": lambda source, amount: credits.append([source is not None, int(amount)]),
        "SoundManager": type("SoundManager", (), {"play": lambda self, *_a, **_k: None}),
        "_ACTIVE_HERO": [None],
        "_credits": credits,
    }
    if helper is not None:
        exec(compile(textwrap.dedent(ast.get_source_segment(text, helper)), "<entity>", "exec"), namespace)
    exec(compile(textwrap.dedent(ast.get_source_segment(text, method)), "<entity>", "exec"), namespace)
    return namespace["take_damage"], namespace


class _StubTower:
    def __init__(self, armor, hp=1000.0):
        self.armor = float(armor)
        self.magic_resist = 0.0
        self.shield = 0
        self.hp = float(hp)
        self.alive = True
        self.no_damage_timer = 0
        self._killed_by = None
        self.school = None


def _tower_ladder(raw, *, sourced, armor=TOWER_ARMOR):
    take_damage, namespace = _tower_take_damage()
    tower = _StubTower(armor)
    source = _StubHero(team="blue") if sourced else None
    namespace["_credits"].clear()
    take_damage(
        tower,
        raw,
        "blue",
        damage_type="normal",
        source=source,
        school="physical" if sourced else None,
    )
    return {
        "hp_loss": int(1000.0 - tower.hp),
        "credits": [row for row in namespace["_credits"]],
    }


def source_fixture() -> dict:
    arm = _run_source_arm()
    record = arm["victims"]["unit_in_cone"].calls
    raw = int(record[0]["damage"]) if record else 0
    hero_take_damage, _credits = _take_damage_callable()
    rows = [
        {
            "name": "hero_victim_no_items",
            "victim": "hero",
            "item_armor": 0,
            "raw_damage": raw,
            "expected": _hero_ladder(hero_take_damage, raw, sourced=False),
            "native_old": _hero_ladder(hero_take_damage, raw, sourced=True),
        },
        {
            "name": "hero_victim_item_armor",
            "victim": "hero",
            "item_armor": 6,
            "raw_damage": raw,
            "expected": _hero_ladder(hero_take_damage, raw, sourced=False, armor=6),
            "native_old": _hero_ladder(hero_take_damage, raw, sourced=True, armor=6),
        },
        {
            "name": "tower_victim_sourceless",
            "victim": "tower",
            "tower_armor": TOWER_ARMOR,
            "raw_damage": raw,
            "expected": _tower_ladder(raw, sourced=False),
            "native_old": _tower_ladder(raw, sourced=True),
        },
        {
            "name": "tower_victim_no_armor",
            "victim": "tower",
            "tower_armor": 0,
            "raw_damage": raw,
            "expected": _tower_ladder(raw, sourced=False, armor=0),
            "native_old": _tower_ladder(raw, sourced=True, armor=0),
        },
    ]
    text = BUNDLE.read_text(encoding="utf-8")
    method_segment = ast.get_source_segment(text, _cast_q_callable()[2])
    shape = {
        "take_damage_has_two_positional_args": "take_damage(int(h.skill_damage * 0.8), h.team)" in method_segment,
        "take_damage_passes_no_source": "source=" not in method_segment,
        "take_damage_passes_no_school": "school=" not in method_segment,
        "damage_multiplier_is_0_8": "skill_damage * 0.8" in method_segment,
        "cone_length_is_60": "cone_length = 60" in method_segment,
        "cone_half_angle_is_30_degrees": "cone_width = math.pi / 3" in method_segment,
        "slow_is_0_4_for_180_ticks": "_apply_slow(e, 0.4, 180)" in method_segment,
    }
    return {
        "source": "hero_skills/_bundle.py::_NS_thorne_skills.cast_q :4563-4609",
        "native_old_model": (
            "pre-9m native arm: `_deliver_hit(hero.id, ..., hero.dmg_school)` -"
            " credits damage_dealt, consults the attacker's true strike/blind and"
            " applies school mitigation on non-hero victims"
        ),
        "arm": {
            "skill_base": THORNE_SKILL_BASE,
            "multiplier": MULTIPLIER,
            "cone_length": CONE_LENGTH,
            "cone_half_angle": CONE_HALF_ANGLE,
            "slow": SLOW,
            "record": record,
            "hit_targets": sorted(name for name, victim in arm["victims"].items() if victim.calls),
            "slow_targets": arm["skill"].slows,
        },
        "shape": shape,
        "cases": rows,
    }


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
    if committed != fixture:
        print("FAIL: fixture drift vs %s" % FIXTURE)
        return 1
    print("sourceless skill oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
