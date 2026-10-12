"""9j: source oracle for the Tempest Veil gates of `Hero`.

`hero_items.HeroItemInventory.is_veiled` (`hero_items.py:2119-2121`) is
`veil_timer > 0`, and the source reads it from three places in `_entity.py`:

* `:3799` - `Hero.update` builds `_disabled = stun_timer > 0 or
  inv.is_veiled()` and skips the opt-in auto-cast while it is set;
* `:4241` - `Hero._do_attack` returns before the swing is attempted;
* `:4589` - `Hero.take_damage` returns before evasion, mitigation, credit and
  every reactive item hook, so the owner is immune to ALL incoming damage
  (the gate needs `damage > 0`, and it sits after Shadow Realm, Windrun and
  Wind Wall, so those keep their own order and RNG draws).

This oracle executes the real `Hero.take_damage` method plus the real
module-level `resolve_damage_school` / `_is_physical_hit` helpers from
`_entity.py` (read-only) against a stub hero, and records what the ladder
does: HP delta, `credit_hero_damage` calls, `notify_damage_taken` calls,
Bristleback reflect calls, and how many `random.random()` draws the frame
consumed. The `native_old` column re-runs each case with the veil flag off,
which is exactly how the native build behaved before this layer (it read
`is_veiled()` only for the hero's own attack).

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""
import argparse
import ast
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_entity.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_veil_immunity_source.json"


def _source_text() -> str:
    return SOURCE.read_text(encoding="utf-8")


def _method_node(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for entry in node.body:
                if isinstance(entry, ast.FunctionDef) and entry.name == method_name:
                    return entry
    raise AssertionError("missing %s.%s" % (class_name, method_name))


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("missing module function " + name)


def _exec(segment: str, namespace: dict) -> None:
    exec(compile(textwrap.dedent(segment), "<entity-source>", "exec"), namespace)


def _take_damage_callable() -> object:
    """Compile the real `Hero.take_damage` body into a plain callable."""
    tree = ast.parse(_source_text())
    method = _method_node(tree, "Hero", "take_damage")
    helpers = [
        _function_node(tree, "_is_physical_hit"),
        _function_node(tree, "resolve_damage_school"),
    ]

    class _Recorder:
        def __init__(self):
            self.rolls = []

        def __call__(self, _source, _damage):
            self.rolls.append([_source is not None, int(_damage)])

    credits = _Recorder()
    namespace = {
        "random": _RecordingRandom([0.0]),
        "credit_hero_damage": lambda source, damage: credits(source, damage),
        "_ACTIVE_HERO": [None],
        "_recorder": credits,
    }
    for node in helpers:
        _exec(ast.get_source_segment(_source_text(), node), namespace)
    _exec(ast.get_source_segment(_source_text(), method), namespace)
    return namespace["take_damage"], credits


class _RecordingRandom:
    """`random` replacement that counts draws and replays a fixed script."""

    def __init__(self, draws):
        self.script = list(draws)
        self.draws = 0

    def random(self):
        self.draws += 1
        if self.script:
            return self.script.pop(0)
        return 0.0


class _FakeItems:
    def __init__(self, veil=False, evasion=0.0, armor=0, block=None, guard=0):
        self.veil = veil
        self.evasion = evasion
        self.armor = armor
        self.block = block
        self.aura_guard_block = guard
        self.notified = 0

    def is_veiled(self):
        return self.veil

    def get_evasion(self):
        return self.evasion

    def has_true_strike(self):
        return False

    def get_armor(self):
        return self.armor

    def get_block(self):
        return self.block

    def notify_damage_taken(self, damage=0, source=None):
        self.notified += 1


class _FakeHero:
    def __init__(self, case):
        self.hp = 1000.0
        self.alive = True
        self.team = "blue"
        self.x = 0.0
        self.y = 0.0
        self.radius = 16.0
        self.stun_timer = 0
        self.auto_cast_enabled = False
        self.dmg_amp_timer = int(case.get("dmg_amp_timer", 0))
        self.dmg_amp_amount = float(case.get("dmg_amp_amount", 0.0))
        self.armor_shred_amount = float(case.get("armor_shred", 0.0))
        self.blind_timer = 0
        self.blind_amount = 0.0
        self._school = None
        self._shadow_realm_active = bool(case.get("shadow_realm"))
        self._windrun_active = bool(case.get("windrun"))
        self._wind_wall_timer = 30 if case.get("wind_wall") else 0
        self._bristleback_active = bool(case.get("bristleback"))
        self.items = _FakeItems(
            veil=bool(case.get("veil")),
            evasion=float(case.get("evasion", 0.0)),
            armor=int(case.get("armor", 0)),
            block=case.get("block"),
            guard=int(case.get("guard_block", 0)),
        )
        self.reflects = 0

    def take_damage(self, damage, team, source=None):
        # Bristleback reflect target: only armed when the attacker is a live
        # enemy hero, exactly like the source guard.
        self.reflects += 1


def _case(name, **overrides):
    case = {
        "name": name,
        "veil": False,
        "damage": 200,
        "damage_type": "normal",
        "school": None,
        "source_school": "physical",
        "evasion": 0.0,
        "armor": 0,
        "block": None,
        "guard_block": 0,
        "bristleback": False,
        "shadow_realm": False,
        "windrun": False,
        "wind_wall": False,
        "draws": [0.1],
    }
    case.update(overrides)
    return case


def _run_case(take_damage, case, veil_override=None):
    veil = bool(case["veil"]) if veil_override is None else bool(veil_override)
    active = _case(case["name"], **{k: v for k, v in case.items() if k != "name"})
    active["veil"] = veil
    hero = _FakeHero(active)
    attacker = None
    if case["source_school"] is not None:
        attacker = _FakeHero({"veil": False})
        attacker.dmg_school = case["source_school"]
        attacker.team = "red"
        attacker.alive = True
    rng = _RecordingRandom(case["draws"])
    frame = take_damage.__globals__
    frame["random"] = rng
    frame["_ACTIVE_HERO"] = [None]
    credits_before = len(frame["_recorder"].rolls)
    take_damage(
        hero,
        int(case["damage"]),
        "red",
        damage_type=case["damage_type"],
        source=attacker,
        school=case["school"],
    )
    credits = frame["_recorder"].rolls[credits_before:]
    return {
        # Bristleback reflect lands on the attacker stub, not on the victim.
        "hp_loss": int(1000.0 - hero.hp),
        "school": hero._school,
        "credits": [[bool(row[0]), int(row[1])] for row in credits],
        "notified": hero.items.notified,
        "reflects": attacker.reflects if attacker is not None else 0,
        "random_draws": rng.draws,
    }


CASES = [
    _case("veil_on_normal_hit", veil=True),
    _case("veil_on_projectile_hit", veil=True, damage_type="projectile"),
    _case("veil_on_magic_school", veil=True, school="magic", source_school="magic"),
    _case("veil_on_unarmed_burn", veil=True, damage_type="fire", source_school=None),
    _case("veil_on_zero_damage", veil=True, damage=0, source_school=None),
    _case("veil_off_control", veil=False),
    _case(
        "veil_on_with_bristleback",
        veil=True,
        bristleback=True,
        source_school="physical",
    ),
    _case("veil_on_with_evasion_roll", veil=True, evasion=0.75, draws=[0.01]),
    _case(
        "veil_off_with_evasion_roll",
        veil=False,
        evasion=0.75,
        draws=[0.01],
    ),
    _case("veil_on_with_windrun", veil=True, windrun=True, draws=[0.01]),
    _case("veil_on_with_shadow_realm", veil=True, shadow_realm=True),
    _case("veil_on_with_wind_wall_magic", veil=True, wind_wall=True, school="magic"),
    _case(
        "veil_on_with_wind_wall_physical",
        veil=True,
        wind_wall=True,
        damage_type="projectile",
        draws=[0.01],
    ),
    _case("veil_on_with_armor", veil=True, armor=40),
    _case("veil_off_with_armor", veil=False, armor=40),
]


def _shape_flags() -> dict:
    text = _source_text()
    tree = ast.parse(text)
    veil_branch = _first_if(tree, "is_veiled()", "damage > 0")
    veil_line = veil_branch.lineno
    evasion_line = min(
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and ast.unparse(node.test).startswith("_is_physical_hit(damage_type, self._school)")
    )
    condition = ast.unparse(veil_branch.test)
    update_gate = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "_disabled" for t in node.targets)
    )
    do_attack_source = ast.get_source_segment(
        text, _method_node(tree, "Hero", "_do_attack")
    )
    is_veiled_source = ast.get_source_segment(
        text, _method_node(tree, "HeroItemInventory", "is_veiled")
    ) if _has_class(tree, "HeroItemInventory") else _hero_items_is_veiled()
    return {
        "veil_gate_requires_positive_damage": "damage > 0" in condition,
        "veil_gate_reads_is_veiled": "is_veiled()" in condition,
        "veil_gate_precedes_evasion_block": veil_line < evasion_line,
        "update_gate_disables_autocast_while_veiled": "is_veiled()" in ast.unparse(
            update_gate.value
        ),
        "do_attack_gate_disables_attacks_while_veiled": "is_veiled()"
        in do_attack_source,
        "is_veiled_is_veil_timer_positive": "veil_timer > 0" in is_veiled_source,
        "take_damage_gate_returns_before_mitigation": veil_line
        < _first_if(tree, "damage_type != 'fire'").lineno,
    }


def _first_if(tree: ast.Module, *needles: str) -> ast.If:
    """The earliest `if` whose condition text carries every needle."""
    matches = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        condition = ast.unparse(node.test)
        if all(needle in condition for needle in needles):
            matches.append(node)
    assert matches, "missing branch condition: %s" % " & ".join(needles)
    return min(matches, key=lambda node: node.lineno)


def _has_class(tree: ast.Module, name: str) -> bool:
    return any(isinstance(node, ast.ClassDef) and node.name == name for node in tree.body)


def _hero_items_is_veiled() -> str:
    hero_items = (ROOT / "hero_items.py").read_text(encoding="utf-8")
    tree = ast.parse(hero_items)
    return ast.get_source_segment(hero_items, _method_node(tree, "HeroItemInventory", "is_veiled"))


def source_fixture() -> dict:
    take_damage, _credits = _take_damage_callable()
    rows = []
    for case in CASES:
        expected = _run_case(take_damage, case)
        native_old = _run_case(take_damage, case, veil_override=False)
        rows.append(
            {
                "name": case["name"],
                "veil": bool(case["veil"]),
                "damage": int(case["damage"]),
                "damage_type": case["damage_type"],
                "school": case["school"],
                "source_school": case["source_school"],
                "evasion": float(case["evasion"]),
                "armor": int(case["armor"]),
                "bristleback": bool(case["bristleback"]),
                "shadow_realm": bool(case["shadow_realm"]),
                "windrun": bool(case["windrun"]),
                "wind_wall": bool(case["wind_wall"]),
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": "_entity.py::Hero.take_damage:4525 (+ veil gate :4589) + Hero.update:3799 (_disabled) + Hero._do_attack:4241",
        "cases": rows,
        "shape": _shape_flags(),
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
    print("veil immunity oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
