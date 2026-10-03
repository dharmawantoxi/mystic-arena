"""Static guardrails only; this does not replace native Godot runtime tests.

Run with Python 3, no dependencies: python godot_rebuild/tests/validate_project.py
"""
from pathlib import Path
import re
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
checks = 0


def check(condition, message):
    global checks
    checks += 1
    if not condition:
        errors.append(message)


project = (ROOT / "project.godot").read_text(encoding="utf-8")
for setting in (
    'run/main_scene="res://app/App.tscn"',
    'renderer/rendering_method="gl_compatibility"',
    'window/size/viewport_width=1280',
    'window/size/viewport_height=720',
    'common/physics_ticks_per_second=60',
    'config/custom_user_dir_name="MysticArenaRebuildDev"',
):
    check(setting in project, f"Missing project contract: {setting}")

source_files = [ROOT / "project.godot", *ROOT.rglob("*.gd"), *ROOT.rglob("*.tscn"), *ROOT.rglob("*.tres")]
for path in source_files:
    if ".godot" in path.parts:
        continue
    text = path.read_text(encoding="utf-8")
    for relative in re.findall(r'res://([^"\s]+)', text):
        target = (ROOT / relative).resolve()
        check(target.is_relative_to(ROOT), f"Reference escapes project: {path}: {relative}")
        check(target.is_file(), f"Missing reference: {path}: {relative}")
        # Linux CI is case sensitive, unlike many Windows filesystems.
        check(
            target.parent.is_dir() and target.name in [p.name for p in target.parent.iterdir()],
            f"Wrong path case or missing directory: {relative}",
        )
    check(".gdextension" not in text and "res://../" not in text, f"Unexpected external dependency: {path}")

for path in (ROOT / "scenes").rglob("*.tscn"):
    text = path.read_text(encoding="utf-8")
    names = re.findall(r'\[node name="([^"]+)"[^\n]*\]\nunique_name_in_owner = true', text)
    check(len(names) == len(set(names)), f"Duplicate scene-unique names: {path}")
    scripts = re.findall(r'\[ext_resource type="Script" path="res://([^"]+)"', text)
    for script in scripts:
        source = (ROOT / script).read_text(encoding="utf-8")
        for name in re.findall(r'%([A-Z][A-Za-z0-9_]*)', source):
            check(name in names, f"Missing unique node %{name} used by {script} in {path}")

sim = (ROOT / "scripts/simulation/sandbox_simulation.gd").read_text(encoding="utf-8")
check("func _physics_process(" in sim, "Simulation must own fixed ticks")
check("func _process(" not in sim, "Simulation must not tick on render frames")
check("PROCESS_MODE_PAUSABLE" in sim, "Simulation must pause")
app = (ROOT / "app/app.gd").read_text(encoding="utf-8")
check("queue_free()" in app and "remove_child" in app, "Navigation must clean up screens")
check("call_deferred" in app, "Navigation must leave input callback before replacing screens")

ai_policy = (ROOT / "scripts/match/ai_policy.gd").read_text(encoding="utf-8")
ai_tests = (ROOT / "tests/run_all.gd").read_text(encoding="utf-8")
check("AIPolicyChecks.new().run(_check)" in ai_tests, "AI policy suite must run alongside old suites")
check((ROOT / "AI_CONTRACT.md").is_file(), "AI policy scope must be documented")
check((ROOT / "tests/fixtures/ai_policy_source.json").is_file(), "AI policy needs source oracle fixture")
check("control_heroes.call()" in ai_policy, "AI must control heroes before thinking")

check("AIDraftChecks.new().run(_check)" in ai_tests, "AI draft suite must remain in the native runner")
recruitment = json.loads((ROOT / "data/ai/recruitment.json").read_text(encoding="utf-8"))
check(recruitment["starters"] == ["thorne", "grimjaw", "vex", "sylara", "kaizen", "zephyr"],
      "AI starter preference order must match source")
check(set(recruitment["fallback"]) == set(recruitment["starters"]), "AI fallback is starter catalog only")
check(len(recruitment["levels"]) == 54, "Update AI policy elite level count when source levels change")
for hero_type, entry in recruitment["catalog"].items():
    check(isinstance(hero_type, str) and bool(hero_type), "AI catalog IDs must be nonempty strings")
    check(isinstance(entry["cost"], int) and entry["cost"] > 0, f"Invalid summon price: {hero_type}")
    check(type(entry["is_boss_hero"]) is bool, f"Invalid boss flag: {hero_type}")
for key, entry in recruitment["levels"].items():
    check(key.isdigit() and int(key) >= 1, f"Invalid AI source level: {key}")
    check(all(hero_type in recruitment["catalog"] for hero_type in entry["bosses"]),
          f"Missing summon metadata for level {key}")
check((ROOT / "tests/fixtures/ai_draft_source.json").is_file(), "AI draft needs source fixture")
workflow = (ROOT.parent / ".github/workflows/godot-rebuild.yml").read_text(encoding="utf-8")
check("python godot_rebuild/tests/ai_draft_source_oracle.py" in workflow, "CI must detect recruitment data drift")

check("AIUpgradeChecks.new().run(_check)" in ai_tests, "AI upgrade suite must remain alongside baseline suites")
check((ROOT / "tests/fixtures/ai_upgrade_source.json").is_file(), "AI upgrades require source fixture")
check("python godot_rebuild/tests/ai_upgrade_source_oracle.py" in workflow, "CI must check AI upgrades oracle")
# Candidate ordering oracle runs inside this CI step: no workflow edit needed.
from ai_priority_source_oracle import source_fixture as ai_priority_source_fixture
check("AIPriorityChecks.new().run(_check)" in ai_tests, "AI candidate priority suite must run")
check((ROOT / "tests/fixtures/ai_priority_source.json").is_file(), "AI priority requires source fixture")
if (ROOT / "tests/fixtures/ai_priority_source.json").is_file():
    check(ai_priority_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/ai_priority_source.json").read_text(encoding="utf-8")),
        "AI candidate priority source drift")
ai_upgrades = (ROOT / "scripts/match/ai_upgrades.gd").read_text(encoding="utf-8")
check(ai_upgrades.count("draft.reserve()") == 3, "All three AI upgrade adapters must read live reserve")

# CI already runs validate_project.py, so the read-only item oracle runs here.
from ai_item_source_oracle import source_fixture as ai_item_source_fixture
from ai_item_source_oracle import source_namespace as ai_item_source_namespace
check("AIItemChecks.new().run(_check)" in ai_tests, "AI item suite must run")
check((ROOT / "tests/fixtures/ai_items_source.json").is_file(), "AI items require source fixture")
ai_items_fixture = ai_item_source_fixture()
if (ROOT / "tests/fixtures/ai_items_source.json").is_file():
    check(ai_items_fixture == json.loads(
        (ROOT / "tests/fixtures/ai_items_source.json").read_text(encoding="utf-8")),
        "AI item catalog source drift")
item_catalog = json.loads((ROOT / "data/ai/item_catalog.json").read_text(encoding="utf-8"))
check(item_catalog == ai_items_fixture["catalog"],
      "data/ai/item_catalog.json drifted from source ITEM_CATALOG")
check(len(item_catalog["items"]) == 33, "Update the AI item suite when ITEM_CATALOG changes")
check(item_catalog["flat_cost"] == 4500 and item_catalog["max_slots"] == 6,
      "AI item constants must follow ITEM_FLAT_COST/MAX_ITEM_SLOTS")
check(set(item_catalog["categories"])
      == {entry["category"] for entry in item_catalog["items"].values()},
      "AI item catalog categories must be keyed by the category ids in use")
hero_items = (ROOT / "scripts/match/hero_items.gd").read_text(encoding="utf-8")


def gd_string_array(name):
    body = re.search(r"const %s: Array\[String\] = \[(.*?)\]" % name, hero_items, re.S)
    return [part.strip().strip('"') for part in body.group(1).split(",") if part.strip()]


gd_pools = {name: gd_string_array(name) for name in
            ("TANK_POOL", "MARKSMAN_POOL", "MAGIC_POOL", "FALLBACK_POOL")}
pool_ids = {sid for ids in gd_pools.values() for sid in ids}
check(bool(pool_ids) and pool_ids <= set(item_catalog["items"]),
      "AI item role pools must only reference catalog items")
check(gd_string_array("MAGIC_ROLE_KEYWORDS")
      == list(ai_item_source_namespace()["MAGIC_ROLE_KEYWORDS"]),
      "AI magic role keywords must equal source MAGIC_ROLE_KEYWORDS")
source_pools = {(row["role"], row["range"]): row["order"] for row in ai_items_fixture["pools"]}
# Melee wraps the pool with cleave_axe + holy_rapier, ranged only appends the
# rapier, so the fixture sequence length pins each pool transcription.
check(len(source_pools[("Bruiser", 70)]) == len(gd_pools["TANK_POOL"]) + 2,
      "Tank pool must match the source bruiser purchase order")
check(len(source_pools[("Marksman", 130)]) == len(gd_pools["MARKSMAN_POOL"]) + 1,
      "Marksman pool must match the source marksman purchase order")
check(len(source_pools[("Mage", 130)]) == len(gd_pools["MAGIC_POOL"]) + 1,
      "Magic pool must match the source mage purchase order")
check(len(source_pools[("Ranger", 130)]) == len(gd_pools["FALLBACK_POOL"]) + 1,
      "Fallback pool must match the source fallback purchase order")
ai_items = (ROOT / "scripts/match/ai_items.gd").read_text(encoding="utf-8")
check("draft.reserve()" in ai_items and "_buy_item_for" in ai_items,
      "AI item adapter must use the live draft reserve and the real transaction")
check("total_items" not in ai_items,
      "Source _try_buy_item keeps no counter; the adapter must not add one")
check("hero.alive" in ai_items and "used_slots()" in ai_items,
      "AI item candidates must be alive heroes with a free slot")
check("_buy_item_for" in (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8"),
      "AI item purchase must debit through the match ledger")
check(len(ai_items_fixture["purchases"]) == 9,
      "Update the AI item suite when the purchase cases change")
check(len(ai_items_fixture["stats"]) == 25,
      "Update the AI item suite when the stat loadouts change")
check(all("stats" in entry for entry in item_catalog["items"].values()),
      "AI item catalog must carry the numeric stats the getters sum")
inventory_gd = (ROOT / "scripts/match/hero_item_inventory.gd").read_text(encoding="utf-8")
missing_getters = [name for name in ai_items_fixture["stats"][0]["values"]
                   if name not in ("empower_strike", "empower_charge")
                   and ("func %s(" % name) not in inventory_gd]
check(not missing_getters, f"AI item stat getters missing in the rebuild: {missing_getters}")
check("func _on_item_changed(" not in inventory_gd,
      "HP recalc lives on HeroState, never inside the inventory")
hero_state_gd = (ROOT / "scripts/combat/hero_state.gd").read_text(encoding="utf-8")
unit_state_gd = (ROOT / "scripts/combat/unit_state.gd").read_text(encoding="utf-8")
check("func recalc_item_stats(" in hero_state_gd
      and "func apply_item_change(" in hero_state_gd,
      "HeroState must port Hero._recalc_item_stats and the equip recalc")
check("func apply_heal_amp(" in hero_state_gd and "heal_amp_timer" in unit_state_gd,
      "Heal amp must live on the shared debuff fields like the source")
check("apply_item_change()" in (ROOT / "scripts/match/prototype_battle.gd").read_text(
      encoding="utf-8"), "The item transaction must apply the source HP recalc")
check(len(ai_items_fixture["stat_application"]) == 5,
      "Update the AI item suite when the stat application cases change")
check("hero.items.clear_on_death()" in (ROOT / "scripts/match/prototype_battle.gd")
      .read_text(encoding="utf-8"),
      "The match death hook must destroy Holy Rapier like the source")
check(len(ai_items_fixture["deaths"]) == 3,
      "Update the AI item suite when the death cases change")
check("func tick_timers(" in inventory_gd,
      "The inventory must port the source update() timer state machine")
check("func tick_auto(" in inventory_gd,
      "The inventory must port the auto-trigger half of update() for layer 5c-2")
check("func notify_damage_taken(" in inventory_gd,
      "The inventory must port notify_damage_taken for layer 5c-2")
check("func set_hero_runtime(" in inventory_gd,
      "The inventory must accept runtime hero state via set_hero_runtime")
check(all(('var %s ' % attr) in inventory_gd for attr in ai_items_fixture["timer_attrs"]),
      "Every source timer attribute needs a rebuild field")
check(len(ai_items_fixture["auto_triggers"]) == 18,
      "Update the AI item suite when the auto-trigger cases change")
check(len(ai_items_fixture["notify_damage"]) == 5,
      "Update the AI item suite when the notify_damage cases change")
check("_tick_hero_items" in (ROOT / "scripts/match/prototype_battle.gd")
      .read_text(encoding="utf-8"),
      "The match step_tick must tick item timers and auto-triggers (5c-2)")
check("_notify_item_damage" in (ROOT / "scripts/match/prototype_battle.gd")
      .read_text(encoding="utf-8"),
      "The battle damage path must invoke item notify_damage_taken (5c-2)")
check("_tick_hero_items(hero)" in (ROOT / "scripts/combat/minion_battle.gd")
      .read_text(encoding="utf-8"),
      "minion_battle._tick_hero must call the item tick hook")

# CI already runs validate_project.py: execute the read-only build oracle here so
# the new fixture is enforced without editing the workflow outside godot_rebuild/.
from ai_build_source_oracle import source_fixture as ai_build_source_fixture
check("AIBuildChecks.new().run(_check)" in ai_tests, "AI build domain suite must run")
check((ROOT / "tests/fixtures/ai_build_source.json").is_file(), "AI build requires source fixture")
if (ROOT / "tests/fixtures/ai_build_source.json").is_file():
    check(ai_build_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/ai_build_source.json").read_text(encoding="utf-8")),
        "AI build source oracle drift")
ai_build = (ROOT / "scripts/match/ai_build.gd").read_text(encoding="utf-8")
check("draft.reserve()" in ai_build and "_build_tower_for" in ai_build,
      "AI build must use live draft reserve and real match transaction")

check("ThorneChecks.new().run(_check)" in ai_tests, "Thorne source kit suite must run")
check((ROOT / "tests/fixtures/thorne_source.json").is_file(), "Thorne kit source fixture missing")
if (ROOT / "tests/fixtures/thorne_source.json").is_file():
    from thorne_source_oracle import source_fixture as thorne_source_fixture
    check(thorne_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/thorne_source.json").read_text(encoding="utf-8")),
        "Thorne source skill/reflect/timer drift")

check("GrimjawChecks.new().run(_check)" in ai_tests, "Grimjaw source kit suite must run")
check((ROOT / "tests/fixtures/grimjaw_source.json").is_file(), "Grimjaw kit source fixture missing")
if (ROOT / "tests/fixtures/grimjaw_source.json").is_file():
    from grimjaw_source_oracle import source_fixture as grimjaw_source_fixture
    check(grimjaw_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/grimjaw_source.json").read_text(encoding="utf-8")),
        "Grimjaw source skill/timer/crit drift")

check("SylaraChecks.new().run(_check)" in ai_tests, "Sylara source kit suite must run")
check((ROOT / "tests/fixtures/sylara_source.json").is_file(), "Sylara kit source fixture missing")
if (ROOT / "tests/fixtures/sylara_source.json").is_file():
    from sylara_source_oracle import source_fixture as sylara_source_fixture
    check(sylara_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/sylara_source.json").read_text(encoding="utf-8")),
        "Sylara source skill/evasion/projectile drift")

# Recruitment is staged: only the explicit native registry has playable kits.
# Execute the real Hero source oracle in this CI step (no workflow change).
from ai_recruit_source_oracle import source_fixture as ai_recruit_source_fixture
check("AIRecruitChecks.new().run(_check)" in ai_tests, "Real recruit suite must run")
check((ROOT / "tests/fixtures/ai_recruit_source.json").is_file(), "Recruit source fixture missing")
check((ROOT / "data/ai/hero_combat_stats.json").is_file(), "Hero numeric baseline missing")
if (ROOT / "tests/fixtures/ai_recruit_source.json").is_file() and (ROOT / "data/ai/hero_combat_stats.json").is_file():
    purchases, stats = ai_recruit_source_fixture()
    check(purchases == json.loads((ROOT / "tests/fixtures/ai_recruit_source.json").read_text(encoding="utf-8")),
          "Real source recruit drift")
    check(stats == json.loads((ROOT / "data/ai/hero_combat_stats.json").read_text(encoding="utf-8")),
          "222 source Hero stat baselines drift")
    check(set(stats) == set(recruitment["catalog"]), "Every recruitment ID must have source Hero numbers")

check("AIShieldChecks.new().run(_check)" in ai_tests, "AI shield domain suite must remain in runner")
check("await AIShieldSceneChecks.new().run(self, app, _check)" in ai_tests, "Paid shield refund/reset UI suite must run")
check((ROOT / "tests/fixtures/ai_shield_source.json").is_file(), "AI shields require source fixture")
check("python godot_rebuild/tests/ai_shield_source_oracle.py" in workflow, "CI must check paid shield oracle")
ai_shields = (ROOT / "scripts/match/ai_shields.gd").read_text(encoding="utf-8")
check(ai_shields.count("draft.reserve()") == 2, "Both paid shield adapters must use live reserve")
check("_stable_kills_descending" in ai_shields and "can_activate_regen_shield" in ai_shields,
      "Regen shield candidates must use the source kills-descending stable order")
shield_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
check('tower.sale_value()' in shield_screen, "UI sale quote must include purchased shield")

check((ROOT / "SHIELD_CONTRACT.md").is_file(), "Paid shield semantics must be documented")


from starter_finish_source_oracle import source_fixture as starter_finish_fixture
check(starter_finish_fixture() == json.loads((ROOT / "tests/fixtures/starter_finish_source.json").read_text()), "Vex/Zephyr source behavior drift")
check("StarterFinishChecks.new().run(_check)" in ai_tests, "Starter finish native suite must run")

from boss_level_one_source_oracle import source_fixture as boss_level_one_fixture
check(boss_level_one_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_one_source.json").read_text()), "Boss level one source behavior drift")
check("BossLevelOneChecks.new().run(_check)" in ai_tests, "Boss level one native suite must run")

from hero_status_source_oracle import source_fixture as hero_status_fixture
check(hero_status_fixture() == json.loads((ROOT / "tests/fixtures/hero_status_source.json").read_text()), "Hero status source behavior drift")
check("HeroStatusChecks.new().run(_check)" in ai_tests, "Hero status native suite must run")

from source_shared_boss_oracle import source_fixture as source_shared_fixture
shared = source_shared_fixture()
check(shared == json.loads((ROOT / "tests/fixtures/source_shared_boss.json").read_text()), "Shared source boss behavior drift")
check("SourceSharedBossChecks.new().run(_check)" in ai_tests, "Shared boss per-ID native suite must run")
shared_ids = re.findall(r'"([a-z0-9_]+)"', (ROOT / "scripts/data/source_shared_boss_ids.gd").read_text())
check(shared_ids == shared["ids"], "Native shared-kit membership must exactly match source dispatch")

from hero_school_source_oracle import source_fixture as hero_school_fixture
check(hero_school_fixture() == json.loads((ROOT / "tests/fixtures/hero_school_source.json").read_text()), "Per-ID real hero mitigation and attribution drift")

from alchemist_source_oracle import source_fixture as alchemist_fixture
check(alchemist_fixture() == json.loads((ROOT / "tests/fixtures/alchemist_source.json").read_text()), "Alchemist source behavior drift")
check("AlchemistChecks.new().run(_check)" in ai_tests, "Alchemist native suite must run")

from boss_level_three_source_oracle import source_fixture as boss_level_three_fixture
check(boss_level_three_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_three_source.json").read_text()), "Boss level three source behavior drift")
check("BossLevelThreeChecks.new().run(_check)" in ai_tests, "Boss level three native suite must run")

from boss_level_four_source_oracle import source_fixture as boss_level_four_fixture
check(boss_level_four_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_four_source.json").read_text()), "Boss level four source behavior drift")
check("BossLevelFourChecks.new().run(_check)" in ai_tests, "Boss level four native suite must run")

from boss_level_five_source_oracle import source_fixture as boss_level_five_fixture
check(boss_level_five_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_five_source.json").read_text()), "Boss level five source behavior drift")
check("BossLevelFiveChecks.new().run(_check)" in ai_tests, "Boss level five native suite must run")

from boss_level_six_source_oracle import source_fixture as boss_level_six_fixture
check(boss_level_six_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_six_source.json").read_text()), "Boss level six source behavior drift")
check("BossLevelSixChecks.new().run(_check)" in ai_tests, "Boss level six native suite must run")

from boss_level_seven_source_oracle import source_fixture as boss_level_seven_fixture
check(boss_level_seven_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_seven_source.json").read_text()), "Boss level seven source behavior drift")
check("BossLevelSevenChecks.new().run(_check)" in ai_tests, "Boss level seven native suite must run")
from boss_level_nine_source_oracle import source_fixture as boss_level_nine_fixture
check(boss_level_nine_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_nine_source.json").read_text()), "Boss level nine source behavior drift")
check("BossLevelNineChecks.new().run(_check)" in ai_tests, "Boss level nine native suite must run")
from boss_level_ten_source_oracle import source_fixture as boss_level_ten_fixture
check(boss_level_ten_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_ten_source.json").read_text()), "Boss level ten source behavior drift")
check("BossLevelTenChecks.new().run(_check)" in ai_tests, "Boss level ten native suite must run")
from boss_level_eleven_source_oracle import source_fixture as boss_level_eleven_fixture
check(boss_level_eleven_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_eleven_source.json").read_text()), "Boss level eleven source behavior drift")
check("BossLevelElevenChecks.new().run(_check)" in ai_tests, "Boss level eleven native suite must run")
from boss_level_twelve_source_oracle import source_fixture as boss_level_twelve_fixture
check(boss_level_twelve_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_twelve_source.json").read_text()), "Boss level twelve source behavior drift")
check("BossLevelTwelveChecks.new().run(_check)" in ai_tests, "Boss level twelve native suite must run")
from boss_level_thirteen_source_oracle import source_fixture as boss_level_thirteen_fixture
check(boss_level_thirteen_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_thirteen_source.json").read_text()), "Boss level thirteen source behavior drift")
check("BossLevelThirteenChecks.new().run(_check)" in ai_tests, "Boss level thirteen native suite must run")
from boss_level_fourteen_source_oracle import source_fixture as boss_level_fourteen_fixture
check(boss_level_fourteen_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_fourteen_source.json").read_text()), "Boss level fourteen source behavior drift")
check("BossLevelFourteenChecks.new().run(_check)" in ai_tests, "Boss level fourteen native suite must run")
from boss_level_fifteen_source_oracle import source_fixture as boss_level_fifteen_fixture
check(boss_level_fifteen_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_fifteen_source.json").read_text()), "Boss level fifteen source behavior drift")
check("BossLevelFifteenChecks.new().run(_check)" in ai_tests, "Boss level fifteen native suite must run")
from boss_level_sixteen_source_oracle import source_fixture as boss_level_sixteen_fixture
check(boss_level_sixteen_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_sixteen_source.json").read_text()), "Boss level sixteen source behavior drift")
check("BossLevelSixteenChecks.new().run(_check)" in ai_tests, "Boss level sixteen native suite must run")
from boss_level_seventeen_source_oracle import source_fixture as boss_level_seventeen_fixture
check(boss_level_seventeen_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_seventeen_source.json").read_text()), "Boss level seventeen source behavior drift")
check("BossLevelSeventeenChecks.new().run(_check)" in ai_tests, "Boss level seventeen native suite must run")
from boss_level_eighteen_source_oracle import source_fixture as boss_level_eighteen_fixture
check(boss_level_eighteen_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_eighteen_source.json").read_text()), "Boss level eighteen source behavior drift")
check("BossLevelEighteenChecks.new().run(_check)" in ai_tests, "Boss level eighteen native suite must run")
from boss_level_nineteen_source_oracle import source_fixture as boss_level_nineteen_fixture
check(boss_level_nineteen_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_nineteen_source.json").read_text()), "Boss level nineteen source behavior drift")
check("BossLevelNineteenChecks.new().run(_check)" in ai_tests, "Boss level nineteen native suite must run")
from boss_level_twenty_source_oracle import source_fixture as boss_level_twenty_fixture
check(boss_level_twenty_fixture() == json.loads((ROOT / "tests/fixtures/boss_level_twenty_source.json").read_text()), "Boss level twenty source behavior drift")
check("BossLevelTwentyChecks.new().run(_check)" in ai_tests, "Boss level twenty native suite must run")

check((ROOT / "data/levels/level_1.json").is_file(), "Level 1 config needs source data")
if (ROOT / "data/levels/level_1.json").is_file() and (ROOT / "tests/fixtures/match_source.json").is_file():
    _match_fixture = json.loads((ROOT / "tests/fixtures/match_source.json").read_text(encoding="utf-8"))
    check(
        json.loads((ROOT / "data/levels/level_1.json").read_text(encoding="utf-8"))
        == _match_fixture["level_one"],
        "Level 1 config drifted from its source fixture",
    )
from boss_core_source_oracle import source_fixture as boss_core_fixture
from boss_ability_source_oracle import source_fixture as boss_ability_fixture
from boss_clock_source_oracle import source_fixture as boss_clock_fixture
from boss_debuff_clock_source_oracle import source_fixture as boss_debuff_clock_fixture
from boss_hero_ai_source_oracle import source_fixture as boss_hero_ai_fixture
from boss_kill_credit_source_oracle import source_fixture as boss_kill_credit_fixture
from boss_structure_targeting_source_oracle import source_fixture as boss_structure_targeting_fixture
from boss_motion_source_oracle import (
    smart_ai_boss_types as boss_motion_ai_types,
    source_boss_types as boss_motion_source_types,
    source_fixture as boss_motion_fixture,
)
from boss_presentation_source_oracle import source_fixture as boss_presentation_fixture
check("BossCoreChecks.new().run(_check)" in ai_tests, "Boss entity core suite must run")
check("BossAbilityChecks.new().run(_check)" in ai_tests, "Boss ability suite must run")
check("BossClockChecks.new().run(_check)" in ai_tests, "Boss clock suite must run")
check("BossDebuffClockChecks.new().run(_check)" in ai_tests, "Boss debuff clock suite must run")
check("BossKillCreditChecks.new().run(_check)" in ai_tests, "Boss kill credit suite must run")
check("BossStructureTargetsChecks.new().run(_check)" in ai_tests,
      "Boss structure targeting suite must run")
check("BossPresentationChecks.new().run(_check)" in ai_tests, "Boss presentation suite must run")
check("BossMotionChecks.new().run(_check)" in ai_tests, "Boss motion and kiting suite must run")
check((ROOT / "tests/fixtures/boss_motion_source.json").is_file(), "Boss motion requires source fixture")
if (ROOT / "tests/fixtures/boss_motion_source.json").is_file():
    _boss_motion = boss_motion_fixture()
    check(_boss_motion == json.loads(
        (ROOT / "tests/fixtures/boss_motion_source.json").read_text(encoding="utf-8")),
        "Boss motion and ranged kiting source behavior drift")
    _ranged_motion_cases = _boss_motion.get("ranged_kiting", [])
    check(len(_ranged_motion_cases) == 48
          and all(sum(case["boss_type"] == _boss for case in _ranged_motion_cases) == 4
                  for _boss in {case["boss_type"] for case in _ranged_motion_cases}),
          "Ranged kiting requires exactly four oracle cases per boss")
    _smart_ai_dispatch_cases = _boss_motion.get("smart_ai_dispatch", [])
    _smart_ai_dispatch_types = {case["boss_type"] for case in _smart_ai_dispatch_cases}
    check(len(_smart_ai_dispatch_cases) == 316
          and len(_smart_ai_dispatch_types) == 79
          and _smart_ai_dispatch_types == set(boss_motion_ai_types())
          and all(sum(case["boss_type"] == _boss for case in _smart_ai_dispatch_cases) == 4
                  for _boss in _smart_ai_dispatch_types),
          "Boss smart-AI dispatch requires four oracle cases for all 79 source recipes")
    _basic_attack_cases = _boss_motion.get("basic_attack_source", [])
    _basic_attack_types = {case["boss_type"] for case in _basic_attack_cases}
    check(len(_basic_attack_cases) == 864
          and _basic_attack_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _basic_attack_cases) == 4
                  for _boss in _basic_attack_types),
          "Boss basic attacks require four source-attribution cases for all 216 types")
check((ROOT / "tests/fixtures/boss_kill_credit_source.json").is_file(),
      "Boss kill credit requires source fixture")
if (ROOT / "tests/fixtures/boss_kill_credit_source.json").is_file():
    _boss_kill_credit = boss_kill_credit_fixture()
    check(_boss_kill_credit == json.loads(
        (ROOT / "tests/fixtures/boss_kill_credit_source.json").read_text(encoding="utf-8")),
        "Boss kill credit source attribution drift")
    _kill_credit_cases = _boss_kill_credit.get("killer_cases", [])
    _kill_credit_types = {case["boss_type"] for case in _kill_credit_cases}
    check(len(_kill_credit_cases) == 864
          and _kill_credit_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _kill_credit_cases) == 4
                  for _boss in _kill_credit_types),
          "Boss kill credit requires four source cases for all 216 boss types")
    check(all(case["credited_kills"] == (1 if case["label"] == "blue_hero_lethal_hit" else 0)
              for case in _kill_credit_cases),
          "Only an enemy hero last hit may credit the source kill")
    check(all((case["achievement"] is not None)
              == (case["label"] == "blue_hero_lethal_hit")
              and case["miniboss_kill_count"] + case["trueboss_kill_count"]
              == case["credited_kills"]
              for case in _kill_credit_cases),
          "Boss kill counters must advance exactly with the credited source kills")
check((ROOT / "tests/fixtures/boss_structure_targeting_source.json").is_file(),
      "Boss structure targeting requires source fixture")
if (ROOT / "tests/fixtures/boss_structure_targeting_source.json").is_file():
    _boss_structure_targeting = boss_structure_targeting_fixture()
    check(_boss_structure_targeting == json.loads(
        (ROOT / "tests/fixtures/boss_structure_targeting_source.json").read_text(encoding="utf-8")),
        "Boss structure targeting source behavior drift")
    _structure_targeting_source = _boss_structure_targeting.get("source", {})
    check(all(bool(_structure_targeting_source.get(key, False)) for key in (
        "tower_boss_scan", "castle_uses_all_units", "all_units_includes_boss", "grid_includes_boss")),
        "Source must keep the boss in both structure targeting paths")
    _structure_targeting_cases = _boss_structure_targeting.get("cases", [])
    _structure_targeting_types = {case["boss_type"] for case in _structure_targeting_cases}
    check(len(_structure_targeting_cases) == 1728
          and _structure_targeting_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _structure_targeting_cases) == 8
                  for _boss in _structure_targeting_types),
          "Boss structure targeting requires eight source cases for all 216 boss types")
    check(all(case["expected"] != case["expected_without_boss"] or case["expected"] != "boss"
              for case in _structure_targeting_cases)
          and sum(case["expected"] == "boss" for case in _structure_targeting_cases) == 864
          and all(
              (case["expected"] == "boss")
              == (case["label"] in ("boss_at_range_unit_out_of_range", "boss_ties_nearest_unit"))
              for case in _structure_targeting_cases
          ),
          "In-range boss must win at the range edge and on exact ties for tower and castle")
check((ROOT / "tests/fixtures/boss_presentation_source.json").is_file(), "Boss presentation requires source fixture")
if (ROOT / "tests/fixtures/boss_presentation_source.json").is_file():
    check(boss_presentation_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_presentation_source.json").read_text(encoding="utf-8")),
        "Boss presentation source behavior drift")
check((ROOT / "tests/fixtures/boss_clock_source.json").is_file(), "Boss clock requires source fixture")
if (ROOT / "tests/fixtures/boss_clock_source.json").is_file():
    check(boss_clock_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_clock_source.json").read_text(encoding="utf-8")),
        "Boss clock source behavior drift")
check((ROOT / "tests/fixtures/boss_debuff_clock_source.json").is_file(),
      "Boss debuff clock requires source fixture")
if (ROOT / "tests/fixtures/boss_debuff_clock_source.json").is_file():
    check(boss_debuff_clock_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_debuff_clock_source.json").read_text(encoding="utf-8")),
        "Boss debuff clock source behavior drift")
check("BossHeroAIChecks.new().run(_check)" in ai_tests,
      "Boss hero AI target handoff suite must run")
check((ROOT / "tests/fixtures/boss_hero_ai_source.json").is_file(),
      "Boss hero AI target handoff requires source fixture")
if (ROOT / "tests/fixtures/boss_hero_ai_source.json").is_file():
    check(boss_hero_ai_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_hero_ai_source.json").read_text(encoding="utf-8")),
        "Boss hero AI target handoff source behavior drift")
check((ROOT / "tests/fixtures/boss_ability_source.json").is_file(), "Boss abilities require source fixture")
if (ROOT / "tests/fixtures/boss_ability_source.json").is_file():
    check(boss_ability_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_ability_source.json").read_text(encoding="utf-8")),
        "Boss ability source behavior drift")
check((ROOT / "tests/fixtures/boss_core_source.json").is_file(), "Boss core requires source fixture")
check((ROOT / "data/bosses/boss_stats.json").is_file(), "Boss stats need source data")
if (ROOT / "tests/fixtures/boss_core_source.json").is_file():
    _boss_core = boss_core_fixture()
    check(_boss_core == json.loads(
        (ROOT / "tests/fixtures/boss_core_source.json").read_text(encoding="utf-8")),
        "Boss core source behavior drift")
    check(_boss_core["data"] == json.loads(
        (ROOT / "data/bosses/boss_stats.json").read_text(encoding="utf-8")),
        "Boss stats data drifted from source boss tables")
    check(len(_boss_core["data"]["bosses"]) == 216,
          "Update the boss core suite when the source boss tables change")
boss_state = (ROOT / "scripts/match/boss_state.gd").read_text(encoding="utf-8")
for _method in ("apply_scaling", "apply_slow", "apply_debuff", "apply_stun",
                "clear_tower_debuffs", "set_hp_value", "tick_tower_debuffs",
                "take_damage", "eff_speed", "eff_ability_damage", "blind_live",
                "true_strike_of", "advance_animation_clock",
                "entrance_presentation_state", "advance_combat_clock",
                "move_ranged_kite", "is_in_attack_range", "death_presentation"):
    check("func %s(" % _method in boss_state, "Boss entity core must port %s" % _method)
prototype_battle = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
check("advance_animation_clock()" in prototype_battle
      and "advance_combat_clock()" in prototype_battle,
      "Boss match step must consume entrance and enrage clocks")
boss_step = prototype_battle.split("func _step_active_boss()", 1)[1].split(
    "func _try_spawn_pending_mini_boss()", 1)[0]
check(boss_step.index("tick_tower_debuffs()") < boss_step.index("if boss.stun_timer > 0"),
      "Boss debuffs must tick before the stun and entrance gates")
check("boss.move_ranged_kite(target.position)" in boss_step
      and "RANGED_BOSS_KITERS" in prototype_battle,
      "Ranged boss movement must use the source hysteresis kiting branch")
check("boss.is_in_attack_range(distance)" in boss_step
      and "ai_target = null" in boss_step
      and "BossAI.tick(self, boss, enemies, ai_target, ai_distance)" in boss_step,
      "Boss smart AI must dispatch only inside source attack range")
boss_basic_attack = prototype_battle.split("func _boss_basic_attack(", 1)[1].split(
    "func _step_active_boss()", 1)[0]
check('_deliver_hit(boss.id, boss.team, target, boss.damage, "physical", boss.position)' in boss_basic_attack
      and "_deliver_hit(-1, boss.team, enemy, cleave_damage" in boss_basic_attack,
      "Boss primary hit must preserve source ID while source-omitted cleave remains uncredited")
boss_structure_target = prototype_battle.split("func _structure_target(", 1)[1].split(
    "\nfunc _boss_enemies()", 1)[0]
check("super._structure_target(structure)" in boss_structure_target
      and "distance > structure.definition.attack_range_px" in boss_structure_target
      and "distance <= structure.position.distance_to(target.position)" in boss_structure_target,
      "Towers and the nexus must append the living enemy boss like the source scans")
check("active_boss.tick_item_debuffs()" not in prototype_battle,
      "Boss item debuffs must not tick twice in one match step")
boss_ai_text = (ROOT / "scripts/match/boss_ai.gd").read_text(encoding="utf-8")
for _boss_type in boss_motion_ai_types():
    check('"%s":' % _boss_type in boss_ai_text,
          "Native boss AI dispatch must include source recipe %s" % _boss_type)
check(not re.search(r"^\s*boss\.hp\s*=", boss_ai_text, re.M),
      "Boss AI hp increases must pass through the anti-heal setter")
check(boss_ai_text.count("boss.set_hp_value(") == 6,
      "All source Boss AI healing writes must use the anti-heal setter")
boss_kill_credit = prototype_battle.split("func _process_boss_kill(", 1)[1].split(
    "\nfunc _process_boss_result()", 1)[0]
check("get_unit(boss.last_hit_source_id) as HeroState" in boss_kill_credit
      and "killer.kills += 1" in boss_kill_credit
      and "if killer.team != BLUE:" in boss_kill_credit,
      "Boss kill attribution must credit only a real enemy hero, then blue-side counters")
check("_process_boss_kill(boss)\n\teconomy.credit_kill(BLUE, boss.gold_reward)" in prototype_battle,
      "Boss kill attribution must run before the source reward pass")
check("var miniboss_kill_count := 0" in prototype_battle
      and "var trueboss_kill_count := 0" in prototype_battle,
      "Native match must keep the source mini/true boss kill counters")
check("boss_death_presentations" in prototype_battle
      and "_queue_boss_death_presentation" in prototype_battle,
      "Boss death presentation must survive registry retirement")
prototype_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
check("_draw_boss_entrance" in prototype_view and "_draw_boss_death" in prototype_view,
      "Prototype view must render boss intro and death presentation")
check("PrototypeChecks.new().run(_check)" in ai_tests, "Match prototype suite must run")

from hero_manifest_checks import validate_manifest
validate_manifest(ROOT, check)

for error in errors:
    print("FAIL:", error, file=sys.stderr)
print(f"{'FAIL' if errors else 'PASS'}: {checks} static checks; runtime testing still required.")
sys.exit(bool(errors))
