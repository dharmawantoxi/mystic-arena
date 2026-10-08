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
    'pointing/emulate_mouse_from_touch=false',
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
        # Runtime loaders may keep a res:// directory prefix and append a
        # catalog filename (AudioManager does this for WAV streams).
        exists = target.is_dir() if relative.endswith("/") else target.is_file()
        check(exists, f"Missing reference: {path}: {relative}")
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
from ai_control_tick_source_oracle import source_fixture as ai_control_tick_source_fixture
from ai_roster_source_oracle import source_fixture as ai_roster_source_fixture
check("AIControlTickChecks.new().run(_check)" in ai_tests,
      "Production AI control tick replay must run")
check((ROOT / "tests/fixtures/ai_control_tick_source.json").is_file(),
      "Production AI control tick requires a source fixture")
if (ROOT / "tests/fixtures/ai_control_tick_source.json").is_file():
    check(ai_control_tick_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/ai_control_tick_source.json").read_text(encoding="utf-8")),
        "Production AI control tick source fixture drift")
check("AIRosterChecks.new().run(_check)" in ai_tests,
      "Production AI roster ownership replay must run")
check((ROOT / "tests/fixtures/ai_roster_source.json").is_file(),
      "AI roster ownership requires a source fixture")
if (ROOT / "tests/fixtures/ai_roster_source.json").is_file():
    check(ai_roster_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/ai_roster_source.json").read_text(encoding="utf-8")),
        "AI roster ownership source fixture drift")

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

from player_recruit_source_oracle import source_fixture as player_recruit_source_fixture
check("PlayerRecruitChecks.new().run(_check)" in ai_tests,
      "Player Hero Shop domain suite must run")
check("await PlayerRecruitSceneChecks.new().run(self, app, _check)" in ai_tests,
      "Player Hero Shop scene suite must run")
check((ROOT / "tests/fixtures/player_recruit_source.json").is_file(),
      "Player Hero Shop requires a source fixture")
if (ROOT / "tests/fixtures/player_recruit_source.json").is_file():
    check(player_recruit_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/player_recruit_source.json").read_text(encoding="utf-8")),
        "Player Hero Shop source transaction drift")
check("python godot_rebuild/tests/player_recruit_source_oracle.py" in workflow,
      "CI must execute the player Hero Shop source oracle")
player_shop = (ROOT / "scripts/ui/hero_shop_panel.gd").read_text(encoding="utf-8")
check("hero_requested.emit(hero_type)" in player_shop,
      "Hero Shop panel must route IDs through the fixed-tick session")
check("buy_player_hero(command.hero_type)" in
      (ROOT / "scripts/simulation/prototype_session.gd").read_text(encoding="utf-8"),
      "Player recruit command must execute through the match domain")

from meta_hero_unlock_source_oracle import source_fixture as meta_unlock_source_fixture
check("MetaHeroUnlockChecks.new().run(_check)" in ai_tests,
      "Permanent Hero Shop domain suite must run")
check("await MetaHeroUnlockSceneChecks.new().run(self, app, _check)" in ai_tests,
      "Permanent Hero Shop scene suite must run")
check((ROOT / "tests/fixtures/meta_hero_unlock_source.json").is_file(),
      "Permanent Hero Shop requires a source fixture")
if (ROOT / "tests/fixtures/meta_hero_unlock_source.json").is_file():
    check(meta_unlock_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/meta_hero_unlock_source.json").read_text(encoding="utf-8")),
        "Permanent Hero Shop source transaction drift")
check("python godot_rebuild/tests/meta_hero_unlock_source_oracle.py" in workflow,
      "CI must execute the permanent Hero Shop source oracle")
meta_shop = (ROOT / "scripts/ui/meta_hero_shop_panel.gd").read_text(encoding="utf-8")
meta_menu = (ROOT / "scenes/menu/main_menu.gd").read_text(encoding="utf-8")
meta_domain = (ROOT / "scripts/match/hero_unlock_store.gd").read_text(encoding="utf-8")
check("unlock_requested.emit(hero_type)" in meta_shop and "save_state" not in meta_shop,
      "Permanent shop panel must be request-only")
check("try_unlock(before, hero_type)" in meta_menu
      and "SaveSlotStore.save_path(result.state, progress_path" in meta_menu,
      "Main menu must atomically persist permanent unlock transactions")
check('const DEFAULT_HERO := "kaizen"' in meta_domain
      and "const MINI_BOSS_UNLOCK_COST := 4500" in meta_domain
      and "const TRUE_BOSS_UNLOCK_COST := 4500" in meta_domain,
      "Native permanent unlock policy must match source constants")
check("static func try_unlock" in meta_domain
      and "HeroUnlockStore.new()" not in meta_shop + meta_menu + app,
      "Permanent unlock authority must remain stateless across menu scenes")

from save_slot_source_oracle import source_fixture as save_slot_source_fixture
save_slot_fixture_path = ROOT / "tests/fixtures/save_slot_source.json"
check(save_slot_fixture_path.is_file(), "Save-slot runtime requires a source fixture")
if save_slot_fixture_path.is_file():
    check(save_slot_source_fixture()
          == json.loads(save_slot_fixture_path.read_text(encoding="utf-8")),
          "SaveManager source fixture drift")
check("python godot_rebuild/tests/save_slot_source_oracle.py" in workflow,
      "CI must execute the SaveManager source oracle")
check("- '_system.py'" in workflow, "Save-slot CI must track its real source authority")
check("SaveSlotChecks.new().run(_check)" in ai_tests,
      "Save-slot domain suite must run")
check("await SaveSlotSceneChecks.new().run(self, app, _check)" in ai_tests,
      "Save-slot playable lifecycle suite must run")
save_slot_store = (ROOT / "scripts/match/save_slot_store.gd").read_text(encoding="utf-8")
save_slot_panel = (ROOT / "scripts/ui/save_slot_panel.gd").read_text(encoding="utf-8")
check("const SLOT_COUNT := 3" in save_slot_store
      and "ProgressStore.save_state" in save_slot_store
      and "static func migrate_legacy" in save_slot_store,
      "Native save slots must preserve source count and atomic native storage")
check("slot_requested.emit(slot)" in save_slot_panel
      and "delete_requested.emit(slot)" in save_slot_panel
      and "SaveSlotStore.delete_slot" not in save_slot_panel,
      "Save-slot panel must remain request-only")
check("progress_slot_changed.emit(slot, progress_path)" in meta_menu
      and "current_screen.connect(\"progress_slot_changed\", _select_progress_slot)" in app,
      "Selected slot ownership must cross the menu/App scene boundary")
check("SaveSlotStore.save_path(result.state, path" in
      (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8"),
      "Match result must commit through the active native save slot")

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

from player_structure_command_source_oracle import source_fixture as player_structure_fixture
player_structure_path = ROOT / "tests/fixtures/player_structure_command_source.json"
check(player_structure_path.is_file(), "Player structure commands require a source fixture")
if player_structure_path.is_file():
    check(player_structure_fixture() == json.loads(player_structure_path.read_text(encoding="utf-8")),
          "Player structure command source fixture drift")
check("python godot_rebuild/tests/player_structure_command_source_oracle.py" in workflow,
      "CI must check player structure command oracle")
check("PlayerStructureCommandChecks.new().run(_check)" in ai_tests,
      "Player structure domain parity suite must run")
check("await PlayerStructureCommandSceneChecks.new().run(self, app, _check)" in ai_tests,
      "Player structure playable-scene suite must run")
structure_scene = (ROOT / "scenes/prototype/PrototypeMatch.tscn").read_text(encoding="utf-8")
check(all(name in structure_scene for name in ("RegenShieldButton", "CastleShieldButton")),
      "Playable scene must author both player shield controls")
check(all(path in shield_screen for path in ('"cannon"', '"ice"', '"mage"'))
      and "request_regen_shield" in shield_screen and "request_castle_shield" in shield_screen,
      "Playable scene must route all source build and shield choices")
structure_session = (ROOT / "scripts/simulation/prototype_session.gd").read_text(encoding="utf-8")
check("command.get(\"path\", \"archer\")" in structure_session
      and "activate_player_regen_shield" in structure_session
      and "activate_player_castle_shield" in structure_session,
      "Player structure mutations must cross the fixed-tick session")

from controller_source_oracle import source_fixture as controller_source_fixture
controller_fixture_path = ROOT / "tests/fixtures/controller_source.json"
check(controller_fixture_path.is_file(), "Controller runtime requires a source fixture")
if controller_fixture_path.is_file():
    check(controller_source_fixture()
          == json.loads(controller_fixture_path.read_text(encoding="utf-8")),
          "Controller runtime source fixture drift")
check("python godot_rebuild/tests/controller_source_oracle.py" in workflow,
      "CI must execute the controller source oracle")
check("ControllerRuntimeChecks.new().run(_check)" in ai_tests,
      "Controller source replay suite must run")
check("await ControllerSceneChecks.new().run(self, app, _check)" in ai_tests,
      "Controller playable-scene suite must run")
controller_runtime = (ROOT / "scripts/input/controller_runtime.gd").read_text(encoding="utf-8")
check(all(token in controller_runtime for token in
          ("CURSOR_ACCELERATION", "HAT_REPEAT_DELAY", "SCROLL_SPEED", "rumble")),
      "Native controller must retain cursor, repeat, scroll and rumble policy")
check("ControllerCursor" in structure_scene and "NextLevelButton" in structure_scene,
      "Playable scene must author controller cursor and next-level controls")
check(all(token in shield_screen for token in
          ("_route_controller_action", "_controller_snap", "_controller_scroll")),
      "Playable scene must route controller actions, snapping and scrolling")
check("prototype_is_replay" in app and "_start_next_prototype" in app,
      "App must own replay and next-level controller transitions")

from touch_gesture_source_oracle import source_fixture as touch_gesture_source_fixture
touch_fixture_path = ROOT / "tests/fixtures/touch_gesture_source.json"
check(touch_fixture_path.is_file(), "Touch gesture runtime requires a source fixture")
if touch_fixture_path.is_file():
    check(touch_gesture_source_fixture()
          == json.loads(touch_fixture_path.read_text(encoding="utf-8")),
          "Touch gesture source fixture drift")
check("python godot_rebuild/tests/touch_gesture_source_oracle.py" in workflow,
      "CI must execute the touch gesture source oracle")
check("- 'main.py'" in workflow and "- 'mobile/hud.py'" in workflow,
      "Touch CI must track the source routing and HUD claim authorities")
check("TouchGestureChecks.new().run(_check)" in ai_tests,
      "Touch gesture replay suite must run")
check("await TouchGestureSceneChecks.new().run(self, app, _check)" in ai_tests,
      "Touch gesture playable-scene suite must run")
touch_runtime = (ROOT / "scripts/input/touch_gesture_runtime.gd").read_text(encoding="utf-8")
check(all(token in touch_runtime for token in
          ("LONG_PRESS_MS", "DOUBLE_TAP_MS", "SCROLL_STEP", "FLING_FRICTION")),
      "Native touch runtime must retain hold, double-tap, scroll and fling policy")
check(all(token in shield_screen for token in
          ("_handle_touch_event", "_route_touch_actions", "_cancel_touch_input",
           "TOUCH_TARGET_MIN", "TOUCH_PADDING")),
      "Playable scene must own touch routing, cancellation and source hit areas")
check("request_hero_move" in shield_screen and "request_hero_follow" in shield_screen,
      "Touch world commands must cross the fixed-tick session")

# The native AI adapters are now reachable from the playable prototype, but
# remain explicitly toggleable for replay/debug comparisons.
check("_build_ai_toggle" in shield_screen and "KEY_A" in shield_screen,
      "Prototype scene must expose the AIPlayer QA toggle")
check("set_ai_enabled" in shield_screen and "world.ai_enabled" in shield_screen,
      "AI toggle must use the authoritative world controller state")
check("get_tree().paused" in shield_screen,
      "AI toggle must not mutate controller ownership while paused")
check("_build_migration_status" in shield_screen and "active_boss" in shield_screen,
      "Prototype HUD must expose migrated boss/AI runtime status")

check((ROOT / "SHIELD_CONTRACT.md").is_file(), "Paid shield semantics must be documented")

# The Pygame sound catalog must be available to the Godot client; audio is a
# migrated runtime service, not a Python-only dependency.
audio_script = (ROOT / "scripts/audio/audio_manager.gd")
check(audio_script.is_file(), "Godot audio manager must exist")
if audio_script.is_file():
    audio_text = audio_script.read_text(encoding="utf-8")
    check("play_music" in audio_text and "play_ambient" in audio_text and "set_enabled" in audio_text,
          "Godot audio manager must provide music, ambient and mute controls")
    check("func shutdown()" in audio_text and "player.stream = null" in audio_text,
          "Godot audio manager must release active streams before shutdown")
check((ROOT / "project.godot").read_text(encoding="utf-8").find('AudioManager="*res://scripts/audio/audio_manager.gd"') >= 0,
      "Godot audio manager must be autoloaded")
check((ROOT / "assets/audio/bgm_battle.wav").is_file(), "Migrated battle music asset missing")


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

from level_catalog_source_oracle import check as check_level_catalog
from level_theme_source_oracle import check as check_level_themes
from river_tiles_source_oracle import check as check_river_tiles
from lane_tiles_source_oracle import check as check_lane_tiles
from wall_tiles_source_oracle import check as check_wall_tiles
from terrain_source_oracle import check as check_terrain
check(check_terrain() == 8091, "Source terrain drawing must match native fixture")
check(check_level_themes() == 54, "All 54 native terrain palettes must match source")
check(check_river_tiles() == 1878, "Source tiled river drawing must match native fixture")
check(check_lane_tiles() == 6654, "Source cobblestone drawing must match native fixture")
check(check_wall_tiles() == 1323, "Source border wall drawing must match native fixture")
check("LevelThemeChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native terrain palette suite must run")
check("RiverTilesChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native river tiles suite must run")
check("LaneTilesChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native cobblestone suite must run")
check("WallTilesChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native border wall suite must run")
check("TerrainTilesChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native terrain suite must run")
from level_economy_source_oracle import check as check_level_economy
check(check_level_catalog() == 54, "All 54 native level entries must match Python source")
check(check_level_economy() == 162, "All level economy fixtures must match Python source")
check("LevelCatalogChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native level catalog suite must run")
check("LevelProgressChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native level progress suite must run")
check("LevelProgressStoreChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native progress storage suite must run")
check("func configure_level(number: int" in (ROOT / "scripts/simulation/prototype_session.gd").read_text(encoding="utf-8"), "Match session must expose pre-arena level selection")
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
from boss_minion_targeting_source_oracle import source_fixture as boss_minion_targeting_fixture
from boss_phase_order_source_oracle import source_fixture as boss_phase_order_fixture
from boss_ice_aoe_source_oracle import source_fixture as boss_ice_aoe_fixture
from boss_tower_damage_source_oracle import source_fixture as boss_tower_damage_fixture
from boss_cannon_splash_source_oracle import source_fixture as boss_cannon_splash_fixture
from boss_ice_main_slow_source_oracle import source_fixture as boss_ice_main_slow_fixture
from boss_tower_volley_source_oracle import source_fixture as boss_tower_volley_fixture
from boss_ability_source_attribution_oracle import (
    source_fixture as boss_ability_source_attribution_fixture,
)
from boss_item_stun_source_oracle import source_fixture as boss_item_stun_fixture
from boss_item_silence_source_oracle import source_fixture as boss_item_silence_fixture
from boss_item_slow_source_oracle import source_fixture as boss_item_slow_fixture
from boss_item_aura_source_oracle import source_fixture as boss_item_aura_fixture
from boss_item_cleave_chain_source_oracle import (
    source_fixture as boss_item_cleave_chain_fixture,
)
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
check("BossMinionTargetsChecks.new().run(_check)" in ai_tests,
      "Boss minion targeting suite must run")
check('const BossPhaseOrderChecks = preload("res://tests/boss_phase_order_checks.gd")' in ai_tests,
      "Boss hero-before-boss phase order suite must be preloaded")
check("BossPhaseOrderChecks.new().run(_check)" in ai_tests,
      "Boss hero-before-boss phase order suite must run")
check('const BossIceAoeChecks = preload("res://tests/boss_ice_aoe_checks.gd")' in ai_tests,
      "Boss ice AOE suite must be preloaded")
check("BossIceAoeChecks.new().run(_check)" in ai_tests,
      "Boss ice AOE suite must run")
check('const BossTowerDamageChecks = preload("res://tests/boss_tower_damage_checks.gd")' in ai_tests,
      "Boss tower damage suite must be preloaded")
check("BossTowerDamageChecks.new().run(_check)" in ai_tests,
      "Boss tower damage suite must run")
check('const BossCannonSplashChecks = preload("res://tests/boss_cannon_splash_checks.gd")' in ai_tests,
      "Boss cannon splash suite must be preloaded")
check("BossCannonSplashChecks.new().run(_check)" in ai_tests,
      "Boss cannon splash suite must run")
check('const BossIceMainSlowChecks = preload("res://tests/boss_ice_main_slow_checks.gd")' in ai_tests,
      "Boss ice main slow suite must be preloaded")
check("BossIceMainSlowChecks.new().run(_check)" in ai_tests,
      "Boss ice main slow suite must run")
check('const BossTowerVolleyChecks = preload("res://tests/boss_tower_volley_checks.gd")' in ai_tests,
      "Boss tower volley suite must be preloaded")
check("BossTowerVolleyChecks.new().run(_check)" in ai_tests,
      "Boss tower volley suite must run")
check(
    'const BossAbilitySourceAttributionChecks = preload(\n\t"res://tests/boss_ability_source_attribution_checks.gd"\n)'
    in ai_tests
    or 'const BossAbilitySourceAttributionChecks = preload("res://tests/boss_ability_source_attribution_checks.gd")'
    in ai_tests,
    "Boss ability source attribution suite must be preloaded",
)
check("BossAbilitySourceAttributionChecks.new().run(_check)" in ai_tests,
      "Boss ability source attribution suite must run")
check('const BossItemStunChecks = preload("res://tests/boss_item_stun_checks.gd")' in ai_tests,
      "Boss item stun suite must be preloaded")
check("BossItemStunChecks.new().run(_check)" in ai_tests,
      "Boss item stun suite must run")
check('const BossItemSilenceChecks = preload("res://tests/boss_item_silence_checks.gd")' in ai_tests,
      "Boss item silence suite must be preloaded")
check("BossItemSilenceChecks.new().run(_check)" in ai_tests,
      "Boss item silence suite must run")
check('const BossItemSlowChecks = preload("res://tests/boss_item_slow_checks.gd")' in ai_tests,
      "Boss item slow suite must be preloaded")
check("BossItemSlowChecks.new().run(_check)" in ai_tests,
      "Boss item slow suite must run")
check('const BossItemAuraChecks = preload("res://tests/boss_item_aura_checks.gd")' in ai_tests,
      "Boss item aura suite must be preloaded")
check("BossItemAuraChecks.new().run(_check)" in ai_tests,
      "Boss item aura suite must run")
check('const BossItemCleaveChainChecks = preload(' in ai_tests
      and '"res://tests/boss_item_cleave_chain_checks.gd")' in ai_tests,
      "Boss item cleave/chain suite must be preloaded")
check("BossItemCleaveChainChecks.new().run(_check)" in ai_tests,
      "Boss item cleave/chain suite must run")
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
check((ROOT / "tests/fixtures/boss_minion_targeting_source.json").is_file(),
      "Boss minion targeting requires source fixture")
if (ROOT / "tests/fixtures/boss_minion_targeting_source.json").is_file():
    _boss_minion_targeting = boss_minion_targeting_fixture()
    check(_boss_minion_targeting == json.loads(
        (ROOT / "tests/fixtures/boss_minion_targeting_source.json").read_text(encoding="utf-8")),
        "Boss minion targeting source behavior drift")
    _minion_targeting_source = _boss_minion_targeting.get("source", {})
    check(all(bool(_minion_targeting_source.get(key, False)) for key in (
        "query_radius_source", "grid_indexes_boss", "grid_inserts_heroes", "selection_order",
        "minion_groups_exclude_boss", "siege_group_uses_max_hp")),
        "Source must keep the boss inside the minion lookup path")
    _minion_targeting_cases = _boss_minion_targeting.get("cases", [])
    _minion_targeting_types = {case["boss_type"] for case in _minion_targeting_cases}
    check(len(_minion_targeting_cases) == 864
          and _minion_targeting_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _minion_targeting_cases) == 4
                  for _boss in _minion_targeting_types),
          "Boss minion targeting requires four source cases for all 216 boss types")
    check(all(case["expected"] == "boss" or case["expected"] == case["expected_without_boss"]
              for case in _minion_targeting_cases)
          and sum(case["expected"] == "boss" for case in _minion_targeting_cases) == 432
          and all((case["expected"] == "boss")
                  == (case["label"] in ("boss_at_attack_range_edge", "boss_precedes_siege_tower"))
                  for case in _minion_targeting_cases),
          "Minions must see the boss at the attack-range edge and ahead of appended towers")
    check(all(case["grid_radius"] == case["range"] + 30.0
              and case["boss_distance"] <= case["grid_radius"]
              for case in _minion_targeting_cases),
          "Every recorded case keeps the boss inside the source grid radius")
check((ROOT / "tests/fixtures/boss_phase_order_source.json").is_file(),
      "Boss phase ordering requires source fixture")
if (ROOT / "tests/fixtures/boss_phase_order_source.json").is_file():
    _boss_phase_order = boss_phase_order_fixture()
    _phase_order_path = ROOT / "tests/fixtures/boss_phase_order_source.json"
    check(_boss_phase_order == json.loads(_phase_order_path.read_text(encoding="utf-8")),
          "Boss hero-before-boss source phase order drift")
    _phase_order_source = _boss_phase_order.get("source", {})
    check(_phase_order_source.get("game_update_order") == ["heroes", "boss"]
          and _phase_order_source.get("speed_multiplier_update_order") == ["heroes", "boss"]
          and bool(_phase_order_source.get("boss_update_skips_dead", False)),
          "Both source Game paths update heroes before a live boss")
    _phase_order_cases = _boss_phase_order.get("cases", [])
    _phase_order_types = {case["boss_type"] for case in _phase_order_cases}
    _phase_order_labels = {
        "hero_lethal_hit_precedes_boss",
        "hero_wound_precedes_boss_attack",
        "hero_enters_attack_range_before_boss",
        "hero_exits_target_radius_before_boss",
    }
    check(len(_phase_order_cases) == 864
          and _phase_order_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _phase_order_cases) == 4
                  for _boss in _phase_order_types),
          "Boss phase order requires four source cases for all 216 boss types")
    check(all({case["label"] for case in _phase_order_cases
               if case["boss_type"] == _boss} == _phase_order_labels
              for _boss in _phase_order_types),
          "Boss phase order covers lethal/nonlethal hits and both movement boundaries")
check((ROOT / "tests/fixtures/boss_ice_aoe_source.json").is_file(),
      "Boss ice AOE requires source fixture")
if (ROOT / "tests/fixtures/boss_ice_aoe_source.json").is_file():
    _boss_ice_aoe = boss_ice_aoe_fixture()
    check(_boss_ice_aoe == json.loads(
        (ROOT / "tests/fixtures/boss_ice_aoe_source.json").read_text(encoding="utf-8")),
          "Boss ice AOE source drift")
    _ice_aoe_source = _boss_ice_aoe.get("source", {})
    check(all(bool(_ice_aoe_source.get(_flag, False)) for _flag in (
        "tower_passes_all_units", "castle_omits_all_units", "all_units_includes_boss",
        "ice_aoe_gated", "ice_aoe_radius_inclusive", "ice_aoe_skips_main_allies_dead",
        "ice_aoe_slow_is_polymorphic", "ice_aoe_atk_slow_is_polymorphic",
        "shoot_ice_gates_aoe", "boss_slow_uses_tenacity")),
          "Ice AOE source shape must gate on slow_aoe and slow victims polymorphically")
    _ice_aoe_levels = _ice_aoe_source.get("levels", {})
    check(_ice_aoe_levels.get("6", {}).get("slow_aoe") == 80.0
          and _ice_aoe_levels.get("5", {}).get("slow_aoe") == 0.0
          and _ice_aoe_levels.get("6", {}).get("atk_slow") == 0.4,
          "Only the source level-6 ice tower carries a freeze AOE")
    _ice_aoe_cases = _boss_ice_aoe.get("cases", [])
    _ice_aoe_types = {case["boss_type"] for case in _ice_aoe_cases}
    _ice_aoe_labels = {"aoe_inside_half", "aoe_edge_inclusive", "aoe_outside",
                       "no_aoe_below_level_six"}
    check(len(_ice_aoe_cases) == 864
          and _ice_aoe_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _ice_aoe_cases) == 4
                  for _boss in _ice_aoe_types),
          "Boss ice AOE requires four source cases for all 216 boss types")
    check(all({case["label"] for case in _ice_aoe_cases
               if case["boss_type"] == _boss} == _ice_aoe_labels for _boss in _ice_aoe_types),
          "Boss ice AOE covers the inclusive edge, the outside guard and the level-5 gate")
    check(all((case["expected"]["slow_timer"] > 0)
              == (case["label"] in ("aoe_inside_half", "aoe_edge_inclusive"))
              and case["expected_without_boss"]["slow_timer"] == 0
              for case in _ice_aoe_cases),
          "Only the in-radius level-6 AOE slows the boss, never the pre-layer candidate list")
    check(all(case["expected"]["slow_amount"]
              == min(0.35, case["slow_amount_in"] * (1.0 - case["tenacity"]))
              and case["expected"]["slow_timer"]
              == int(case["slow_duration_in"] * (1.0 - case["tenacity"]))
              and case["expected"]["atk_slow_timer"] == case["expected"]["slow_timer"]
              for case in _ice_aoe_cases if case["expected"]["slow_timer"] > 0),
          "Boss AOE slow must keep the source tenacity cut, 0.35 cap and shared duration")
check((ROOT / "tests/fixtures/boss_tower_damage_source.json").is_file(),
      "Boss tower damage requires source fixture")
if (ROOT / "tests/fixtures/boss_tower_damage_source.json").is_file():
    _boss_tower_damage = boss_tower_damage_fixture()
    check(_boss_tower_damage == json.loads(
        (ROOT / "tests/fixtures/boss_tower_damage_source.json").read_text(encoding="utf-8")),
          "Boss tower damage source drift")
    _tower_damage_source = _boss_tower_damage.get("source", {})
    check(all(bool(_tower_damage_source.get(_flag, False)) for _flag in (
        "main_hit_is_projectile", "hit_passes_no_school", "resolver_none_for_projectile",
        "resolver_rejects_unknown_school", "resolver_reads_source_school",
        "boss_mitigation_gated_by_school", "resolver_documented_none")),
          "Structure shots must resolve to no school and boss mitigation must stay school-gated")
    _tower_damage_cases = _boss_tower_damage.get("cases", [])
    _tower_damage_types = {case["boss_type"] for case in _tower_damage_cases}
    _tower_damage_labels = {"archer_level_one", "cannon_level_six", "ice_level_six",
                            "mage_level_six"}
    check(len(_tower_damage_cases) == 864
          and _tower_damage_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _tower_damage_cases) == 4
                  for _boss in _tower_damage_types),
          "Boss tower damage requires four source cases for all 216 boss types")
    check(all({case["label"] for case in _tower_damage_cases
               if case["boss_type"] == _boss} == _tower_damage_labels
              for _boss in _tower_damage_types),
          "Boss tower damage covers all four structure bullet kinds")
    check(all(case["expected_hp_after"] <= case["expected_physical_hp_after"]
              and case["alive"]
              for case in _tower_damage_cases),
          "School-free source hits must land at least as hard as the declared-school path")
    check(sum(case["expected_hp_after"] != case["expected_physical_hp_after"]
              for case in _tower_damage_cases) == 864,
          "Every boss armor value must make the two paths differ")
    check(all(case["hp_before"] - case["expected_hp_after"] >= 1
              for case in _tower_damage_cases),
          "Every recorded tower hit must damage the boss")
check((ROOT / "tests/fixtures/boss_cannon_splash_source.json").is_file(),
      "Boss cannon splash requires source fixture")
if (ROOT / "tests/fixtures/boss_cannon_splash_source.json").is_file():
    _boss_cannon_splash = boss_cannon_splash_fixture()
    check(_boss_cannon_splash == json.loads(
        (ROOT / "tests/fixtures/boss_cannon_splash_source.json").read_text(encoding="utf-8")),
          "Boss cannon splash source drift")
    _splash_source = _boss_cannon_splash.get("source", {})
    check(all(bool(_splash_source.get(_flag, False)) for _flag in (
        "tower_passes_all_units", "all_units_includes_boss", "splash_damage_scale",
        "splash_radius_inclusive", "splash_skips_main_allies_dead", "splash_hit_has_no_source",
        "splash_burn_uses_source_team", "burn_gated_by_dps", "kill_credit_written_on_lethal")),
          "Cannon splash source shape must stay inclusive, source-omitted and burn-gated")
    _splash_cannon = _splash_source.get("cannon", {})
    check(_splash_cannon.get("splash") == 100.0
          and _splash_cannon.get("splash_damage") == int(_splash_cannon.get("damage", 0) * 0.6),
          "Level-6 cannon splash radius and 60% damage must match the source table")
    _splash_cases = _boss_cannon_splash.get("cases", [])
    _splash_types = {case["boss_type"] for case in _splash_cases}
    _splash_labels = {"splash_inside_half", "splash_edge_inclusive", "splash_outside",
                      "splash_lethal_no_source"}
    check(len(_splash_cases) == 864
          and _splash_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _splash_cases) == 4
                  for _boss in _splash_types),
          "Boss cannon splash requires four source cases for all 216 boss types")
    check(all({case["label"] for case in _splash_cases
               if case["boss_type"] == _boss} == _splash_labels for _boss in _splash_types),
          "Boss cannon splash covers the inclusive edge, the outside guard and a lethal splash")
    check(all((case["expected"]["hp"] < case["hp_before"])
              == (case["label"] != "splash_outside")
              and case["expected_without_boss"]["hp"] == case["hp_before"]
              and case["expected_without_boss"]["burn_timer"] == 0
              for case in _splash_cases),
          "Only the in-radius splash hurts the boss, never the pre-layer candidate list")
    check(all((case["expected"]["burn_timer"] == case["burn_duration_in"])
              == (case["expected"]["hp"] < case["hp_before"] and case["expected"]["alive"])
              and (case["expected"]["burn_team"] == "blue")
              == (case["expected"]["burn_timer"] > 0)
              for case in _splash_cases),
          "Splash burn must land on survivors only and keep the shooter team")
    check(all((not case["expected"]["alive"]) == (case["label"] == "splash_lethal_no_source")
              and (case["expected"]["killed_by_none"] or case["expected"]["alive"])
              for case in _splash_cases),
          "A lethal splash must kill without crediting any source")
    check(all(case["expected"]["hp"] <= case["expected_physical_hp_after"]
              for case in _splash_cases if case["expected"]["hp"] < case["hp_before"]),
          "School-free splash must land at least as hard as the declared-school path")
check((ROOT / "tests/fixtures/boss_ice_main_slow_source.json").is_file(),
      "Boss ice main slow requires source fixture")
if (ROOT / "tests/fixtures/boss_ice_main_slow_source.json").is_file():
    _boss_ice_main = boss_ice_main_slow_fixture()
    check(_boss_ice_main == json.loads(
        (ROOT / "tests/fixtures/boss_ice_main_slow_source.json").read_text(encoding="utf-8")),
          "Boss ice main slow source drift")
    _ice_main_source = _boss_ice_main.get("source", {})
    check(all(bool(_ice_main_source.get(_flag, False)) for _flag in (
        "main_slow_is_polymorphic", "main_atk_slow_is_polymorphic", "main_atk_slow_gated",
        "boss_slow_requires_alive", "boss_slow_uses_tenacity", "boss_slow_cuts_duration",
        "boss_atk_slow_uses_tenacity", "mixin_slow_has_no_tenacity")),
          "Ice main-target slow must stay polymorphic and boss-only tenacity-gated")
    _ice_main_cases = _boss_ice_main.get("cases", [])
    _ice_main_types = {case["boss_type"] for case in _ice_main_cases}
    _ice_main_labels = {"level_six_single", "level_five_single",
                        "strong_then_weak_keeps_strongest", "weak_then_strong_refreshes"}
    check(len(_ice_main_cases) == 864
          and _ice_main_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _ice_main_cases) == 4
                  for _boss in _ice_main_types),
          "Boss ice main slow requires four source cases for all 216 boss types")
    check(all({case["label"] for case in _ice_main_cases
               if case["boss_type"] == _boss} == _ice_main_labels
              for _boss in _ice_main_types),
          "Boss ice main slow covers both ice levels and both store-rule directions")
    check(all(case["expected"]["slow_amount"] < case["expected_mixin"]["slow_amount"]
              and case["expected"]["slow_timer"] < case["expected_mixin"]["slow_timer"]
              and case["expected"]["atk_slow_amount"] < case["expected_mixin"]["atk_slow_amount"]
              for case in _ice_main_cases),
          "Boss tenacity must cut both slow magnitude and duration below the mixin store")
    check(all(case["expected"]["slow_amount"]
              == min(0.35, max(row["slow"] for row in case["inputs"])
                     * (1.0 - case["tenacity"]))
              and case["expected"]["atk_slow_amount"]
              == min(0.35, max(row["atk_slow"] for row in case["inputs"])
                     * (1.0 - case["tenacity"]))
              for case in _ice_main_cases),
          "Boss main-target slow must equal the tenacity cut of the strongest ice level")
    check(all(case["expected_mixin"]["slow_amount"]
              == max(row["slow"] for row in case["inputs"])
              and case["expected_mixin"]["atk_slow_amount"]
              == max(row["atk_slow"] for row in case["inputs"])
              for case in _ice_main_cases),
          "Non-boss main targets must keep the raw mixin store")
check((ROOT / "tests/fixtures/boss_tower_volley_source.json").is_file(),
      "Boss tower volley requires source fixture")
if (ROOT / "tests/fixtures/boss_tower_volley_source.json").is_file():
    _boss_tower_volley = boss_tower_volley_fixture()
    check(_boss_tower_volley == json.loads(
        (ROOT / "tests/fixtures/boss_tower_volley_source.json").read_text(encoding="utf-8")),
          "Boss tower volley source drift")
    _volley_source = _boss_tower_volley.get("source", {})
    check(all(bool(_volley_source.get(_flag, False)) for _flag in (
        "tower_boss_scan_in_update", "tower_update_passes_enemies_to_shoot",
        "shoot_dispatches_archer_and_mage", "archer_volley_scans_enemies_inclusive",
        "archer_volley_refills_primary", "mage_chain_scans_enemies_inclusive",
        "mage_chain_has_no_refill", "all_units_includes_boss")),
          "Tower volley and chain source shape must keep the boss scan, inclusive range and refill split")
    check(_volley_source.get("archer_l5", {}).get("volley_count") == 2
          and _volley_source.get("archer_l6", {}).get("volley_count") == 3
          and _volley_source.get("mage_l2", {}).get("chain") == 2
          and _volley_source.get("mage_l6", {}).get("chain") == 4,
          "Source archer volley and mage chain counts must match the tier tables")
    _volley_cases = _boss_tower_volley.get("cases", [])
    _volley_types = {case["boss_type"] for case in _volley_cases}
    _volley_labels = {"archer_l5_boss_at_range_edge", "archer_l6_unit_fills_before_boss",
                      "mage_l2_boss_at_range_edge", "mage_l6_boss_outside_range"}
    check(len(_volley_cases) == 864
          and _volley_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _volley_cases) == 4
                  for _boss in _volley_types),
          "Boss tower volley requires four source cases for all 216 boss types")
    check(all({case["label"] for case in _volley_cases
               if case["boss_type"] == _boss} == _volley_labels
              for _boss in _volley_types),
          "Boss tower volley covers archer L5/L6 volleys, mage L2 chain edge and mage L6 outside guard")
    check(all((case["expected"]["boss_shots"] == 1) == case["boss_in_range"]
              and case["expected_without_boss"]["boss_shots"] == 0
              for case in _volley_cases),
          "Only an in-range boss takes a secondary volley/chain shot, never the pre-layer scan")
    check(all(case["expected"]["shot_targets"] != case["expected_without_boss"]["shot_targets"]
              for case in _volley_cases if case["boss_in_range"]),
          "Every in-range boss case must diverge from the pre-layer units-only target list")
    check(all(case["expected"]["shot_count"] == case["slot_count"]
              and case["expected_without_boss"]["shot_count"] == case["slot_count"]
              for case in _volley_cases if case["tower_path"] == "archer"),
          "Archer volleys must always emit their full arrow count via secondary targets or primary refill")
    check(all(case["expected"]["shot_count"] == 2
              and case["expected_without_boss"]["shot_count"] == 1
              for case in _volley_cases if case["label"] == "mage_l2_boss_at_range_edge"),
          "Mage L2 must emit a second chain bolt to the in-range boss and omit it without the boss")
check((ROOT / "tests/fixtures/boss_ability_source_attribution.json").is_file(),
      "Boss ability source attribution requires source fixture")
if (ROOT / "tests/fixtures/boss_ability_source_attribution.json").is_file():
    _boss_ability_attr = boss_ability_source_attribution_fixture()
    check(_boss_ability_attr == json.loads(
        (ROOT / "tests/fixtures/boss_ability_source_attribution.json").read_text(encoding="utf-8")),
        "Boss ability source attribution source behavior drift")
    _attr_source = _boss_ability_attr.get("source", {})
    check(all(bool(_attr_source.get(_flag)) for _flag in (
        "basic_attack_passes_source_self", "cleave_omits_source",
        "generic_ability_omits_source", "all_ability_take_damage_calls_omit_source",
        "hero_blind_requires_source", "bristleback_reflect_requires_source",
        "razor_carapace_reflect_requires_source", "hero_killed_by_requires_source")),
          "Boss ability source attribution shape must keep source=None on all ability/skill hits")
    check(_attr_source.get("ability_take_damage_call_count") == 177
          and _attr_source.get("razor_carapace_armor") == 12
          and _attr_source.get("razor_carapace_reflect_pct") == 0.35
          and _attr_source.get("leviathan_combat_timeout") == 300,
          "Boss ability source attribution metadata must match source call count and item constants")
    _attr_cases = _boss_ability_attr.get("cases", [])
    _attr_types = {case["boss_type"] for case in _attr_cases}
    _attr_scenarios = {
        "blind_boss_ability_lands",
        "bristleback_mitigates_without_reflect",
        "razor_carapace_combat_timer_without_reflect",
        "lethal_ability_preserves_uncredited_killed_by",
    }
    check(len(_attr_cases) == 864
          and _attr_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _attr_cases) == 4
                  for _boss in _attr_types),
          "Boss ability source attribution requires four source cases for all 216 boss types")
    check(all({case["scenario"] for case in _attr_cases
               if case["boss_type"] == _boss} == _attr_scenarios
              for _boss in _attr_types),
          "Boss ability source attribution covers blind, Bristleback, Razor Carapace and lethal killed_by")
    check(all(case["expected"] != case["expected_with_boss_source"]
              and not case["expected"]["hit_source_attributed"]
              and case["expected_with_boss_source"]["hit_source_attributed"]
              for case in _attr_cases),
          "Every boss ability attribution case must differ between source=None and source=boss")
    check(all(case["expected"]["damage_taken"] > 0
              and case["expected_with_boss_source"]["damage_taken"] == 0
              for case in _attr_cases if case["scenario"] == "blind_boss_ability_lands"),
          "Blinded boss abilities must land when uncredited and miss only when source=boss is injected")
    check(all(case["expected"]["reflect_raw"] == 0
              and case["expected_with_boss_source"]["reflect_raw"] > 0
              and case["expected"]["target_hp"] == case["expected_with_boss_source"]["target_hp"]
              for case in _attr_cases
              if case["scenario"] in (
                  "bristleback_mitigates_without_reflect",
                  "razor_carapace_combat_timer_without_reflect",
              )),
          "Bristleback and Razor Carapace must mitigate boss abilities without reflecting onto the boss")
    check(all(not case["expected"]["target_alive"]
              and case["expected"]["target_deaths"] == 1
              and not case["expected"]["killed_by_boss"]
              and case["expected_with_boss_source"]["killed_by_boss"]
              for case in _attr_cases
              if case["scenario"] == "lethal_ability_preserves_uncredited_killed_by"),
          "Lethal boss abilities must not overwrite hero killed_by with the boss")
check((ROOT / "tests/fixtures/boss_item_stun_source.json").is_file(),
      "Boss item stun requires source fixture")
if (ROOT / "tests/fixtures/boss_item_stun_source.json").is_file():
    _boss_item_stun = boss_item_stun_fixture()
    check(_boss_item_stun == json.loads(
        (ROOT / "tests/fixtures/boss_item_stun_source.json").read_text(encoding="utf-8")),
        "Boss item stun source behavior drift")
    _stun_source = _boss_item_stun.get("source", {})
    check(all(bool(_stun_source.get(_flag)) for _flag in (
        "apply_stun_to_uses_getattr_apply_stun",
        "boss_apply_stun_scales_by_0_45",
        "boss_apply_stun_uses_max_timer",
        "boss_update_ticks_debuffs_before_stun_gate",
        "boss_update_stun_gate_returns_before_combat")),
          "Boss item stun shape must delegate _apply_stun_to to boss.apply_stun and gate Boss.update")
    check(_stun_source.get("sundering_cudgel_stun_ticks") == 15
          and _stun_source.get("sundering_cudgel_cooldown") == 120
          and _stun_source.get("abyss_breaker_bash_stun_ticks") == 54
          and _stun_source.get("abyss_breaker_bash_cooldown") == 140
          and _stun_source.get("abyss_breaker_overwhelm_stun_ticks") == 72
          and _stun_source.get("abyss_breaker_overwhelm_cooldown") == 1500
          and _stun_source.get("fenrir_chain_root_duration") == 72
          and _stun_source.get("fenrir_chain_cooldown") == 1080
          and _stun_source.get("hex_idol_stun_ticks") == 150
          and _stun_source.get("hex_idol_cooldown") == 1800,
          "Boss item stun metadata must match source item stun durations and cooldowns")
    _stun_cases = _boss_item_stun.get("cases", [])
    _stun_types = {case["boss_type"] for case in _stun_cases}
    _stun_scenarios = {
        "sundering_cudgel_pierce_bash",
        "abyss_breaker_bash",
        "abyss_breaker_overwhelm",
        "hex_idol_hexcraft",
    }
    check(len(_stun_cases) == 864
          and _stun_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _stun_cases) == 4
                  for _boss in _stun_types),
          "Boss item stun requires four source cases for all 216 boss types")
    check(all({case["scenario"] for case in _stun_cases
               if case["boss_type"] == _boss} == _stun_scenarios
              for _boss in _stun_types),
          "Boss item stun covers Sundering Cudgel, Abyss Breaker Bash/Overwhelm and Hex Idol")
    check(all(case["expected"] != case["expected_without_boss_stun"]
              and case["expected"]["stun_on_apply"] == int(case["expected"]["raw_stun"] * 0.45)
              and case["expected"]["stun_after_step"] == case["expected"]["stun_on_apply"] - 1
              and not case["expected"]["boss_basic_attack_fired"]
              and case["expected_without_boss_stun"]["boss_basic_attack_fired"]
              for case in _stun_cases),
          "Every boss item stun case must apply 45% stun duration and gate Boss.update")
    check(all(case["expected"]["boss_ability2_timer_after"] == 0
              and case["expected_without_boss_stun"]["boss_ability2_timer_after"] > 0
              for case in _stun_cases if case["boss_class"] == "true"),
          "Stunned true bosses must not cast their low-HP heal until stun_timer reaches zero")
check((ROOT / "tests/fixtures/boss_item_silence_source.json").is_file(),
      "Boss item silence requires source fixture")
if (ROOT / "tests/fixtures/boss_item_silence_source.json").is_file():
    _boss_item_silence = boss_item_silence_fixture()
    check(_boss_item_silence == json.loads(
        (ROOT / "tests/fixtures/boss_item_silence_source.json").read_text(encoding="utf-8")),
        "Boss item silence source behavior drift")
    _silence_source = _boss_item_silence.get("source", {})
    check(all(bool(_silence_source.get(_flag)) for _flag in (
        "silence_applies_atk_slow_then_skill_down",
        "silence_uses_apply_debuff_branch",
        "boss_debuff_cuts_atk_slow_by_tenacity",
        "boss_debuff_leaves_skill_down_untouched",
        "boss_debuff_delegates_to_mixin_store",
        "mixin_store_is_strongest_wins")),
          "Boss item silence shape must route _apply_silence_to through Boss.apply_debuff")
    check(_silence_source.get("sanguine_thorn_silence_duration") == 300
          and _silence_source.get("sanguine_thorn_cooldown") == 1080
          and _silence_source.get("sanguine_thorn_damage_amp") == 0.3
          and _silence_source.get("astral_codex_silence_duration") == 90
          and _silence_source.get("astral_codex_trigger_enemies") == 2
          and _silence_source.get("astral_codex_cooldown") == 1440
          and _silence_source.get("hex_idol_silence_ticks") == 150
          and _silence_source.get("hex_idol_stun_ticks") == 150
          and _silence_source.get("hex_idol_cooldown") == 1800,
          "Boss item silence metadata must match source item silence durations and cooldowns")
    _silence_cases = _boss_item_silence.get("cases", [])
    _silence_types = {case["boss_type"] for case in _silence_cases}
    _silence_scenarios = {
        "sanguine_thorn_soul_rend",
        "astral_codex_arcane_nova",
        "hex_idol_hexcraft",
        "soul_rend_and_arcane_nova_keep_longest_store",
    }
    check(len(_silence_cases) == 864
          and _silence_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _silence_cases) == 4
                  for _boss in _silence_types),
          "Boss item silence requires four source cases for all 216 boss types")
    check(all({case["scenario"] for case in _silence_cases
               if case["boss_type"] == _boss} == _silence_scenarios
              for _boss in _silence_types),
          "Boss item silence covers Soul Rend, Arcane Nova, Hexcraft and the stacked store")
    check(all(case["expected"] != case["expected_without_boss_tenacity"]
              and case["expected"]["atk_slow_amount"] == 0.35
              and case["expected"]["skill_down_amount"] == 1.0
              and case["expected"]["atk_slow_amount"]
              < case["expected_without_boss_tenacity"]["atk_slow_amount"]
              and case["expected"]["atk_slow_timer"]
              < case["expected_without_boss_tenacity"]["atk_slow_timer"]
              and case["expected_without_boss_tenacity"]["atk_slow_amount"] == 1.0
              and case["expected_without_boss_tenacity"]["atk_slow_timer"]
              == max(case["expected"]["raw_silence_durations"])
              for case in _silence_cases),
          "Every boss item silence case must cut atk_slow by tenacity and keep skill_down raw")
check((ROOT / "tests/fixtures/boss_item_slow_source.json").is_file(),
      "Boss item slow requires source fixture")
if (ROOT / "tests/fixtures/boss_item_slow_source.json").is_file():
    _boss_item_slow = boss_item_slow_fixture()
    check(_boss_item_slow == json.loads(
        (ROOT / "tests/fixtures/boss_item_slow_source.json").read_text(encoding="utf-8")),
        "Boss item slow source behavior drift")
    _slow_source = _boss_item_slow.get("source", {})
    check(all(bool(_slow_source.get(_flag)) for _flag in (
        "vine_rod_roots_with_full_slow",
        "vine_rod_cooldown_armed_before_root",
        "arctic_blast_slows_each_nearby_enemy",
        "arctic_blast_uses_hasattr_gate",
        "frostbite_slows_target",
        "frostbite_applies_atk_slow_and_anti_heal",
        "boss_apply_slow_cuts_by_tenacity",
        "boss_apply_slow_uses_amount_or_timer_store",
        "boss_apply_debuff_cuts_only_atk_slow")),
          "Boss item slow shape must route target.apply_slow/apply_debuff through Boss.apply_slow")
    check(_slow_source.get("vine_rod_root_magnitude") == 1.0
          and _slow_source.get("vine_rod_root_duration") == 60
          and _slow_source.get("vine_rod_cooldown") == 540
          and _slow_source.get("everfrost_slow") == 0.45
          and _slow_source.get("everfrost_slow_duration") == 210
          and _slow_source.get("everfrost_radius") == 280
          and _slow_source.get("everfrost_trigger_enemies") == 2
          and _slow_source.get("everfrost_cooldown") == 1440
          and _slow_source.get("frostbound_slow") == 0.28
          and _slow_source.get("frostbound_atk_slow") == 0.28
          and _slow_source.get("frostbound_anti_heal") == 0.45
          and _slow_source.get("frostbound_duration") == 180,
          "Boss item slow metadata must match source item slow payloads and cooldowns")
    _slow_cases = _boss_item_slow.get("cases", [])
    _slow_types = {case["boss_type"] for case in _slow_cases}
    _slow_scenarios = {
        "vine_rod_root_on_boss",
        "everfrost_arctic_blast_on_boss",
        "frostbound_frostbite_on_boss",
        "root_then_frostbite_store_rule",
    }
    check(len(_slow_cases) == 864
          and _slow_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _slow_cases) == 4
                  for _boss in _slow_types),
          "Boss item slow requires four source cases for all 216 boss types")
    check(all({case["scenario"] for case in _slow_cases
               if case["boss_type"] == _boss} == _slow_scenarios
              for _boss in _slow_types),
          "Boss item slow covers Entangle, Arctic Blast, Frostbite and the stacked store")
    _slow_want = {
        "vine_rod_root_on_boss": (0.35, 30),
        "everfrost_arctic_blast_on_boss": (0.225, 105),
        "frostbound_frostbite_on_boss": (0.14, 90),
        "root_then_frostbite_store_rule": (0.14, 90),
    }
    _slow_raw = {
        "vine_rod_root_on_boss": (1.0, 60),
        "everfrost_arctic_blast_on_boss": (0.45, 210),
        "frostbound_frostbite_on_boss": (0.28, 180),
        "root_then_frostbite_store_rule": (1.0, 180),
    }
    check(all(case["expected"]["slow_calls"] == case["expected_without_boss_tenacity"]["slow_calls"]
              and case["expected"]["boss_slow_amount"]
              == _slow_want[case["scenario"]][0]
              and case["expected"]["boss_slow_timer"] == _slow_want[case["scenario"]][1]
              and case["expected_without_boss_tenacity"]["boss_slow_amount"]
              == _slow_raw[case["scenario"]][0]
              and case["expected_without_boss_tenacity"]["boss_slow_timer"]
              == _slow_raw[case["scenario"]][1]
              and case["expected"]["boss_slow_amount"]
              < case["expected_without_boss_tenacity"]["boss_slow_amount"]
              and case["expected"]["boss_slow_timer"]
              < case["expected_without_boss_tenacity"]["boss_slow_timer"]
              for case in _slow_cases),
          "Every boss item slow case must cut magnitude and duration by tenacity 0.50")
    check(all(case["expected"]["boss_atk_slow_amount"] == 0.14
              and case["expected"]["boss_atk_slow_timer"] == 90
              and case["expected_without_boss_tenacity"]["boss_atk_slow_amount"] == 0.28
              and case["expected"]["boss_anti_heal_amount"] == 0.45
              and case["expected"]["boss_anti_heal_timer"] == 180
              for case in _slow_cases
              if case["scenario"] == "frostbound_frostbite_on_boss"),
          "Frostbite must cut atk_slow by tenacity and keep anti_heal untempered")
    check(all(case["expected"]["cooldowns"]["vine_rod"] == 540
              and case["expected"]["cooldowns"]["everfrost_guard"] == 0
              for case in _slow_cases if case["scenario"] == "vine_rod_root_on_boss"),
          "Vine Rod must arm its 540-tick cooldown when the root lands")
    check(all(case["expected"]["cooldowns"]["everfrost_guard"] == 1440
              and case["expected_without_boss_tenacity"]["cooldowns"]["everfrost_guard"] == 1440
              for case in _slow_cases
              if case["scenario"] == "everfrost_arctic_blast_on_boss"),
          "Everfrost Arctic Blast must arm its 1440-tick cooldown in both columns")
check((ROOT / "tests/fixtures/boss_item_cleave_chain_source.json").is_file(),
      "Boss item cleave/chain requires source fixture")
if (ROOT / "tests/fixtures/boss_item_cleave_chain_source.json").is_file():
    _boss_item_cc = boss_item_cleave_chain_fixture()
    check(_boss_item_cc == json.loads(
        (ROOT / "tests/fixtures/boss_item_cleave_chain_source.json").read_text(encoding="utf-8")),
        "Boss item cleave/chain source behavior drift")
    _cc_source = _boss_item_cc.get("source", {})
    check(all(bool(_cc_source.get(_flag)) for _flag in (
        "melee_onhit_list_appends_live_boss",
        "collect_onhit_units_appends_live_boss",
        "cleave_iterates_all_units",
        "cleave_radius_is_inclusive",
        "cleave_skips_same_team",
        "cleave_skips_the_main_target",
        "chain_iterates_all_units",
        "chain_appends_inside_radius",
        "chain_breaks_when_slots_are_full",
        "chain_damage_is_magic")),
          "Boss item cleave/chain shape must scan the source on-hit unit list")
    check(_cc_source.get("cleave_pct") == 0.50
          and _cc_source.get("cleave_radius") == 110.0
          and _cc_source.get("chain_chance") == 0.20
          and _cc_source.get("chain_damage") == 45
          and _cc_source.get("chain_targets") == 3
          and _cc_source.get("chain_radius") == 240.0
          and _cc_source.get("coil_damage") == 40
          and _cc_source.get("coil_targets") == 3
          and _cc_source.get("coil_radius") == 240.0
          and _cc_source.get("basic_damage") == 50,
          "Boss item cleave/chain metadata must match the source item payloads")
    _cc_cases = _boss_item_cc.get("cases", [])
    _cc_types = {case["boss_type"] for case in _cc_cases}
    _cc_scenarios = {
        "cleave_splashes_boss_inside_radius",
        "cleave_skips_boss_outside_radius",
        "fenrir_chain_hits_boss",
        "chain_slots_fill_before_boss",
    }
    check(len(_cc_cases) == 864
          and _cc_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _cc_cases) == 4
                  for _boss in _cc_types),
          "Boss item cleave/chain requires four source cases for all 216 boss types")
    check(all({case["scenario"] for case in _cc_cases if case["boss_type"] == _boss}
              == _cc_scenarios for _boss in _cc_types),
          "Boss item cleave/chain covers cleave, cleave radius, arc chain and full slots")
    _cc_cleave = [case for case in _cc_cases
                  if case["scenario"] == "cleave_splashes_boss_inside_radius"]
    _cc_out = [case for case in _cc_cases
               if case["scenario"] == "cleave_skips_boss_outside_radius"]
    _cc_chain = [case for case in _cc_cases if case["scenario"] == "fenrir_chain_hits_boss"]
    _cc_full = [case for case in _cc_cases
                if case["scenario"] == "chain_slots_fill_before_boss"]
    check(all(case["expected"]["boss_hits"] == [25]
              and case["expected"]["minion_hits"] == [25]
              and case["expected"]["target_hits"] == []
              and case["expected_without_boss"]["boss_hits"] == []
              and case["expected_without_boss"]["minion_hits"] == [25]
              for case in _cc_cleave),
          "Cleave must splash 25 onto the boss inside the 110 px radius")
    check(all(case["expected"]["boss_hits"] == []
              and case["expected_without_boss"]["boss_hits"] == []
              and case["expected"]["minion_hits"] == [25]
              for case in _cc_out),
          "Cleave must skip the boss beyond the radius in both columns")
    check(all(case["expected"]["boss_hits"] == [45]
              and case["expected"]["target_hits"] == [45]
              and case["expected"]["chain_roles"] == ["target", "minion", "boss"]
              and case["expected"]["chain_damage_type"] == "magic"
              and case["expected_without_boss"]["boss_hits"] == []
              and case["expected_without_boss"]["chain_roles"] == ["target", "minion"]
              for case in _cc_chain),
          "Arc chain must append the boss as the last slot and deal 45 magic")
    check(all(case["expected"]["boss_hits"] == []
              and case["expected_without_boss"]["boss_hits"] == []
              and case["expected"]["chain_roles"] == ["target", "minion", "minion"]
              and case["expected_without_boss"]["chain_roles"] == ["target", "minion", "minion"]
              for case in _cc_full),
          "Full chain slots must end the scan before the boss in both columns")
check((ROOT / "tests/fixtures/boss_item_aura_source.json").is_file(),
      "Boss item aura requires source fixture")
if (ROOT / "tests/fixtures/boss_item_aura_source.json").is_file():
    _boss_item_aura = boss_item_aura_fixture()
    check(_boss_item_aura == json.loads(
        (ROOT / "tests/fixtures/boss_item_aura_source.json").read_text(encoding="utf-8")),
        "Boss item aura source behavior drift")
    _aura_source = _boss_item_aura.get("source", {})
    check(all(bool(_aura_source.get(_flag)) for _flag in (
        "auras_loop_over_collected_units",
        "collect_all_units_appends_live_boss",
        "collect_all_units_requires_alive_boss",
        "everfrost_aura_applies_atk_slow_and_anti_heal",
        "solar_aura_burns_with_source_team",
        "solar_aura_blinds_via_miss_chance",
        "searbrand_aura_applies_anti_heal_and_burn",
        "aura_arms_skip_the_source_team",
        "boss_apply_debuff_cuts_only_atk_slow",
        "tower_store_resets_expired_burn_clock")),
          "Boss item aura shape must route the aura arms through Boss.apply_debuff")
    check(_aura_source.get("everfrost_aura_radius") == 300
          and _aura_source.get("everfrost_aura_atk_slow") == 0.30
          and _aura_source.get("everfrost_aura_anti_heal") == 0.40
          and _aura_source.get("solar_aura_radius") == 280
          and _aura_source.get("solar_aura_burn_dps") == 28.0
          and _aura_source.get("solar_aura_blind") == 0.18
          and _aura_source.get("searbrand_aura_radius") == 300
          and _aura_source.get("searbrand_aura_anti_heal") == 0.50
          and _aura_source.get("searbrand_aura_burn_dps") == 6.0
          and _aura_source.get("searbrand_burst_burn_dps") == 22.0
          and _aura_source.get("searbrand_burst_burn_duration") == 180
          and _aura_source.get("aura_debuff_ticks") == 30
          and _aura_source.get("burn_tick") == 30,
          "Boss item aura metadata must match the source aura payloads")
    _aura_cases = _boss_item_aura.get("cases", [])
    _aura_types = {case["boss_type"] for case in _aura_cases}
    _aura_scenarios = {
        "everfrost_freezing_aura_on_boss",
        "solar_scorched_earth_on_boss",
        "searbrand_cauterize_on_boss",
        "brand_burst_burn_after_expired_burn",
    }
    check(len(_aura_cases) == 864
          and _aura_types == set(boss_motion_source_types())
          and all(sum(case["boss_type"] == _boss for case in _aura_cases) == 4
                  for _boss in _aura_types),
          "Boss item aura requires four source cases for all 216 boss types")
    check(all({case["scenario"] for case in _aura_cases if case["boss_type"] == _boss}
              == _aura_scenarios for _boss in _aura_types),
          "Boss item aura covers Freezing Aura, Scorched Earth, Cauterize and the burn clock")
    _frost = [case for case in _aura_cases
              if case["scenario"] == "everfrost_freezing_aura_on_boss"]
    _solar = [case for case in _aura_cases
              if case["scenario"] == "solar_scorched_earth_on_boss"]
    _sear = [case for case in _aura_cases
             if case["scenario"] == "searbrand_cauterize_on_boss"]
    _burst = [case for case in _aura_cases
              if case["scenario"] == "brand_burst_burn_after_expired_burn"]
    check(all(case["expected"]["boss_atk_slow_amount"] == 0.15
              and case["expected"]["boss_atk_slow_timer"] == 15
              and case["expected_without_boss_store"]["boss_atk_slow_amount"] == 0.30
              and case["expected_without_boss_store"]["boss_atk_slow_timer"] == 30
              and case["expected"]["boss_atk_slow_amount"]
              < case["expected_without_boss_store"]["boss_atk_slow_amount"]
              and case["expected"]["boss_anti_heal_amount"] == 0.40
              and case["expected"]["boss_anti_heal_amount"]
              == case["expected_without_boss_store"]["boss_anti_heal_amount"]
              and case["expected"]["apply_atk_slow_calls"] == [[0.3, 30]]
              and case["expected_without_boss_store"]["apply_atk_slow_calls"] == [[0.3, 30]]
              for case in _frost),
          "Freezing Aura must cut the boss atk_slow to 0.15/15 and keep anti_heal 0.40/30")
    check(all(case["expected"]["boss_burn_dps"] == 28.0
              and case["expected"]["boss_burn_timer"] == 30
              and case["expected"]["boss_burn_team"] == 0
              and case["expected"]["boss_burn_tick_cd"] == 30
              and case["expected_without_boss_store"]["boss_burn_tick_cd"] == 30
              and case["expected"]["boss_blind_amount"] == 0.18
              and case["expected"]["boss_blind_timer"] == 30
              and case["expected"]["apply_burn_calls"] == [[28.0, 30, 0]]
              and case["expected"]["apply_miss_chance_calls"] == [[0.18, 30]]
              for case in _solar),
          "Scorched Earth must burn 28/30 in blue and blind 0.18/30 on the boss")
    check(all(case["expected"]["boss_anti_heal_amount"] == 0.50
              and case["expected"]["boss_anti_heal_timer"] == 30
              and case["expected"]["boss_burn_dps"] == 6.0
              and case["expected"]["boss_burn_team"] == 0
              and case["expected"]["apply_anti_heal_calls"] == [[0.5, 30]]
              and case["expected"]["apply_burn_calls"] == [[6.0, 30, 0]]
              for case in _sear),
          "Cauterize must anti-heal 0.50/30 and burn 6/30 on the boss")
    check(all(case["expected"]["after_delivery"]["burn_tick_cd"] == 30
              and case["expected"]["burn_damage_after_23_ticks"] == 0
              and case["expected_without_boss_store"]["after_delivery"]["burn_tick_cd"] == 23
              and case["expected_without_boss_store"]["burn_damage_after_23_ticks"] == 8
              and case["expected"]["apply_burn_calls"] == [[22.0, 180, 0]]
              and case["pre_fix_delivery"] == "burn_field_write"
              for case in _burst),
          "Brand Burst burn must restart the boss clock instead of reusing the stale tick")
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
siege_battle = (ROOT / "scripts/combat/siege_battle.gd").read_text(encoding="utf-8")
ice_impact = siege_battle.split("func _ice_impact(", 1)[1].split("\nfunc ", 1)[0]
check("_ice_main(shot, main)" in ice_impact and "_ice_aoe(shot, main)" in ice_impact,
      "Ice impact must delegate both the main-target and the AOE arm")
ice_main_base = siege_battle.split("func _ice_main(", 1)[1].split("\nfunc ", 1)[0]
check("apply_slow(main.id, shot.slow_amount, shot.slow_duration)" in ice_main_base
      and "apply_atk_slow(main.id, shot.atk_slow_amount, shot.slow_duration)" in ice_main_base,
      "Base ice main target must keep the world-level mixin stores")
boss_ice_main = prototype_battle.split("func _ice_main(", 1)[1].split("\nfunc ", 1)[0]
check("main as BossState" in boss_ice_main
      and "super._ice_main(shot, main)" in boss_ice_main
      and "boss.apply_slow(shot.slow_amount, shot.slow_duration)" in boss_ice_main
      and 'boss.apply_debuff("atk_slow", shot.atk_slow_amount, shot.slow_duration)'
      in boss_ice_main,
      "Boss main target must take the ice slow through its own tenacity methods")
cannon_impact = siege_battle.split("func _cannon_impact(", 1)[1].split("\nfunc ", 1)[0]
check("_cannon_splash(shot, main)" in cannon_impact,
      "Cannon impact must delegate its splash arm so the match layer can widen it")
cannon_splash_base = siege_battle.split("func _cannon_splash(", 1)[1].split("\nfunc ", 1)[0]
check("for victim in units:" in cannon_splash_base
      and "_projectile_school(victim, \"physical\")" in cannon_splash_base
      and "victim.position.distance_to(main.position) > shot.splash_radius" in cannon_splash_base,
      "Base cannon splash must keep the source scan, inclusive radius and resolved school")
boss_cannon_splash = prototype_battle.split("func _cannon_splash(", 1)[1].split("\nfunc ", 1)[0]
check("super._cannon_splash(shot, main)" in boss_cannon_splash
      and "boss.position.distance_to(main.position) > shot.splash_radius" in boss_cannon_splash
      and "_deliver_hit(" in boss_cannon_splash
      and "-1, shot.team, boss, splash_damage" in boss_cannon_splash
      and 'boss.apply_debuff("burn", shot.burn_dps, shot.burn_duration, shot.team)'
      in boss_cannon_splash,
      "Match layer must splash the living boss with source-omitted attribution and burn")
projectile_delivery = siege_battle.split("func _update_projectiles(", 1)[1].split("\nfunc ", 1)[0]
check("_projectile_school(target, school)" in projectile_delivery
      and "_hero_blocks_projectile(target, school)" in projectile_delivery,
      "Structure impacts must deliver damage under the resolved projectile school")
projectile_school_base = siege_battle.split("func _projectile_school(", 1)[1].split("\nfunc ", 1)[0]
check("return school" in projectile_school_base,
      "Base projectile school must stay the declared school for units and heroes")
boss_projectile_school = prototype_battle.split("func _projectile_school(", 1)[1].split(
    "\nfunc ", 1)[0]
check("if target is BossState:" in boss_projectile_school
      and 'return "neutral"' in boss_projectile_school,
      "Boss targets must take structure shots without school mitigation, like the source")
ice_aoe_base = siege_battle.split("func _ice_aoe(", 1)[1].split("\nfunc ", 1)[0]
check("for victim in units:" in ice_aoe_base
      and "victim.position.distance_to(main.position) > shot.slow_aoe" in ice_aoe_base
      and "if shot.slow_aoe <= 0:" in ice_aoe_base,
      "Base ice AOE must keep the source candidate scan, gate and inclusive radius")
boss_ice_aoe = prototype_battle.split("func _ice_aoe(", 1)[1].split("\nfunc ", 1)[0]
check("super._ice_aoe(shot, main)" in boss_ice_aoe
      and "boss.position.distance_to(main.position) > shot.slow_aoe" in boss_ice_aoe
      and "boss.apply_slow(shot.slow_amount, shot.slow_duration)" in boss_ice_aoe
      and 'boss.apply_debuff("atk_slow", shot.atk_slow_amount, shot.slow_duration)'
      in boss_ice_aoe
      and "not boss.alive or boss.team == shot.team" in boss_ice_aoe,
      "Match layer must add the living boss to the ice AOE with the source tenacity dispatch")
fire_projectile_base = siege_battle.split("func fire_projectile(", 1)[1].split("\nfunc ", 1)[0]
check("_append_volley_targets(source, target, targets, count)" in fire_projectile_base
      and "if not is_mage:" in fire_projectile_base,
      "Structure fire_projectile must delegate secondary volley/chain target selection before archer refill")
volley_targets_base = siege_battle.split("func _append_volley_targets(", 1)[1].split("\nfunc ", 1)[0]
check("for candidate in units:" in volley_targets_base
      and "if targets.size() >= count:" in volley_targets_base
      and "source.position.distance_to(candidate.position) <= source.definition.attack_range_px"
      in volley_targets_base,
      "Base volley target scan must keep the source order, slot cap and inclusive range")
boss_volley_targets = prototype_battle.split("func _append_volley_targets(", 1)[1].split(
    "\nfunc ", 1)[0]
check("super._append_volley_targets(source, target, targets, count)" in boss_volley_targets
      and "if targets.size() >= count or boss == null or boss == target:" in boss_volley_targets
      and "if not boss.alive or boss.team == source.team:" in boss_volley_targets
      and "source.position.distance_to(boss.position) <= source.definition.attack_range_px"
      in boss_volley_targets
      and "targets.append(boss)" in boss_volley_targets,
      "Match layer must append the living in-range enemy boss after ordinary volley/chain candidates")
minion_battle = (ROOT / "scripts/combat/minion_battle.gd").read_text(encoding="utf-8")
boss_minion_target = prototype_battle.split("func _find_target(unit: UnitState)", 1)[1].split(
    "\nfunc _structure_target(", 1)[0]
check("super._find_target(unit)" in boss_minion_target
      and "unit.definition.attack_range_px + 30.0" in boss_minion_target
      and boss_minion_target.index("ordered.append(boss)")
      < boss_minion_target.index("for structure in structures:"),
      "Minions must index the living enemy boss inside the source grid radius, before structures")
check(minion_battle.count("_is_minion_candidate(") == 4
      and 'candidate.get("boss_type") == null' in minion_battle
      and "not (pair[0] is StructureState)" not in minion_battle,
      "Source Minion groups must exclude the boss from the lane/lowest-hp minion picks")
boss_phase_step = prototype_battle.split("func step_tick()", 1)[1].split("\nfunc ", 1)[0]
_phase_positions = [
    boss_phase_step.index("super.step_tick()"),
    boss_phase_step.index("_step_hero_act()"),
    boss_phase_step.index("_spawn_true_boss_if_ready()"),
    boss_phase_step.index("_step_active_boss()"),
    boss_phase_step.index("_process_boss_result()"),
    boss_phase_step.index("_step_hero_respawns()"),
]
check(_phase_positions == sorted(_phase_positions),
      "Match tick must update live heroes, spawn/check boss, then tick boss before respawns")
boss_hero_phase = prototype_battle.split("func _step_hero_act()", 1)[1].split("\nfunc ", 1)[0]
check("unit.is_hero and unit.alive" in boss_hero_phase
      and "_step_hero_respawn(" not in boss_hero_phase,
      "Only living heroes act in the source pre-boss entity phase")
boss_respawn_phase = prototype_battle.split("func _step_hero_respawns()", 1)[1].split(
    "\nfunc ", 1)[0]
check("unit.is_hero and not unit.alive" in boss_respawn_phase
      and "_step_hero_respawn(" in boss_respawn_phase,
      "Dead hero respawn timers stay in the source post-boss phase")
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
boss_ai_hit = boss_ai_text.split("static func _hit(", 1)[1].split(
    "\nstatic func _slow(", 1)[0]
check("world._deliver_hit(-1, boss.team, target, raw_damage, school, boss.position)" in boss_ai_hit
      and "world._deliver_hit(boss.id," not in boss_ai_hit,
      "Boss AI ability/skill hits must omit source attribution like source Boss._use_ability/_smart_ai_*")
battle_item_effects_text = (ROOT / "scripts/match/battle_item_effects.gd").read_text(encoding="utf-8")
battle_item_apply_stun = battle_item_effects_text.split("func apply_stun(", 1)[1].split(
    "\nfunc apply_silence(", 1)[0]
check('elif t != null and t.has_method("apply_stun"):' in battle_item_apply_stun
      and "t.apply_stun(duration)" in battle_item_apply_stun,
      "BattleItemEffects.apply_stun must delegate to BossState.apply_stun like source _apply_stun_to")
battle_item_apply_slow = battle_item_effects_text.split("func apply_slow(", 1)[1].split(
    "\nfunc apply_burn(", 1)[0]
check('if t.has_method("apply_slow"):' in battle_item_apply_slow
      and "t.apply_slow(amount, duration)" in battle_item_apply_slow,
      "BattleItemEffects.apply_slow must delegate to BossState.apply_slow like source target.apply_slow")
battle_item_apply_atk_slow = battle_item_effects_text.split("func apply_atk_slow(", 1)[1].split(
    "\nfunc apply_anti_heal(", 1)[0]
check('if t != null and t.has_method("apply_debuff"):' in battle_item_apply_atk_slow
      and 't.apply_debuff("atk_slow", amount, duration)' in battle_item_apply_atk_slow,
      "BattleItemEffects.apply_atk_slow must delegate to BossState.apply_debuff like source Frostbite")
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

from boss_polycephaly_source_oracle import source_fixture as polycephaly_fixture
_poly = polycephaly_fixture()
check(_poly == json.loads((ROOT / "tests/fixtures/boss_polycephaly_source.json").read_text()),
      "9a Polycephaly fixture matches source")
check(_poly["source"]["exact_distance_sort"], "9a Python sorts exact distances")
check(len(_poly["cases"]) == 864 and len({r["boss_type"] for r in _poly["cases"]}) == 216,
      "9a four cases per 216 boss types")
check('const BossPolycephalyChecks = preload("res://tests/boss_polycephaly_checks.gd")' in ai_tests
      and "BossPolycephalyChecks.new().run(_check)" in ai_tests, "9a replay registered")
for _row in _poly["cases"]:
    _roles = {
        "nearer_boss_takes_last_slot": ["unit_a", "boss"],
        "exact_tie_keeps_unit_slot": ["unit_a", "unit_b"],
        "boss_first_despite_insertion": ["boss", "unit_a"],
        "farther_boss_stays_out": ["unit_a", "unit_b"],
    }[_row["scenario"]]
    check(_row["expected"] == [[role, 35, "magic"] for role in _roles]
          and _row["expected_without_exact_sort"] == [["unit_a", 35, "magic"], ["unit_b" if _row["scenario"] != "boss_first_despite_insertion" else "boss", 35, "magic"]],
          "9a exact and epsilon-sort payload " + _row["boss_type"] + "/" + _row["scenario"])

from boss_miasma_source_oracle import source_fixture as miasma_fixture
_miasma = miasma_fixture()
_miasma_file = json.loads((ROOT / "tests/fixtures/boss_miasma_source.json").read_text())
check(_miasma == _miasma_file, "9b Miasma fixture matches Python source execution")
check(_miasma["source"]["ast_shape"] == {
    "global_target_key": True,
    "source_replaced": True,
    "damage_max": True,
    "timer_max": True,
    "tick_cd_min": True,
    "tick_uses_stored_source": True,
    "tick_reset_30": True,
}, "9b Python AST proves shared-target merge and stored-source tick")
check(len(_miasma["cases"]) == 864
      and len({row["boss_type"] for row in _miasma["cases"]}) == 216
      and _miasma["source"]["boss_types"] == 216,
      "9b four cases for each of 216 bosses")
_miasma_inventory = (ROOT / "scripts/match/hero_item_inventory.gd").read_text()
_miasma_prototype = (ROOT / "scripts/match/prototype_battle.gd").read_text()
_miasma_bus = (ROOT / "scripts/match/battle_item_effects.gd").read_text()
_miasma_effects = (ROOT / "scripts/match/item_effects.gd").read_text()
check("func _bind_miasma_registry(hero: HeroState) -> void" in _miasma_prototype
      and "source_hero.items.miasma = _miasma_registry" in _miasma_prototype
      and _miasma_prototype.count("_bind_miasma_registry(hero)") >= 2,
      "9b on-hit/tick hero inventories bind or merge into the match Miasma registry")
check('prev["source_id"] = hero_id' in _miasma_inventory
      and 'prev["source_team"] = hero_team' in _miasma_inventory
      and 'effects.deal_damage_from(' in _miasma_inventory,
      "9b native reapply transfers source and tick uses stored owner")
check("func deal_damage_from(" in _miasma_effects
      and "func deal_damage_from(" in _miasma_bus
      and "var landed: bool = world._deliver_hit(" in _miasma_bus
      and "source_id, source_team, tgt, amount, school, origin, damage_type" in _miasma_bus,
      "9b damage bridge delivers poison using the stored source hero")
check('const BossMiasmaChecks = preload("res://tests/boss_miasma_checks.gd")' in ai_tests
      and "BossMiasmaChecks.new().run(_check)" in ai_tests,
      "9b real-path boss Miasma replay registered")


def _miasma_events_match(actual, expected):
    if len(actual) != len(expected):
        return False
    for actual_row, expected_row in zip(actual, expected):
        if (int(float(actual_row[0])) != int(float(expected_row[0]))
                or str(actual_row[1]) != str(expected_row[1])
                or int(float(actual_row[2])) != int(float(expected_row[2]))):
            return False
    return True


_expected_frames = {
    "same_frame_reapply": [15, "hero_b"],
    "reapply_near_tick": [1, "hero_b"],
    "reapply_after_first_tick": [15, "hero_b"],
    "reapplying_hero_dies": [30, "hero_b"],
}
_old_frames = {
    "same_frame_reapply": [],
    "reapply_near_tick": [],
    "reapply_after_first_tick": [[15, "hero_a"]],
    "reapplying_hero_dies": [[30, "hero_a"]],
}
for _row in _miasma["cases"]:
    _data = _miasma["source"]["on_attack"]
    _damage = max(6, min(int(_data["cap_damage"]),
                         int(float(_row["boss_max_hp"]) * float(_data["max_hp_pct_per_tick"]))))
    _scenario = _row["scenario"]
    _tracker = _row["expected"]["tracker"]
    _pre = int(_row["pre_frames"])
    _old_trackers = _row["native_old"]["trackers"]
    _old_a = next(t for t in _old_trackers if t["owner"] == "hero_a")
    _old_b = next(t for t in _old_trackers if t["owner"] == "hero_b")
    _check_expected = [[*_expected_frames[_scenario], _damage]]
    _check_old = [[frame, owner, _damage] for frame, owner in _old_frames[_scenario]]
    check(_tracker["count"] == 1 and _tracker["owner"] == "hero_b"
          and int(_tracker["damage"]) == _damage
          and int(_tracker["timer"]) == int(_data["duration"])
          and int(_tracker["tick_cd"]) == (2 if _pre == 14 else int(_data["tick"])),
          "9b merged tracker values " + _row["boss_type"] + "/" + _scenario)
    check(_miasma_events_match(_row["expected"]["events"], _check_expected)
          and _miasma_events_match(_row["native_old"]["events"], _check_old)
          and not _miasma_events_match(_check_expected, _check_old),
          "9b expected-vs-old gameplay events " + _row["boss_type"] + "/" + _scenario)
    check(_row["native_old"]["tracker_count"] == 2
          and len(_old_trackers) == 2
          and int(_old_a["timer"]) == int(_data["duration"]) - _pre
          and int(_old_a["tick_cd"]) == int(_data["tick"]) - _pre
          and int(_old_b["timer"]) == int(_data["duration"])
          and int(_old_b["tick_cd"]) == int(_data["tick"]),
          "9b per-inventory counterfactual trackers " + _row["boss_type"] + "/" + _scenario)

from boss_miasma_blind_source_oracle import source_fixture as miasma_blind_fixture
_blind = miasma_blind_fixture()
_blind_file = json.loads(
    (ROOT / "tests/fixtures/boss_miasma_blind_source.json").read_text()
)
check(_blind == _blind_file, "9c Miasma blind-gate fixture matches Python source execution")
check(_blind["source"]["ast_shape"] == {
    "tick_passes_magic": True,
    "tick_passes_no_source": True,
    "gate_needs_normal": True,
    "gate_reads_blind": True,
    "gate_reads_true_strike": True,
}, "9c Python AST proves the Miasma tick is magic and carries no source")
check(len(_blind["cases"]) == 864
      and len({row["boss_type"] for row in _blind["cases"]}) == 216
      and _blind["source"]["boss_types"] == 216,
      "9c four cases for each of 216 bosses")
_blind_inventory = (ROOT / "scripts/match/hero_item_inventory.gd").read_text()
_blind_bus = (ROOT / "scripts/match/battle_item_effects.gd").read_text()
_blind_effects = (ROOT / "scripts/match/item_effects.gd").read_text()
_blind_boss = (ROOT / "scripts/match/boss_state.gd").read_text()
_blind_proto = (ROOT / "scripts/match/prototype_battle.gd").read_text()
check('effects.deal_damage_from(' in _blind_inventory
      and 'damage_type: String = "magic"' in _blind_effects
      and 'damage_type: String = "magic"' in _blind_bus
      and "var landed: bool = world._deliver_hit(" in _blind_bus
      and "source_id, source_team, tgt, amount, school, origin, damage_type" in _blind_bus,
      "9c Miasma tick carries its magic damage_type through the item bus")
check('if damage_type != "normal":' in _blind_boss
      and "blind_live(source, damage_type)" in _blind_boss
      and 'damage_type: String = "normal"' in _blind_proto,
      "9c boss blind gate stays limited to plain hits from a live attacker")
check('const BossMiasmaBlindChecks = preload("res://tests/boss_miasma_blind_checks.gd")' in ai_tests
      and "BossMiasmaBlindChecks.new().run(_check)" in ai_tests,
      "9c real-path Miasma blind-gate replay registered")


def _blind_events_match(actual, expected):
    if len(actual) != len(expected):
        return False
    for actual_row, expected_row in zip(actual, expected):
        if (int(float(actual_row[0])) != int(float(expected_row[0]))
                or int(float(actual_row[1])) != int(float(expected_row[1]))):
            return False
    return True


_expected_tick_frames = {
    "blind_owner_tick_blocked": [30],
    "blind_owner_second_tick": [30, 60],
    "blind_owner_true_strike_pierces": [30],
    "blind_owner_zero_amount": [30],
}
_native_old_tick_frames = {
    "blind_owner_tick_blocked": [],
    "blind_owner_second_tick": [30],
    "blind_owner_true_strike_pierces": [30],
    "blind_owner_zero_amount": [30],
}
for _row in _blind["cases"]:
    _blind_data = _blind["source"]["on_attack"]
    _tick_damage = max(6, min(int(_blind_data["cap_damage"]),
                              int(float(_row["boss_max_hp"]) * float(_blind_data["max_hp_pct_per_tick"]))))
    _scenario = _row["scenario"]
    _exp_frames = _expected_tick_frames[_scenario]
    _old_frames = _native_old_tick_frames[_scenario]
    check(int(_row["miasma_damage"]) == _tick_damage
          and _blind_events_match(_row["expected"]["events"],
                                  [[frame, _tick_damage] for frame in _exp_frames])
          and _blind_events_match(_row["native_old"]["events"],
                                  [[frame, _tick_damage] for frame in _old_frames])
          and int(_row["expected"]["damage_total"]) == _tick_damage * len(_exp_frames)
          and int(_row["native_old"]["damage_total"]) == _tick_damage * len(_old_frames)
          and (_row["expected"] != _row["native_old"]) == (len(_exp_frames) != len(_old_frames)),
          "9c Miasma blind-gate payload " + _row["boss_type"] + "/" + _scenario)

from boss_miasma_kill_credit_source_oracle import source_fixture as miasma_kill_credit_fixture

_miasma_kill = miasma_kill_credit_fixture()
_miasma_kill_file = json.loads(
    (ROOT / "tests/fixtures/boss_miasma_kill_credit_source.json").read_text(encoding="utf-8")
)
check(_miasma_kill == _miasma_kill_file,
      "9d Miasma boss kill-credit fixture matches source Python execution")
_miasma_kill_cases = _miasma_kill.get("cases", [])
_miasma_kill_types = {row["boss_type"] for row in _miasma_kill_cases}
_miasma_kill_scenarios = {
    "miasma_lethal_blue_owner",
    "miasma_lethal_red_owner",
    "miasma_nonlethal_then_hero_lethal",
    "miasma_nonlethal_only",
}
check(len(_miasma_kill_cases) == 864
      and _miasma_kill_types == set(boss_motion_source_types())
      and all(sum(row["boss_type"] == boss for row in _miasma_kill_cases) == 4
              for boss in _miasma_kill_types)
      and all({row["scenario"] for row in _miasma_kill_cases
               if row["boss_type"] == boss} == _miasma_kill_scenarios
              for boss in _miasma_kill_types)
      and all("expected" in row and "native_old" in row for row in _miasma_kill_cases),
      "9d four expected/counterfactual cases cover every boss type")
_miasma_kill_shape = _miasma_kill.get("source", {}).get("ast_shape", {})
check(_miasma_kill_shape == {
    "miasma_tick_calls_magic_without_source": True,
    "boss_stores_source_only_in_lethal_branch": True,
    "boss_kill_pass_reads_killed_by": True,
    "boss_kill_pass_requires_hero": True,
}, "9d Python AST proves the boss Miasma tick omits source attribution")
_miasma_kill_gap = {"miasma_lethal_blue_owner", "miasma_lethal_red_owner"}
check(all(
    (row["expected"]["owner_kills"] == 0
     and row["native_old"]["owner_kills"] == 1)
    if row["scenario"] in _miasma_kill_gap
    else row["expected"] == row["native_old"]
    for row in _miasma_kill_cases
), "9d only lethal Miasma diverges; direct-hero and nonlethal controls match")
_miasma_kill_bus = (ROOT / "scripts/match/battle_item_effects.gd").read_text(encoding="utf-8")
_miasma_kill_proto = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
check("if landed and tgt is BossState:" in _miasma_kill_bus
      and "(tgt as BossState).last_hit_is_miasma_tick = true" in _miasma_kill_bus
      and "var landed: bool = world._deliver_hit(" in _miasma_kill_bus
      and "if boss.last_hit_is_miasma_tick:" in _miasma_kill_proto
      and "boss.last_hit_is_miasma_tick = false" in _miasma_kill_proto,
      "9d event source is retained while Miasma hits are excluded from boss kill credit")
check('const BossMiasmaKillCreditChecks = preload("res://tests/boss_miasma_kill_credit_checks.gd")' in ai_tests
      and "BossMiasmaKillCreditChecks.new().run(_check)" in ai_tests,
      "9d production-path replay is registered")


# ── 9e: the cleave splash arm on the active boss uses the source call shape ──
from boss_item_cleave_damage_source_oracle import source_fixture as cleave_damage_fixture
_cleave_dmg = cleave_damage_fixture()
_cleave_dmg_file = json.loads(
    (ROOT / "tests/fixtures/boss_item_cleave_damage_source.json").read_text(encoding="utf-8")
)
check(_cleave_dmg == _cleave_dmg_file,
      "9e cleave damage fixture matches Python source execution")
_cleave_dmg_cases = _cleave_dmg.get("cases", [])
_cleave_dmg_types = {row["boss_type"] for row in _cleave_dmg_cases}
_cleave_dmg_scenarios = {
    "cleave_school_vs_boss_armor",
    "cleave_blind_owner_still_lands",
    "cleave_lethal_without_kill_credit",
    "cleave_outside_radius_control",
}
check(len(_cleave_dmg_cases) == 864
      and _cleave_dmg_types == set(boss_motion_source_types())
      and all(sum(row["boss_type"] == boss for row in _cleave_dmg_cases) == 4
              for boss in _cleave_dmg_types)
      and all({row["scenario"] for row in _cleave_dmg_cases
               if row["boss_type"] == boss} == _cleave_dmg_scenarios
              for boss in _cleave_dmg_types)
      and all("expected" in row and "native_old" in row for row in _cleave_dmg_cases),
      "9e four expected/counterfactual cleave cases cover every boss type")
check(_cleave_dmg.get("source", {}).get("ast_shape", {}) == {
    "cleave_take_damage_positional_args": 2,
    "cleave_take_damage_keywords": [],
    "boss_blind_block_requires_source": True,
    "boss_school_comes_from_resolver": True,
    "resolver_returns_none_without_school_or_source": True,
    "boss_lethal_branch_stores_source": True,
}, "9e Python AST proves the cleave splash omits both source and school")
check(all(
    (row["expected"] == row["native_old"])
    == (row["scenario"] == "cleave_outside_radius_control")
    for row in _cleave_dmg_cases
), "9e only the boss arm scenarios diverge; the out-of-radius control matches")
check(all(
    row["expected"]["minion_hits"] == row["native_old"]["minion_hits"] == [25]
    and row["expected"]["target_hits"] == row["native_old"]["target_hits"] == []
    for row in _cleave_dmg_cases
), "9e the regular-unit cleave arm keeps its payload in both columns")
check(all(
    row["expected"]["owner_kills"] == 0 and row["native_old"]["owner_kills"] == 1
    for row in _cleave_dmg_cases
    if row["scenario"] == "cleave_lethal_without_kill_credit"
), "9e a lethal cleave splash credits nobody in the source column")
_cleave_dmg_bus = (ROOT / "scripts/match/battle_item_effects.gd").read_text(encoding="utf-8")
check('world._deliver_hit(-1, src_team, boss, splash, "neutral", src_pos)' in _cleave_dmg_bus
      and 'world._deliver_hit(dealer_id, src_team, u, splash, "physical", src_pos)'
      in _cleave_dmg_bus,
      "9e the boss cleave arm is source-less and school-less while units stay physical")
check('const BossItemCleaveDamageChecks = preload("res://tests/boss_item_cleave_damage_checks.gd")'
      in ai_tests
      and "BossItemCleaveDamageChecks.new().run(_check)" in ai_tests,
      "9e production-path cleave replay is registered")



# ── 9f: the Abyss Breaker Bash arm on the active boss uses the source shape ──
from boss_item_bash_damage_source_oracle import source_fixture as bash_damage_fixture
_bash_dmg = bash_damage_fixture()
_bash_dmg_file = json.loads(
    (ROOT / "tests/fixtures/boss_item_bash_damage_source.json").read_text(encoding="utf-8")
)
check(_bash_dmg == _bash_dmg_file,
      "9f bash damage fixture matches Python source execution")
_bash_dmg_cases = _bash_dmg.get("cases", [])
_bash_dmg_types = {row["boss_type"] for row in _bash_dmg_cases}
_bash_dmg_scenarios = {
    "bash_school_vs_boss_armor",
    "bash_blind_owner_still_lands",
    "bash_lethal_without_kill_credit",
    "bash_internal_cooldown_control",
}
check(len(_bash_dmg_cases) == 864
      and _bash_dmg_types == set(boss_motion_source_types())
      and all(sum(row["boss_type"] == boss for row in _bash_dmg_cases) == 4
              for boss in _bash_dmg_types)
      and all({row["scenario"] for row in _bash_dmg_cases
               if row["boss_type"] == boss} == _bash_dmg_scenarios
              for boss in _bash_dmg_types)
      and all("expected" in row and "native_old" in row for row in _bash_dmg_cases),
      "9f four expected/counterfactual bash cases cover every boss type")
check(_bash_dmg.get("source", {}).get("ast_shape", {}) == {
    "bash_take_damage_positional_args": 2,
    "bash_take_damage_keywords": [],
    "bash_requires_internal_cooldown": True,
    "bash_sets_internal_cooldown": True,
    "boss_blind_block_requires_source": True,
    "boss_school_comes_from_resolver": True,
    "boss_lethal_branch_stores_source": True,
}, "9f Python AST proves the bash bonus omits both source and school")
check(all(
    (row["expected"] == row["native_old"])
    == (row["scenario"] == "bash_internal_cooldown_control")
    for row in _bash_dmg_cases
), "9f only the proccing bash scenarios diverge; the cooldown control matches")
check(all(
    row["expected"]["owner_kills"] == 0 and row["native_old"]["owner_kills"] == 1
    for row in _bash_dmg_cases
    if row["scenario"] == "bash_lethal_without_kill_credit"
), "9f a lethal bash credits nobody in the source column")
_bash_dmg_bus = (ROOT / "scripts/match/battle_item_effects.gd").read_text(encoding="utf-8")
_bash_dmg_base = (ROOT / "scripts/match/item_effects.gd").read_text(encoding="utf-8")
_bash_dmg_inv = (ROOT / "scripts/match/hero_item_inventory.gd").read_text(encoding="utf-8")
check("func deal_damage_sourceless(" in _bash_dmg_base
      and "func deal_damage_sourceless(" in _bash_dmg_bus
      and 'world._deliver_hit(-1, source_team, tgt, amount, "neutral", dealer_pos)'
      in _bash_dmg_bus
      and "effects.deal_damage_sourceless(" in _bash_dmg_inv,
      "9f the bash arm routes through the source-less bus entry")
check('const BossItemBashDamageChecks = preload("res://tests/boss_item_bash_damage_checks.gd")'
      in ai_tests
      and "BossItemBashDamageChecks.new().run(_check)" in ai_tests,
      "9f production-path bash replay is registered")



# ── 9g: the on-hit magic arms on the active boss use the source call shape ──
from boss_item_magic_damage_source_oracle import source_fixture as magic_damage_fixture
_magic_dmg = magic_damage_fixture()
_magic_dmg_file = json.loads(
    (ROOT / "tests/fixtures/boss_item_magic_damage_source.json").read_text(encoding="utf-8")
)
check(_magic_dmg == _magic_dmg_file,
      "9g magic damage fixture matches Python source execution")
_magic_dmg_cases = _magic_dmg.get("cases", [])
_magic_dmg_types = {row["boss_type"] for row in _magic_dmg_cases}
_magic_dmg_arms = {"chain", "pierce_bash", "polycephaly", "empower"}
_magic_dmg_scenarios = {
    arm: {
        arm + "_magic_arm_vs_boss_resist",
        arm + "_blind_owner_still_lands",
        arm + "_lethal_without_kill_credit",
        _magic_dmg.get("source", {}).get("arms", {}).get(arm, {}).get("control_scenario"),
    }
    for arm in _magic_dmg_arms
}
check(len(_magic_dmg_cases) == 3456
      and _magic_dmg_types == set(boss_motion_source_types())
      and all(sum(row["boss_type"] == boss for row in _magic_dmg_cases) == 16
              for boss in _magic_dmg_types)
      and {row["arm"] for row in _magic_dmg_cases} == _magic_dmg_arms
      and all({row["scenario"] for row in _magic_dmg_cases if row["arm"] == arm}
              == _magic_dmg_scenarios[arm]
              for arm in _magic_dmg_arms)
      and all("expected" in row and "native_old" in row for row in _magic_dmg_cases),
      "9g sixteen expected/counterfactual magic arm cases cover every boss type")
check(_magic_dmg.get("source", {}).get("ast_shape", {}) == {
    "chain_take_damage_positional_args": 3,
    "chain_take_damage_keywords": [],
    "chain_take_damage_third_arg": "'magic'",
    "pierce_bash_take_damage_positional_args": 3,
    "pierce_bash_take_damage_keywords": [],
    "pierce_bash_take_damage_third_arg": "'magic'",
    "polycephaly_take_damage_positional_args": 3,
    "polycephaly_take_damage_keywords": [],
    "polycephaly_take_damage_third_arg": "'magic'",
    "empower_take_damage_positional_args": 3,
    "empower_take_damage_keywords": [],
    "empower_take_damage_third_arg": "'magic'",
    "boss_blind_block_requires_source": True,
    "boss_school_comes_from_resolver": True,
    "resolver_returns_none_without_school_or_source": True,
    "boss_lethal_branch_stores_source": True,
    "arms_are_reached_from_basic_attack": True,
    "chain_uses_the_chain_getter": True,
    "pierce_uses_the_cudgel_bash_block": True,
}, "9g Python AST proves all four magic arms omit source and school")
check(_magic_dmg.get("source", {}).get("owner_true_strike") == {
    "chain": False,
    "pierce_bash": True,
    "polycephaly": False,
    "empower": False,
}, "9g only Sundering Cudgel carries true strike against the blind gate")
_magic_controls = {name: arm["control_scenario"]
                   for name, arm in _magic_dmg.get("source", {}).get("arms", {}).items()}
check(all(
    (row["expected"] == row["native_old"]) == (row["scenario"] == _magic_controls[row["arm"]])
    for row in _magic_dmg_cases
), "9g only the proccing magic arm scenarios diverge; the gate controls match")
check(all(
    row["expected"]["regular_hits"] == row["native_old"]["regular_hits"]
    for row in _magic_dmg_cases
), "9g the regular-unit arm of every magic effect keeps its payload in both columns")
check(all(
    row["expected"]["owner_kills"] == 0 and row["expected"]["boss_counter"] == 0
    and row["native_old"]["owner_kills"] == 1 and row["native_old"]["boss_counter"] == 1
    for row in _magic_dmg_cases
    if row["scenario"].endswith("lethal_without_kill_credit")
), "9g a lethal magic proc credits nobody in the source column")
check(all(
    row["expected"]["boss_hp_loss"] > 0 and row["native_old"]["boss_hp_loss"] == 0
    for row in _magic_dmg_cases
    if row["scenario"].endswith("blind_owner_still_lands") and row["arm"] != "pierce_bash"
), "9g a blinded owner still lands the source-less magic proc")
check(all(
    row["expected"]["boss_hp_loss"] > 0 and row["native_old"]["boss_hp_loss"] > 0
    for row in _magic_dmg_cases
    if row["scenario"].endswith("blind_owner_still_lands") and row["arm"] == "pierce_bash"
), "9g Sundering Cudgel true strike pierces blind in both columns")
_magic_dmg_base = (ROOT / "scripts/match/item_effects.gd").read_text(encoding="utf-8")
_magic_dmg_bus = (ROOT / "scripts/match/battle_item_effects.gd").read_text(encoding="utf-8")
_magic_dmg_inv = (ROOT / "scripts/match/hero_item_inventory.gd").read_text(encoding="utf-8")
check("func deal_damage_magic_sourceless(" in _magic_dmg_base
      and "func deal_damage_magic_sourceless(" in _magic_dmg_bus
      and 'world._deliver_hit(-1, source_team, tgt, amount, "neutral", dealer_pos, "magic")'
      in _magic_dmg_bus
      # 9h extends the same bus entry to six auto arms, so the total grows from
      # four to ten; the on-hit four are still present.
      and _magic_dmg_inv.count("effects.deal_damage_magic_sourceless(") >= 4,
      "9g the four on-hit magic arms route through the typed source-less bus entry")
check('const BossItemMagicDamageChecks = preload("res://tests/boss_item_magic_damage_checks.gd")'
      in ai_tests
      and "BossItemMagicDamageChecks.new().run(_check)" in ai_tests,
      "9g production-path magic arm replay is registered")



# ── 9h: the auto/active magic arms on the active boss use the source shape ──
from boss_item_auto_magic_damage_source_oracle import source_fixture as auto_magic_fixture
_auto_dmg = auto_magic_fixture()
_auto_dmg_file = json.loads(
    (ROOT / "tests/fixtures/boss_item_auto_magic_damage_source.json").read_text(encoding="utf-8")
)
check(_auto_dmg == _auto_dmg_file,
      "9h auto magic fixture matches Python source execution")
_auto_dmg_cases = _auto_dmg.get("cases", [])
_auto_dmg_types = {row["boss_type"] for row in _auto_dmg_cases}
_auto_dmg_arms = {"fenrir", "thunder", "everfrost", "searbrand", "astral", "fulgur"}
_auto_dmg_scenarios = {
    arm: {
        arm + "_magic_arm_vs_boss_resist",
        arm + "_blind_owner_still_lands",
        arm + "_lethal_without_kill_credit",
        _auto_dmg.get("source", {}).get("arms", {}).get(arm, {}).get("control_scenario"),
    }
    for arm in _auto_dmg_arms
}
check(len(_auto_dmg_cases) == 5184
      and _auto_dmg_types == set(boss_motion_source_types())
      and all(sum(row["boss_type"] == boss for row in _auto_dmg_cases) == 24
              for boss in _auto_dmg_types)
      and {row["arm"] for row in _auto_dmg_cases} == _auto_dmg_arms
      and all({row["scenario"] for row in _auto_dmg_cases if row["arm"] == arm}
              == _auto_dmg_scenarios[arm]
              for arm in _auto_dmg_arms)
      and all("expected" in row and "native_old" in row for row in _auto_dmg_cases),
      "9h twenty-four expected/counterfactual auto cases cover every boss type")
_auto_shape = _auto_dmg.get("source", {}).get("ast_shape", {})
_auto_expected_shape = {
    "boss_blind_block_requires_source": True,
    "boss_school_comes_from_resolver": True,
    "resolver_returns_none_without_school_or_source": True,
    "boss_lethal_branch_stores_source": True,
    "arms_are_reached_from_hero_update": True,
    "update_wraps_magic_arms_in_try_except": True,
}
for _arm in sorted(_auto_dmg_arms):
    _auto_expected_shape[_arm + "_take_damage_positional_args"] = 3
    _auto_expected_shape[_arm + "_take_damage_keywords"] = []
    _auto_expected_shape[_arm + "_take_damage_third_arg"] = "'magic'"
    _auto_expected_shape[_arm + "_take_damage_fallback_positional_args"] = 2
    _auto_expected_shape[_arm + "_take_damage_fallback_keywords"] = []
check(_auto_shape == _auto_expected_shape,
      "9h Python AST proves all six auto arms omit source and school")
_auto_controls = {name: arm["control_scenario"]
                  for name, arm in _auto_dmg.get("source", {}).get("arms", {}).items()}
check(all(
    (row["expected"] == row["native_old"]) == (row["scenario"] == _auto_controls[row["arm"]])
    for row in _auto_dmg_cases
), "9h only the proccing auto scenarios diverge; the gate controls match")
check(all(
    row["expected"]["regular_hits"] == row["native_old"]["regular_hits"]
    for row in _auto_dmg_cases
), "9h the regular-unit arm of every auto effect keeps its payload in both columns")
check(all(
    row["expected"]["owner_kills"] == 0 and row["expected"]["boss_counter"] == 0
    and row["native_old"]["owner_kills"] == 1 and row["native_old"]["boss_counter"] == 1
    for row in _auto_dmg_cases
    if row["scenario"].endswith("lethal_without_kill_credit")
), "9h a lethal auto proc credits nobody in the source column")
check(all(
    row["expected"]["boss_hp_loss"] > 0 and row["native_old"]["boss_hp_loss"] == 0
    for row in _auto_dmg_cases
    if row["scenario"].endswith("blind_owner_still_lands")
), "9h a blinded owner still lands the source-less auto proc")
_auto_dmg_inv = (ROOT / "scripts/match/hero_item_inventory.gd").read_text(encoding="utf-8")
check(_auto_dmg_inv.count("effects.deal_damage_magic_sourceless(") == 10
      and _auto_dmg_inv.count("effects.deal_damage(source_id, hero_team, dmg, \"magic\")") == 1,
      "9h the six auto magic arms route through the typed source-less bus entry")
check('const BossItemAutoMagicDamageChecks = preload("res://tests/boss_item_auto_magic_damage_checks.gd")'
      in ai_tests
      and "BossItemAutoMagicDamageChecks.new().run(_check)" in ai_tests,
      "9h production-path auto magic replay is registered")


# ── 9i: the Thornmail reflect on the attacking boss uses the source shape ──
from boss_item_reflect_carapace_source_oracle import source_fixture as reflect_fixture
_reflect = reflect_fixture()
_reflect_file = json.loads(
    (ROOT / "tests/fixtures/boss_item_reflect_carapace_source.json").read_text(encoding="utf-8")
)
check(_reflect == _reflect_file,
      "9i reflect carapace fixture matches Python source execution")
_reflect_cases = _reflect.get("cases", [])
_reflect_types = {row["boss_type"] for row in _reflect_cases}
_reflect_scenarios = {
    "reflect_vs_boss_resist",
    "reflect_to_minion_unchanged",
    "reflect_thorn_inactive",
    "reflect_lethal_no_credit",
}
check(len(_reflect_cases) == 864
      and _reflect_types == set(boss_motion_source_types())
      and all(sum(row["boss_type"] == boss for row in _reflect_cases) == 4
              for boss in _reflect_types)
      and {row["arm"] for row in _reflect_cases} == {"reflect"}
      and {row["scenario"] for row in _reflect_cases} == _reflect_scenarios
      and all("expected" in row and "native_old" in row for row in _reflect_cases),
      "9i four expected/counterfactual reflect cases cover every boss type")
_reflect_shape = _reflect.get("source", {}).get("ast_shape", {})
_reflect_expected_shape = {
    "reflect_take_damage_positional_args": 3,
    "reflect_take_damage_keywords": [],
    "reflect_take_damage_third_arg": "'magic'",
    "reflect_take_damage_fallback_positional_args": 2,
    "reflect_take_damage_fallback_keywords": [],
    "reflect_pct_needs_thorn_timer": True,
    "reflect_pct_needs_razor": True,
    "reflect_guard_requires_alive_attacker": True,
    "reflect_guard_requires_enemy_team": True,
    "notify_is_reached_from_hero_take_damage": True,
    "notify_wraps_reflect_in_try_except": True,
    "boss_blind_block_requires_source": True,
    "boss_school_comes_from_resolver": True,
    "resolver_returns_none_without_school_or_source": True,
    "boss_lethal_branch_stores_source": True,
}
check(_reflect_shape == _reflect_expected_shape,
      "9i Python AST proves the reflect arm omits source and school")
_reflect_controls = set(
    _reflect.get("source", {}).get("arm", {}).get("control_scenarios", []))
check(all(
    (row["expected"] == row["native_old"]) == (row["scenario"] in _reflect_controls)
    for row in _reflect_cases
), "9i only the proccing reflect scenarios diverge; the controls match")
check(all(
    row["expected"]["regular_hits"] == row["native_old"]["regular_hits"]
    and row["expected"]["reflect_sent"] == row["native_old"]["reflect_sent"]
    for row in _reflect_cases
), "9i the minion payload and the reflect math keep their values in both columns")
check(all(
    row["expected"]["owner_kills"] == 0 and row["expected"]["boss_counter"] == 0
    and row["native_old"]["owner_kills"] == 0 and row["native_old"]["boss_counter"] == 0
    for row in _reflect_cases
    if row["scenario"] == "reflect_lethal_no_credit"
), "9i a lethal reflect credits nobody in either column")
check(all(
    row["expected"]["boss_hp_loss"] >= row["native_old"]["boss_hp_loss"]
    for row in _reflect_cases
    if row["scenario"] == "reflect_vs_boss_resist"
) and any(
    row["expected"]["boss_hp_loss"] != row["native_old"]["boss_hp_loss"]
    for row in _reflect_cases
    if row["scenario"] == "reflect_vs_boss_resist"
), "9i boss magic resist no longer cuts the reflected payload")
_reflect_bus = (ROOT / "scripts/match/reflect_item_effects.gd").read_text(encoding="utf-8")
check("attacker is BossState" in _reflect_bus
      and 'world._deliver_hit(-1, src_team, attacker, amount, "neutral", attacker.position, "magic")'
      in _reflect_bus
      and _auto_dmg_inv.count("effects.deal_damage(source_id, hero_team, dmg, \"magic\")") == 1,
      "9i the reflect bus sends the boss the source-less neutral magic hit")
check('const BossItemReflectCarapaceChecks = preload("res://tests/boss_item_reflect_carapace_checks.gd")'
      in ai_tests
      and "BossItemReflectCarapaceChecks.new().run(_check)" in ai_tests,
      "9i production-path reflect replay is registered")


for error in errors:
    print("FAIL:", error, file=sys.stderr)
print(f"{'FAIL' if errors else 'PASS'}: {checks} static checks; runtime testing still required.")
sys.exit(bool(errors))
