"""Pin the attribution contract of the shared skill-delivery helper.

The source skill kits deliver damage through three shapes, all in
`hero_skills/_bundle.py`:

* `BaseSkill._deal_aoe_damage` (`:105-119`) - ATTRIBUTED. It sends
  `take_damage(damage, team, source=self.hero, school=<hero dmg_school>)`, so a
  tower armour/magic-resist cut applies and the dealing hero is credited.
* the kit tick/cast loops that call `take_damage(damage, team, source=h)` -
  ATTRIBUTED, with the school resolved from `source.dmg_school` inside
  `resolve_damage_school` (`_entity.py:106-130`) because no `school=` is sent.
* every other recipe call (`e.take_damage(int(h.skill_damage * mult), h.team)`)
  - SOURCELESS: two positional arguments, no `source=`, no `school=`, so the
  victim ladder sees `source=None` / `_school=None`: no credit, no armour cut.

The native port encodes that split in `skill_common.gd::hit(..., attributed)`
(`Common.hit(..., true)` = attributed) plus `world._deal_hero_aoe(...)` for the
attributed AoE helper. This oracle classifies every native site and every source
row, asserts the per-kit attributed/sourceless counts and the attributed
multiplier multisets, and executes the real ladders for the attributed and
sourceless shapes so the fixture records both columns.

`--self-test` verifies the executed rows and the site table against the
committed fixture; `--write` is the only fixture writer.
"""

import argparse
import ast
import json
import re
from pathlib import Path

from hero_skill_sourceless_source_oracle import (
    THORNE_SKILL_BASE,
    _StubTower,
    _tower_take_damage,
)
from hero_veil_immunity_source_oracle import _case, _run_case, _take_damage_callable
from minion_damage_ladder_source_oracle import (
    _FakeMinion,
    _case as _minion_case,
    _minion_take_damage_callable,
)
from minion_melee_school_source_oracle import _tres_number

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "hero_skills" / "_bundle.py"
SCRIPTS = ROOT / "godot_rebuild" / "scripts"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "skill_hit_attribution_source.json"
# The kits whose delivery sites the native port spells out per file. The boss
# recipes (`boss_level_*_skills.gd`) all run through `Common.hit` without the
# attributed flag, matching `BossHeroSkills` recipes in the source.
KITS = ("GrimjawSkills", "KaizenSkills", "ThorneSkills", "VexSkills", "ZephyrSkills", "BossHeroSkills")
FILE_KITS = {
    "grimjaw_skills.gd": "GrimjawSkills",
    "thorne_skills.gd": "ThorneSkills",
    "vex_skills.gd": "VexSkills",
    "zephyr_skills.gd": "ZephyrSkills",
    "minion_battle.gd": "KaizenSkills",
    "source_shared_boss_skills.gd": "BossHeroSkills",
    "alchemist_skills.gd": "BossHeroSkills",
}
VEX_MULTIPLIER = 2.5
GORNAK_MULTIPLIER = 1.2


def _native_sites() -> dict:
    """Classify every native delivery site (file -> counts + multiset)."""
    rows = {}
    for path in sorted(SCRIPTS.rglob("*.gd")):
        text = path.read_text(encoding="utf-8")
        hits = re.findall(r"Common\.hit\((.*?)\)\n", text, re.S)
        attributed = [row for row in hits if row.rstrip().endswith("true")]
        aoe = len(re.findall(r"_deal_hero_aoe\(", text)) - len(re.findall(r"func _deal_hero_aoe\(", text))
        direct = [
            " ".join(match.split())
            for match in re.findall(r"_deliver_hit\((.{0,200}?)\)", text, re.S)
        ]
        attributed_direct = [
            row for row in direct if row.startswith(("world.", "hero.id", "attacker.id"))
        ]
        sourceless_direct = [row for row in direct if row.startswith("-1")]
        if not hits and not aoe and not direct:
            continue
        rows[path.name] = {
            "hit_total": len(hits),
            "hit_attributed": len(attributed),
            "hit_sourceless": len(hits) - len(attributed),
            "aoe_sites": aoe,
            "direct_attributed": len(attributed_direct),
            "direct_sourceless": len(sourceless_direct),
            "attributed_mults": sorted(
                (" ".join(row.split())[:40]) for row in attributed
            ),
        }
    return rows


def _source_rows() -> list:
    """Every `take_damage` / `_deal_aoe_damage` row of the shared kits."""
    text = BUNDLE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    rows = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name not in KITS:
            continue
        for fn in node.body:
            if not isinstance(fn, ast.FunctionDef):
                continue
            for stmt in ast.walk(fn):
                if not isinstance(stmt, ast.Call):
                    continue
                callee = getattr(stmt.func, "attr", getattr(stmt.func, "id", ""))
                if callee == "take_damage":
                    args = [ast.unparse(arg) for arg in stmt.args]
                    attributed = any(
                        kw.arg == "source"
                        and not (isinstance(kw.value, ast.Constant) and kw.value.value is None)
                        for kw in stmt.keywords
                    )
                    rows.append(
                        dict(kit=node.name, method=fn.name, kind="hit",
                             multiplier=args[0] if args else "", attributed=attributed)
                    )
                elif callee == "_deal_aoe_damage":
                    mult = None
                    for kw in stmt.keywords:
                        if kw.arg == "damage_multiplier":
                            mult = ast.unparse(kw.value)
                    if mult is None and len(stmt.args) > 3:
                        mult = ast.unparse(stmt.args[3])
                    rows.append(
                        dict(kit=node.name, method=fn.name, kind="aoe",
                             multiplier=mult or "", attributed=True)
                    )
    return rows


def _native_tokens() -> dict:
    """Plain substring counts the GDScript suite recomputes live."""
    tokens = {}
    for path in sorted(SCRIPTS.rglob("*.gd")):
        text = path.read_text(encoding="utf-8")
        if not text.count("Common.hit(") and not text.count("_deal_hero_aoe(") and not text.count(
            "_deliver_hit("
        ):
            continue
        hits = re.findall(r"Common\.hit\((.*?)\)\n", text, re.S)
        tokens["res://scripts/%s" % path.relative_to(SCRIPTS).as_posix()] = {
            "common_hit": len(hits),
            # Only the `Common.hit(...)` bodies count, so an unrelated
            # `, true)` (e.g. the 9z burn tick passing its team-guard flag)
            # cannot drift this token.
            "hit_true_suffix": sum(1 for row in hits if row.rstrip().endswith("true")),
            "aoe_calls": text.count("_deal_hero_aoe(") - text.count("func _deal_hero_aoe("),
        }
    return tokens


def _kit_counts(rows, kit) -> dict:
    subset = [row for row in rows if row["kit"] == kit]
    return {
        "attributed": sum(1 for row in subset if row["attributed"]),
        "sourceless": sum(1 for row in subset if not row["attributed"]),
        "aoe_sites": sum(1 for row in subset if row["kind"] == "aoe"),
        "attributed_multipliers": sorted(row["multiplier"] for row in subset if row["attributed"]),
    }


class _StubSource:
    """Minimal attacker stub the compiled ladders credit."""

    def __init__(self, school="physical", team="blue"):
        self.dmg_school = school
        self.team = team
        self.damage_dealt = 0
        self.alive = True
        self.hp = 1000.0
        self.max_hp = 1000.0


def _tres_text(path, key) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(key + " "):
            return line.split("=", 1)[1].strip().strip('"')
    raise KeyError(key)


def _minion_row(raw, *, school, sourced, armor=2.0, magic_resist=0.05) -> dict:
    take_damage, _resolve, recorder = _minion_take_damage_callable()
    victim = _FakeMinion(_minion_case("row", armor=armor, magic_resist=magic_resist))
    recorder.rolls.clear()
    take_damage(
        victim,
        raw,
        "blue",
        damage_type="normal",
        source=_StubSource(school) if sourced else None,
        school=school if sourced else None,
    )
    return {
        "hp_loss": int(1000 - victim.hp),
        "credited_total": sum(row[1] for row in recorder.rolls if row[0]),
    }


def _tower_row(raw, *, school, sourced, armor=3.0) -> dict:
    take_damage, namespace = _tower_take_damage()
    tower = _StubTower(armor)
    namespace["_credits"].clear()
    take_damage(
        tower,
        raw,
        "blue",
        damage_type="normal",
        source=_StubSource(school) if sourced else None,
        school=school if sourced else None,
    )
    return {
        "hp_loss": int(1000.0 - tower.hp),
        "credited_total": sum(row[1] for row in namespace["_credits"] if row[0]),
    }


class _StubMinion:
    def __init__(self, armor=2.0, magic_resist=0.05, hp=1000.0):
        self.hp = float(hp)
        self.max_hp = float(hp)
        self.alive = True
        self.armor = float(armor)
        self.magic_resist = float(magic_resist)
        self.armor_shred_amount = 0.0
        self.dmg_amp_timer = 0
        self.dmg_amp_amount = 0.0
        self.shadow_realm_timer = 0
        self.team = "red"


def _stub_minion() -> "_StubMinion":
    return _StubMinion()


def _stub_source() -> "_StubSource":
    return _StubSource()


def source_fixture() -> dict:
    native = _native_sites()
    rows = _source_rows()
    heroes = ROOT / "godot_rebuild" / "data" / "heroes"
    vex_base = int(_tres_number(heroes / "vex.tres", "base_skill"))
    thorne_base = int(_tres_number(heroes / "thorne.tres", "base_skill"))
    gornak_base = int(_tres_number(heroes / "gornak.tres", "base_skill"))
    vex_school = _tres_text(heroes / "vex.tres", "dmg_school")
    thorne_school = _tres_text(heroes / "thorne.tres", "dmg_school")
    vex_raw = int(vex_base * VEX_MULTIPLIER)
    thorne_raw = int(thorne_base * 1.2)
    gornak_raw = int(gornak_base * GORNAK_MULTIPLIER)
    cases = [
        dict(
            name="vex_r_attributed_on_troll",
            cast='VexSkills.cast(key="r")',
            source_shape="`_deal_aoe_damage` sends source=hero and school=hero.dmg_school",
            victim_kind="minion",
            school=vex_school,
            payload=vex_raw,
            expected=_minion_row(vex_raw, school=vex_school, sourced=True),
        ),
        dict(
            name="vex_r_sourceless_on_troll",
            cast='VexSkills.cast(key="r")',
            source_shape="two positional arguments (no source, no school)",
            victim_kind="minion",
            school=None,
            payload=vex_raw,
            expected=_minion_row(vex_raw, school=vex_school, sourced=False),
        ),
        dict(
            name="thorne_e_attributed_on_tower",
            cast='ThorneSkills.cast(key="e")',
            source_shape="`_deal_aoe_damage` credits the dealing hero",
            victim_kind="tower",
            school=thorne_school,
            payload=thorne_raw,
            expected=_tower_row(thorne_raw, school=thorne_school, sourced=True),
        ),
        dict(
            name="gornak_q_sourceless_on_troll",
            cast="BossHeroSkills._cast_q_mana_break",
            source_shape="`e.take_damage(int(h.skill_damage * 1.2), h.team)`",
            victim_kind="minion",
            school=None,
            payload=gornak_raw,
            expected=_minion_row(gornak_raw, school="magic", sourced=False),
        ),
    ]
    return {
        "source": "`hero_skills/_bundle.py` delivery shapes run through the real `Minion.take_damage`, `Tower.take_damage` and `Hero.take_damage`",
        "callsite": "godot_rebuild/scripts/combat/skill_common.gd::hit",
        "native_model": "`Common.hit(..., true)` and `world._deal_hero_aoe(...)` are the attributed arms; plain `Common.hit` and `_deliver_hit(-1, ...)` are sourceless",
        "native_sites": native,
        "native_site_tokens": _native_tokens(),
        "source_counts": {kit: _kit_counts(rows, kit) for kit in KITS},
        "source_rows": rows,
        "live_stats": {
            "vex_skill_base": vex_base,
            "thorne_skill_base": thorne_base,
            "gornak_skill_base": gornak_base,
            "vex_school": vex_school,
            "thorne_school": thorne_school,
            "vex_multiplier": VEX_MULTIPLIER,
            "gornak_multiplier": GORNAK_MULTIPLIER,
            "tower_armor": 3.0,
            "troll_armor": 2.0,
            "troll_magic_resist": 0.05,
        },
        "cases": cases,
    }


def _take_damage():
    from hero_veil_immunity_source_oracle import _take_damage_callable

    fn, _credits = _take_damage_callable()
    return fn


def _parity(fixture: dict) -> list:
    """Every kit's attributed/sourceless split must match the source."""
    problems = []
    native = fixture["native_sites"]
    counts = fixture["source_counts"]
    total_hits = sum(row["hit_total"] for row in native.values())
    total_attr = sum(row["hit_attributed"] for row in native.values())
    if (total_hits, total_attr) != (116, 9):
        problems.append("native Common.hit sites: %d total / %d attributed" % (total_hits, total_attr))
    # file -> (kit, attributed deliveries the file must carry)
    expected = {
        "vex_skills.gd": ("VexSkills", counts["VexSkills"]["attributed"]),
        "zephyr_skills.gd": ("ZephyrSkills", counts["ZephyrSkills"]["attributed"]),
        "grimjaw_skills.gd": ("GrimjawSkills", counts["GrimjawSkills"]["attributed"]),
        "thorne_skills.gd": ("ThorneSkills", counts["ThorneSkills"]["attributed"]),
        "minion_battle.gd": ("KaizenSkills", counts["KaizenSkills"]["attributed"]),
        "source_shared_boss_skills.gd": (
            "BossHeroSkills",
            counts["BossHeroSkills"]["attributed"],
        ),
        "alchemist_skills.gd": ("BossHeroSkills", 0),
    }
    if counts["BossHeroSkills"]["attributed"] != 2:
        problems.append("BossHeroSkills attributed rows: %d" % counts["BossHeroSkills"]["attributed"])
    if counts["BossHeroSkills"]["aoe_sites"] != 0:
        problems.append("boss recipes must stay sourceless, found AoE rows")
    for name, (kit, want) in expected.items():
        row = native.get(name)
        if row is None:
            problems.append("%s missing from the native scan" % name)
            continue
        if name == "minion_battle.gd":
            # The file also carries the hero basic attack (`apply_hit`), so only
            # the four Kaizen kit AoE arms count as skill deliveries here.
            got = row["aoe_sites"]
        else:
            got = row["hit_attributed"] + row["aoe_sites"] + row["direct_attributed"]
        if got != want:
            problems.append("%s attributed deliveries: native %d vs %s %d" % (name, got, kit, want))
    for name in ("boss_level_one_skills.gd", "boss_level_seven_skills.gd", "boss_level_twenty_skills.gd"):
        row = native.get(name)
        if row is None:
            problems.append("%s missing from the native scan" % name)
        elif row["hit_attributed"] or row["direct_attributed"]:
            problems.append("%s carries an attributed delivery" % name)
    return problems


def _attributed_multiplier_check(fixture: dict) -> list:
    """The attributed sites' multipliers must be the source attribute rows."""
    problems = []
    native = fixture["native_sites"]
    counts = fixture["source_counts"]
    if counts["VexSkills"]["attributed_multipliers"] != [
        "2.5",
        "int(h.skill_damage * 0.3)",
        "int(h.skill_damage * 0.4)",
    ]:
        problems.append("VexSkills attributed multipliers drifted")
    zephyr = counts["ZephyrSkills"]["attributed_multipliers"]
    if zephyr != ["1.8", "int(h.skill_damage * 0.3)", "int(h.skill_damage * 0.35)", "int(h.skill_damage * 0.5)"]:
        problems.append("ZephyrSkills attributed multipliers drifted")
    grimjaw = counts["GrimjawSkills"]["attributed_multipliers"]
    if grimjaw != ["1.5", "2.0", "h.skill_damage", "int(h.skill_damage * 0.6)"]:
        problems.append("GrimjawSkills attributed multipliers drifted")
    thorne = counts["ThorneSkills"]["attributed_multipliers"]
    if thorne != ["0.5", "1.2", "1.5"]:
        problems.append("ThorneSkills attributed multipliers drifted")
    if counts["ThorneSkills"]["sourceless"] != 1:
        problems.append("ThorneSkills must keep exactly one sourceless row")
    for name, row in native.items():
        for mult in row["attributed_mults"]:
            if name.startswith("boss_level_") or name in ("alchemist_skills.gd",):
                problems.append("%s attributed site %s" % (name, mult))
    return problems


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
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if args.write:
        return 0
    problems = _parity(fixture) + _attributed_multiplier_check(fixture)
    if fixture != committed:
        problems.append("fixture drift vs %s" % FIXTURE.name)
    if problems:
        for row in problems:
            print("FAIL: %s" % row)
        return 1
    print("skill hit attribution oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
