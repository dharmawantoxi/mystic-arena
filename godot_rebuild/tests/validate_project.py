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
    'config/cloud_save_enabled=true',
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

from hero_veil_immunity_source_oracle import source_fixture as hero_veil_fixture
check('const HeroVeilImmunityChecks = preload("res://tests/hero_veil_immunity_checks.gd")'
      in ai_tests, "Tempest Veil suite must be preloaded")
check("HeroVeilImmunityChecks.new().run(_check)" in ai_tests,
      "Tempest Veil suite must run")

from hero_block_source_oracle import source_fixture as hero_block_fixture
check('const HeroBlockChecks = preload("res://tests/hero_block_checks.gd")' in ai_tests,
      "Hero block suite must be preloaded")
check("HeroBlockChecks.new().run(_check)" in ai_tests, "Hero block suite must run")

from hero_armor_model_source_oracle import source_fixture as hero_armor_fixture
check('const HeroArmorModelChecks = preload("res://tests/hero_armor_model_checks.gd")' in ai_tests,
      "Hero armour model suite must be preloaded")
check("HeroArmorModelChecks.new().run(_check)" in ai_tests,
      "Hero armour model suite must run")

from hero_skill_sourceless_source_oracle import source_fixture as sourceless_fixture
check('const HeroSkillSourcelessChecks = preload("res://tests/hero_skill_sourceless_checks.gd")'
      in ai_tests, "Sourceless skill suite must be preloaded")
check("HeroSkillSourcelessChecks.new().run(_check)" in ai_tests,
      "Sourceless skill suite must run")

from minion_damage_ladder_source_oracle import source_fixture as minion_ladder_fixture
check('const MinionDamageLadderChecks = preload("res://tests/minion_damage_ladder_checks.gd")' in ai_tests,
      "Minion damage ladder suite must be preloaded")
check("MinionDamageLadderChecks.new().run(_check)" in ai_tests,
      "Minion damage ladder suite must run")

from item_structure_arm_source_oracle import source_fixture as structure_arm_fixture
from item_unit_arm_source_oracle import source_fixture as unit_arm_fixture
from item_cleave_splash_source_oracle import source_fixture as cleave_splash_fixture
from item_magic_arm_unit_source_oracle import source_fixture as magic_arm_unit_fixture
from item_reflect_unit_source_oracle import source_fixture as reflect_unit_fixture
from hero_bristleback_reflect_source_oracle import source_fixture as bristleback_reflect_fixture
from sylara_skill_arm_source_oracle import source_fixture as sylara_skill_arm_fixture
from grimjaw_skill_arm_source_oracle import source_fixture as grimjaw_skill_arm_fixture
from tower_bullet_school_source_oracle import source_fixture as tower_bullet_school_fixture
from minion_melee_school_source_oracle import source_fixture as minion_melee_school_fixture
from skill_hit_attribution_source_oracle import source_fixture as skill_hit_attribution_fixture
from burn_tick_delivery_source_oracle import source_fixture as burn_tick_delivery_fixture
from burn_boss_delivery_source_oracle import source_fixture as burn_boss_delivery_fixture
from boss_sourceless_delivery_source_oracle import source_fixture as boss_sourceless_delivery_fixture
from boss_debuff_tenacity_source_oracle import source_fixture as boss_debuff_tenacity_fixture
from item_slow_resist_source_oracle import source_fixture as item_slow_resist_fixture
from item_silence_store_source_oracle import source_fixture as item_silence_store_fixture
from boss_ai_slow_source_oracle import source_fixture as boss_ai_slow_fixture
from balance_baseline_source_oracle import balance_baseline as balance_baseline_fixture
from sprite_lighting_source_oracle import lighting_fixture as sprite_lighting_fixture
from combat_audio_source_oracle import source_fixture as combat_audio_fixture
from side_panel_source_oracle import source_fixture as side_panel_fixture
from splash_screen_source_oracle import source_fixture as splash_screen_fixture
from topup_source_oracle import source_fixture as topup_fixture
from level_intro_draw_source_oracle import source_fixture as level_intro_draw_fixture
from boss_attack_lock_source_oracle import source_fixture as boss_attack_lock_fixture
from boss_buff_expiry_source_oracle import source_fixture as boss_buff_expiry_fixture
from boss_buff_scaling_source_oracle import source_fixture as boss_buff_scaling_fixture
from boss_shake_sites_source_oracle import source_fixture as boss_shake_sites_fixture
from debuff_payload_reach_source_oracle import source_fixture as debuff_payload_reach_fixture
from hero_marker_source_oracle import source_fixture as hero_marker_fixture
from miasma_tick_delivery_source_oracle import source_fixture as miasma_tick_delivery_fixture
check('const ItemStructureArmChecks = preload("res://tests/item_structure_arm_checks.gd")' in ai_tests,
      "Item structure arm suite must be preloaded")
check("ItemStructureArmChecks.new().run(_check)" in ai_tests,
      "Item structure arm suite must run")
check((ROOT / "tests/fixtures/item_structure_arm_source.json").is_file(),
      "Item structure arm fixture must exist")
if (ROOT / "tests/fixtures/item_structure_arm_source.json").is_file():
    check(structure_arm_fixture() == json.loads(
        (ROOT / "tests/fixtures/item_structure_arm_source.json").read_text(encoding="utf-8")),
          "Item structure arm fixture must not drift from the oracle")
check('const ItemUnitArmChecks = preload("res://tests/item_unit_arm_checks.gd")' in ai_tests,
      "Item unit arm suite must be preloaded")
check("ItemUnitArmChecks.new().run(_check)" in ai_tests,
      "Item unit arm suite must run")
check((ROOT / "tests/fixtures/item_unit_arm_source.json").is_file(),
      "Item unit arm fixture must exist")
if (ROOT / "tests/fixtures/item_unit_arm_source.json").is_file():
    check(unit_arm_fixture() == json.loads(
        (ROOT / "tests/fixtures/item_unit_arm_source.json").read_text(encoding="utf-8")),
          "Item unit arm fixture must not drift from the oracle")
check('const ItemCleaveSplashChecks = preload("res://tests/item_cleave_splash_checks.gd")' in ai_tests,
      "Item cleave splash suite must be preloaded")
check("ItemCleaveSplashChecks.new().run(_check)" in ai_tests,
      "Item cleave splash suite must run")
check((ROOT / "tests/fixtures/item_cleave_splash_source.json").is_file(),
      "Item cleave splash fixture must exist")
if (ROOT / "tests/fixtures/item_cleave_splash_source.json").is_file():
    check(cleave_splash_fixture() == json.loads(
        (ROOT / "tests/fixtures/item_cleave_splash_source.json").read_text(encoding="utf-8")),
          "Item cleave splash fixture must not drift from the oracle")
check('const ItemMagicArmUnitChecks = preload("res://tests/item_magic_arm_unit_checks.gd")' in ai_tests,
      "Item magic arm unit suite must be preloaded")
check("ItemMagicArmUnitChecks.new().run(_check)" in ai_tests,
      "Item magic arm unit suite must run")
check((ROOT / "tests/fixtures/item_magic_arm_unit_source.json").is_file(),
      "Item magic arm unit fixture must exist")
if (ROOT / "tests/fixtures/item_magic_arm_unit_source.json").is_file():
    check(magic_arm_unit_fixture() == json.loads(
        (ROOT / "tests/fixtures/item_magic_arm_unit_source.json").read_text(encoding="utf-8")),
          "Item magic arm unit fixture must not drift from the oracle")
check('const ItemReflectUnitChecks = preload("res://tests/item_reflect_unit_checks.gd")' in ai_tests,
      "Item reflect unit suite must be preloaded")
check("ItemReflectUnitChecks.new().run(_check)" in ai_tests,
      "Item reflect unit suite must run")
check((ROOT / "tests/fixtures/item_reflect_unit_source.json").is_file(),
      "Item reflect unit fixture must exist")
if (ROOT / "tests/fixtures/item_reflect_unit_source.json").is_file():
    check(reflect_unit_fixture() == json.loads(
        (ROOT / "tests/fixtures/item_reflect_unit_source.json").read_text(encoding="utf-8")),
          "Item reflect unit fixture must not drift from the oracle")
check('const HeroBristlebackReflectChecks = preload("res://tests/hero_bristleback_reflect_checks.gd")' in ai_tests,
      "Hero bristleback reflect suite must be preloaded")
check("HeroBristlebackReflectChecks.new().run(_check)" in ai_tests,
      "Hero bristleback reflect suite must run")
check((ROOT / "tests/fixtures/hero_bristleback_reflect_source.json").is_file(),
      "Hero bristleback reflect fixture must exist")
if (ROOT / "tests/fixtures/hero_bristleback_reflect_source.json").is_file():
    check(bristleback_reflect_fixture() == json.loads(
        (ROOT / "tests/fixtures/hero_bristleback_reflect_source.json").read_text(encoding="utf-8")),
          "Hero bristleback reflect fixture must not drift from the oracle")
check('const SylaraSkillArmChecks = preload("res://tests/sylara_skill_arm_checks.gd")' in ai_tests,
      "Sylara skill arm suite must be preloaded")
check("SylaraSkillArmChecks.new().run(_check)" in ai_tests,
      "Sylara skill arm suite must run")
check((ROOT / "tests/fixtures/sylara_skill_arm_source.json").is_file(),
      "Sylara skill arm fixture must exist")
if (ROOT / "tests/fixtures/sylara_skill_arm_source.json").is_file():
    check(sylara_skill_arm_fixture() == json.loads(
        (ROOT / "tests/fixtures/sylara_skill_arm_source.json").read_text(encoding="utf-8")),
          "Sylara skill arm fixture must not drift from the oracle")
check('const GrimjawSkillArmChecks = preload("res://tests/grimjaw_skill_arm_checks.gd")' in ai_tests,
      "Grimjaw skill arm suite must be preloaded")
check("GrimjawSkillArmChecks.new().run(_check)" in ai_tests,
      "Grimjaw skill arm suite must run")
check((ROOT / "tests/fixtures/grimjaw_skill_arm_source.json").is_file(),
      "Grimjaw skill arm fixture must exist")
if (ROOT / "tests/fixtures/grimjaw_skill_arm_source.json").is_file():
    check(grimjaw_skill_arm_fixture() == json.loads(
        (ROOT / "tests/fixtures/grimjaw_skill_arm_source.json").read_text(encoding="utf-8")),
          "Grimjaw skill arm fixture must not drift from the oracle")
check('const TowerBulletSchoolChecks = preload("res://tests/tower_bullet_school_checks.gd")' in ai_tests,
      "Tower bullet school suite must be preloaded")
check("TowerBulletSchoolChecks.new().run(_check)" in ai_tests,
      "Tower bullet school suite must run")
check((ROOT / "tests/fixtures/tower_bullet_school_source.json").is_file(),
      "Tower bullet school fixture must exist")
if (ROOT / "tests/fixtures/tower_bullet_school_source.json").is_file():
    check(tower_bullet_school_fixture() == json.loads(
        (ROOT / "tests/fixtures/tower_bullet_school_source.json").read_text(encoding="utf-8")),
          "Tower bullet school fixture must not drift from the oracle")
check('const MinionMeleeSchoolChecks = preload("res://tests/minion_melee_school_checks.gd")' in ai_tests,
      "Minion melee school suite must be preloaded")
check("MinionMeleeSchoolChecks.new().run(_check)" in ai_tests,
      "Minion melee school suite must run")
check((ROOT / "tests/fixtures/minion_melee_school_source.json").is_file(),
      "Minion melee school fixture must exist")
if (ROOT / "tests/fixtures/minion_melee_school_source.json").is_file():
    check(minion_melee_school_fixture() == json.loads(
        (ROOT / "tests/fixtures/minion_melee_school_source.json").read_text(encoding="utf-8")),
          "Minion melee school fixture must not drift from the oracle")
check('const SkillHitAttributionChecks = preload("res://tests/skill_hit_attribution_checks.gd")' in ai_tests,
      "Skill hit attribution suite must be preloaded")
check("SkillHitAttributionChecks.new().run(_check)" in ai_tests,
      "Skill hit attribution suite must run")
check('const BossSourcelessDeliveryChecks = preload("res://tests/boss_sourceless_delivery_checks.gd")' in ai_tests,
      "Boss sourceless delivery suite must be preloaded")
check("BossSourcelessDeliveryChecks.new().run(_check)" in ai_tests,
      "Boss sourceless delivery suite must run")
check('const BossDebuffTenacityChecks = preload("res://tests/boss_debuff_tenacity_checks.gd")' in ai_tests,
      "Boss debuff tenacity suite must be preloaded")
check("BossDebuffTenacityChecks.new().run(_check)" in ai_tests,
      "Boss debuff tenacity suite must run")
check((ROOT / "tests/fixtures/boss_debuff_tenacity_source.json").is_file(),
      "Boss debuff tenacity fixture must exist")
if (ROOT / "tests/fixtures/boss_debuff_tenacity_source.json").is_file():
    check(boss_debuff_tenacity_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_debuff_tenacity_source.json").read_text(encoding="utf-8")),
          "Boss debuff tenacity fixture must not drift from the oracle")
check('const ItemSlowResistChecks = preload("res://tests/item_slow_resist_checks.gd")' in ai_tests,
      "Item slow resist suite must be preloaded")
check("ItemSlowResistChecks.new().run(_check)" in ai_tests,
      "Item slow resist suite must run")
check((ROOT / "tests/fixtures/item_slow_resist_source.json").is_file(),
      "Item slow resist fixture must exist")
if (ROOT / "tests/fixtures/item_slow_resist_source.json").is_file():
    check(item_slow_resist_fixture() == json.loads(
        (ROOT / "tests/fixtures/item_slow_resist_source.json").read_text(encoding="utf-8")),
          "Item slow resist fixture must not drift from the oracle")
check('const ItemSilenceStoreChecks = preload("res://tests/item_silence_store_checks.gd")' in ai_tests,
      "Item silence store suite must be preloaded")
check("ItemSilenceStoreChecks.new().run(_check)" in ai_tests,
      "Item silence store suite must run")
check((ROOT / "tests/fixtures/item_silence_store_source.json").is_file(),
      "Item silence store fixture must exist")
if (ROOT / "tests/fixtures/item_silence_store_source.json").is_file():
    check(item_silence_store_fixture() == json.loads(
        (ROOT / "tests/fixtures/item_silence_store_source.json").read_text(encoding="utf-8")),
          "Item silence store fixture must not drift from the oracle")
check('const BossAiSlowChecks = preload("res://tests/boss_ai_slow_checks.gd")' in ai_tests,
      "Boss AI slow suite must be preloaded")
check("BossAiSlowChecks.new().run(_check)" in ai_tests,
      "Boss AI slow suite must run")
check((ROOT / "tests/fixtures/boss_ai_slow_source.json").is_file(),
      "Boss AI slow fixture must exist")
if (ROOT / "tests/fixtures/boss_ai_slow_source.json").is_file():
    check(boss_ai_slow_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_ai_slow_source.json").read_text(encoding="utf-8")),
          "Boss AI slow fixture must not drift from the oracle")
check('const BossAttackLockChecks = preload("res://tests/boss_attack_lock_checks.gd")' in ai_tests,
      "Boss attack lock suite must be preloaded")
check("BossAttackLockChecks.new().run(_check)" in ai_tests,
      "Boss attack lock suite must run")
check((ROOT / "tests/fixtures/boss_attack_lock_source.json").is_file(),
      "Boss attack lock fixture must exist")
if (ROOT / "tests/fixtures/boss_attack_lock_source.json").is_file():
    check(boss_attack_lock_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_attack_lock_source.json").read_text(encoding="utf-8")),
          "Boss attack lock fixture must not drift from the oracle")
check('const BossBuffExpiryChecks = preload("res://tests/boss_buff_expiry_checks.gd")' in ai_tests,
      "Boss buff expiry suite must be preloaded")
check("BossBuffExpiryChecks.new().run(_check)" in ai_tests,
      "Boss buff expiry suite must run")
check((ROOT / "tests/fixtures/boss_buff_expiry_source.json").is_file(),
      "Boss buff expiry fixture must exist")
if (ROOT / "tests/fixtures/boss_buff_expiry_source.json").is_file():
    check(boss_buff_expiry_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_buff_expiry_source.json").read_text(encoding="utf-8")),
          "Boss buff expiry fixture must not drift from the oracle")
check('const BossBuffScalingChecks = preload("res://tests/boss_buff_scaling_checks.gd")' in ai_tests,
      "Boss buff scaling suite must be preloaded")
check("BossBuffScalingChecks.new().run(_check)" in ai_tests,
      "Boss buff scaling suite must run")
check((ROOT / "tests/fixtures/boss_buff_scaling_source.json").is_file(),
      "Boss buff scaling fixture must exist")
if (ROOT / "tests/fixtures/boss_buff_scaling_source.json").is_file():
    check(boss_buff_scaling_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_buff_scaling_source.json").read_text(encoding="utf-8")),
          "Boss buff scaling fixture must not drift from the oracle")
check('const BossShakeSitesChecks = preload("res://tests/boss_shake_sites_checks.gd")' in ai_tests,
      "Boss shake site suite must be preloaded")
check("BossShakeSitesChecks.new().run(_check)" in ai_tests,
      "Boss shake site suite must run")
check((ROOT / "tests/fixtures/boss_shake_sites_source.json").is_file(),
      "Boss shake site fixture must exist")
if (ROOT / "tests/fixtures/boss_shake_sites_source.json").is_file():
    check(boss_shake_sites_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_shake_sites_source.json").read_text(encoding="utf-8")),
          "Boss shake site fixture must not drift from the oracle")
check('const BalanceBaselineChecks = preload("res://tests/balance_baseline_checks.gd")' in ai_tests,
      "Balance baseline suite must be preloaded")
check("BalanceBaselineChecks.new().run(_check)" in ai_tests,
      "Balance baseline suite must run")
check((ROOT / "tests/fixtures/balance_baseline_ingame.json").is_file(),
      "Balance baseline fixture must exist")
if (ROOT / "tests/fixtures/balance_baseline_ingame.json").is_file():
    check(balance_baseline_fixture() == json.loads(
        (ROOT / "tests/fixtures/balance_baseline_ingame.json").read_text(encoding="utf-8")),
          "Balance baseline fixture must not drift from the oracle")
check((ROOT / "BALANCE_CONTRACT.md").is_file(),
      "The balance contract must document the rebaseline doctrine")
check('const BalanceOverrideLayerChecks = preload("res://tests/balance_override_layer_checks.gd")'
      in ai_tests,
      "Balance override layer suite must be preloaded")
check("BalanceOverrideLayerChecks.new().run(_check)" in ai_tests,
      "Balance override layer suite must run")
_balance_overrides_text = (ROOT / "scripts/data/balance_overrides.gd").read_text(encoding="utf-8")
check("const STARTER_DAMAGE_MULT := 1.5" in _balance_overrides_text,
      "The S1 starter catch-up multiplier must stay pinned at 1.5 (gap 5.67x -> 3.97x)")
for _starter_id in ("kaizen", "thorne", "grimjaw", "sylara", "vex", "zephyr"):
    check('\t"%s":\n\t{\n\t\t"damage_mult": STARTER_DAMAGE_MULT,' % _starter_id
          in _balance_overrides_text,
          "Starter %s must carry the S1 catch-up override entry" % _starter_id)
check('const S1_REASON := "S1 starter catch-up 2026-10-16: starter gap 5.67x -> 3.97x (target <= 4.0x)"'
      in _balance_overrides_text,
      "The S1 reason must record the measured before/after starter gap")
check(_balance_overrides_text.count('"reason": S1_REASON + "; auto-attack damage ') == 6,
      "Exactly the six S1 starter entries carry the measured before/after reason")
check("const PHYSICAL_TANK_DAMAGE_MULT := 0.85" in _balance_overrides_text,
      "The S2 PHYSICAL|TANK multiplier must stay pinned at 0.85 (cell power 1.38 -> 1.25)")
check('const S2_REASON := "S2 PHYSICAL|TANK nerf 2026-10-16: cell power 1.38 -> 1.25 (prose cap 1.25)"'
      in _balance_overrides_text,
      "The S2 reason must record the measured before/after cell power")
check(_balance_overrides_text.count('"reason": S2_REASON + "; auto-attack damage ') == 39,
      "Exactly the 39 PHYSICAL|TANK heroes carry the S2 nerf entry")
for _tank_id in ("akaroth", "cogsworth", "hollowbane", "sasori", "zhyvrek"):
    check('\t"%s":\n\t{\n\t\t"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,' % _tank_id
          in _balance_overrides_text,
          "PHYSICAL|TANK %s must carry the S2 nerf override entry" % _tank_id)
_prototype_text = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
check('const BalanceOverrides = preload("res://scripts/data/balance_overrides.gd")'
      in _prototype_text,
      "Prototype battle must preload the rebalance surface")
check('"troll":\n\t{\n\t\t"regen_per_tick": 0.15,' in _balance_overrides_text,
      "The S3 production troll regen override must stay pinned at 0.15 HP/tick")
check("static func minion_definition_for(definition: MinionDefinition) -> MinionDefinition:"
      in _balance_overrides_text and "definition.duplicate() as MinionDefinition" in _balance_overrides_text,
      "The minion override must duplicate the definition, never mutate the .tres")
check("target = BalanceOverrides.minion_definition_for(definition)" in _prototype_text,
      "The production wave spawn must route the minion override surface")
check("regen_per_tick = 0.6" in (ROOT / "data/minions/troll.tres").read_text(encoding="utf-8"),
      "The troll .tres must keep the 0.6 source regen (lab parity)")
check("var balance_overrides_enabled := false" in _prototype_text
      and "or not balance_overrides_enabled:" in _prototype_text,
      "The rebalance table must be opt-in per world (off for parity suites and the lab)")
check("session.enable_balance_overrides()" in (ROOT / "app/app.gd").read_text(encoding="utf-8"),
      "The playable match flow must opt the arena into the rebalance table")
check("func enable_balance_overrides() -> void:" in
      (ROOT / "scripts/simulation/prototype_session.gd").read_text(encoding="utf-8"),
      "PrototypeSession must expose the rebalance opt-in for app.gd")
check(_prototype_text.count("_spawn_production_hero(") == 5,
      "All four production hero spawns plus the wrapper must route the rebalance surface")
check('const DebuffPayloadReachChecks = preload("res://tests/debuff_payload_reach_checks.gd")' in ai_tests,
      "Debuff payload reach suite must be preloaded")
check("DebuffPayloadReachChecks.new().run(_check)" in ai_tests,
      "Debuff payload reach suite must run")
check((ROOT / "tests/fixtures/debuff_payload_reach_source.json").is_file(),
      "Debuff payload reach fixture must exist")
if (ROOT / "tests/fixtures/debuff_payload_reach_source.json").is_file():
    check(debuff_payload_reach_fixture() == json.loads(
        (ROOT / "tests/fixtures/debuff_payload_reach_source.json").read_text(encoding="utf-8")),
          "Debuff payload reach fixture must not drift from the oracle")
check('const HeroMarkerChecks = preload("res://tests/hero_marker_checks.gd")' in ai_tests,
      "Hero marker suite must be preloaded")
check("HeroMarkerChecks.new().run(_check)" in ai_tests, "Hero marker suite must run")
check((ROOT / "tests/fixtures/hero_marker_source.json").is_file(),
      "Hero marker golden fixture must exist")
if (ROOT / "tests/fixtures/hero_marker_source.json").is_file():
    check(hero_marker_fixture() == json.loads(
        (ROOT / "tests/fixtures/hero_marker_source.json").read_text(encoding="utf-8")),
          "Hero marker fixture must not drift from the oracle")
view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
check("HeroMarker.silhouette(" in view, "The arena view must draw the readable silhouette")
check("HeroMarker.body(" not in view, "The arena view must not fall back to the placeholder body")
check((ROOT / "tests/fixtures/boss_sourceless_delivery_source.json").is_file(),
      "Boss sourceless delivery fixture must exist")
if (ROOT / "tests/fixtures/boss_sourceless_delivery_source.json").is_file():
    check(boss_sourceless_delivery_fixture() == json.loads(
        (ROOT / "tests/fixtures/boss_sourceless_delivery_source.json").read_text(encoding="utf-8")),
          "Boss sourceless delivery fixture must not drift from the oracle")
check('const BurnBossDeliveryChecks = preload("res://tests/burn_boss_delivery_checks.gd")' in ai_tests,
      "Burn boss delivery suite must be preloaded")
check("BurnBossDeliveryChecks.new().run(_check)" in ai_tests,
      "Burn boss delivery suite must run")
check((ROOT / "tests/fixtures/burn_boss_delivery_source.json").is_file(),
      "Burn boss delivery fixture must exist")
if (ROOT / "tests/fixtures/burn_boss_delivery_source.json").is_file():
    check(burn_boss_delivery_fixture() == json.loads(
        (ROOT / "tests/fixtures/burn_boss_delivery_source.json").read_text(encoding="utf-8")),
          "Burn boss delivery fixture must not drift from the oracle")
check('const BurnTickDeliveryChecks = preload("res://tests/burn_tick_delivery_checks.gd")' in ai_tests,
      "Burn tick delivery suite must be preloaded")
check("BurnTickDeliveryChecks.new().run(_check)" in ai_tests,
      "Burn tick delivery suite must run")
check((ROOT / "tests/fixtures/burn_tick_delivery_source.json").is_file(),
      "Burn tick delivery fixture must exist")
if (ROOT / "tests/fixtures/burn_tick_delivery_source.json").is_file():
    check(burn_tick_delivery_fixture() == json.loads(
        (ROOT / "tests/fixtures/burn_tick_delivery_source.json").read_text(encoding="utf-8")),
          "Burn tick delivery fixture must not drift from the oracle")
check('const MiasmaTickDeliveryChecks = preload("res://tests/miasma_tick_delivery_checks.gd")'
      in ai_tests,
      "Miasma tick delivery suite must be preloaded")
check("MiasmaTickDeliveryChecks.new().run(_check)" in ai_tests,
      "Miasma tick delivery suite must run")
check((ROOT / "tests/fixtures/miasma_tick_delivery_source.json").is_file(),
      "Miasma tick delivery fixture must exist")
if (ROOT / "tests/fixtures/miasma_tick_delivery_source.json").is_file():
    check(miasma_tick_delivery_fixture() == json.loads(
        (ROOT / "tests/fixtures/miasma_tick_delivery_source.json").read_text(encoding="utf-8")),
          "Miasma tick delivery fixture must not drift from the oracle")
check((ROOT / "tests/fixtures/skill_hit_attribution_source.json").is_file(),
      "Skill hit attribution fixture must exist")
if (ROOT / "tests/fixtures/skill_hit_attribution_source.json").is_file():
    check(skill_hit_attribution_fixture() == json.loads(
        (ROOT / "tests/fixtures/skill_hit_attribution_source.json").read_text(encoding="utf-8")),
          "Skill hit attribution fixture must not drift from the oracle")
check((ROOT / "tests/fixtures/minion_damage_ladder_source.json").is_file(),
      "Minion damage ladder fixture must exist")
if (ROOT / "tests/fixtures/minion_damage_ladder_source.json").is_file():
    check(minion_ladder_fixture() == json.loads(
        (ROOT / "tests/fixtures/minion_damage_ladder_source.json").read_text(encoding="utf-8")),
          "Minion damage ladder fixture must not drift from the oracle")
check((ROOT / "tests/fixtures/hero_skill_sourceless_source.json").is_file(),
      "Sourceless skill arm requires a source fixture")
if (ROOT / "tests/fixtures/hero_skill_sourceless_source.json").is_file():
    check(sourceless_fixture() == json.loads(
        (ROOT / "tests/fixtures/hero_skill_sourceless_source.json").read_text(encoding="utf-8")),
        "Sourceless skill arm source fixture drift")
check((ROOT / "tests/fixtures/hero_armor_model_source.json").is_file(),
      "Hero armour model requires a source fixture")
if (ROOT / "tests/fixtures/hero_armor_model_source.json").is_file():
    check(hero_armor_fixture() == json.loads(
        (ROOT / "tests/fixtures/hero_armor_model_source.json").read_text(encoding="utf-8")),
        "Hero armour model source fixture drift")
check((ROOT / "tests/fixtures/hero_block_source.json").is_file(),
      "Hero block requires a source fixture")
if (ROOT / "tests/fixtures/hero_block_source.json").is_file():
    check(hero_block_fixture() == json.loads(
        (ROOT / "tests/fixtures/hero_block_source.json").read_text(encoding="utf-8")),
        "Hero block source fixture drift")
check((ROOT / "tests/fixtures/hero_veil_immunity_source.json").is_file(),
      "Tempest Veil requires a source fixture")
if (ROOT / "tests/fixtures/hero_veil_immunity_source.json").is_file():
    check(hero_veil_fixture() == json.loads(
        (ROOT / "tests/fixtures/hero_veil_immunity_source.json").read_text(encoding="utf-8")),
        "Tempest Veil source fixture drift")
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
# Layer 9aq: lighting.py port (mask math exact, vector adapter in the view).
check('const SpriteLightingChecks = preload("res://tests/sprite_lighting_checks.gd")' in ai_tests
      and "SpriteLightingChecks.new().run(_check)" in ai_tests,
      "9aq sprite lighting suite must be preloaded and run")
check("python godot_rebuild/tests/sprite_lighting_source_oracle.py" in workflow,
      "9aq CI must regenerate the sprite lighting fixture from lighting.py")
check((ROOT / "tests/fixtures/sprite_lighting_source.json").is_file(),
      "9aq sprite lighting fixture must exist")
if (ROOT / "tests/fixtures/sprite_lighting_source.json").is_file():
    check(sprite_lighting_fixture() == json.loads(
        (ROOT / "tests/fixtures/sprite_lighting_source.json").read_text(encoding="utf-8")),
          "9aq sprite lighting fixture must not drift from lighting.py")
_sprite_lighting_text = (ROOT / "scripts/ui/sprite_lighting.gd").read_text(encoding="utf-8")
check("const LIGHT_DIR := Vector2i(-1, -1)" in _sprite_lighting_text
      and "const RIM_ADD := Vector3i(30, 26, 44)" in _sprite_lighting_text
      and "const SHADE_MUL := 168" in _sprite_lighting_text
      and "const BAND2_RATIO := 0.42" in _sprite_lighting_text
      and "const GRAD_DARK := 205" in _sprite_lighting_text
      and "const GRAD_SHEEN := 22" in _sprite_lighting_text
      and "const MIN_SOLID := 24" in _sprite_lighting_text,
      "9aq sprite lighting constants must mirror lighting.py")
check("_draw_lit_polygon(HeroMarker.silhouette(" in view
      and "_draw_lit_polygon(SpriteLighting.circle_points(point, radius)" in view
      and 'const SpriteLighting = preload("res://scripts/ui/sprite_lighting.gd")' in view,
      "9aq the arena view must route hero silhouettes and boss bodies through the lighting pass")
check("import " not in _sprite_lighting_text and "load(" not in _sprite_lighting_text,
      "9aq sprite lighting stays asset-free (procedural shading only)")
# Layer 9ar: mobile/combat_audio.py port (combat SFX gate + attack call sites).
check('const CombatAudioChecks = preload("res://tests/combat_audio_checks.gd")' in ai_tests
      and "CombatAudioChecks.new().run(_check)" in ai_tests,
      "9ar combat audio suite must be preloaded and run")
check("python godot_rebuild/tests/combat_audio_source_oracle.py" in workflow,
      "9ar CI must regenerate the combat audio fixture from mobile/combat_audio.py")
check((ROOT / "tests/fixtures/combat_audio_source.json").is_file(),
      "9ar combat audio fixture must exist")
if (ROOT / "tests/fixtures/combat_audio_source.json").is_file():
    check(combat_audio_fixture() == json.loads(
        (ROOT / "tests/fixtures/combat_audio_source.json").read_text(encoding="utf-8")),
          "9ar combat audio fixture must not drift from mobile/combat_audio.py")
_combat_audio_text = (ROOT / "scripts/audio/combat_audio.gd").read_text(encoding="utf-8")
check("const RANGED_THRESHOLD := 100.0" in _combat_audio_text
      and "const FRAME_BUDGET := 4" in _combat_audio_text
      and "const MIXER_CHANNELS := 24" in _combat_audio_text
      and "MINION_HIT: [0.50, 140, false]" in _combat_audio_text
      and "HERO_MELEE: [0.78, 90, false]" in _combat_audio_text,
      "9ar combat audio gate constants must mirror _KONFIG")
for _name in ("hero_melee.wav", "hero_ranged.wav", "tower_archer.wav", "tower_cannon.wav",
              "tower_ice.wav", "tower_mage.wav", "minion_hit.ogg"):
    check((ROOT / "assets/audio" / _name).is_file(), "9ar combat sound %s must ship" % _name)
_audio_manager_text = (ROOT / "scripts/audio/audio_manager.gd").read_text(encoding="utf-8")
check("func play_combat(" in _audio_manager_text
      and "func combat_free_channels(" in _audio_manager_text
      and "func combat_global_volume(" in _audio_manager_text
      and "const COMBAT_CHANNELS := 24" in _audio_manager_text,
      "9ar AudioManager must expose the 24-channel combat pool")
_proto_text = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
_minion_text = (ROOT / "scripts/combat/minion_battle.gd").read_text(encoding="utf-8")
_siege_text = (ROOT / "scripts/combat/siege_battle.gd").read_text(encoding="utf-8")
check("CombatAudio.play_hero_basic(hero)" in _proto_text
      and "CombatAudio.play(CombatAudio.attack_kind(boss.attack_range))" in _proto_text,
      "9ar hero basic attack and boss attack must play through the gate")
check("CombatAudio.play(CombatAudio.MINION_HIT)" in _minion_text
      and "CombatAudio.shared().new_frame()" in _minion_text,
      "9ar minion swing must play through the gate and the budget resets per tick")
check("CombatAudio.tower_kind(source.settings().tower_path)" in _siege_text
      and "1.0 if source.team == BLUE else 0.8" in _siege_text,
      "9ar tower shots must play per path with the blue/red volume split")
# Layer 9as: mobile/sidepanel.py port (wide-screen right panel).
check('const SidePanelChecks = preload("res://tests/side_panel_checks.gd")' in ai_tests
      and "SidePanelChecks.new().run(_check)" in ai_tests,
      "9as side panel suite must be preloaded and run")
check("python godot_rebuild/tests/side_panel_source_oracle.py" in workflow,
      "9as CI must regenerate the side panel fixture from mobile/sidepanel.py")
check((ROOT / "tests/fixtures/side_panel_source.json").is_file(),
      "9as side panel fixture must exist")
if (ROOT / "tests/fixtures/side_panel_source.json").is_file():
    check(side_panel_fixture() == json.loads(
        (ROOT / "tests/fixtures/side_panel_source.json").read_text(encoding="utf-8")),
          "9as side panel fixture must not drift from mobile/sidepanel.py")
_side_layout_text = (ROOT / "scripts/ui/side_panel_layout.gd").read_text(encoding="utf-8")
check("const MAX_DISPLAY_WIDTH := 2200" in _side_layout_text
      and "const MIN_PANEL_WIDTH := 120" in _side_layout_text
      and "const REFRESH_MS := 250" in _side_layout_text
      and "const MIN_TAP := 80" in _side_layout_text
      and "const HERO_BOX_MAX := 236" in _side_layout_text,
      "9as side panel layout constants must mirror sidepanel.py / platform_utils.py")
_side_screen_text = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
check("side_panel.pause_requested.connect(pause_match)" in _side_screen_text
      and "side_panel.tactical_down.connect(_start_panel_tactical)" in _side_screen_text
      and "side_panel.tactical_up.connect(_finish_tactical)" in _side_screen_text
      and "var docked := side_panel.is_active()" in _side_screen_text
      and "%TacticalToggleButton.visible = not docked" in _side_screen_text
      and "%TacticalPanel.visible = _tactical_panel_open and not docked" in _side_screen_text,
      "9as the match screen must mount the side panel and dock tactical controls")
_project_text = (ROOT / "project.godot").read_text(encoding="utf-8")
check('window/stretch/aspect="expand"' in _project_text,
      "9as the viewport must expand so wide screens expose the right panel")
# Layer 9at: splash_screen.py port (boot splash before the menu).
check('const SplashScreenChecks = preload("res://tests/splash_screen_checks.gd")' in ai_tests
      and "SplashScreenChecks.new().run(_check)" in ai_tests,
      "9at splash suite must be preloaded and run")
check('application boots into the splash' in ai_tests and 'splash skip hands over to the menu' in ai_tests,
      "9at runtime suite must boot through the splash into the menu")
check("python godot_rebuild/tests/splash_screen_source_oracle.py" in workflow,
      "9at CI must regenerate the splash fixture from splash_screen.py")
check((ROOT / "tests/fixtures/splash_screen_source.json").is_file(),
      "9at splash fixture must exist")
if (ROOT / "tests/fixtures/splash_screen_source.json").is_file():
    check(splash_screen_fixture() == json.loads(
        (ROOT / "tests/fixtures/splash_screen_source.json").read_text(encoding="utf-8")),
          "9at splash fixture must not drift from splash_screen.py")
_splash_timeline_text = (ROOT / "scripts/ui/splash_timeline.gd").read_text(encoding="utf-8")
check("const DURATION := 3.0" in _splash_timeline_text
      and "const SKIP_FADE := 0.25" in _splash_timeline_text
      and "const PARTICLE_COUNT := 46" in _splash_timeline_text
      and "const LOGO_BOX := Vector2(340.0, 320.0)" in _splash_timeline_text
      and "const VIGNETTE_MAX := 140" in _splash_timeline_text,
      "9at splash timeline constants must mirror splash_screen.py")

# Layer 9au: top-up / voucher flow port (topup_currency.py, topup_voucher.py,
# Menu.topup_* of _core.py, HTTP client for server/app.py).
check('const TopupChecks = preload("res://tests/topup_checks.gd")' in ai_tests
      and "TopupChecks.new().run(_check)" in ai_tests,
      "9au top-up suite must be preloaded and run")
check('const TopupSceneChecks = preload("res://tests/topup_scene_checks.gd")' in ai_tests
      and "await TopupSceneChecks.new().run(root.get_tree(), app, _check)" in ai_tests,
      "9au top-up scene suite must run against the live menu")
check("python godot_rebuild/tests/topup_source_oracle.py" in workflow,
      "9au CI must regenerate the top-up fixture from the source modules")
check((ROOT / "tests/fixtures/topup_source.json").is_file(),
      "9au top-up fixture must exist")
if (ROOT / "tests/fixtures/topup_source.json").is_file():
    check(topup_fixture() == json.loads(
        (ROOT / "tests/fixtures/topup_source.json").read_text(encoding="utf-8")),
          "9au top-up fixture must not drift from the source modules")
_topup_flow_text = (ROOT / "scripts/match/topup_flow.gd").read_text(encoding="utf-8")
check('{"label": "PAKET 50K", "gold": 50000, "bonus": 0, "price": 10000}' in _topup_flow_text
      and "const PROCESSING_SECONDS := 1.6" in _topup_flow_text
      and "const POLL_DELAY_FIRST := 60" in _topup_flow_text
      and "const POLL_DELAY_REPEAT := 120" in _topup_flow_text
      and "const HTTP_TIMEOUT := 6.0" in _topup_flow_text
      and 'const ENV_SERVER_URL := "MYSTIC_TOPUP_URL"' in _topup_flow_text
      and 'const CREATE_PATH := "/api/topup/create"' in _topup_flow_text,
      "9au top-up flow constants must mirror _core.py / server/app.py")
_topup_voucher_text = (ROOT / "scripts/match/topup_voucher.gd").read_text(encoding="utf-8")
check('const CODE_PREFIX := "MA-"' in _topup_voucher_text
      and "const MAX_DIGITS := 6" in _topup_voucher_text
      and 'const CODE_PATTERN := "^MA-(\\\\d{4,8})$"' in _topup_voucher_text,
      "9au voucher constants must mirror topup_voucher.py")
_main_menu_text = (ROOT / "scenes/menu/main_menu.gd").read_text(encoding="utf-8")
check("hero_shop_panel.topup_requested.connect(_open_topup)" in _main_menu_text
      and "topup_client.configure(topup_flow)" in _main_menu_text
      and "topup_panel.bind(topup_flow)" in _main_menu_text,
      "9au menu must wire the hero shop TOP UP button to the dialog, client and flow")
for _topup_path in ("scripts/match/topup_currency.gd", "scripts/net/topup_client.gd",
                    "scripts/ui/topup_panel.gd"):
    check((ROOT / _topup_path).is_file(), f"9au {_topup_path} must exist")

# Layer 9av: LevelIntroScreen.draw() visuals (split screen, boss silhouette,
# prompt) as a pure op list rendered by the prototype view.
check('const LevelIntroDrawChecks = preload("res://tests/level_intro_draw_checks.gd")' in ai_tests
      and "LevelIntroDrawChecks.new().run(_check)" in ai_tests,
      "9av level intro draw suite must be preloaded and run")
check("python godot_rebuild/tests/level_intro_draw_source_oracle.py" in workflow,
      "9av CI must regenerate the level intro draw fixture from _render.py")
check((ROOT / "tests/fixtures/level_intro_draw_source.json").is_file(),
      "9av level intro draw fixture must exist")
if (ROOT / "tests/fixtures/level_intro_draw_source.json").is_file():
    check(level_intro_draw_fixture() == json.loads(
        (ROOT / "tests/fixtures/level_intro_draw_source.json").read_text(encoding="utf-8")),
          "9av level intro draw fixture must not drift from _render.py")
_level_intro_layout_text = (ROOT / "scripts/ui/level_intro_layout.gd").read_text(encoding="utf-8")
check("const FADE_IN := 30" in _level_intro_layout_text
      and '"desert": [100, 60, 20]' in _level_intro_layout_text
      and 'const WARNING_TEXT := "PREPARE FOR BATTLE"' in _level_intro_layout_text
      and "func _silhouette(" in _level_intro_layout_text
      and "func _space_prompt(" in _level_intro_layout_text,
      "9av level intro layout must mirror LevelIntroScreen.draw()")
_prototype_view_text = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
check("LevelIntroLayout.ops(" in _prototype_view_text
      and "func _draw_intro_op(" in _prototype_view_text
      and "_measure_intro_text" in _prototype_view_text,
      "9av prototype view must render the level intro from the layout ops")
check('const SPLASH = preload("res://scenes/splash/SplashScreen.tscn")' in app
      and "_install_screen(SPLASH)" in app
      and 'current_screen.connect("finished", show_menu)' in app,
      "9at the app must boot into the splash and hand over to the menu")
check((ROOT / "scenes/splash/SplashScreen.tscn").is_file()
      and (ROOT / "scenes/splash/splash_screen.gd").is_file()
      and (ROOT / "assets/logo.png").is_file(),
      "9at splash scene, script and logo must ship")
check("python godot_rebuild/tests/balance_baseline_source_oracle.py" in workflow,
      "CI must pin the ingame balance baseline")

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

from level_stats_source_oracle import source_fixture as level_stats_source_fixture
level_stats_fixture_path = ROOT / "tests/fixtures/level_stats_source.json"
check(level_stats_fixture_path.is_file(), "Level-stat runtime requires a source fixture")
if level_stats_fixture_path.is_file():
    check(level_stats_source_fixture()
          == json.loads(level_stats_fixture_path.read_text(encoding="utf-8")),
          "Source match rewards or per-level statistics drift")
check("python godot_rebuild/tests/level_stats_source_oracle.py" in workflow,
      "CI must execute the level-stat source oracle")
check("- '_render.py'" in workflow,
      "Level-stat CI must track the real ComboCounter authority")
check("LevelStatsChecks.new().run(_check)" in ai_tests,
      "Level-stat source replay suite must run")
check("await LevelStatsSceneChecks.new().run(self, app, _check)" in ai_tests,
      "Level-stat playable save/retry/menu suite must run")
level_stats_domain = (ROOT / "scripts/match/level_stats.gd").read_text(encoding="utf-8")
progress_store = (ROOT / "scripts/match/level_progress_store.gd").read_text(encoding="utf-8")
prototype_world = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
check("static func update_level_stats" in level_stats_domain
      and "static func get_level_stats" in level_stats_domain
      and "static func valid_map" in level_stats_domain,
      "Native level statistics must preserve source transaction and validation policy")
check("LevelStats.valid_map" in progress_store,
      "Atomic progress loading must deeply validate per-level statistics")
check("func match_stats_snapshot" in prototype_world
      and "total_kills += 1" in prototype_world
      and "combo_count > max_combo" in prototype_world
      and "LevelStats.update_level_stats" in prototype_world,
      "Playable reward runtime must feed score, kills, combo and time into persistence")
check("LevelStats.get_level_stats" in meta_menu and "%LevelStatsLabel" in meta_menu,
      "Selected-level source statistics must reload in the main menu")

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
check('position = Vector2(0, 0)' in structure_scene
      and 'scale = Vector2(1, 1)' in structure_scene,
      "Prototype arena must fill its 1280x720 logical viewport")
check('name="TacticalToggleButton"' in structure_scene
      and 'visible = false\noffset_left = 1032.0' in structure_scene,
      "Prototype tactical dock must be closed behind a compact HUD toggle")
check('[node name="BottomBar" type="PanelContainer" parent="HUD"]\n'
      'unique_name_in_owner = true\nvisible = false' in structure_scene
      and 'name="CommandDockToggle"' in structure_scene
      and '%CommandDockToggle.toggled.connect(_set_command_dock_open)' in shield_screen,
      "Prototype commands must stay available in a closed, toggleable bottom dock")
check('const PrototypeLayoutChecks = preload("res://tests/prototype_layout_checks.gd")' in ai_tests
      and 'await PrototypeLayoutChecks.new().run(self, app, _check)' in ai_tests,
      "Prototype full-screen overlay layout must have a registered scene proof")
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
audio_panel = ROOT / "scripts/ui/audio_settings_panel.gd"
menu_scene = (ROOT / "scenes/menu/MainMenu.tscn").read_text(encoding="utf-8")
check(audio_panel.is_file() and "SettingsButton" in menu_scene,
      "Live audio controls must be reachable from the playable MainMenu")
check("func set_mix_volume(" in audio_script.read_text(encoding="utf-8")
      and "func adjust_volume(" in audio_script.read_text(encoding="utf-8"),
      "Native audio manager must expose bounded live mix controls")
check("AudioSettingsChecks.new().run(_check)" in ai_tests
      and "await AudioSettingsSceneChecks.new().run(root.get_tree(), app, _check)" in ai_tests,
      "Audio mixer native and playable-scene checks must be registered")
from audio_settings_source_oracle import source_fixture as audio_settings_source_fixture
check((ROOT / "tests/fixtures/audio_settings_source.json").is_file(),
      "Audio settings source oracle fixture must be present")
if (ROOT / "tests/fixtures/audio_settings_source.json").is_file():
    check(audio_settings_source_fixture() == json.loads(
        (ROOT / "tests/fixtures/audio_settings_source.json").read_text(encoding="utf-8")),
        "Audio settings source fixture drift")

from frame_rate_limit_source_oracle import source_fixture as frame_rate_limit_source_fixture
frame_rate_fixture_path = ROOT / "tests/fixtures/frame_rate_limit_source.json"
check(frame_rate_fixture_path.is_file(), "Frame-rate setting source fixture must be present")
if frame_rate_fixture_path.is_file():
    check(frame_rate_limit_source_fixture() == json.loads(
        frame_rate_fixture_path.read_text(encoding="utf-8")),
        "Frame-rate setting source fixture drift")
frame_rate_runtime = ROOT / "scripts/settings/frame_rate_limit_runtime.gd"
frame_rate_store = ROOT / "scripts/settings/frame_rate_limit_store.gd"
check(frame_rate_runtime.is_file() and frame_rate_store.is_file(),
      "Native frame-rate runtime and atomic settings store must exist")
if frame_rate_runtime.is_file():
    frame_rate_text = frame_rate_runtime.read_text(encoding="utf-8")
    check("Engine.max_fps" in frame_rate_text and "func resolve_limit(" in frame_rate_text,
          "Frame-rate runtime must apply the user render cap")
    check("physics_ticks_per_second" not in frame_rate_text and "GameSpeed" not in frame_rate_text,
          "Frame-rate runtime must not control fixed simulation speed")
check('FrameRateLimit="*res://scripts/settings/frame_rate_limit_runtime.gd"' in project,
      "Native frame-rate runtime must be autoloaded before gameplay")
check("FrameRateLimitChecks.new().run(_check)" in ai_tests
      and "await FrameRateLimitSceneChecks.new().run(root.get_tree(), app, _check)" in ai_tests,
      "Frame-rate native and playable-scene checks must be registered")
check("FrameRateNext" in (ROOT / "scripts/ui/audio_settings_panel.gd").read_text(encoding="utf-8"),
      "MainMenu settings must expose the source FPS-limit control")

from adaptive_quality_source_oracle import source_fixture as adaptive_quality_source_fixture
adaptive_fixture_path = ROOT / "tests/fixtures/adaptive_quality_source.json"
check(adaptive_fixture_path.is_file(), "Adaptive-quality source fixture must be present")
if adaptive_fixture_path.is_file():
    check(adaptive_quality_source_fixture() == json.loads(
        adaptive_fixture_path.read_text(encoding="utf-8")),
        "Adaptive-quality source fixture drift")
adaptive_controller = ROOT / "scripts/settings/adaptive_quality_controller.gd"
adaptive_runtime = ROOT / "scripts/settings/adaptive_quality_runtime.gd"
check(adaptive_controller.is_file() and adaptive_runtime.is_file(),
      "Adaptive-quality controller and runtime must exist")
if adaptive_runtime.is_file():
    adaptive_text = adaptive_runtime.read_text(encoding="utf-8")
    check("Engine.get_frames_per_second()" in adaptive_text
          and 'set_quality_target_fps' in adaptive_text,
          "Adaptive quality must consume live render FPS and update the existing limiter")
    check("physics_ticks_per_second" not in adaptive_text and "GameSpeed" not in adaptive_text,
          "Adaptive quality must remain separate from simulation speed and fixed ticks")
check('AdaptiveQuality="*res://scripts/settings/adaptive_quality_runtime.gd"' in project,
      "Adaptive-quality runtime must be autoloaded")
check("AdaptiveQualityChecks.new().run(_check)" in ai_tests
      and "await AdaptiveQualitySceneChecks.new().run(root.get_tree(), app, _check)" in ai_tests,
      "Adaptive-quality native and playable-scene tests must be registered")

from localization_source_oracle import source_fixture as localization_source_fixture
localization_catalog_path = ROOT / "data/localization_catalog.json"
localization_contract_path = ROOT / "tests/fixtures/localization_source_contract.json"
check(localization_catalog_path.is_file() and localization_contract_path.is_file(),
      "Localization catalog and source contract fixture must be present")
if localization_catalog_path.is_file() and localization_contract_path.is_file():
    source_localization = localization_source_fixture()
    check(source_localization == json.loads(
        localization_catalog_path.read_text(encoding="utf-8")),
        "Native localization catalog drifted from active Python data")
    source_contract = {key: value for key, value in source_localization.items() if key != "texts"}
    check(source_contract == json.loads(
        localization_contract_path.read_text(encoding="utf-8")),
        "Language default, labels or persistence contract drift")
language_runtime = ROOT / "scripts/settings/localization_runtime.gd"
language_store = ROOT / "scripts/settings/language_store.gd"
check(language_runtime.is_file() and language_store.is_file(),
      "Native language runtime and atomic preference store must exist")
if language_runtime.is_file():
    language_text = language_runtime.read_text(encoding="utf-8")
    check("func translate(" in language_text and "language_changed.emit" in language_text,
          "Language selection must update live translation lookups")
check('Localization="*res://scripts/settings/localization_runtime.gd"' in project,
      "Native localization runtime must be autoloaded")
check("LocalizationChecks.new().run(_check)" in ai_tests
      and "await LocalizationSceneChecks.new().run(root.get_tree(), app, _check)" in ai_tests,
      "Localization native and playable-scene tests must be registered")
check("LanguageNext" in (ROOT / "scripts/ui/audio_settings_panel.gd").read_text(encoding="utf-8")
      and "language_changed" in (ROOT / "scenes/menu/main_menu.gd").read_text(encoding="utf-8"),
      "Settings language selector must relabel the active MainMenu and panel")

cloud_runtime = (ROOT / "scripts/match/cloud_save_runtime.gd")
cloud_codec = (ROOT / "scripts/match/cloud_save_codec.gd")
check(cloud_runtime.is_file() and cloud_codec.is_file(), "Native cloud codec/runtime must exist")
check('CloudSave="*res://scripts/match/cloud_save_runtime.gd"' in project,
      "Native cloud runtime must be autoloaded")
check((ROOT / "addons/mystic_cloud/export_plugin.gd").is_file()
      and (ROOT / "android_plugin/cloud_save/plugin/src/main/java/io/github/dharmawantoxi/mysticarena/godot/GodotCloudSavePlugin.java").is_file(),
      "Cloud integration must include the Godot Android plugin-v2 export path")
if cloud_runtime.is_file():
    cloud_text = cloud_runtime.read_text(encoding="utf-8")
    check("OS.get_user_data_dir()" in cloud_text and "storage_paths" not in cloud_text
          and "mobile/cloud_save" not in cloud_text,
          "Godot cloud runtime must use only Godot-native storage")
check("CloudSaveChecks.new().run(_check)" in ai_tests
      and "await CloudSaveSceneChecks.new().run(root.get_tree(), app, _check)" in ai_tests,
      "Cloud payload and playable-menu tests must be registered")
check((ROOT / "tests/cloud_save_source_oracle.py").is_file()
      and (ROOT / "tests/fixtures/cloud_save_source.json").is_file(),
      "Cloud source oracle and fixture must be present")


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
check("BossDeathPauseChecks.new().run(_check)" in ai_tests, "Boss death-pause unit suite must run")
check("BossDeathPauseSceneChecks.new().run(root.get_tree(), _check)" in ai_tests,
      "Boss death-pause playable-scene suite must run")
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
check('var declared := "magic" if shot.kind == "mage" else "physical"' in projectile_delivery
      and "var school := _projectile_school(target, declared)" in projectile_delivery
      and "_hero_blocks_projectile(target, school)" in projectile_delivery,
      "Structure impacts must gate and deliver under the resolved projectile school")
projectile_school_base = siege_battle.split("func _projectile_school(", 1)[1].split("\nfunc ", 1)[0]
check('return "neutral"' in projectile_school_base,
      "Structure shots must land school-free on every victim, like Bullet._on_hit")
check("func _projectile_school(" not in prototype_battle,
      "Match layer must not re-declare the resolved projectile school")
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
# Layer 9am: boss self-buff stat lifecycles (Chemical Rage persistence +
# Shukuchi raw-catalog speed writes), pinned against the source oracle.
check("var catalog_speed := 0.0" in boss_state,
      "Boss state must snapshot the raw catalog speed for Shukuchi parity")
check('catalog_speed = float(stats.get("speed", 1.15))' in boss_state,
      "Catalog speed must come from the raw boss_data row")
check("boss.speed_px_per_tick = boss.catalog_speed * 1.8" in boss_ai_text,
      "Shukuchi cast must write the 1.8x raw catalog speed boost")
check(boss_ai_text.count("boss.speed_px_per_tick = boss.catalog_speed\n") == 1,
      "Shukuchi expiry must restore the raw catalog speed exactly once")
check(boss_ai_text.count("boss.damage = _source_damage(boss)") == 5,
      "Dragon form plus the four buff expiries must reset via the scaled source read")
# Layer 9an: the four buff damage writes read the scaled catalog damage -
# `_get_boss_stats()["damage"]` rounded ONCE - while the xerathis arcane pair
# stays verbatim on the difficulty-baked base_damage attribute.
check("var catalog_damage := 0" in boss_state,
      "Boss state must snapshot the raw catalog damage for the scaled stats read")
check("catalog_damage = damage" in boss_state,
      "Catalog damage must be captured before difficulty scaling bakes base_damage")
check("return _skill_damage(boss, boss.catalog_damage)" in boss_ai_text,
      "_source_damage must be the single-round scaled catalog read")
check(boss_ai_text.count("int(float(_source_damage(boss)) *") == 8,
      "Every stats-read buff cast must compound off _source_damage")
check(boss_ai_text.count("boss.damage = boss.base_damage") == 1
      and boss_ai_text.count("int(float(boss.base_damage) *") == 1,
      "Only the xerathis arcane pair may keep the verbatim base_damage path")
# Layer 9ao: the one-shot enrage shake payload rides the death-shake gate.
check("var enrage_fx_shake := 0" in boss_state,
      "Boss state must carry the one-shot enrage shake payload")
check(("maxi(18, int(float(attack_cooldown) * 0.75))\n\t\t\tenrage_fx_shake = 25" in boss_state
       and "maxi(20, int(float(attack_cooldown) * 0.80))\n\t\t\tenrage_fx_shake = 15"
       in boss_state),
      "The enrage transitions must store the source 25/15 shake intensities")
_proto_text = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
check("func _present_boss_enrage_shake(boss: BossState) -> void:" in _proto_text
      and "if boss.enrage_fx_shake > 0:\n\t\t_present_boss_enrage_shake(boss)" in _proto_text,
      "The boss step must consume the enrage shake payload")
check("boss.enrage_fx_shake = 0" in _proto_text
      and _proto_text.count("effects.shake_screen(shake)") == 2,
      "The enrage shake must clear one-shot and route like the death shake")
# Layer 9ao-2/9ao-3/9ao-4: ALL boss families wire the complete 126-site cast
# shake table through the BossAI._shake helper (intensity multiset pinned by
# the oracle; `_gorath_r` answers two smart-AI gates so the native file
# carries 127 call sites for the 126 wired source rows).
check("static func _shake(world, intensity: float) -> void:" in boss_ai_text,
      "Boss AI must carry the presentation shake helper")
check(len(re.findall(r"_shake\(world, \d+\)", boss_ai_text)) == 127,
      "The boss families must wire exactly the 126 source cast shake sites")
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
check("_process_boss_kill(boss)" in prototype_battle
      and "boss_death_pause_ticks = maxi(" in prototype_battle
      and "economy.credit_kill(BLUE, boss.gold_reward)" in prototype_battle
      and prototype_battle.index("_process_boss_kill(boss)")
      < prototype_battle.index("boss_death_pause_ticks = maxi(")
      < prototype_battle.index("economy.credit_kill(BLUE, boss.gold_reward)"),
      "Boss kill attribution and pause must precede the source reward pass")
_boss_step = prototype_battle.split("func step_tick()", 1)[1].split("\nfunc ", 1)[0]
check("hit_stop_state.consume_frame()" in _boss_step
      and "if boss_death_pause_ticks > 0:" in _boss_step
      and _boss_step.index("hit_stop_state.consume_frame()")
      < _boss_step.index("if boss_death_pause_ticks > 0:")
      < _boss_step.index("economy.step_tick(wave_count)"),
      "Boss death pause must yield to hit-stop and gate the fixed match tick")
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
check("world._deliver_hit(-1, source_team, tgt, amount, school, origin, damage_type, true)"
      in _miasma_bus,
      "9aa poison bridge is sourceless for non-boss victims and skips the team guard")
check('effects.deal_damage_from(' in _miasma_inventory
      and 'source_id, source_team, source_pos, tgt_id, dmg, "neutral", "magic"' in _miasma_inventory,
      "9aa miasma tick resolves no school and uses the magic damage-type branch")
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
check("if not (tgt is BossState):" in _miasma_kill_bus
      and "if landed:" in _miasma_kill_bus
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
      and 'world._deliver_hit(-1, src_team, u, splash, "neutral", src_pos)' in _cleave_dmg_bus
      and 'world._deliver_hit(dealer_id, src_team, u, splash, "physical", src_pos)'
      not in _cleave_dmg_bus,
      "9q both cleave arms are source-less and school-less")
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
check("attacker is BossState" not in _reflect_bus
      and 'world._deliver_hit(' in _reflect_bus
      and 'amount, "neutral", attacker.position, "magic"' in _reflect_bus
      and _auto_dmg_inv.count("effects.deal_damage(source_id, hero_team, dmg, \"magic\")") == 1,
      "9i/9s the reflect bus sends every attacker the source-less neutral magic hit")
check('const BossItemReflectCarapaceChecks = preload("res://tests/boss_item_reflect_carapace_checks.gd")'
      in ai_tests
      and "BossItemReflectCarapaceChecks.new().run(_check)" in ai_tests,
      "9i production-path reflect replay is registered")

# ── Layer 9ak: stale AI status claims reconciled (docs-only slice) ──
# "AIPlayer penuh" was closed by layers 6a-6f plus ai_match_integration_checks.gd,
# but five documents still carried mid-migration status lines ("belum port",
# "masih pending", "belum aktif"). Those lines were corrected in place with
# explicit markers; these pins keep the stale phrasing from creeping back and
# bind every corrected claim to the code anchor that justifies it.


def _flat(text):
    return re.sub(r"\s+", " ", text)


_ai_contract_doc = _flat((ROOT / "AI_CONTRACT.md").read_text(encoding="utf-8"))
_shield_contract_doc = _flat((ROOT / "SHIELD_CONTRACT.md").read_text(encoding="utf-8"))
_nexus_contract_doc = _flat((ROOT / "NEXUS_CONTRACT.md").read_text(encoding="utf-8"))
_upgrade_contract_doc = _flat((ROOT / "UPGRADE_CONTRACT.md").read_text(encoding="utf-8"))
_hero_progress_doc = _flat((ROOT / "HERO_MIGRATION_PROGRESS.md").read_text(encoding="utf-8"))
_peta_doc = _flat((ROOT / "PETA_SISA_MIGRASI.md").read_text(encoding="utf-8"))

for stale in (
    "Belum port AIPlayer lengkap",
    "Scene pertandingan masih memakai defender lama",
    "masih pending",
    "Policy scheduler dan wiring scene belum aktif",
    "Scene belum memanggil AI shield otomatis",
    "AIPlayer penuh, rebalance dan art final tetap belum selesai",
):
    check(stale not in _ai_contract_doc,
          f"9ak AI_CONTRACT.md must not reclaim the stale status {stale!r}")
check("merekonsiliasi klaim status AI yang stale" in _ai_contract_doc,
      "9ak AI_CONTRACT.md must keep the reconciliation layer record")
check("AIPlayer lengkap sudah diport dan aktif di scene pertandingan" in _ai_contract_doc,
      "9ak AI_CONTRACT.md package status must state the port is complete and wired")

for stale in (
    "Belum ada tombol beli shield atau AI otomatis di scene",
    "kills descending masih pending",
):
    check(stale not in _shield_contract_doc,
          f"9ak SHIELD_CONTRACT.md must not reclaim the stale status {stale!r}")
check("sudah memanggil AI shield otomatis" in _shield_contract_doc
      and "_stable_kills_descending" in _shield_contract_doc,
      "9ak SHIELD_CONTRACT.md must state the automatic shield arms and stable kills order")

check("loop AI otomatis belum aktif" not in _nexus_contract_doc,
      "9ak NEXUS_CONTRACT.md must not reclaim the stale status 'loop AI otomatis belum aktif'")
check("loop AI otomatis aktif" in _nexus_contract_doc
      and "Adapter upgrade red (AIPlayer penuh — selesai)" in _nexus_contract_doc,
      "9ak NEXUS_CONTRACT.md must state the AI loop is active")

check("urutan kandidat dan loop AI scene belum aktif" not in _upgrade_contract_doc
      and "## Adapter AI (WIP)" not in _upgrade_contract_doc,
      "9ak UPGRADE_CONTRACT.md must not reclaim the stale WIP status")
check("loop AI scene aktif" in _upgrade_contract_doc,
      "9ak UPGRADE_CONTRACT.md must state the scene AI loop is active")

check("Pekerjaan berikutnya (di luar migrasi kit): AIPlayer penuh" not in _hero_progress_doc,
      "9ak HERO_MIGRATION_PROGRESS.md copy-paste message must not list AIPlayer penuh as pending")
check("Pembaruan 9ak" in _hero_progress_doc and "AIPlayer penuh SUDAH selesai" in _hero_progress_doc,
      "9ak HERO_MIGRATION_PROGRESS.md must carry the update banner and the corrected message")
check("tabel produksi kosong by decision" not in _hero_progress_doc
      and "Arahan rebalance 2026-10-16 SUDAH terpasang di tabel itu (PR #333)" in _hero_progress_doc,
      "9c-S3 HERO_MIGRATION_PROGRESS.md copy-paste message must not claim the override table is empty")

check("efektif tinggal AIPlayer penuh dan art final. (**Koreksi 9ak:**" in _peta_doc
      and "Rekonsiliasi klaim status AI (layer 9ak, doc-only)" in _peta_doc,
      "9ak PETA_SISA_MIGRASI.md must cross-correct the stale remaining-work line")

# Code anchors: the corrected claims must stay true in the shipped code.
_session = (ROOT / "scripts/simulation/prototype_session.gd").read_text(encoding="utf-8")
_battle = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
_items = (ROOT / "scripts/match/ai_items.gd").read_text(encoding="utf-8")
_shields = (ROOT / "scripts/match/ai_shields.gd").read_text(encoding="utf-8")
_upgrades = (ROOT / "scripts/match/ai_upgrades.gd").read_text(encoding="utf-8")
_match_scene = (ROOT / "scenes/prototype/PrototypeMatch.tscn").read_text(encoding="utf-8")
_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
check("set_ai_enabled(true)" in _session and "reset_ai(AI_MATCH_SEED)" in _session,
      "9ak anchor: the session must still arm the seeded AI from the first tick")
check("ai_controller.tick(" in _battle,
      "9ak anchor: the match must still tick the AI controller every tick")
for arm in ("build", "buy_hero", "upgrade_hero", "buy_item",
            "upgrade_tower", "regen_shield", "castle_shield", "upgrade_nexus"):
    check(f'"{arm}"' in ai_policy,
          f"9ak anchor: ai_policy.gd must keep the source priority arm {arm!r}")
check("draft.reserve()" in _items,
      "9ak anchor: AI item purchases must still read the live draft reserve")
check("draft.reserve()" in _shields and "_stable_kills_descending" in _shields,
      "9ak anchor: AI shields must still read the live reserve and sort kills descending")
check("_stable_kills_descending" in _upgrades
      and "func try_tower_priority" in _upgrades
      and "func try_hero_priority" in _upgrades,
      "9ak anchor: AI upgrades must still expose the stable kills-descending priorities")
check("AIMatchIntegrationChecks.new().run(_check)" in ai_tests,
      "9ak anchor: the full AI integration suite must stay registered in run_all.gd")
check('name="RegenShieldButton"' in _match_scene and 'name="CastleShieldButton"' in _match_scene,
      "9ak anchor: the player shield purchase buttons must stay in the HUD scene")
check("request_regen_shield" in _screen and "request_castle_shield" in _screen,
      "9ak anchor: the shield buttons must stay wired to the session requests")

# ── Layer 9al: level intro gold/passive run the full _core path ──
# `_render.py:3073-3094` calls `_core.compute_starting_gold` /
# `compute_gold_per_second` / `format_gold_rate` so the intro card shows the
# same numbers `Game.reset()` grants. The pre-9al port mirrored only the
# source's except fallbacks while the match ledger already ran the full path,
# so level >1 or non-normal difficulty displayed the wrong gold/passive text.
_intro = (ROOT / "scripts/ui/level_intro_screen.gd").read_text(encoding="utf-8")
_economy = (ROOT / "scripts/match/match_economy.gd").read_text(encoding="utf-8")
check("static func format_gold_rate" in _economy,
      "9al match_economy.gd must port _core.format_gold_rate")
check("Economy.starting_gold(" in _intro
      and "Economy.passive_rate(" in _intro
      and "Economy.format_gold_rate(" in _intro,
      "9al the level intro card must use the shared full _core economy path")
check("MapRenderer.MAP_HEIGHT, difficulty" in _battle,
      "9al the match must configure the intro card with the live difficulty")
_intro_fixture_path = ROOT / "tests/fixtures/level_intro_screen_source.json"
check(_intro_fixture_path.is_file(), "9al level intro fixture must exist")
if _intro_fixture_path.is_file():
    _intro_rows = json.loads(_intro_fixture_path.read_text(encoding="utf-8"))["difficulty_rows"]
    check(len(_intro_rows) == 60,
          "9al level intro fixture must keep 20 levels x 3 difficulties")
    check(all("starting_gold_fallback" in row and "passive_text_fallback" in row
              for row in _intro_rows),
          "9al every difficulty row must carry the pre-9al fallback columns")
    _intro_diverging = sum(
        1 for row in _intro_rows
        if row["starting_gold"] != row["starting_gold_fallback"]
        or row["passive_text"] != row["passive_text_fallback"]
    )
    check(_intro_diverging == 59,
          "9al exactly the level-1 normal row may coincide with the fallback")
    check(all(
        row["passive_text"].startswith("PASSIVE +") and row["passive_text"].endswith("/s")
        for row in _intro_rows
    ), "9al passive text keeps the source format on the full path")


# ── Layer 9aw: complete wave banner and path arrow geometry ──
_wave_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_path_script = (ROOT / "scripts/ui/path_preview.gd").read_text(encoding="utf-8")
_wave_script = (ROOT / "scripts/ui/wave_announcer.gd").read_text(encoding="utf-8")
_wave_fixture = json.loads((ROOT / "tests/fixtures/wave_announcer_source.json").read_text(encoding="utf-8"))
_path_fixture = json.loads((ROOT / "tests/fixtures/path_preview_source.json").read_text(encoding="utf-8"))
check("visual_rect(screen_w: int, screen_h: int)" in _wave_script,
      "9aw wave banner must expose source-derived draw bounds")
check("for row in range(80)" in _wave_view and "_draw_gold_corner_ticks" in _wave_view
      and "E N E M I E S   I N C O M I N G" in _wave_view,
      "9aw WaveAnnouncer must render gradient, gold corner detail, and subtitle")
check("arrow_points(" in _path_script and "draw_colored_polygon(points" in _wave_view,
      "9aw PathPreview must render source-geometry arrow polygons")
check(_wave_fixture.get("visual_sample", {}).get("center_box", [])[2:4] == [400, 80],
      "9aw source fixture must pin the banner's 400x80 visual box")
check(all(len(arrow) >= 4 and len(arrow[3]) == 3
          for sample in _path_fixture.get("samples", []) for arrow in sample.get("arrows", [])),
      "9aw PathPreview oracle must pin all three world-space vertices per arrow")
check("path_preview_source_oracle.py" in workflow and "wave_announcer_source_oracle.py" in workflow,
      "9aw source oracles must remain in CI")

# ── Layer 9ax: AchievementPopup icon primitives ──
_achievement_script = (ROOT / "scripts/ui/achievement_popup.gd").read_text(encoding="utf-8")
_achievement_checks = (ROOT / "tests/achievement_popup_checks.gd").read_text(encoding="utf-8")
_achievement_fixture = json.loads(
    (ROOT / "tests/fixtures/achievement_popup_source.json").read_text(encoding="utf-8")
)
check("func icon_ops(" in _achievement_script and "_draw_achievement_icon(icon_ops)" in _wave_view,
      "9ax achievement icons must be exposed from the port and rendered in PrototypeView")
check("_check_icons(check, popup, data)" in _achievement_checks
      and "AchievementPopupChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"),
      "9ax icon oracle checks must be registered in the native suite")
check(set(_achievement_fixture.get("icons", {})) == {"star", "sword", "skull", "shield", "gold", "unknown"},
      "9ax fixture must pin all five source icons and the unknown-type fallback")
check("achievement_popup_source_oracle.py" in workflow,
      "9ax source icon oracle must remain in CI")

# ── AchievementPopup panel visual presentation ──
_achievement_panel_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_achievement_panel_checks = (ROOT / "tests/achievement_popup_checks.gd").read_text(encoding="utf-8")
_achievement_panel_samples = _achievement_fixture.get("panel_visuals", [])
check("_draw_achievement_outline(rect, 6.0" in _achievement_panel_view
      and "_draw_achievement_ticks(rect" in _achievement_panel_view
      and "_fit_achievement_label" in _achievement_panel_view,
      "Achievement popup panel renderer must keep rounded gold borders, corner ticks, and text clipping")
check("_check_panel_visuals(check, data)" in _achievement_panel_checks
      and "AchievementPopupChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"),
      "Achievement popup panel oracle checks must be registered in the native suite")
check(len(_achievement_panel_samples) == 3
      and all(len(sample.get("ops", [])) >= 79 for sample in _achievement_panel_samples),
      "Achievement popup fixture must pin fade, held, glow, and clipped-text panel draws")
check("achievement_popup_source_oracle.py" in workflow,
      "Achievement popup panel source oracle must remain in CI")

# ── Layer 9ay: HitParticle pre-rendered spark visual ──
_hit_particle_script = (ROOT / "scripts/ui/hit_particle.gd").read_text(encoding="utf-8")
_hit_particle_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_hit_particle_checks = (ROOT / "tests/hit_particle_checks.gd").read_text(encoding="utf-8")
_hit_particle_fixture = json.loads(
    (ROOT / "tests/fixtures/hit_particle_source.json").read_text(encoding="utf-8")
)
_hit_particle_layout = (ROOT / "scripts/ui/hit_particle_layout.gd").read_text(encoding="utf-8")
check("func core_radius()" in _hit_particle_script
      and "HitParticleLayout.ops(" in _hit_particle_view
      and "float(core) * factor" in _hit_particle_layout,
      "9ay HitParticle must render the lifetime-scaled inner sprite circle (9bg: via the layout)")
check('"color": [255, 255, 255, 255]' in _hit_particle_layout
      and "particle.core_radius()" not in _hit_particle_view,
      "9ay HitParticle's white source sprite core must remain visible (9bg: layout op)")
check("_check_sprite(entry, check)" in _hit_particle_checks
      and "HitParticleChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"),
      "9ay source sprite geometry must be checked in the native suite")
check(all(len(case.get("sprite", {}).get("circles", [])) == 2
          for case in _hit_particle_fixture.get("cases", [])),
      "9ay HitParticle oracle must capture both original source sprite circles")
check("hit_particle_source_oracle.py" in workflow,
      "9ay HitParticle source oracle must remain in CI")

# ── FloatingText source draw presentation ──
_floating_script = (ROOT / "scripts/ui/floating_text.gd").read_text(encoding="utf-8")
_floating_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_floating_checks = (ROOT / "tests/floating_text_checks.gd").read_text(encoding="utf-8")
_floating_fixture = json.loads(
    (ROOT / "tests/fixtures/floating_text_source.json").read_text(encoding="utf-8")
)
check("func presentation_state()" in _floating_script
      and "item.presentation_state()" in _floating_view,
      "FloatingText renderer must consume its source-equivalent presentation state")
check('"shadow_center": [int(x) + 1, int(y) + 2]' in _floating_script
      and "draw_string(" in _floating_view
      and "shadow_color" in _floating_view,
      "FloatingText must preserve source shadow offset, font and alpha layers")
check("_visual_matches(item, draw_by_tick[index])" in _floating_checks
      and "FloatingTextChecks.new().run(_check)" in (ROOT / "tests/run_all.gd").read_text(encoding="utf-8"),
      "FloatingText source draw samples must replay in the native suite")
check(all(len(case.get("draw_samples", [])) == 7
          for case in _floating_fixture.get("cases", [])),
      "FloatingText source oracle must pin normal, critical and heal draw samples")
check("floating_text_source_oracle.py" in workflow,
      "FloatingText draw oracle must remain in CI")

# ── Layer 9bb: KillFeed.draw() visuals as a pure op list ──
from kill_feed_draw_source_oracle import source_fixture as kill_feed_draw_fixture
_kill_feed_draw_path = ROOT / "tests/fixtures/kill_feed_draw_source.json"
_kill_feed_layout = (ROOT / "scripts/ui/kill_feed_layout.gd").read_text(encoding="utf-8")
_kill_feed_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_kill_feed_draw_checks = (ROOT / "tests/kill_feed_draw_checks.gd").read_text(encoding="utf-8")
check('const KillFeedDrawChecks = preload("res://tests/kill_feed_draw_checks.gd")' in ai_tests
      and "KillFeedDrawChecks.new().run(_check)" in ai_tests,
      "9bb kill feed draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/kill_feed_draw_source_oracle.py" in workflow,
      "9bb CI must run the KillFeed.draw() source oracle")
check(_kill_feed_draw_path.is_file(), "9bb kill feed draw fixture must exist")
if _kill_feed_draw_path.is_file():
    _kill_feed_draw_frames = json.loads(_kill_feed_draw_path.read_text(encoding="utf-8"))
    check(kill_feed_draw_fixture() == _kill_feed_draw_frames,
          "9bb kill feed draw fixture must not drift from _render.py")
    _kill_feed_frames = _kill_feed_draw_frames["frames"]
    check(len(_kill_feed_frames) == 31
          and sum(len(frame["ops"]) for frame in _kill_feed_frames) == 192
          and all([op["kind"] for op in frame["ops"]]
                  == ["fill", "rect", "text"] * (len(frame["ops"]) // 3)
                  for frame in _kill_feed_frames),
          "9bb oracle must pin 31 frames of fill+border+text triples")
    check(any(frame["phase"] == "pre" and not frame["ops"] and frame["entries"]
              for frame in _kill_feed_frames)
          and {op["mult"] for frame in _kill_feed_frames for op in frame["ops"]
               if op["kind"] == "text"} >= {5, 34, 136, 238, 249, 255},
          "9bb oracle must cover the transparent fresh kill plus fade-in, hold and fade-out")
    check(max(len(frame["entries"]) for frame in _kill_feed_frames) == 5
          and {entry["color"][0] for frame in _kill_feed_frames for entry in frame["entries"]}
          == {100, 255},
          "9bb oracle must cover the 5 entry cap and both team colours")
check("static func fade_alpha(" in _kill_feed_layout
      and "static func slide_x(" in _kill_feed_layout
      and "const BASE_Y := 250" in _kill_feed_layout
      and 'const FONT_STYLE := "body_medium"' in _kill_feed_layout
      and "const BOX_INSET_X := 6" in _kill_feed_layout,
      "9bb kill feed layout must mirror KillFeed.draw()")
check("KillFeedLayout.ops(" in _kill_feed_view
      and "func kill_feed_draw_ops(" in _kill_feed_view
      and "func _draw_kill_feed_op(" in _kill_feed_view
      and "rect.grow(-inset)" in _kill_feed_view,
      "9bb PrototypeView must paint the kill feed from the source op list")
check("Vector2(980.0, y_pos)" not in _kill_feed_view,
      "9bb the invented 14 px right-aligned kill feed text must not return")
check("_check_recorded_frames(check, data, screen)" in _kill_feed_draw_checks
      and "_check_production_replay(check, data, screen)" in _kill_feed_draw_checks
      and "_check_view_wiring(check)" in _kill_feed_draw_checks,
      "9bb kill feed draw suite must replay recorded and production frames plus the view")

# ── Layer 9bc: ComboCounter.draw() visuals as a pure op list ──
from combo_counter_draw_source_oracle import source_fixture as combo_counter_draw_fixture
_combo_draw_path = ROOT / "tests/fixtures/combo_counter_draw_source.json"
_combo_layout = (ROOT / "scripts/ui/combo_counter_layout.gd").read_text(encoding="utf-8")
_combo_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_combo_draw_checks = (ROOT / "tests/combo_counter_draw_checks.gd").read_text(encoding="utf-8")
check('const ComboCounterDrawChecks = preload("res://tests/combo_counter_draw_checks.gd")' in ai_tests
      and "ComboCounterDrawChecks.new().run(_check)" in ai_tests,
      "9bc combo counter draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/combo_counter_draw_source_oracle.py" in workflow,
      "9bc CI must run the ComboCounter.draw() source oracle")
check(_combo_draw_path.is_file(), "9bc combo counter draw fixture must exist")
if _combo_draw_path.is_file():
    _combo_draw = json.loads(_combo_draw_path.read_text(encoding="utf-8"))
    check(combo_counter_draw_fixture() == _combo_draw,
          "9bc combo counter draw fixture must not drift from _render.py")
    _combo_frames = _combo_draw["frames"]
    _combo_texts = [(frame, op) for frame in _combo_frames for op in frame["ops"]
                    if op["kind"] == "text"]
    check(len(_combo_frames) == 52 and sum(len(frame["ops"]) for frame in _combo_frames) == 426,
          "9bc oracle must pin 52 frames and 426 recorded draw ops")
    check({op["text"] for _, op in _combo_texts if op["style"] == "body"}
          == {"KILLING SPREE!", "RAMPAGE!", "UNSTOPPABLE!", "GODLIKE!"},
          "9bc oracle must cover all four tier labels")
    check(any(frame["state"]["count"] == 1 and frame["ops"]
              and all(op["kind"] == "text" for op in frame["ops"]) for frame in _combo_frames)
          and any(frame["state"]["count"] == 0 and any(op["text"] == "x0" for op in frame["ops"]
                                                       if op["kind"] == "text")
                  for frame in _combo_frames),
          "9bc oracle must pin the x1 pop without a bar and the x0 fade-out quirks")
    check(any(frame["label"] == "double_kill" and frame["phase"] == "pre"
              and [op["kind"] for op in frame["ops"]] == ["rect", "rect"]
              for frame in _combo_frames),
          "9bc oracle must pin the timer bar drawn before the sub 8 px count text is skipped")
    check(sum(1 for frame in _combo_frames if not frame["cheap_alpha"]) == 5
          and all(len([op for op in frame["ops"] if op["kind"] == "text"
                       and op["style"] == "body_bold" and op["color"][:3] == [0, 0, 0]])
                  == (8 if frame["cheap_alpha"] else 1)
                  for frame in _combo_frames
                  if any(op["kind"] == "text" for op in frame["ops"])),
          "9bc oracle must pin the 8-way and the single (2, 2) count shadow")
check("static func tier(" in _combo_layout
      and "static func flash_color(" in _combo_layout
      and "const RIGHT_INSET := 100" in _combo_layout
      and "const CENTER_Y := 100" in _combo_layout
      and "const BAR_WIDTH := 80" in _combo_layout
      and 'const COUNT_STYLE := "body_bold"' in _combo_layout,
      "9bc combo counter layout must mirror ComboCounter.draw()")
check("ComboCounterLayout.ops(" in _combo_view
      and "func combo_counter_draw_ops(" in _combo_view,
      "9bc PrototypeView must paint the combo counter from the source op list")
check("HIT COMBO" not in _combo_view,
      "9bc the invented HIT COMBO text must not return")
check("_check_recorded_frames(check, data, screen)" in _combo_draw_checks
      and "_check_production_replay(check, data, screen)" in _combo_draw_checks
      and "_check_view_wiring(check)" in _combo_draw_checks,
      "9bc combo draw suite must replay recorded and production frames plus the view")

# ── Layer 9bd: BossIntroCinematic.draw() visuals as a pure op list ──
from boss_intro_draw_source_oracle import source_fixture as boss_intro_draw_fixture
_boss_draw_path = ROOT / "tests/fixtures/boss_intro_draw_source.json"
_boss_layout = (ROOT / "scripts/ui/boss_intro_layout.gd").read_text(encoding="utf-8")
_boss_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_boss_draw_checks = (ROOT / "tests/boss_intro_draw_checks.gd").read_text(encoding="utf-8")
check('const BossIntroDrawChecks = preload("res://tests/boss_intro_draw_checks.gd")' in ai_tests
      and "BossIntroDrawChecks.new().run(_check)" in ai_tests,
      "9bd boss intro draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/boss_intro_draw_source_oracle.py" in workflow,
      "9bd CI must run the BossIntroCinematic.draw() source oracle")
check(_boss_draw_path.is_file(), "9bd boss intro draw fixture must exist")
if _boss_draw_path.is_file():
    _boss_draw = json.loads(_boss_draw_path.read_text(encoding="utf-8"))
    check(boss_intro_draw_fixture() == _boss_draw,
          "9bd boss intro draw fixture must not drift from _render.py")
    _boss_frames = _boss_draw["frames"]
    _boss_drawn = [frame for frame in _boss_frames if frame["ops"]]
    check(len(_boss_frames) == 22 and sum(len(frame["ops"]) for frame in _boss_frames) == 279,
          "9bd oracle must pin 22 frames and 279 recorded draw ops")
    check(all(len([op for op in frame["ops"] if op["kind"] == "line"])
              == (8 if frame["ops"][1]["color"][3] > 60 else 0) for frame in _boss_drawn),
          "9bd oracle must pin the eight gold corner ticks only above alpha 60")
    check(all(frame["ops"][-1]["color"] == [255, 255, 255, 255] and frame["ops"][-1]["width"] == 1
              and frame["ops"][-1]["radius"] == 5 and frame["ops"][-1]["mult"] == 255
              for frame in _boss_drawn)
          and any(frame["ops"][0]["color"][3] == 0 and frame["ops"][-1]["color"][3] == 255
                  for frame in _boss_drawn),
          "9bd oracle must pin the HP bar staying opaque while the banner fades")
    check(any(not frame["state"]["active"] and frame["ops"] == [] for frame in _boss_frames)
          and any(frame["label"] == "narrow" and frame["ops"][0]["rect"][2] == 440
                  for frame in _boss_drawn),
          "9bd oracle must pin the finished intro and the narrow-screen banner clamp")
    _boss_texts = [op for frame in _boss_drawn for op in frame["ops"] if op["kind"] == "text"]
    check({op["text"] for op in _boss_texts} >= {"TRUE BOSS", "MINI BOSS"}
          and any(op["style"] == "title" and op["size"] == 46 for op in _boss_texts)
          and any(op["text"].startswith('"') and op["text"].endswith('"') for op in _boss_texts),
          "9bd oracle must pin both tags, the 46 px title-font name and the quoted title")
check("static func ops(" in _boss_layout
      and "const TICK_MIN_ALPHA := 60" in _boss_layout
      and "const BANNER_RADIUS := 10" in _boss_layout
      and 'const NAME_STYLE := "title"' in _boss_layout
      and "func _corner_ticks(" in _boss_layout,
      "9bd boss intro layout must mirror BossIntroCinematic.draw()")
check("BossIntroLayout.ops(" in _boss_view
      and "func boss_intro_draw_ops(" in _boss_view
      and "func _draw_banner_op(" in _boss_view,
      "9bd PrototypeView must paint the boss intro from the source op list")
check("%s · %s" not in _boss_view,
      "9bd the invented TAG - NAME header must not return")
check("_check_recorded_frames(check, data)" in _boss_draw_checks
      and "_check_production_replay(check, data)" in _boss_draw_checks
      and "_check_quirks(check, data)" in _boss_draw_checks
      and "_check_view_wiring(check, data)" in _boss_draw_checks,
      "9bd boss intro draw suite must replay recorded and production frames plus the view")

# ── Layer 9be: BossDeathAnimation._draw_celebration() visuals as a pure op list ──
from boss_celebration_draw_source_oracle import source_fixture as boss_celebration_fixture
_cele_path = ROOT / "tests/fixtures/boss_celebration_draw_source.json"
_cele_layout = (ROOT / "scripts/ui/boss_celebration_layout.gd").read_text(encoding="utf-8")
_cele_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_cele_checks = (ROOT / "tests/boss_celebration_draw_checks.gd").read_text(encoding="utf-8")
check('const BossCelebrationDrawChecks = preload("res://tests/boss_celebration_draw_checks.gd")'
      in ai_tests and "BossCelebrationDrawChecks.new().run(_check)" in ai_tests,
      "9be boss celebration draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/boss_celebration_draw_source_oracle.py" in workflow,
      "9be CI must run the BossDeathAnimation._draw_celebration() source oracle")
check(_cele_path.is_file(), "9be boss celebration draw fixture must exist")
if _cele_path.is_file():
    _cele = json.loads(_cele_path.read_text(encoding="utf-8"))
    check(boss_celebration_fixture() == _cele,
          "9be boss celebration draw fixture must not drift from _render.py")
    _cele_frames = _cele["frames"]
    check(len(_cele_frames) == 20 and sum(len(frame["ops"]) for frame in _cele_frames) == 547,
          "9be oracle must pin 20 frames and 547 recorded draw ops")

    def _cele_texts(frame, text):
        return [op for op in frame["ops"] if op["kind"] == "text" and op["text"] == text]

    check(all(len(_cele_texts(frame, "BOSS DEFEATED!")) == (7 if frame["cheap_alpha"] else 2)
              and _cele_texts(frame, "BOSS DEFEATED!")[-1]["color"] == [255, 220, 100, 255]
              and _cele_texts(frame, "BOSS DEFEATED!")[-1]["size"] == 66
              and _cele_texts(frame, "BOSS DEFEATED!")[-1]["style"] == "title"
              for frame in _cele_frames),
          "9be oracle must pin the 66 px gold title with six shadows (one without cheap_alpha)")
    _cele_abaddon = {frame["tick"]: frame for frame in _cele_frames
                     if frame["label"] == "abaddon"}
    check(all(any(op["kind"] == "fill" and op["color"] == [80, 60, 20, 40]
                  for op in frame["ops"]) == (tick < 102)
              for tick, frame in _cele_abaddon.items())
          and all(any(op["kind"] == "darken" for op in frame["ops"]) == (tick > 0)
                  and (tick == 0 or frame["ops"][0]["alpha"] <= 180)
                  for tick, frame in _cele_abaddon.items()),
          "9be oracle must pin the gold tint ending at 85 % and the darken fade")
    check(all(bool(_cele_texts(frame, "+ 1500 GOLD")) == (tick >= 37)
              and bool(_cele_texts(frame, "H E R O   U N L O C K E D !")) == (tick >= 37)
              and (sum(op["kind"] == "circle" for op in frame["ops"]) == (16 if tick >= 49
                   else 4 if tick >= 37 else 0))
              and bool(_cele_texts(frame, "[SPACE] to continue")) == (tick >= 61)
              for tick, frame in _cele_abaddon.items() if tick != 40),
          "9be oracle must pin reward after 30 %, sparkles after 40 %, hint after 50 %")
    check(all(sum(op["kind"] == "line" for op in frame["ops"]) == 8
              for tick, frame in _cele_abaddon.items() if tick >= 37)
          and any(op["kind"] == "circle" and op["radius"] == 1.5
                  for frame in _cele_frames for op in frame["ops"]),
          "9be oracle must pin the two four-line vector stars with 1.5 px centres")
    check(_cele_texts(_cele_abaddon[49], '"Lord of Avernus"')[0]["size"] == 32
          and _cele_texts(_cele_abaddon[49], "Abaddon")[-1]["color"] == [100, 220, 240, 255]
          and _cele_texts(_cele_abaddon[49], "Abaddon")[0]["color"] == [0, 0, 0, 255]
          and any(frame["label"] == "alchemist_small" and frame["ops"][1]["rect"] == [0, 0, 960, 540]
                  for frame in _cele_frames),
          "9be oracle must pin the boss name in its entrance colour, the quoted title and a small screen")
check("static func ops(" in _cele_layout
      and "const TINT_RGBA := [80, 60, 20, 40]" in _cele_layout
      and "func _headline(" in _cele_layout
      and "func _star(" in _cele_layout
      and "func _sparkles(" in _cele_layout
      and "LevelIntro.letter(" in _cele_layout,
      "9be boss celebration layout must mirror _draw_celebration()")
check("BossCelebrationLayout.ops(" in _cele_view
      and "func boss_celebration_draw_ops(" in _cele_view,
      "9be PrototypeView must paint the celebration from the source op list")
check("%s DEFEATED!" not in _cele_view and "GOLD REWARD" not in _cele_view
      and "PRESS SPACE OR ESC" not in _cele_view,
      "9be the invented celebration text must not return")
check("_check_recorded_frames(check, data)" in _cele_checks
      and "_check_production_replay(check, data)" in _cele_checks
      and "_check_stages(check, data)" in _cele_checks
      and "_check_view_wiring(check, data)" in _cele_checks,
      "9be celebration draw suite must replay recorded and production frames plus the view")

# ── Layer 9bf: BossDeathAnimation._draw_death_sequence() visuals as a pure op list ──
from boss_death_sequence_draw_source_oracle import source_fixture as boss_death_sequence_fixture
_seq_path = ROOT / "tests/fixtures/boss_death_sequence_draw_source.json"
_seq_layout = (ROOT / "scripts/ui/boss_death_sequence_layout.gd").read_text(encoding="utf-8")
_seq_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_seq_checks = (ROOT / "tests/boss_death_sequence_draw_checks.gd").read_text(encoding="utf-8")
_seq_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
check('const BossDeathSequenceDrawChecks = preload("res://tests/boss_death_sequence_draw_checks.gd")'
      in ai_tests and "BossDeathSequenceDrawChecks.new().run(_check)" in ai_tests,
      "9bf boss death sequence draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/boss_death_sequence_draw_source_oracle.py" in workflow,
      "9bf CI must run the BossDeathAnimation._draw_death_sequence() source oracle")
check(_seq_path.is_file(), "9bf boss death sequence draw fixture must exist")
if _seq_path.is_file():
    _seq = json.loads(_seq_path.read_text(encoding="utf-8"))
    check(boss_death_sequence_fixture() == _seq,
          "9bf boss death sequence draw fixture must not drift from _render.py")
    _seq_frames = _seq["frames"]
    check(len(_seq_frames) == 12 and sum(len(frame["ops"]) for frame in _seq_frames) == 2299,
          "9bf oracle must pin 12 frames and 2299 recorded draw ops")
    check(all((frame["ops"][0]["kind"] == "flash") == (frame["tick"] < 15)
              and (frame["tick"] >= 15
                   or frame["ops"][0]["alpha"] == int(200 * (1 - frame["tick"] / 15)))
              for frame in _seq_frames),
          "9bf oracle must pin the additive flash fading over the first 15 ticks")
    _seq_rings = [op for frame in _seq_frames for op in frame["ops"]
                  if op["kind"] == "circle" and op["width"] == 3]
    check(_seq_rings and all(op["center"] == [642, 362] for op in _seq_rings),
          "9bf oracle must pin the waves sitting 2 px off the boss")
    _seq_shards = {(frame["label"], frame["tick"]): sum(op["kind"] == "polygon"
                                                         for op in frame["ops"])
                   for frame in _seq_frames}
    check(all(_seq_shards[("abaddon_true", tick)] == 50 for tick in (0, 7, 15, 25, 44, 45, 57))
          and _seq_shards[("abaddon_true", 60)] == 0 and _seq_shards[("abaddon_true", 89)] == 0
          and _seq_shards[("drakar_mini", 2)] == 30 and _seq_shards[("drakar_mini", 30)] == 30
          and _seq_shards[("drakar_mini", 58)] == 0,
          "9bf oracle must pin 25 / 15 fragments (fill + edge) until their alpha drops below 10")
    check(all(sum(op["kind"] == "polygon" and op["width"] == 1 for op in frame["ops"])
              == sum(op["kind"] == "polygon" and op["width"] == 0 for op in frame["ops"])
              for frame in _seq_frames),
          "9bf oracle must pin one 1 px edge polygon per filled fragment")
    check(any(op["kind"] == "circle" and op["width"] == 0 and op["radius"] == 1
              and op["color"][:3] == [255, 255, 255]
              for frame in _seq_frames for op in frame["ops"])
          and any(op["kind"] == "circle" and op["width"] == 0 and op["color"][3] == 0
                  for frame in _seq_frames for op in frame["ops"]),
          "9bf oracle must pin the white 1 px core and the alpha-0 outer glow disc")
    check(all(len(_seq["scenarios"][i]["fragments"]) == (25, 15)[i]
              and len(_seq["scenarios"][i]["rising"]) == (30, 15)[i] for i in range(2)),
          "9bf oracle must store the seeded fragment / rising particle replay specs")
check("static func ops(" in _seq_layout
      and "const RING_WIDTH := 3" in _seq_layout
      and "func _wave(" in _seq_layout
      and "func _fragment(" in _seq_layout
      and "func _rising(" in _seq_layout
      and '"covered"' in _seq_layout and '"ring_inner"' in _seq_layout,
      "9bf boss death sequence layout must mirror _draw_death_sequence()")
check("BossDeathSequenceLayout.ops(" in _seq_view
      and "func boss_death_draw_ops(" in _seq_view
      and "func _draw_death_op(" in _seq_view
      and "func _draw_polygon_edge(" in _seq_view
      and "func _draw_boss_death_animation(" in _seq_view
      and "_draw_boss_death_sequence(" not in _seq_view,
      "9bf PrototypeView must paint the death sequence from the source op list")
check('"boss_death":\n\t\t\t_draw_boss_death_animation(world)' in _seq_view
      and _seq_core.index("self.level_intro.draw(self.screen)")
      < _seq_core.index("self.boss_death.draw(self.screen)"),
      "9bf boss_death.draw() runs after the level intro in the source; the view dispatches it "
      "as the last overlay (order pinned by 9bi)")
check("_check_production_replay(check, data)" in _seq_checks
      and "_check_stages(check, data)" in _seq_checks
      and "_check_overwrite_hints(check, data)" in _seq_checks
      and "_check_view_wiring(check, data)" in _seq_checks,
      "9bf death sequence draw suite must replay production frames plus the view")

# ── Layer 9bg: DeathExplosion.draw() + HitParticle.draw() visuals as pure op lists ──
from death_explosion_draw_source_oracle import source_fixture as death_explosion_draw_fixture
_burst_path = ROOT / "tests/fixtures/death_explosion_draw_source.json"
_burst_layout = (ROOT / "scripts/ui/death_explosion_layout.gd").read_text(encoding="utf-8")
_spark_layout = (ROOT / "scripts/ui/hit_particle_layout.gd").read_text(encoding="utf-8")
_burst_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_burst_checks = (ROOT / "tests/death_explosion_draw_checks.gd").read_text(encoding="utf-8")
check('const DeathExplosionDrawChecks = preload("res://tests/death_explosion_draw_checks.gd")'
      in ai_tests and "DeathExplosionDrawChecks.new().run(_check)" in ai_tests,
      "9bg death explosion draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/death_explosion_draw_source_oracle.py" in workflow,
      "9bg CI must run the DeathExplosion.draw() / HitParticle.draw() source oracle")
check(_burst_path.is_file(), "9bg death explosion draw fixture must exist")
if _burst_path.is_file():
    _burst = json.loads(_burst_path.read_text(encoding="utf-8"))
    check(death_explosion_draw_fixture() == _burst,
          "9bg death explosion draw fixture must not drift from _render.py")
    _burst_frames = _burst["frames"]
    check(len(_burst_frames) == 25 and sum(len(frame["ops"]) for frame in _burst_frames) == 582,
          "9bg oracle must pin 25 frames and 582 recorded draw ops")
    _burst_flashes = [frame for frame in _burst_frames
                      if frame["label"] != "sparks" and frame["state"]["flash_timer"] > 0]
    check(len(_burst_flashes) == 10
          and all(frame["ops"][0]["color"]
                  == [255, 255, 200, int(200 * frame["state"]["flash_timer"] / 8)]
                  and frame["ops"][0]["radius"] == int(20 * frame["state"]["flash_timer"] / 8)
                  and frame["ops"][1]["color"]
                  == [255, 255, 255, int(255 * frame["state"]["flash_timer"] / 8)]
                  and frame["ops"][1]["radius"] == frame["ops"][0]["radius"] // 2
                  for frame in _burst_flashes),
          "9bg oracle must pin the two flash discs shrinking and fading over 8 ticks")
    check(all(frame["ops"][0]["center"] == [int(scenario["x"]), int(scenario["y"])]
              for frame in _burst_flashes for scenario in _burst["scenarios"]
              if scenario["label"] == frame["label"]),
          "9bg oracle must pin the int() anchor of the flash (fractional x / y truncated)")
    _burst_sparks = [op for frame in _burst_frames
                     for op in frame["ops"][(2 if frame in _burst_flashes else 0):]]
    check(len(_burst_sparks) % 2 == 0
          and all(_burst_sparks[i]["center"] == _burst_sparks[i + 1]["center"]
                  and _burst_sparks[i + 1]["color"] == [255, 255, 255, 255]
                  and _burst_sparks[i]["mult"] == _burst_sparks[i + 1]["mult"]
                  for i in range(0, len(_burst_sparks), 2)),
          "9bg oracle must pin each spark as a colour disc plus a white core at one anchor")
    check(any(isinstance(op["center"][0], float) and op["radius"] < 1
              for frame in _burst_frames if frame["label"] == "sparks" for op in frame["ops"]),
          "9bg oracle must pin a scaled sprite (fractional centre, sub-pixel core)")
    check(_burst["scenarios"][3]["kind"] == "sparks"
          and sum(frame["state"].get("alive", [True]).count(False) for frame in _burst_frames
                  if frame["label"] == "sparks") == 1
          and len(_burst["scenarios"][0]["particles"]) == 8
          and len(_burst["scenarios"][1]["particles"]) == 15
          and len(_burst["scenarios"][2]["particles"]) == 25,
          "9bg oracle must store the seeded spark specs (8 / 15 / 25) and a dead standalone spark")
check("static func ops(" in _burst_layout
      and "HitParticleLayout.ops(" in _burst_layout
      and "const FLASH_PEAK_ALPHA := 200.0" in _burst_layout
      and '"ring_inner"' in _burst_layout
      and "static func ops(" in _spark_layout
      and "float(half) * factor" in _spark_layout
      and '"covered": core >= base' in _spark_layout,
      "9bg explosion and spark layouts must mirror DeathExplosion.draw() / HitParticle.draw()")
check("DeathExplosionLayout.ops(" in _burst_view
      and "HitParticleLayout.ops(" in _burst_view
      and "func death_explosion_draw_ops(" in _burst_view
      and "func hit_particle_draw_ops(" in _burst_view
      and "f_intensity" not in _burst_view and "spark.current_size()" not in _burst_view,
      "9bg PrototypeView must paint explosions and sparks from the source op lists")
check("_check_production_replay(check, data)" in _burst_checks
      and "_check_flash(check, data)" in _burst_checks
      and "_check_sparks(check, data)" in _burst_checks
      and "_check_view_wiring(check, data)" in _burst_checks,
      "9bg death explosion draw suite must replay production frames plus the view")

# ── Layer 9bh: MapRenderer.draw() ambient tint as a pure op list ──
from map_tint_draw_source_oracle import source_fixture as map_tint_draw_fixture
_tint_path = ROOT / "tests/fixtures/map_tint_draw_source.json"
_tint_layout = (ROOT / "scripts/ui/map_tint_layout.gd").read_text(encoding="utf-8")
_tint_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_tint_base = (ROOT / "scenes/combat/minion_view.gd").read_text(encoding="utf-8")
_tint_checks = (ROOT / "tests/map_tint_draw_checks.gd").read_text(encoding="utf-8")
_tint_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
check('const MapTintDrawChecks = preload("res://tests/map_tint_draw_checks.gd")' in ai_tests
      and "MapTintDrawChecks.new().run(_check)" in ai_tests,
      "9bh map tint draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/map_tint_draw_source_oracle.py" in workflow,
      "9bh CI must run the MapRenderer.draw() ambient tint source oracle")
check(_tint_path.is_file(), "9bh map tint draw fixture must exist")
if _tint_path.is_file():
    _tint = json.loads(_tint_path.read_text(encoding="utf-8"))
    check(map_tint_draw_fixture() == _tint,
          "9bh map tint draw fixture must not drift from _render.py / map_components")
    check(len(_tint["tints"]) == 54 and len(_tint["frames"]) == 108
          and sum(len(frame["ops"]) for frame in _tint["frames"]) == 106,
          "9bh oracle must pin 54 themes, 108 frames and 106 recorded draw ops")
    _tint_rows = {name: None if value == "null" else json.loads(value)
                  for name, value in re.findall(r'^\t"(\w+)": (null|\[[^\]]*\]),$',
                                                _tint_layout, re.M)}
    check(_tint_rows == _tint["tints"],
          "9bh map_tint_layout.gd TINTS must equal the source theme tints")
    check(_tint["tints"]["forest"] is None
          and sum(value is not None for value in _tint["tints"].values()) == 53
          and all(len(value) == 4 for value in _tint["tints"].values() if value is not None),
          "9bh oracle must pin forest without tint and 53 RGBA theme tints")
    check(all(frame["ops"] == [] for frame in _tint["frames"] if _tint["tints"][frame["theme"]] is None)
          and all(frame["ops"] == [{"kind": "fill", "rect": [0, 0, 1280, 720],
                                    "color": _tint["tints"][frame["theme"]], "mult": 255,
                                    "blend": 0}]
                  for frame in _tint["frames"]
                  if frame["cheap_alpha"] and _tint["tints"][frame["theme"]] is not None),
          "9bh oracle must pin the screen-sized alpha blit of the theme tint")
    check(all(len(frame["ops"]) == 1 and frame["ops"][0]["blend"] == 3
              and frame["ops"][0]["color"][3] == 255
              and all(a >= b for a, b in zip([255, 255, 255],
                                              frame["ops"][0]["color"][:3]))
              for frame in _tint["frames"]
              if not frame["cheap_alpha"] and _tint["tints"][frame["theme"]] is not None),
          "9bh oracle must pin the BLEND_RGB_MULT path of the non-cheap tint")
check("static func ops(" in _tint_layout
      and "static func tint_for(" in _tint_layout
      and "const BLEND_RGB_MULT := 3" in _tint_layout
      and "const TINTS := {" in _tint_layout,
      "9bh map tint layout must mirror MapRenderer.draw()'s tint step")
check("MapTintLayout.ops(" in _tint_view
      and "func map_tint_draw_ops(" in _tint_view
      and "func _draw_map_overlay(" in _tint_view
      and "func _draw_map_overlay(" in _tint_base
      and _tint_base.index("draw_texture(wall_texture")
      < _tint_base.index("_draw_map_overlay()")
      < _tint_base.index("_draw_base(Layout.BLUE_BASE"),
      "9bh the tint must be painted right after the map layers and before the units")
check(_tint_core.index("self.map_renderer.draw(draw_target") < _tint_core.index("h.draw(draw_target)"),
      "9bh the source draws the map (and its tint) before the heroes")
check("_check_table(check, data)" in _tint_checks
      and "_check_frames(check, data)" in _tint_checks
      and "_check_quirks(check, data)" in _tint_checks
      and "_check_view_wiring(check)" in _tint_checks,
      "9bh map tint draw suite must replay every theme frame plus the view")

# ── Layer 9bi: paint order of the world layers and screen overlays ──
from draw_order_source_oracle import source_fixture as draw_order_fixture
_order_path = ROOT / "tests/fixtures/draw_order_source.json"
_order_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_order_checks = (ROOT / "tests/draw_order_checks.gd").read_text(encoding="utf-8")
check('const DrawOrderChecks = preload("res://tests/draw_order_checks.gd")' in ai_tests
      and "DrawOrderChecks.new().run(_check)" in ai_tests,
      "9bi draw order suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/draw_order_source_oracle.py" in workflow,
      "9bi CI must run the draw order source oracle")
check(_order_path.is_file(), "9bi draw order fixture must exist")
if _order_path.is_file():
    _order = json.loads(_order_path.read_text(encoding="utf-8"))
    check(draw_order_fixture() == _order, "9bi draw order fixture must not drift from the source")
    check(_order["game_draw"] == ["map", "effects", "tactical_world", "boss_intro", "effects_ui",
                                  "level_intro", "boss_death"]
          and _order["effects_draw"] == ["path_preview", "explosions", "particles",
                                         "floating_texts"]
          and _order["effects_draw_ui"] == ["wave_announcer", "achievement"],
          "9bi oracle must pin Game.draw and EffectManager.draw / draw_ui order")
    _order_live = ["boss_intro", *_order["effects_draw_ui"], "level_intro", "boss_death"]
    _order_block = re.search(r"const OVERLAY_ORDER := \[(.*?)\]", _order_view, re.S)
    _order_view_layers = re.findall(r'"(\w+)"', _order_block.group(1)) if _order_block else []
    check([name for name in _order_view_layers if name in _order_live] == _order_live
          and _order_view_layers[-1] == "boss_death"
          and _order_view_layers.index("boss_intro") < _order_view_layers.index("wave_announcer"),
          "9bi OVERLAY_ORDER must follow the source stack (banner < announcer < achievement < "
          "level intro < boss death)")
    check(re.search(r'const WORLD_LAYER_ORDER := \["path_preview", "effects", "tactical"\]',
                    _order_view) is not None,
          "9bi WORLD_LAYER_ORDER must be path preview, effects, then tactical world")
_order_effects = _order_view[_order_view.index("func _draw_world_effects("):]
check(_order_effects.index("DeathExplosionLayout.ops(")
      < _order_effects.index("HitParticleLayout.ops(")
      < _order_effects.index("world.effects.floating_texts"),
      "9bi world effects must paint explosions, particles, then floating texts")
check("for layer in OVERLAY_ORDER:" in _order_view
      and "for layer in WORLD_LAYER_ORDER:" in _order_view
      and "func _draw_overlay_layer(" in _order_view
      and "func _draw_world_layer(" in _order_view
      and "func overlay_paint_order(" in _order_view
      and "func world_layer_order(" in _order_view
      and "\t_draw_wave_announcer(world)\n\t_draw_combo_counter(world)\n" not in _order_view,
      "9bi PrototypeView must paint from the order constants, not a fixed call list")
check("_check_overlays(check, data, view.overlay_paint_order())" in _order_checks
      and "_check_world(check, data, view.world_layer_order())" in _order_checks,
      "9bi draw order suite must read the view's order back")

# ── Layer 9bj: baked map decorations + shop buildings (bake/bake_map_overlay.py) ──
import hashlib
import math
import struct

_art_manifest_path = ROOT / "data/art/map_overlay.json"
_art_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_art_base = (ROOT / "scenes/combat/minion_view.gd").read_text(encoding="utf-8")
_art_loader = (ROOT / "scripts/ui/map_art.gd").read_text(encoding="utf-8")
_art_checks = (ROOT / "tests/map_art_checks.gd").read_text(encoding="utf-8")
_art_render = (ROOT.parent / "_render.py").read_text(encoding="utf-8")
_art_bake = (ROOT / "bake/bake_map_overlay.py").read_text(encoding="utf-8")
_art_env = (ROOT / "bake/pygame_env.py").read_text(encoding="utf-8")
check('const MapArtChecks = preload("res://tests/map_art_checks.gd")' in ai_tests
      and "MapArtChecks.new().run(_check)" in ai_tests,
      "9bj map art suite must be preloaded and run in the native suite")
check(_art_manifest_path.is_file(), "9bj map overlay manifest must exist")
if _art_manifest_path.is_file():
    _art = json.loads(_art_manifest_path.read_text(encoding="utf-8"))
    _art_palette = json.loads((ROOT / "data/levels/theme_palette.json").read_text(encoding="utf-8"))
    _art_levels = {
        json.loads(path.read_text(encoding="utf-8")).get("map_theme")
        for path in (ROOT / "data/levels").glob("level_*.json")
    }
    check(sorted(_art["themes"]) == sorted(_art_palette) and len(_art["themes"]) == 54,
          "9bj one overlay per palette theme (54)")
    check(_art_levels <= set(_art["themes"]) and len(_art_levels) == 54,
          "9bj every level's map_theme must have a baked overlay")
    check(_art["generator"] == "godot_rebuild/bake/bake_map_overlay.py"
          and "layers 4-5" in _art["layers"],
          "9bj manifest must name its generator and the source layers")
    for _theme, _entry in sorted(_art["themes"].items()):
        _png = ROOT / "assets/art/map" / f"{_theme}.png"
        check(_png.is_file(), f"9bj overlay PNG must ship: {_theme}")
        if not _png.is_file():
            continue
        _raw = _png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _entry["size"] == [1280, 720]
              and (_depth, _color) == (8, 6),
              f"9bj overlay must be a 1280x720 RGBA8 PNG: {_theme}")
        check(len(_raw) == _entry["bytes"] and hashlib.sha256(_raw).hexdigest() == _entry["sha256"],
              f"9bj overlay must match its manifest hash: {_theme}")
        check(_entry["covered_pixels"] >= 10000, f"9bj overlay must hold real decorations: {_theme}")
check(_art_render.index("DecorationRenderer.draw_all(surf, self)")
      < _art_render.index("ShopRenderer.draw(surf, self.radiant_shop_pos")
      < _art_render.index("StaticRenderer.draw_border_wall(surf"),
      "9bj the source paints decorations, then shops, then the border wall")
check("DecorationRenderer.draw_all(full, mr)" in _art_bake
      and "ShopRenderer.draw(full, mr.radiant_shop_pos, mr.dire_shop_pos)" in _art_bake
      and "assert (composite == full_rgb).all()" in _art_bake,
      "9bj the bake must run source layers 4-5 and prove overlay + base == source")
check("storage_paths._PROJECT_ROOT = tempfile.mkdtemp" in _art_env,
      "9bj bake scripts must keep the game's save folder out of the repo")
check("MapArt.overlay_texture(cached_river_theme)" in _art_view
      and "func _draw_map_decor(" in _art_view and "func _draw_map_decor(" in _art_base
      and _art_base.index("draw_texture(lane_texture") < _art_base.index("_draw_map_decor()")
      < _art_base.index("draw_texture(wall_texture"),
      "9bj the view must paint the overlay after the lanes and before the border wall")
check("ResourceLoader.exists(overlay_path(theme))" in _art_loader
      and "static func overlay_texture(" in _art_loader,
      "9bj the loader must tolerate a theme that is not imported")
check("_check_files(check, manifest)" in _art_checks
      and "_check_textures(check)" in _art_checks
      and "_check_view_wiring(check)" in _art_checks,
      "9bj map art suite must check files, loaded textures and the view wiring")

# ── Layer 9bj2: baked map base (layers 1-3) + border wall (bake/bake_map_base.py) ──
_mb_manifest_path = ROOT / "data/art/map_base.json"
_mb_bake = (ROOT / "bake/bake_map_base.py").read_text(encoding="utf-8")
_mb_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_mb_base = (ROOT / "scenes/combat/minion_view.gd").read_text(encoding="utf-8")
_mb_loader = (ROOT / "scripts/ui/map_art.gd").read_text(encoding="utf-8")
_mb_checks = (ROOT / "tests/map_art_checks.gd").read_text(encoding="utf-8")
check(_mb_manifest_path.is_file() and _art_manifest_path.is_file(), "9bj2 map base manifest must exist")
if _mb_manifest_path.is_file() and _art_manifest_path.is_file():
    _mb = json.loads(_mb_manifest_path.read_text(encoding="utf-8"))
    _mb_overlay = json.loads(_art_manifest_path.read_text(encoding="utf-8"))
    check(sorted(_mb["themes"]) == sorted(_mb_overlay["themes"]) and len(_mb["themes"]) == 54,
          "9bj2 one baked base per overlay theme (54)")
    check(_mb["generator"] == "godot_rebuild/bake/bake_map_base.py"
          and "layers 1-3" in _mb["layers"] and "6 (border wall)" in _mb["layers"]
          and _mb["seed"] == "{theme}:base",
          "9bj2 manifest must name its generator, the source layers and the overlay seed")
    _mb_files = [(f"{_theme}.png", _entry) for _theme, _entry in sorted(_mb["themes"].items())]
    _mb_files.append(("border_wall.png", _mb["wall"]))
    for _name, _entry in _mb_files:
        _png = ROOT / "assets/art/map_base" / _name
        check(_png.is_file(), f"9bj2 PNG must ship: {_name}")
        if not _png.is_file():
            continue
        _raw = _png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _entry["size"] == [1280, 720]
              and (_depth, _color) == (8, 6),
              f"9bj2 PNG must be a 1280x720 RGBA8 image: {_name}")
        check(len(_raw) == _entry["bytes"] and hashlib.sha256(_raw).hexdigest() == _entry["sha256"],
              f"9bj2 PNG must match its manifest hash: {_name}")
    check(all(len(_entry.get("probes", [])) == 7 for _entry in _mb["themes"].values()),
          "9bj2 every base must pin its probe pixels")
    check(_mb["wall"].get("covered_pixels", 0) > 50000, "9bj2 the border wall must hold real wall pixels")
check('random.seed(f"{renderer.theme_name}:base")' in _mb_bake
      and 'random.seed(f"{theme_name}:base")' in _art_bake
      and 'random.seed(f"{name}:decorations")' in _mb_bake
      and 'random.seed(f"{theme_name}:decorations")' in _art_bake
      and 'random.seed(f"{name}:shops")' in _mb_bake
      and 'random.seed(f"{theme_name}:shops")' in _art_bake,
      "9bj2 the base bake must seed every layer exactly like the overlay bake")
check("assert (composite == full_rgb).all()" in _mb_bake
      and "StaticRenderer.draw_border_wall(full, " in _mb_bake
      and "assert (theme_wall == wall).all()" in _mb_bake,
      "9bj2 the bake must prove base + overlay + wall == the source static map")
check(_art_render.index("StaticRenderer.draw_terrain(surf") < _art_render.index("StaticRenderer.draw_river(surf")
      < _art_render.index("StaticRenderer.draw_lane(surf")
      < _art_render.index("DecorationRenderer.draw_all(surf, self)"),
      "9bj2 the source paints terrain, river and lanes before the decorations")
check("func cache_static_map(map_theme: String)" in _mb_view
      and "MapArt.base_texture(map_theme)" in _mb_view and "MapArt.wall_texture()" in _mb_view
      and "if cached_river_theme != map_theme:\n\t\tcache_static_map(map_theme)" in _mb_view
      and "TerrainTiles.raster(terrain_palette)" in _mb_view,
      "9bj2 the view must cache the baked base and wall, with the native rasters as fallback")
check("var baked_static_base := false" in _mb_base
      and _mb_base.index("if not baked_static_base:") < _mb_base.index("draw_texture(river_texture")
      < _mb_base.index("draw_texture(lane_texture") < _mb_base.index("_draw_map_decor()"),
      "9bj2 the baked base must skip the native river and lanes, under the decor")
check("ResourceLoader.exists(base_path(theme))" in _mb_loader
      and "ResourceLoader.exists(wall_path())" in _mb_loader,
      "9bj2 the loader must tolerate a base or wall that is not imported")
check(all(f"_check_base_{_part}(check)" in _mb_checks for _part in ("manifest", "files", "textures", "view")),
      "9bj2 map art suite must check the base manifest, files, textures and the view")
check('"Selected map paints the baked source terrain, river and lanes"' in ai_tests,
      "9bj2 the scene suite must prove the live arena paints the baked base")

# ── Layer 9d0: native DynamicRenderer + source state/op oracle ──
_dyn_manifest_path = ROOT / "data/art/map_dynamic.json"
_dyn_fixture_path = ROOT / "tests/fixtures/dynamic_renderer_source.json"
_dyn_state = (ROOT / "scripts/ui/dynamic_map_renderer.gd").read_text(encoding="utf-8")
_dyn_layout = (ROOT / "scripts/ui/dynamic_map_layout.gd").read_text(encoding="utf-8")
_dyn_painter = (ROOT / "scripts/ui/dynamic_map_painter.gd").read_text(encoding="utf-8")
_dyn_checks = (ROOT / "tests/dynamic_map_renderer_checks.gd").read_text(encoding="utf-8")
_dyn_oracle = (ROOT / "tests/dynamic_renderer_source_oracle.py").read_text(encoding="utf-8")
_dyn_source = (ROOT.parent / "map_components/_bundle.py").read_text(encoding="utf-8")
check('const DynamicMapRendererChecks = preload("res://tests/dynamic_map_renderer_checks.gd")' in ai_tests
      and "DynamicMapRendererChecks.new().run(_check)" in ai_tests,
      "9d0 dynamic renderer suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/dynamic_renderer_source_oracle.py" in workflow,
      "9d0 source oracle must run in the static workflow")
check(_dyn_manifest_path.is_file() and _dyn_fixture_path.is_file(),
      "9d0 dynamic manifest and source fixture must exist")
if _dyn_manifest_path.is_file():
    _dyn = json.loads(_dyn_manifest_path.read_text(encoding="utf-8"))
    _dyn_palette = json.loads((ROOT / "data/levels/theme_palette.json").read_text(encoding="utf-8"))
    check(_dyn["source"] == "map_components/_bundle.py::DynamicRenderer"
          and _dyn["generator"] == "godot_rebuild/tests/dynamic_renderer_source_oracle.py",
          "9d0 manifest must name its real source and generator")
    check(sorted(_dyn["themes"]) == sorted(_dyn_palette) and len(_dyn["themes"]) == 54,
          "9d0 all 54 themes must have dynamic data")
    check(len(_dyn["layout"]["river_points"]) == 61
          and len(_dyn["layout"]["torch_stones"]) == 18 and _dyn["layout_seed"] == 42,
          "9d0 source river and seed-42 torch layout must be pinned")
    for _theme, _entry in sorted(_dyn["themes"].items()):
        check(all(level in _entry["states"] for level in ("low", "medium", "high")),
              f"9d0 quality states missing: {_theme}")
if _dyn_fixture_path.is_file():
    _dyn_fixture = json.loads(_dyn_fixture_path.read_text(encoding="utf-8"))
    _dyn_ops = sum(len(frame["ops"]) for case in _dyn_fixture["cases"] for frame in case["frames"])
    check(len(_dyn_fixture["cases"]) == 10 and len(_dyn_fixture["torch_cases"]) == 15
          and _dyn_ops >= 2000,
          "9d0 fixture must cover particle/boss/quality cases and all torch palettes")
check("class DynamicRenderer" in _dyn_source and "def _boss_dynamic_draw" in _dyn_source
      and "def _draw_boss_environment" in _dyn_source,
      "9d0 source must retain the base class and true-boss overrides")
check('rec.harvest(BUNDLE, ["_NS_generators", "DynamicRenderer"])' in _dyn_oracle
      and "RandomRecorder" in _dyn_oracle and '"low"' in _dyn_oracle
      and '"medium"' in _dyn_oracle and '"high"' in _dyn_oracle,
      "9d0 oracle must execute real source with random replay and all quality presets")
check("func update()" in _dyn_state and "func _update_boss_particles" in _dyn_state
      and "func set_random_replay" in _dyn_state and "func configure_state" in _dyn_state,
      "9d0 native state must implement base/boss updates and the fixture replay seam")
check("static func torch_ops" in _dyn_layout and "static func _boss_ops" in _dyn_layout
      and '"mist"' not in _dyn_layout,
      "9d0 layout must cover torches/boss effects without inventing a mist particle painter")
check('"ellipse":' in _dyn_painter and '"arc":' in _dyn_painter
      and "draw_colored_polygon" in _dyn_painter and "draw_polyline" in _dyn_painter,
      "9d0 painter must handle fog ellipses and boss arcs natively")
check(_art_base.index("draw_texture(wall_texture") < _art_base.index("_draw_map_dynamic()")
      < _art_base.index("_draw_map_overlay()")
      and "dynamic_map.draw(self, world.tick_count)" in _art_view
      and "dynamic_map.configure(cached_river_theme)" in _art_view,
      "9d0 view must draw dynamic ops after the wall and before ambient tint")
check("_replay_case(case_value as Dictionary, check)" in _dyn_checks
      and "_check_torch_case(case_value as Dictionary, check)" in _dyn_checks
      and "random_replay_complete()" in _dyn_checks,
      "9d0 native suite must replay state, random streams and every source op")

# ── Layer 9bk: baked minion sprites (bake/bake_minion_atlas.py) ──
_mn_path = ROOT / "data/art/minions.json"
_mn_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
_mn_entity = (ROOT.parent / "_entity.py").read_text(encoding="utf-8")
_mn_bundle = (ROOT.parent / "minions/_bundle.py").read_text(encoding="utf-8")
_mn_bake = (ROOT / "bake/bake_minion_atlas.py").read_text(encoding="utf-8")
_mn_art = (ROOT / "scripts/ui/minion_art.gd").read_text(encoding="utf-8")
_mn_anim = (ROOT / "scripts/ui/minion_anim.gd").read_text(encoding="utf-8")
_mn_view = (ROOT / "scenes/combat/minion_view.gd").read_text(encoding="utf-8")
_mn_state = (ROOT / "scripts/combat/unit_state.gd").read_text(encoding="utf-8")
_mn_battle = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
_mn_checks = (ROOT / "tests/minion_art_checks.gd").read_text(encoding="utf-8")
check('const MinionArtChecks = preload("res://tests/minion_art_checks.gd")' in ai_tests
      and "MinionArtChecks.new().run(_check)" in ai_tests,
      "9bk minion art suite must be preloaded and run in the native suite")
check("      - 'minions/_bundle.py'" in workflow and workflow.count("minions/_bundle.py") == 2,
      "9bk CI must run when the source minion art changes (push and pull_request)")
check(_mn_path.is_file(), "9bk minion atlas manifest must exist")
if _mn_path.is_file():
    _mn = json.loads(_mn_path.read_text(encoding="utf-8"))
    _mn_block = re.search(r"^MINION_TYPES = \{\n(.*?)^\}", _mn_core, re.S | re.M)
    _mn_source_types = re.findall(r'^    "(\w+)": \{', _mn_block.group(1), re.M)
    check(_mn["types"] == _mn_source_types == ["goblin", "orc", "troll", "undead", "dark_rider"],
          "9bk baked types must be the source MINION_TYPES")
    check(_mn["teams"] == ["blue", "red"] and _mn["levels"] == [1, 2, 3, 4, 5]
          and len(_mn["atlases"]) == 50,
          "9bk one atlas per type x team x nexus level")
    check(_mn["states"] == {"atk": 13, "walk": 8, "idle": 4}
          and f"self.attack_anim_max = {_mn['attack_anim_max']}" in _mn_entity
          and _mn["attack_anim_max"] == 24,
          "9bk pose counts and attack_anim_max must match the source")
    check(len(_mn["key_cases"]) >= 90
          and {row[4] for row in _mn["key_cases"]} == {"atk", "walk", "idle"},
          "9bk the manifest must carry the source pose keys")
    _mn_poses = [f"{kind}{i}" for kind, n in (("atk", 13), ("walk", 8), ("idle", 4))
                 for i in range(n)]
    for _name, _entry in sorted(_mn["atlases"].items()):
        _png = ROOT / "assets/art/minions" / f"{_name}.png"
        check(_png.is_file(), f"9bk atlas PNG must ship: {_name}")
        if not _png.is_file():
            continue
        _raw = _png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _entry["size"]
              and (_depth, _color) == (8, 6),
              f"9bk atlas must be an RGBA8 PNG of its manifest size: {_name}")
        check(len(_raw) == _entry["bytes"] and hashlib.sha256(_raw).hexdigest() == _entry["sha256"],
              f"9bk atlas must match its manifest hash: {_name}")
        _rows = _entry["frames"]
        check(sorted(_rows) == sorted(f"{pose}:{d}" for pose in _mn_poses for d in (1, -1)),
              f"9bk atlas must hold every pose in both directions: {_name}")
        check(all(w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= _entry["size"][0]
                  and y + h <= _entry["size"][1] and 0 <= ax <= w and 0 <= ay <= h
                  for x, y, w, h, ax, ay in _rows.values()),
              f"9bk every frame must lie inside its atlas with its anchor in the crop: {_name}")
for _fragment in (
    "state = ('atk', atk // 2)",
    "state = ('walk', int(getattr(minion, 'walk_cycle', 0) * 2) % 8)",
    "state = ('idle', int(getattr(minion, 'anim_time', 0) * 0.05) % 4)",
    "1 if getattr(minion, 'direction', 1) >= 0 else -1",
    "_CANVAS_W = 120",
    "if getattr(minion, \"team\", \"blue\") == \"red\":",
):
    check(_fragment in _mn_bundle, f"9bk the source sprite cache must still key on {_fragment!r}")
for _fragment in ("self.walk_cycle += 0.25", "self.hurt_flash_timer = 8",
                  "self.attack_anim_timer = self.attack_anim_max", "self.anim_time += 1"):
    check(_fragment in _mn_entity, f"9bk the source minion clock must still read {_fragment!r}")
check("minion.attack_anim_timer = min(24, 2 * index + 1)" in _mn_bake
      and "minion.walk_cycle = index / 2.0" in _mn_bake
      and "minion.anim_time = 20 * index" in _mn_bake
      and "minion.draw(pygame.Surface" in _mn_bake
      and "bundle._minion_cache_key(minion)" in _mn_bake
      and "cache.get_cached_sprite_cropped(key" in _mn_bake,
      "9bk the bake must drive the real Minion.draw and read the sprite cache")
for _fragment in ("bg_color = (12, 22, 44)", "border_color = (90, 165, 255)",
                  "bg_color = (44, 12, 10)", "border_color = (255, 95, 85)",
                  "col = (70, 200, 80)", "col = (225, 190, 60)", "col = (215, 60, 55)",
                  "if hp_ratio > 0.6:", "elif hp_ratio > 0.3:", "bar_h = 4",
                  "fill = int(w * hp_ratio)", "bar_w = radius * 2 + 6", "by = y - radius - 18"):
    check(_fragment in _mn_bundle, f"9bk the source minion HP bar must still read {_fragment!r}")
for _fragment in ("Color8(12, 22, 44)", "Color8(90, 165, 255)", "Color8(44, 12, 10)",
                  "Color8(255, 95, 85)", "Color8(70, 200, 80)", "Color8(225, 190, 60)",
                  "Color8(215, 60, 55)", "ratio <= 0.3", "ratio <= 0.6",
                  "var width := radius * 2 + 6", "int(point.y) - radius - 18",
                  "Color8(150, 220, 255, 80)", "Color8(200, 240, 255)"):
    check(_fragment in _mn_view, f"9bk the view must paint the source minion bars: {_fragment!r}")
check("(150, 220, 255, 80)" in _mn_entity and "(200, 240, 255)" in _mn_entity
      and "angle = self.anim_time * 0.1 + i * 2" in _mn_entity,
      "9bk the source slow aura must still read as the view paints it")
check("var nexus_level := 1" in _mn_state and "unit.nexus_level = current" in _mn_battle,
      "9bk spawned minions must carry their nexus tier for the sprite pick")
check("static func pose_key(" in _mn_anim and "attack >> 1" in _mn_anim
      and "int(walk_cycle * 2.0) % WALK_POSES" in _mn_anim
      and "int(float(anim_time) * 0.05) % IDLE_POSES" in _mn_anim
      and "WALK_STEP := 0.25" in _mn_anim and "HURT_FLASH_TICKS := 8" in _mn_anim
      and "ATTACK_ANIM_MAX := 24" in _mn_anim,
      "9bk the pose picker must mirror the source cache key and clocks")
check("ResourceLoader.exists(atlas_path(name))" in _mn_art
      and "static func frame(" in _mn_art and "\"anchor\"" in _mn_art,
      "9bk the loader must tolerate an atlas that is not imported")
check("func _draw_minion_sprite(" in _mn_view and "MinionArt.frame(" in _mn_view
      and "minion_anim.observe(unit, session.world.tick_count," in _mn_view
      and "draw_texture_rect_region(" in _mn_view and "return false" in _mn_view
      and "if not unit.is_hero and _draw_minion_sprite(unit):" in _mn_view
      and "minion_anim.prune(session.world.units)" in _mn_view,
      "9bk the view must draw the baked sprite and fall back to the circle")
check("_check_atlases(check, manifest)" in _mn_checks and "_check_key_cases(check, manifest)" in _mn_checks
      and "_check_clocks(check)" in _mn_checks and "_check_spawn_level(check)" in _mn_checks
      and "_check_view_wiring(check)" in _mn_checks,
      "9bk minion art suite must check atlases, pose keys, clocks, spawn tier and wiring")

# ── Layer 9bl: baked tower, castle and armor-crest sprites (bake/bake_structure_atlas.py) ──
_st_path = ROOT / "data/art/structures.json"
_st_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
_st_entity = (ROOT.parent / "_entity.py").read_text(encoding="utf-8")
_st_bake = (ROOT / "bake/bake_structure_atlas.py").read_text(encoding="utf-8")
_st_art = (ROOT / "scripts/ui/structure_art.gd").read_text(encoding="utf-8")
_st_anim = (ROOT / "scripts/ui/structure_anim.gd").read_text(encoding="utf-8")
_st_siege = (ROOT / "scenes/siege/siege_view.gd").read_text(encoding="utf-8")
_st_base = (ROOT / "scenes/combat/minion_view.gd").read_text(encoding="utf-8")
_st_checks = (ROOT / "tests/structure_art_checks.gd").read_text(encoding="utf-8")
check('const StructureArtChecks = preload("res://tests/structure_art_checks.gd")' in ai_tests
      and "StructureArtChecks.new().run(_check)" in ai_tests,
      "9bl structure art suite must be preloaded and run in the native suite")
check(_st_path.is_file(), "9bl structure atlas manifest must exist")
if _st_path.is_file():
    _st = json.loads(_st_path.read_text(encoding="utf-8"))
    check(_st["tower_types"] == ["archer", "cannon", "ice", "mage"]
          and _st["shoot_timers"] == [0, 5, 8, 10]
          and _st["castle"] == {"levels": [1, 2, 3, 4, 5], "timers": [0, 3, 5, 8, 10],
                                "scale": 0.85, "size": [153, 136], "anchor": [76, 101]},
          "9bl manifest must carry the tower paths, the representative timers and the castle blit")
    check({kind: len(levels) for kind, levels in _st["tower_levels"].items()}
          == {"archer": 6, "cannon": 5, "ice": 5, "mage": 5}
          and len(_st["towers"]) == 42 and len(_st["castles"]) == 10
          and len(_st["crests"]["frames"]) == 88,
          "9bl one sheet per tower path x team x level, per castle team x level, plus crests")
    _st_sheets = {f"tower_{n}": e for n, e in _st["towers"].items()}
    _st_sheets.update({f"castle_{n}": e for n, e in _st["castles"].items()})
    _st_sheets["crests"] = _st["crests"]
    for _stem, _entry in sorted(_st_sheets.items()):
        _png = ROOT / "assets/art/structures" / f"{_stem}.png"
        check(_png.is_file(), f"9bl structure sheet must ship: {_stem}")
        if not _png.is_file():
            continue
        _raw = _png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _entry["size"]
              and (_depth, _color) == (8, 6),
              f"9bl sheet must be an RGBA8 PNG of its manifest size: {_stem}")
        check(len(_raw) == _entry["bytes"] and hashlib.sha256(_raw).hexdigest() == _entry["sha256"],
              f"9bl sheet must match its manifest hash: {_stem}")
        check(all(w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= _entry["size"][0]
                  and y + h <= _entry["size"][1] and 0 <= ax <= w and 0 <= ay <= h
                  for x, y, w, h, ax, ay in _entry["frames"].values()),
              f"9bl every frame must lie inside its sheet: {_stem}")
        _want = 88 if _stem == "crests" else (5 if _stem.startswith("castle_") else 8)
        check(len(_entry["frames"]) == _want, f"9bl sheet must hold {_want} frames: {_stem}")
    for _team in ("blue", "red"):
        for _tres in sorted((ROOT / "data/structures").glob("*.tres")):
            _text = _tres.read_text(encoding="utf-8")
            _kind = re.search(r'structure_kind = "(\w+)"', _text)
            _path = re.search(r'tower_path = "(\w+)"', _text)
            _level_match = re.search(r"^level = (\d+)", _text, re.M)
            _level = int(_level_match.group(1)) if _level_match else 1  # default is omitted
            if _kind and _kind.group(1) == "nexus":
                check(f"{_team}_{_level}" in _st["castles"],
                      f"9bl every nexus level needs a castle sheet: {_tres.name} {_team}")
            else:
                _name = f"{_path.group(1) if _path else 'archer'}_{_team}_{_level}"
                check(_name in _st["towers"], f"9bl every tower level needs a sheet: {_name}")
    check(set(_st["tower_top_y"]) == {"archer", "cannon", "ice", "mage"}
          and all(len(v) == len(_st["tower_levels"][k]) for k, v in _st["tower_top_y"].items()),
          "9bl every tower level must carry its bar offset")
for _fragment in (
    'key = ("tw", self.tower_type, self.team, self.level,',
    "shoot_b = self.shoot_flash_timer // 3",
    "face = 1 if (self.target is not None",
    "cw, ch = 180, 160",
    "SCALE = 0.85",
    "final_x = int(self.x - new_w // 2)",
    "final_y = int(self.y - new_h + 35)",
    "scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))",
    "flicker = int((timer * 0.4 + offset) % 5)",
    "crest_x = x + 26",
    "crest_y = y - 28 - self.level",
    "crest_size = 14",
    "crest_size = 18",
    "ratio_b = min(10, max(0, int(fill_ratio * 10 + 0.5)))",
    "bar_w = 44",
    "bar_h = 5",
    "by = self._top_fn(self.x, self.y, self.level) - 14",
    "by = y - 26",
    "shield_bar_y = by - bar_h - 2",
    "(30, 30, 50)",
    "(40, 0, 0)",
    "shine_h = max(1, bar_h // 2)",
    "bar_w = 60",
    "bar_h = 6",
    "by = int(self.y - 80)",
    'f"SHIELD {int(ratio*100)}%"',
    "bob = int(math.sin(self.pulse * 1.2) * 2)",
    "self.pulse += 0.05",
    "self.shoot_flash_timer = 10",
    "self.shoot_flash_timer = 8",
):
    check(_fragment in _st_entity, f"9bl the source tower/castle code must still read {_fragment!r}")
check("TOWER_SHIELD_REGEN_DELAY = 180" in _st_core
      and "SHIELD_COLOR_BLUE = (100, 180, 255)" in _st_core
      and "SHIELD_COLOR_RED = (255, 100, 100)" in _st_core
      and "CASTLE_SHIELD_COLOR_BLUE = (100, 200, 255)" in _st_core
      and "CASTLE_SHIELD_COLOR_RED = (255, 120, 120)" in _st_core,
      "9bl the source shield colours and regen delay must still read as the view paints them")
check("tower._draw_tower_body(" in _st_bake and "entity._render_castle_full(" in _st_bake
      and "entity._render_dynamic_effects(" in _st_bake
      and "pygame.transform.smoothscale(frame, (new_w, new_h))" in _st_bake
      and "entity._build_armor_crest(" in _st_bake
      and 'key = ("tw", tower_type, team, level, face, timer // 3)' in _st_bake
      and "SHOOT_TIMERS = (0, 5, 8, 10)" in _st_bake
      and "CASTLE_TIMERS = (0, 3, 5, 8, 10)" in _st_bake,
      "9bl the bake must drive the real tower, castle and crest code at the source timers")
for _fragment in (
    "const TOWER_BAR_WIDTH := 44", "const TOWER_BAR_HEIGHT := 5",
    "Color(100 / 255.0, 180 / 255.0, 255 / 255.0)", "Color(255 / 255.0, 100 / 255.0, 100 / 255.0)",
    "Color(100 / 255.0, 200 / 255.0, 255 / 255.0)", "Color(255 / 255.0, 120 / 255.0, 120 / 255.0)",
    "Color(30 / 255.0, 30 / 255.0, 50 / 255.0)", "Color(40 / 255.0, 0 / 255.0, 0 / 255.0)",
    "Color(50 / 255.0, 200 / 255.0, 50 / 255.0)", "Color(220 / 255.0, 50 / 255.0, 50 / 255.0)",
    "Vector2(x + 26, y - 28 - data.level)", "crest_frame(14,", "crest_frame(18,",
    "- TOWER_BAR_HEIGHT - 2", "tower_top_y(data.tower_path, data.level) - 14",
    "hp_ratio <= 0.3", "hp_ratio <= 0.6", "maxi(1, TOWER_BAR_HEIGHT >> 1)",
    "int(structure.position.y) - 80", "int(structure.position.x) - 30",
    '"SHIELD %d%%" % int(ratio * 100.0)', "float(session.world.tick_count) * 0.05 * 1.2",
    "structure.no_damage_ticks >= data.shield_regen_delay_ticks",
    "func _draw_pill(", "func _draw_regen_plus(", "func _draw_level_badge(",
):
    check(_fragment in _st_siege, f"9bl the siege view must paint the source bars: {_fragment!r}")
check("if not _draw_structure_art(structure):" in _st_siege
      and _st_siege.index("if not _draw_structure_art(structure):")
      < _st_siege.index("_draw_structure_plain(structure)\n\n\n## Layer 9bl")
      and "func _draw_structures() -> void:" in _st_siege
      and "func _draw_structures() -> void:" in _st_base
      and _st_base.index("_draw_base(Layout.RED_BASE") < _st_base.index("\t_draw_structures()\n")
      < _st_base.index("minion_anim.prune(session.world.units)"),
      "9bl structures must paint before the units, with the plain boxes as the fallback")
check("ResourceLoader.exists(sheet_path(stem))" in _st_art and "static func tower_frame(" in _st_art
      and "static func castle_frame(" in _st_art and "static func crest_frame(" in _st_art
      and "DEFAULT_TOP_Y := -26" in _st_art,
      "9bl the loader must tolerate a sheet that is not imported")
check("floori(float(flash) / 3.0)" in _st_anim and "int(float(tick) * 0.4) % FLICKER_STEPS" in _st_anim
      and "FLASH_TICKS := 8" in _st_anim and "CANNON_FLASH_TICKS := 10" in _st_anim,
      "9bl the clocks must mirror the source flash timers and flame flicker")
check("_check_sheets(check, manifest)" in _st_checks and "_check_definitions(check)" in _st_checks
      and "_check_clocks(check, manifest)" in _st_checks and "_check_view_wiring(check)" in _st_checks,
      "9bl structure art suite must check sheets, definitions, clocks and wiring")

# ── Layer 9bm: baked build-slot markers (bake/bake_slot_atlas.py) ──
_sl_path = ROOT / "data/art/slots.json"
_sl_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
_sl_ui = (ROOT.parent / "ui_components/_bundle.py").read_text(encoding="utf-8")
_sl_bake = (ROOT / "bake/bake_slot_atlas.py").read_text(encoding="utf-8")
_sl_art = (ROOT / "scripts/ui/slot_art.gd").read_text(encoding="utf-8")
_sl_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_sl_checks = (ROOT / "tests/slot_art_checks.gd").read_text(encoding="utf-8")
check('const SlotArtChecks = preload("res://tests/slot_art_checks.gd")' in ai_tests
      and "SlotArtChecks.new().run(_check)" in ai_tests,
      "9bm slot art suite must be preloaded and run in the native suite")
check(workflow.count("      - 'ui_components/_bundle.py'") == 2,
      "9bm CI must run when the source slot art changes (push and pull_request)")
check(_sl_path.is_file(), "9bm slot manifest must exist")
if _sl_path.is_file():
    _sl = json.loads(_sl_path.read_text(encoding="utf-8"))
    _sl_sheet = _sl["sheet"]
    _sl_png = ROOT / "assets/art/slots/slots.png"
    check(_sl_png.is_file(), "9bm slot sheet must ship")
    if _sl_png.is_file():
        _raw = _sl_png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _sl_sheet["size"] == [240, 38]
              and (_depth, _color) == (8, 6),
              "9bm slot sheet must be a 240x38 RGBA8 PNG")
        check(len(_raw) == _sl_sheet["bytes"] and hashlib.sha256(_raw).hexdigest() == _sl_sheet["sha256"],
              "9bm slot sheet must match its manifest hash")
    check(sorted(_sl_sheet["frames"]) == sorted(["red"] + [f"blue:{k}" for k in range(-2, 3)])
          and all(row[2:] == [40, 38, 20, 17] for row in _sl_sheet["frames"].values()),
          "9bm five blue pulse frames and one red frame, all 40x38 anchored at (20, 17)")
    check(_sl["pulses"] == [-2, -1, 0, 1, 2] and len(_sl["pulse_cases"]) >= 50
          and {row[1] for row in _sl["pulse_cases"]} == {-2, -1, 0, 1, 2},
          "9bm the manifest must carry the source pulse answers across every glow size")
for _fragment in (
    "pulse = math.sin(g.animation_time * 0.08) * 2",
    "pk = int(round(pulse))",
    "surface.blit(bslot, (sx - 20, sy - 17))",
    "surface.blit(rsurf, (sx - 20, sy - 17))",
    "s = pygame.Surface((40, 38), pygame.SRCALPHA)",
    "15 + pk",
    "plus_size = 8 + pk",
):
    check(_fragment in _sl_ui, f"9bm the source slot code must still read {_fragment!r}")
_sl_draw = _sl_core[_sl_core.index("self.ui.draw_build_slots(draw_target)"):]
check(_sl_draw.index("for b in self.bases:") < _sl_draw.index("for t in self.towers:\n            t.draw(draw_target)")
      < _sl_draw.index("for m in self.minions:"),
      "9bm the source paints the build slots, then the castles, the towers and the minions")
check("component._render_blue_slot_surface(pulse)" in _sl_bake
      and "component._render_red_slot_surface()" in _sl_bake
      and "game.ui.build_slots_component" in _sl_bake
      and "PULSES = (-2, -1, 0, 1, 2)" in _sl_bake
      and "int(round(math.sin(tick * 0.08) * 2))" in _sl_bake,
      "9bm the bake must render the real slot surfaces and record the source pulse formula")
check("PULSE_SPEED := 0.08" in _sl_art and "roundi(sin(float(tick) * PULSE_SPEED) * 2.0)" in _sl_art
      and "ResourceLoader.exists(SHEET)" in _sl_art,
      "9bm the loader must mirror the source pulse and tolerate a missing import")
check("SlotArt.frame(slot.team, world.tick_count)" in _sl_view
      and "func _draw_build_slots(" in _sl_view and "func _draw_slot_outline(" in _sl_view
      and _sl_view.count("for slot in world.slots:") == 1
      and _sl_view.index("func _draw_structures() -> void:") < _sl_view.index("_draw_build_slots(session.world")
      < _sl_view.index("super._draw_structures()"),
      "9bm the view must paint the slot art from the structure layer, below the towers")
check("_check_pulse(check, manifest)" in _sl_checks and "_check_frames(check)" in _sl_checks
      and "_check_view_wiring(check)" in _sl_checks,
      "9bm slot art suite must check the pulse, the frames and the wiring")

# ── Layer 9bn: the painters run for real in the headless scene suite ──
_pt_checks = (ROOT / "tests/painter_scene_checks.gd").read_text(encoding="utf-8")
_pt_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
check('const PainterSceneChecks = preload("res://tests/painter_scene_checks.gd")' in ai_tests
      and "await PainterSceneChecks.new().run(root.get_tree(), app, _check)" in ai_tests
      and "painter scene restores the menu" in ai_tests,
      "9bn the painter scene suite must be preloaded, awaited and followed by the menu check")
check("var draw_count := 0" in _pt_view and "\tdraw_count += 1\n\tif session == null:" in _pt_view,
      "9bn PrototypeView must count real _draw calls")
check("view.draw_count > first_draw" in _pt_checks and "world.step_tick()" in _pt_checks
      and "world.build_tower(0, slot.id, \"archer\")" in _pt_checks
      and "world.upgrade_tower(tower.id, 1, PATHS[index])" in _pt_checks
      and "view.minion_anim.tracked() > 0" in _pt_checks
      and "view.structure_anim.tracked() > 0" in _pt_checks
      and 'const TYPES := ["goblin", "orc", "troll", "undead", "dark_rider"]' in _pt_checks
      and "unit.slow_timer = 60" in _pt_checks and "tower.cooldown_ticks" in _pt_checks,
      "9bn the painter suite must prove _draw ran and exercise every minion type, towers, slow and fire")

def _webp_dimensions(raw):
    """Dimensions of the dependency-free lossless WebP subset emitted by the bakes."""
    if len(raw) < 26 or raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
        return None
    if raw[12:16] == b"VP8L" and raw[20] == 0x2F:
        bits = int.from_bytes(raw[21:25], "little")
        return [(bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1]
    if raw[12:16] == b"VP8X" and len(raw) >= 30:
        return [1 + int.from_bytes(raw[24:27], "little"),
                1 + int.from_bytes(raw[27:30], "little")]
    return None


# ── Layer 9bo: baked hero bodies (bake/bake_hero_atlas.py) ──
_hr_path = ROOT / "data/art/heroes.json"
_hr_pkg = (ROOT.parent / "heroes/__init__.py").read_text(encoding="utf-8")
_hr_entity = (ROOT.parent / "_entity.py").read_text(encoding="utf-8")
_hr_perf = (ROOT.parent / "mobile/perf.py").read_text(encoding="utf-8")
_hr_bake = (ROOT / "bake/bake_hero_atlas.py").read_text(encoding="utf-8")
_hr_art = (ROOT / "scripts/ui/hero_art.gd").read_text(encoding="utf-8")
_hr_anim = (ROOT / "scripts/ui/hero_anim.gd").read_text(encoding="utf-8")
_hr_painter = (ROOT / "scripts/ui/hero_painter.gd").read_text(encoding="utf-8")
_hr_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_hr_checks = (ROOT / "tests/hero_art_checks.gd").read_text(encoding="utf-8")
check('const HeroArtChecks = preload("res://tests/hero_art_checks.gd")' in ai_tests
      and "HeroArtChecks.new().run(_check)" in ai_tests,
      "9bo hero art suite must be preloaded and run in the native suite")
check(workflow.count("      - 'heroes/__init__.py'") == 2 and workflow.count("      - 'heroes/_bundle.py'") == 2,
      "9bo CI must run when the source hero renderers change (push and pull_request)")
check(_hr_path.is_file(), "9bo hero atlas manifest must exist")
if _hr_path.is_file():
    _hr = json.loads(_hr_path.read_text(encoding="utf-8"))
    _hr_heroes = _hr["heroes"]
    _hr_non_boss = ["grimjaw", "kaizen", "sylara", "thorne", "vex", "zephyr"]
    _hr_shared = _hr["shared_red_bosses"]
    _hr_expected = {f"{hero}_blue" for hero in _hr_heroes}
    _hr_expected |= {f"{hero}_red" for hero in _hr_non_boss}
    check(len(_hr_heroes) == 222 and len(_hr_shared) == 216
          and _hr["non_boss"] == _hr_non_boss and _hr["teams"] == ["blue", "red"]
          and set(_hr["atlases"]) == _hr_expected and len(_hr["atlases"]) == 228
          and sorted(_hr["meta"]) == sorted(_hr_heroes)
          and _hr["phases"] == 8 and _hr["atk_quant"] == 3
          and _hr["skill_quant"] == 2 and _hr["skill_samples"] == 2
          and _hr["skill_heroes"] == _hr_non_boss
          and _hr["format"] == "webp-lossless-v0",
          "9bo all 222 heroes: 222 blue + six red atlases, with 216 shared red boss-heroes")
    check(len(_hr["key_cases"]) >= 200 and {row[3] for row in _hr["key_cases"]} == {"atk", "walk", "idle"},
          "9bo the manifest must carry the source pose keys")
    for _hero in _hr_heroes:
        _facts = _hr["meta"][_hero]
        check((ROOT / "data/heroes" / f"{_hero}.tres").is_file()
              and _facts["radius"] == 16 and _facts["top_offset"] > 0 and _facts["cooldown"] > 0
              and _facts["hero_scale"] > 0 and _facts["name"],
              f"9bo source facts and a Godot definition must exist for {_hero}")
    for _name, _entry in _hr["atlases"].items():
        _hero = _name.rsplit("_", 1)[0]
        _facts = _hr["meta"][_hero]
        _sheet = ROOT / "assets/art/heroes" / f"{_name}.webp"
        check(_sheet.is_file(), f"9bo hero atlas must ship: {_name}")
        if not _sheet.is_file():
            continue
        _raw = _sheet.read_bytes()
        check(_webp_dimensions(_raw) == _entry["size"],
              f"9bo atlas must be lossless WebP at its manifest size: {_name}")
        check(len(_raw) == _entry["bytes"] and hashlib.sha256(_raw).hexdigest() == _entry["sha256"],
              f"9bo atlas must match its manifest hash: {_name}")
        _poses = [f"idle{n}" for n in range(8)]
        if _facts["walk_poses"]:
            _poses += [f"walk{n}" for n in range(8)]
        _poses += [f"atk{k}" for k in range(_facts["cooldown"] // 3 + 1)]
        _skills = _entry["skills"]
        check((set(_skills) == set("qwer")) == (_hero in _hr_non_boss)
              and all(len(poses) == 2 for poses in _skills.values())
              and _entry["skill_quant"] == 2,
              f"9bo only non-boss sheets carry two frames for each Q/W/E/R skill: {_name}")
        for _skill_poses in _skills.values():
            _poses += _skill_poses
        _rows = _entry["frames"]
        check(sorted(_rows) == sorted(f"{pose}:{d}" for pose in _poses for d in (1, -1)),
              f"9bo atlas must hold every pose in both directions: {_name}")
        check(0 < _entry["unique_frames"] <= len(_rows)
              and all(w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= _entry["size"][0]
                      and y + h <= _entry["size"][1] and 0 <= ax <= w and 0 <= ay <= h
                      for x, y, w, h, ax, ay in _rows.values()),
              f"9bo every frame must lie inside its atlas with its anchor in the crop: {_name}")
for _fragment in (
    "phase = int(getattr(hero, 'pulse', 0.0) * 2.0) % HERO_ANIM_PHASES",
    "return (hero_type, team, level, facing, 'skill', skill,",
    "skill_t // (_skill_quant() * _q))",
    "timer // (_atk_quant() * _q)",
    "return (hero_type, team, level, facing, 'idle', phase,",
    "bool(getattr(hero, '_moving_cached', False)))",
    "_HERO_RENDER_LEFT[0] = int(getattr(_Qb, \"max_hero_render\", 6))",
):
    check(_fragment in _hr_pkg, f"9bo the source hero cache must still key on {_fragment!r}")
check("HERO_ANIM_PHASES = 8" in _hr_pkg and "self.atk_quant_floor = 6 if low else (4 if med else 3)" in _hr_perf,
      "9bo the PC quality preset must still give 8 idle phases and an attack quantum of 3")
for _fragment in (
    "self.pulse += 0.1", "self.attack_timer = _eff_cd",
    "pygame.draw.ellipse(surface, (0, 0, 0, 100),", "(x - self.radius, y + self.radius - 4,",
    "self.radius * 2, 8))", "(x - self.radius - 3,", "y + self.radius - 6,", "(self.radius + 3) * 2, 10), 2)",
    "r_color = (*self.color, 30)", "border_c = (*self.color, 100)",
    "label_anchor = y - max(self.radius, sprite_top) - 6",
    "bar_w = 45", "bar_h = 6", "by = label_anchor", "pygame.draw.rect(surface, (40, 0, 0), (bx, by, bar_w, bar_h))",
    "hp_color = GREEN if hp_ratio > 0.5 else (", "YELLOW if hp_ratio > 0.25 else RED)",
    "pygame.draw.rect(surface, WHITE, (bx, by, bar_w, bar_h), 1)",
    "badge_top = by - badge.get_height() - 3",
    "star_w = (self.level * 10) if self.level <= 5 else 18", "bw = max(name_lbl.get_width(), star_w) + 8",
    "nh = name_lbl.get_height() + 4", "bh = 12 + nh", "sx = bw // 2 - (self.level - 1) * 5 + i * 10",
    "(sx, sy - 3), (sx + 2, sy),", "total_w = 9 + lvl_txt.get_width()",
    "y + self.radius + 8", "int(45 * cd_ratio)", "self.name = ",
):
    check(_fragment in _hr_entity, f"9bo the source hero overlay must still read {_fragment!r}")
check("DARK_GRAY  = (60,  60,  70 )" in (ROOT.parent / "_core.py").read_text(encoding="utf-8")
      and "ORANGE     = (255, 140, 0  )" in (ROOT.parent / "_core.py").read_text(encoding="utf-8"),
      "9bo the source cooldown-strip colours must still read as the painter draws them")
check("_detect_moving" in (ROOT.parent / "heroes/_bundle.py").read_text(encoding="utf-8")
      and "hero._moving_cached = moving" in (ROOT.parent / "heroes/_bundle.py").read_text(encoding="utf-8")
      and "dx + dy > 0.3" in (ROOT.parent / "heroes/_bundle.py").read_text(encoding="utf-8"),
      "9bo the source renderers must still detect movement as |dx| + |dy| > 0.3")
check("heroes_mod._reset_hero_render_budget()" in _hr_bake and "hero.draw(surface)" in _hr_bake
      and "heroes_mod._hero_cache_key(hero_type, hero)" in _hr_bake
      and "hero.x = 400.0 + step * 2.0" in _hr_bake
      and "hero.attack_timer = cooldown" in _hr_bake and "IDLE_STEPS = 40" in _hr_bake
      and "hero.active_skill = skill" in _hr_bake and "_skill_sample_names(" in _hr_bake
      and "NON_BOSS_SKILL_DURATIONS" in _hr_bake and "SKILL_SAMPLES = 2" in _hr_bake
      and "env.virtual_ticks(pygame, ticks)" in _hr_bake,
      "9bo the bake must drive real timelines and skill casts with a deterministic virtual wall clock")
check("static func resolve(" in _hr_art and "ResourceLoader.exists(atlas_path(name))" in _hr_art
      and "pose.begins_with(\"walk\")" in _hr_art and "pose.begins_with(\"atk\")" in _hr_art
      and "static func _shared_boss_frame(" in _hr_art and "BossArt.frame(hero_id, direction, pose)" in _hr_art
      and 'art["scale"] = float(facts.get("hero_scale", 1.0))' in _hr_art,
      "9bo the loader must resolve every roster hero and share red boss frames at source scale")
check("floori(float(attack_timer) / float(ATK_QUANT))" in _hr_anim
      and "int(pulse * 2.0) % PHASES" in _hr_anim and "PULSE_STEP := 0.1" in _hr_anim
      and "MOVE_EPSILON := 0.3" in _hr_anim and "PHASES := 8" in _hr_anim,
      "9bo the pose picker must mirror the source cache key and clocks")
for _fragment in (
    "const BAR_WIDTH := 45", "const BAR_HEIGHT := 6",
    "Color(50 / 255.0, 200 / 255.0, 50 / 255.0)", "Color(255 / 255.0, 220 / 255.0, 0 / 255.0)",
    "Color(220 / 255.0, 50 / 255.0, 50 / 255.0)", "Color(255 / 255.0, 140 / 255.0, 0 / 255.0)",
    "Color(60 / 255.0, 60 / 255.0, 70 / 255.0)", "Color(40 / 255.0, 0 / 255.0, 0 / 255.0)",
    "Rect2(point.x - radius, point.y + radius - 4, radius * 2, 8)",
    "Rect2(point.x - radius - 3, point.y + radius - 6, (radius + 3) * 2, 10)",
    "const SHADOW := Color(0, 0, 0)", "_ellipse(shadow), SHADOW)", "Color(ink, 30.0 / 255.0)", "Color(ink, 100.0 / 255.0)",
    "maxi(radius, int(facts.get(\"top_offset\", radius))) - 6", "bar_top - height - 3",
    "level * 10 if level <= 5 else 18", "maxi(int(name_size.x), star_width) + 8",
    "int(name_size.y) + 4", "12 + name_height", "(level - 1) * 5 + index * 10",
    "var total := 9 + int(label_width)", "int(point.y) + radius + 8",
    "ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)", "int(float(BAR_WIDTH) * ratio)",
):
    check(_fragment in _hr_painter, f"9bo the painter must draw the source hero overlay: {_fragment!r}")
check("if _draw_hero_sprite(hero):" in _hr_view and "func _draw_hero_sprite(" in _hr_view
      and "HeroPainter.paint(self, hero, art, hero.id == session.selected_id, debuff_ops)"
      in _hr_view
      and "hero_anim.prune(session.world.units)" in _hr_view
      and _hr_view.index("if _draw_hero_sprite(hero):") < _hr_view.index("HeroMarker.silhouette(point, radius"),
      "9bo the view must draw the baked hero first and keep the marker as the fallback")
check("_check_atlases(check)" in _hr_checks and "_check_key_cases(check, manifest)" in _hr_checks
      and "_check_shared_bosses(check, manifest)" in _hr_checks
      and "_check_clocks(check)" in _hr_checks and "_check_view_wiring(check)" in _hr_checks
      and "src.size * scale" in _hr_painter,
      "9bo hero art suite must check all atlases, shared frames, pose keys, clocks and scaling")

# ── Layer 9bp: baked tower bullets (bake/bake_bullet_atlas.py) ──
_bl_path = ROOT / "data/art/bullets.json"
_bl_entity = (ROOT.parent / "_entity.py").read_text(encoding="utf-8")
_bl_bake = (ROOT / "bake/bake_bullet_atlas.py").read_text(encoding="utf-8")
_bl_art = (ROOT / "scripts/ui/bullet_art.gd").read_text(encoding="utf-8")
_bl_view = (ROOT / "scenes/siege/siege_view.gd").read_text(encoding="utf-8")
_bl_painter = (ROOT / "tests/painter_scene_checks.gd").read_text(encoding="utf-8")
check('const BulletArtChecks = preload("res://tests/bullet_art_checks.gd")' in ai_tests
      and "BulletArtChecks.new().run(_check)" in ai_tests,
      "9bp bullet art suite must be preloaded and run in the native suite")
check(_bl_path.is_file(), "9bp bullet atlas manifest must exist")
if _bl_path.is_file():
    _bl = json.loads(_bl_path.read_text(encoding="utf-8"))
    _bl_sheet = _bl["sheet"]
    _bl_png = ROOT / "assets/art/bullets/bullets.png"
    check(_bl_png.is_file(), "9bp bullet sheet must ship")
    if _bl_png.is_file():
        _raw = _bl_png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _bl_sheet["size"]
              and (_depth, _color) == (8, 6),
              "9bp bullet sheet must be an RGBA8 PNG of its manifest size")
        check(len(_raw) == _bl_sheet["bytes"] and hashlib.sha256(_raw).hexdigest() == _bl_sheet["sha256"],
              "9bp bullet sheet must match its manifest hash")
    _bl_keys = sorted(
        [f"normal:{team}:{n}" for team in ("blue", "red") for n in range(16)]
        + [f"{kind}:{team}" for team in ("blue", "red") for kind in ("cannon", "ice", "mage")])
    check(sorted(_bl_sheet["frames"]) == _bl_keys and _bl["buckets"] == 16
          and _bl["types"] == ["normal", "cannon", "ice", "mage"],
          "9bp the sheet must hold 16 arrows and three bolts per team")
    check(all(w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= _bl_sheet["size"][0]
              and y + h <= _bl_sheet["size"][1] and 0 <= ax <= w and 0 <= ay <= h
              for x, y, w, h, ax, ay in _bl_sheet["frames"].values()),
          "9bp every bullet frame must lie inside the sheet with its anchor in the crop")
    _bl_cases = _bl["angle_cases"]
    check(len(_bl_cases) >= 60 and {row[1] for row in _bl_cases} == set(range(16))
          and all((int(a / (2 * math.pi) * 16) + 16) % 16 == k for a, k in _bl_cases),
          "9bp the recorded bearings must reach all 16 buckets under the source formula")
for _fragment in (
    "angle_k = (int(ang / (math.pi * 2) * 16) + 16) % 16",
    "key = (bullet.bullet_type, bullet.team, angle_k)",
    "canvas = pygame.Surface((48, 48), pygame.SRCALPHA)", "cx = cy = 24",
    "pygame.draw.circle(canvas, (60, 60, 60), (cx, cy), 6)",
    "pygame.draw.circle(canvas, (255, 255, 200), (cx + 3, cy - 3), 1)",
    "pygame.draw.polygon(canvas, (150, 220, 255), [",
    "(cx, cy - 5), (cx + 3, cy), (cx, cy + 5), (cx - 3, cy)])",
    "color = (180, 80, 220)", "alpha = 200 - r * 20",
    "rect = canvas.get_bounding_rect(min_alpha=8)",
    "(int(self.x - ent[1]), int(self.y - ent[2])))",
    "shaft_dark = (85, 55, 25)", "shaft_dark = (60, 30, 15)",
):
    check(_fragment in _bl_entity, f"9bp the source bullet sprite must still read {_fragment!r}")
check("entity._get_bullet_sprite(bullet)" in _bl_bake and "entity._BULLET_SPRITE_CACHE.clear()" in _bl_bake
      and "entity._DummyBulletTarget" in _bl_bake and "BUCKETS = 16" in _bl_bake,
      "9bp the bake must run the real _get_bullet_sprite for every bucket")
check("(int(bearing / TAU * float(BUCKETS)) + BUCKETS) % BUCKETS" in _bl_art
      and "ResourceLoader.exists(SHEET)" in _bl_art and 'if kind == "normal":' in _bl_art,
      "9bp the loader must mirror the bucket formula and tolerate a missing import")
check("BulletArt.frame(shot.kind, shot.team, bearing)" in _bl_view
      and "bearing = (target.position - shot.position).angle()" in _bl_view
      and "Vector2(int(shot.position.x - anchor.x), int(shot.position.y - anchor.y))" in _bl_view
      and "draw_circle(shot.position, 4, color)" in _bl_view,
      "9bp the siege view must blit the baked bullet at the source point with the dot as fallback")
check("SHOT_KINDS := [" in _bl_painter and "world.projectiles.append(shot)" in _bl_painter,
      "9bp the painter suite must put one shot of each kind in flight")

# ── Layer 9bq: baked boss bodies (bake/bake_boss_atlas.py) ──
_bs_path = ROOT / "data/art/bosses.json"
_bs_stats = json.loads((ROOT / "data/bosses/boss_stats.json").read_text(encoding="utf-8"))["bosses"]
_bs_boss = (ROOT.parent / "bosses/base_boss.py").read_text(encoding="utf-8")
_bs_pkg = (ROOT.parent / "heroes/__init__.py").read_text(encoding="utf-8")
_bs_bake = (ROOT / "bake/bake_boss_atlas.py").read_text(encoding="utf-8")
_bs_art = (ROOT / "scripts/ui/boss_art.gd").read_text(encoding="utf-8")
_bs_anim = (ROOT / "scripts/ui/boss_anim.gd").read_text(encoding="utf-8")
_bs_checks = (ROOT / "tests/boss_art_checks.gd").read_text(encoding="utf-8")
_bs_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_bs_painter = (ROOT / "tests/painter_scene_checks.gd").read_text(encoding="utf-8")
check('const BossArtChecks = preload("res://tests/boss_art_checks.gd")' in ai_tests
      and "BossArtChecks.new().run(_check)" in ai_tests,
      "9bq boss art suite must be preloaded and run in the native suite")
check(workflow.count("      - 'bosses/**'") == 2,
      "9bq CI must run when the source boss renderers change (push and pull_request)")
check(_bs_path.is_file(), "9bq boss atlas manifest must exist")
if _bs_path.is_file():
    _bs = json.loads(_bs_path.read_text(encoding="utf-8"))
    check(sorted(_bs["bosses"]) == sorted(_bs_stats) and len(_bs["bosses"]) == 216
          and _bs["facings"] == [-1, 1] and _bs["phases"] == 8
          and _bs["attack_samples"] == 4 and _bs["skill_samples"] == 2
          and len(_bs["smart_bosses"]) == 79 and _bs["format"] == "webp-lossless-v0",
          "9bq animated sheets for 216 bosses, both facings and source smart skills")
    check(all((1 if d > 0 else -1) == f for d, f in _bs["facing_cases"])
          and len(_bs["facing_cases"]) >= 5,
          "9bq the recorded facings must follow the source key rule")
    _bs_skill_rows = 0
    _bs_walking = 0
    for _boss_id, _entry in sorted(_bs["bosses"].items()):
        _facts = _bs_stats[_boss_id]
        check(_entry["radius"] == _facts["radius"] and _entry["class"] == _facts["boss_class"]
              and 0 < _entry["label_top"] < 400 and _entry["cooldown"] > 0
              and 0 < _entry["attack_quant"] <= 32 and 0 < _entry["skill_quant"] <= 32
              and not _entry["unbaked_poses"],
              f"9bq baked facts, quanta and complete direct fallback must hold: {_boss_id}")
        _sheet = ROOT / "assets/art/bosses" / f"{_boss_id}.webp"
        check(_sheet.is_file(), f"9bq boss sheet must ship: {_boss_id}")
        if not _sheet.is_file():
            continue
        _raw = _sheet.read_bytes()
        check(_webp_dimensions(_raw) == _entry["size"],
              f"9bq boss sheet must be lossless WebP at its manifest size: {_boss_id}")
        check(len(_raw) == _entry["bytes"] and hashlib.sha256(_raw).hexdigest() == _entry["sha256"],
              f"9bq boss sheet must match its manifest hash: {_boss_id}")
        _poses = [f"idle{n}" for n in range(8)]
        if _entry["walk_poses"]:
            _poses += [f"walk{n}" for n in range(8)]
            _bs_walking += 1
        _poses += _entry["attack_poses"]
        for _skill, _skill_poses in _entry["skills"].items():
            _poses += _skill_poses
            _bs_skill_rows += 1
        _rows = _entry["frames"]
        check(sorted(_rows) == sorted(f"{pose}:{d}" for pose in _poses for d in (1, -1))
              and 0 < _entry["unique_frames"] <= len(_rows)
              and all(w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= _entry["size"][0]
                      and y + h <= _entry["size"][1] and 0 <= ax <= w and 0 <= ay <= h
                      for x, y, w, h, ax, ay in _rows.values()),
              f"9bq every animated pose must have two in-bounds facings: {_boss_id}")
        if _boss_id in _bs["smart_bosses"]:
            # nyxareth's source smart AI casts the numbered keys "1".."4" instead of Q/W/E/R.
            _bs_keys = ["1", "2", "3", "4"] if _boss_id == "nyxareth" else ["e", "q", "r", "w"]
            check(sorted(_entry["skills"]) == _bs_keys,
                  f"9bq every source smart-skill key must be baked: {_boss_id}")
    check(_bs_walking > 0 and _bs_skill_rows == 316,
          "9bq walking and all 316 source smart-skill families must be represented")
check('SCREEN_LAYERS = {"nyxareth": ("_draw_astro_realm_bg",)}' in _bs_bake
      and "with without_screen_layers(heroes_mod, boss_type):" in _bs_bake
      and "isinstance(active, str) and active" in _bs_bake,
      "9bq the bake must harvest every constant smart-skill key and skip screen-wide layers")
_bs_l17 = (ROOT.parent / "bosses/level17.py").read_text(encoding="utf-8")
check('"""Background layer of ultimate - covers entire screen."""' in _bs_l17
      and '_set_skill(boss, "4", 95)' in (ROOT / "scripts/match/boss_ai.gd").read_text(encoding="utf-8"),
      "9bq nyxareth's skipped layer must still be the source full-screen ultimate background")
for _fragment in (
    "head_top = max(int(BOSS_LABEL_TOP.get(self.boss_type, r)), r)",
    "bar_w = 70 if is_true else 60", "bar_h = 10 if is_true else 8", "by = y - head_top - 6 - bar_h",
    "shadow_w = r * 2 + (10 if is_true else 0)", "pygame.draw.ellipse(surface, (0, 0, 0, 120),",
    "(x - shadow_w // 2, y + r - 5, shadow_w, 12))", "_draw_fn = _get_boss_draw_func(self.boss_type)",
    "border_c = (255, 60, 60) if self.is_enraged else ((255, 100, 100) if is_true else (255, 200, 50))",
):
    check(_fragment in _bs_boss, f"9bq the source boss overlay must still read {_fragment!r}")
for _fragment in (
    'facing = 1 if int(getattr(boss, "direction", -1) or -1) >= 0 else -1',
    'phase = int(getattr(boss, "pulse", 0.0) * 2.0) % BOSS_ANIM_PHASES',
    'return head + ("idle", phase, moving, ability, proj)',
    'head = (boss_type, "B", klass, team, facing, hurt, rage, alive)',
    "def _boss_render_sprite_fast(boss_type, boss, draw_fn, kind):",
    "box = canvas.get_bounding_rect(min_alpha=8)",
):
    check(_fragment in _bs_pkg, f"9bq the source boss cache must still read {_fragment!r}")
check("heroes_mod._boss_render_sprite_fast(boss_type, boss, draw_fn, key[8])" in _bs_bake
      and "heroes_mod._boss_cache_key(boss_type, boss)" in _bs_bake
      and "IDLE_STEPS = 40" in _bs_bake and "ATTACK_SAMPLES = 4" in _bs_bake
      and "SKILL_SAMPLES = 2" in _bs_bake and "smart_skill_durations()" in _bs_bake
      and "draw_fn(canvas, boss, center, center)" in _bs_bake and "tight=True" in _bs_bake
      and "env.virtual_ticks(heroes_mod.pygame, ticks)" in _bs_bake
      and "MAX_TRIES = 12" in _bs_bake and "BOSS_LABEL_TOP.get(boss_type, probe.radius)" in _bs_bake,
      "9bq the bake must run real idle/walk/attack/skill timelines with direct fallback")
check("return 1 if direction > 0 else -1" in _bs_art and "ResourceLoader.exists(path_for(boss_type))" in _bs_art
      and "maxi(int(row.get(\"label_top\", radius)), radius)" in _bs_art
      and "static func _nearest(" in _bs_art and "static func resolve(" in _bs_art
      and 'return ROOT + boss_type + ".webp"' in _bs_art,
      "9bq the loader must resolve animated keyframes, facing, labels and missing imports")
check("var pose := BossAnim.from_boss(boss)" in _bs_view
      and "BossArt.frame(boss.boss_type, boss.direction, pose)" in _bs_view
      and "boss_pose_draws[pose]" in _bs_view
      and "bar_top = point.y - head_top - 6.0 - bar_height" in _bs_view
      and "var shadow := Rect2(x - (shadow_width >> 1), y + radius - 5, shadow_width, 12)" in _bs_view
      and "var shadow_width := radius * 2 + (10 if boss.boss_class == \"true\" else 0)" in _bs_view
      and "draw_colored_polygon(HeroPainter.ellipse(shadow), HeroPainter.SHADOW)" in _bs_view
      and "Rect2(corner, src.size), src, tint)" in _bs_view and "func _draw_boss_plain(" in _bs_view,
      "9bq the match view must draw animated boss poses with source overlays and fallback")
check("floori(float(active_skill_timer) / float(skill_quant))" in _bs_anim
      and "floori(float(timer) / float(attack_quant))" in _bs_anim
      and "int(pulse * 2.0) % PHASES" in _bs_anim and "PHASES := 8" in _bs_anim,
      "9bq native pose selection must mirror source skill/attack/idle cache keys")
check("_check_pose_keys(check)" in _bs_checks and "_check_sheets(check)" in _bs_checks
      and "unbaked == 0" in _bs_checks and "_check_frames(check)" in _bs_checks,
      "9bq native tests must cover every sheet, source quantum, keyframe and fallback")
check("_seed_boss(world)" in _bs_painter
      and "world._spawn_boss(BOSS_TYPE)" in _bs_painter and "view.boss_sprite_draws > 0" in _bs_painter
      and 'begins_with("skill_q_")' in _bs_painter and 'begins_with("skill_w_")' in _bs_painter
      and 'begins_with("atk")' in _bs_painter,
      "9bq the painter suite must draw attack and smart-skill poses on a live boss")

# ── Layer 9bq3: nyxareth's full-screen ultimate realm as a native screen-space layer ──
from nyxareth_realm_draw_source_oracle import source_fixture as nyxareth_realm_fixture
_nr_path = ROOT / "tests/fixtures/nyxareth_realm_draw_source.json"
_nr_layout = (ROOT / "scripts/ui/nyxareth_realm_layout.gd").read_text(encoding="utf-8")
_nr_checks = (ROOT / "tests/nyxareth_realm_draw_checks.gd").read_text(encoding="utf-8")
_nr_src = (ROOT.parent / "bosses/level17.py").read_text(encoding="utf-8")
check('const NyxarethRealmDrawChecks = preload("res://tests/nyxareth_realm_draw_checks.gd")'
      in ai_tests and "NyxarethRealmDrawChecks.new().run(_check)" in ai_tests,
      "9bq3 nyxareth realm draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/nyxareth_realm_draw_source_oracle.py" in workflow,
      "9bq3 CI must run the _draw_astro_realm_bg source oracle")
check(_nr_path.is_file(), "9bq3 nyxareth realm draw fixture must exist")
if _nr_path.is_file():
    _nr = json.loads(_nr_path.read_text(encoding="utf-8"))
    check(nyxareth_realm_fixture() == _nr,
          "9bq3 nyxareth realm draw fixture must not drift from bosses/level17.py")
    _nr_frames = _nr["frames"]
    check(len(_nr_frames) == 7 and all(len(frame["ops"]) == 109 for frame in _nr_frames),
          "9bq3 oracle must pin 7 frames of one screen fill plus 108 star rects")
    check(all(frame["ops"][0]["kind"] == "fill"
              and frame["ops"][0]["rect"] == [0, 0] + frame["screen"]
              and frame["ops"][0]["color"][:3] == [25, 5, 55] for frame in _nr_frames),
          "9bq3 oracle must pin the cosmic layer covering the whole render surface")
    check([frame["ops"][0]["color"][3] for frame in _nr_frames] == [50, 64, 80, 80, 80, 80, 80],
          "9bq3 oracle must pin the cosmic layer fading in from alpha 50 to 80")
check("def _draw_astro_realm_bg(surface, boss, x, y, timer, phase):" in _nr_src
      and "num_stars = 60" in _nr_src and "w, h = surface.get_size()" in _nr_src,
      "9bq3 the source realm must still be the 60-star layer sized by its render surface")
check("static func ops(" in _nr_layout and "const DURATION := 120" in _nr_layout
      and "const STAR_COUNT := 60" in _nr_layout and "const OPAQUE_STARS := true" in _nr_layout
      and "fposmod(float(i * 37) + phase * 5.0, float(size.x))" in _nr_layout
      and 'const SKILL := "4"' in _nr_layout,
      "9bq3 the realm layout must mirror the source formula")
_nr_draw = _bs_view[_bs_view.index("func _draw_boss(boss: BossState)"):
                    _bs_view.index("func _draw_boss_plain(")]
check("var realm_ops := nyxareth_realm_draw_ops(boss)" in _nr_draw
      and _nr_draw.index("boss_true_aura_draw_ops(boss)")
      < _nr_draw.index("nyxareth_realm_draw_ops(boss)")
      < _nr_draw.index("_draw_boss_sprite(boss, art)")
      and "boss_screen_layer_draws += 1" in _nr_draw
      and 'solid["color"] = [rgba[0], rgba[1], rgba[2], 255]' in _nr_draw,
      "9bq3 the view must paint the realm after the boss auras and before the body")
check('SCREEN_LAYERS = {"nyxareth": ("_draw_astro_realm_bg",)}' in _bs_bake,
      "9bq3 the atlas bake must keep the realm out of the body frames")
check("await _check_realm(tree, view, boss, check)" in _bs_painter
      and "view.boss_screen_layer_draws > painted_before" in _bs_painter
      and 'begins_with("skill_4_")' in _bs_painter,
      "9bq3 the painter suite must paint the realm in the live scene")
check("_check_frames(check, frames)" in _nr_checks and "_check_gate(check)" in _nr_checks
      and "_check_view_wiring(check, frames)" in _nr_checks,
      "9bq3 the realm suite must replay the source frames, the gate and the view")

# ── Layer 9bq4: urgharun's R/enrage foreground FX as a native op layer ──
from urgharun_enrage_fx_source_oracle import source_fixture as urgharun_enrage_fixture
_ue_path = ROOT / "tests/fixtures/urgharun_enrage_fx_source.json"
_ue_layout = (ROOT / "scripts/ui/urgharun_enrage_fx_layout.gd").read_text(encoding="utf-8")
_ue_checks = (ROOT / "tests/urgharun_enrage_fx_checks.gd").read_text(encoding="utf-8")
_ue_src = (ROOT.parent / "bosses/level40.py").read_text(encoding="utf-8")
_ue_fn = _ue_src[_ue_src.index("def _draw_enrage_fx("):_ue_src.index("# YHORANTH")]
_ue_order = _ue_src[_ue_src.index("def draw_urgharun("):_ue_src.index("def _update_urg_attack_anim(")]
_ue_painter = (ROOT / "tests/painter_scene_checks.gd").read_text(encoding="utf-8")
check('const UrgharunEnrageFxChecks = preload("res://tests/urgharun_enrage_fx_checks.gd")'
      in ai_tests and "UrgharunEnrageFxChecks.new().run(_check)" in ai_tests,
      "9bq4 urgharun enrage FX suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/urgharun_enrage_fx_source_oracle.py" in workflow,
      "9bq4 CI must run the _draw_enrage_fx source oracle")
check(_ue_path.is_file(), "9bq4 urgharun enrage FX fixture must exist")
if _ue_path.is_file():
    _ue = json.loads(_ue_path.read_text(encoding="utf-8"))
    check(urgharun_enrage_fixture() == _ue,
          "9bq4 urgharun enrage FX fixture must not drift from bosses/level40.py")
    _ue_frames = _ue["frames"]
    check(len(_ue_frames) == 7 and all(len(frame["ops"]) == 68 for frame in _ue_frames)
          and sum(len(frame["ops"]) for frame in _ue_frames) == 476,
          "9bq4 oracle must pin 7 frames of 68 ops (ten flames, the aura ring, six embers)")
    _ue_mid = next(f for f in _ue_frames if f["label"] == "mid")
    _ue_ignored = next(f for f in _ue_frames if f["label"] == "timer_ignored")
    check(_ue_mid["timer"] != _ue_ignored["timer"]
          and _ue_mid["ops"] == _ue_ignored["ops"],
          "9bq4 oracle must pin the source quirk: the cast timer never changes an op")
    _ue_cast = next(f for f in _ue_frames if f["label"] == "cast")
    check([op["radius"] for op in _ue_mid["ops"][50:56]] == [38, 37, 36, 35, 34, 33]
          and [op["color"][3] for op in _ue_cast["ops"][0:50:5]]
          == [220, 187, 154, 121, 88, 55, 22, 209, 176, 143]
          and [op["color"][3] for op in _ue_mid["ops"][56:68:2]] == [211, 175, 139, 103, 67, 31]
          and _ue["palette"]["fury_light"] == [255, 110, 90],
          "9bq4 oracle must pin the aura ring radii, the flame/ember alpha decay and the palette")
    check(_ue["boss_type"] == "urgharun" and _ue["skill"] == "r" and _ue["duration"] == 80,
          "9bq4 the layer belongs to urgharun's R cast normalised by 80 ticks")
check("def _draw_enrage_fx(surface, boss, x, y, timer, pulse):" in _ue_src
      and "def _draw_enrage_ground(surface, boss, x, y, timer, phase):" in _ue_src,
      "9bq4 the source must still split the R ground FX from its foreground FX")
check(_ue_fn.count("progress") == 1 and "duration = 80" in _ue_fn
      and "flame_h = int(6 + flame_t * 4)" in _ue_fn,
      "9bq4 the source foreground FX must still drop progress and flame_h")
check(_ue_order.index("_draw_enrage_ground(surface, boss, x, y, skill_timer, pulse)")
      < _ue_order.index("_draw_urg_attack(surface, boss, x, y, active_skill)")
      < _ue_order.index("_draw_enrage_fx(surface, boss, x, y, skill_timer, pulse)"),
      "9bq4 the source must paint the enrage foreground after the body and the ground FX")
check('const SKILL := "r"' in _ue_layout and "const DURATION := 80" in _ue_layout
      and "const FLAME_COUNT := 10" in _ue_layout and "const AURA_TOP := 38" in _ue_layout
      and "const AURA_BOTTOM := 32" in _ue_layout and "const EMBER_COUNT := 6" in _ue_layout
      and "int(cos(angle) * float(FLAME_RADIUS))" in _ue_layout
      and "fposmod(pulse * 0.6 + float(index) * 0.15, 1.0)" in _ue_layout
      and "int(flame_t * 20.0)" in _ue_layout
      and "range(AURA_TOP, AURA_BOTTOM, -1)" in _ue_layout
      and "_alpha(180.0 * aura_pulse * float(AURA_TOP - radius) / float(AURA_STEPS))" in _ue_layout
      and "_alpha(240.0 * (1.0 - ember_t))" in _ue_layout,
      "9bq4 the enrage layout must mirror the source flame, aura and ember formulas")
_ue_draw = _bs_view[_bs_view.index("func _draw_boss(boss: BossState)"):
                    _bs_view.index("func _draw_boss_plain(")]
check("func urgharun_enrage_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "UrgharunEnrageFxLayout.active(boss.boss_type, boss.active_skill)" in _bs_view
      and "int(boss.position.x), int(boss.position.y), boss.active_skill_timer, boss.pulse"
      in _bs_view,
      "9bq4 the view must build the layer from the live anchor, cast timer and pulse")
check("var enrage_ops := urgharun_enrage_draw_ops(boss)" in _ue_draw
      and _ue_draw.index("_draw_boss_sprite(boss, art)")
      < _ue_draw.index("urgharun_enrage_draw_ops(boss)")
      < _ue_draw.index("var bar_position := Vector2(")
      and "boss_enrage_fx_draws += 1" in _ue_draw
      and "boss_enrage_fx_ops += enrage_ops.size()" in _ue_draw,
      "9bq4 the view must paint the enrage layer over the body and under the HP bar")
check("await _check_urgharun_enrage(tree, view, boss, check)" in _ue_painter
      and "view.boss_enrage_fx_draws > draws_before" in _ue_painter
      and 'boss.boss_type = "urgharun"' in _ue_painter
      and "int(count) % 68 == 0" in _ue_painter,
      "9bq4 the painter suite must paint the enrage layer across the live cast phases")
check("_check_frames(check, frames)" in _ue_checks and "_check_timing(check, frames)" in _ue_checks
      and "_check_gate(check)" in _ue_checks and "_check_view_wiring(check, frames)" in _ue_checks,
      "9bq4 the enrage suite must replay the source frames, the timing quirk, the gate and the view")

# ── Layer 9bq5: urgharun's R/enrage ground FX (behind the body) ──
from urgharun_enrage_ground_source_oracle import source_fixture as urgharun_ground_fixture
_ug_path = ROOT / "tests/fixtures/urgharun_enrage_ground_source.json"
_ug_layout = (ROOT / "scripts/ui/urgharun_enrage_ground_layout.gd").read_text(encoding="utf-8")
_ug_checks = (ROOT / "tests/urgharun_enrage_ground_checks.gd").read_text(encoding="utf-8")
_ug_painter = (ROOT / "tests/painter_scene_checks.gd").read_text(encoding="utf-8")
_ug_src = (ROOT.parent / "bosses/level40.py").read_text(encoding="utf-8")
_ug_fn = _ug_src[_ug_src.index("def _draw_enrage_ground("):_ug_src.index("def _draw_enrage_fx(")]
check('const UrgharunEnrageGroundChecks = preload("res://tests/urgharun_enrage_ground_checks.gd")'
      in ai_tests and "UrgharunEnrageGroundChecks.new().run(_check)" in ai_tests,
      "9bq5 urgharun enrage ground suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/urgharun_enrage_ground_source_oracle.py" in workflow,
      "9bq5 CI must run the _draw_enrage_ground source oracle")
check(_ug_path.is_file(), "9bq5 urgharun enrage ground fixture must exist")
if _ug_path.is_file():
    _ug = json.loads(_ug_path.read_text(encoding="utf-8"))
    check(urgharun_ground_fixture() == _ug,
          "9bq5 urgharun enrage ground fixture must not drift from bosses/level40.py")
    _ug_frames = _ug["frames"]
    check(len(_ug_frames) == 8 and all(len(frame["ops"]) == 26 for frame in _ug_frames)
          and sum(len(frame["ops"]) for frame in _ug_frames) == 208,
          "9bq5 oracle must pin 8 frames of 26 ops (six ring outlines, ten rune pairs)")
    _ug_mid = next(f for f in _ug_frames if f["label"] == "mid")
    _ug_ignored = next(f for f in _ug_frames if f["label"] == "timer_ignored")
    check(_ug_mid["timer"] != _ug_ignored["timer"]
          and _ug_mid["ops"] == _ug_ignored["ops"],
          "9bq5 oracle must pin the source quirk: the cast timer never changes an op")
    check([op["width"] for op in _ug_mid["ops"][:6]] == [3, 2, 1, 3, 2, 1]
          and [op["color"][3] for op in _ug_mid["ops"][:6]] == [218, 218, 218, 178, 178, 178]
          and [op["color"][3] for op in _ug_mid["ops"][7:26:2]] == [255] * 10
          and _ug["palette"]["fury_hot"] == [255, 180, 140],
          "9bq5 oracle must pin the nested ring widths, the ring alpha and the opaque rune cores")
check("def _draw_enrage_ground(surface, boss, x, y, timer, phase):" in _ug_src
      and _ug_fn.count("progress") == 1 and "duration = 80" in _ug_fn
      and "r = int(35 + i * 8 + math.sin(phase * 2) * 3)" in _ug_fn
      and "alpha = _NS_urgharun._alpha(220 * pulse - i * 40)" in _ug_fn
      and "rune_r = 38" in _ug_fn,
      "9bq5 the source ground FX must still drop progress and use the recorded ring formula")
check('const SKILL := "r"' in _ug_layout and "const RING_COUNT := 2" in _ug_layout
      and "const RUNE_COUNT := 10" in _ug_layout and "const RUNE_RADIUS := 38" in _ug_layout
      and "int(35.0 + float(index) * 8.0 + sin(pulse * 2.0) * 3.0)" in _ug_layout
      and "_alpha(220.0 * ring_pulse - float(index) * 40.0)" in _ug_layout
      and "floori(float(radius) / 3.0)" in _ug_layout and "floori(float(radius * 2) / 3.0)" in _ug_layout
      and "int(sin(angle) * float(RUNE_RADIUS) * 0.4)" in _ug_layout
      and "out.append(_rect([rune_x, rune_y, 1, 1], FURY_SHINE, 255))" in _ug_layout,
      "9bq5 the ground layout must mirror the source ring, rune and core formulas")
check("func urgharun_enrage_ground_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "UrgharunEnrageGroundLayout.active(boss.boss_type, boss.active_skill)" in _bs_view,
      "9bq5 the view must gate the ground layer on urgharun's R")
_ug_draw = _bs_view[_bs_view.index("func _draw_boss(boss: BossState)"):
                    _bs_view.index("func _draw_boss_plain(")]
check("var ground_ops := urgharun_enrage_ground_draw_ops(boss)" in _ug_draw
      and _ug_draw.index("nyxareth_realm_draw_ops(boss)")
      < _ug_draw.index("urgharun_enrage_ground_draw_ops(boss)")
      < _ug_draw.index("var art := BossArt.frame(")
      and "boss_enrage_ground_draws += 1" in _ug_draw and "boss_enrage_ground_ops += 1" not in _ug_draw,
      "9bq5 the view must paint the ground FX after the aura rings and before the body")
check('"ellipse":' in _bs_view and "func _ellipse_outline(rect: Rect2) -> PackedVector2Array:"
      in _bs_view and "draw_polyline(outline, color, float(ellipse_width), true)" in _bs_view
      and "draw_colored_polygon(_ellipse_outline(ellipse_rect), color)" in _bs_view,
      "9bq5 the shared op painter must render the source's ellipse fill and outline")
check("boss_enrage_ground_draws > ground_before" in _ug_painter
      and "int(count) % 26 == 0" in _ug_painter,
      "9bq5 the painter suite must paint the ground layer across the live cast phases")
check("_check_frames(check, frames)" in _ug_checks and "_check_rings(check, frames)" in _ug_checks
      and "_check_timing(check, frames)" in _ug_checks and "_check_view_wiring(check, frames)"
      in _ug_checks,
      "9bq5 the ground suite must replay the frames, the rings, the timing quirk and the view")

# ── Layer 9bq6: urgharun LAYER 1 (fury aura + ground ring) and the Q/W/E skill FX ──
from urgharun_skill_fx_source_oracle import source_fixture as urgharun_skill_fixture
_us_path = ROOT / "tests/fixtures/urgharun_skill_fx_source.json"
_us_layout = (ROOT / "scripts/ui/urgharun_skill_fx_layout.gd").read_text(encoding="utf-8")
_us_checks = (ROOT / "tests/urgharun_skill_fx_checks.gd").read_text(encoding="utf-8")
_us_painter = (ROOT / "tests/painter_scene_checks.gd").read_text(encoding="utf-8")
_us_view_preloads_unit_state = ('const UnitState = preload(' in _bs_view)
_us_battle = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
_us_src = (ROOT.parent / "bosses/level40.py").read_text(encoding="utf-8")
_us_urg = _us_src[_us_src.index("class _NS_urgharun:"):_us_src.index("class _NS_yhoranth:")]
check('const UrgharunSkillFxChecks = preload("res://tests/urgharun_skill_fx_checks.gd")'
      in ai_tests and "UrgharunSkillFxChecks.new().run(_check)" in ai_tests,
      "9bq6 urgharun skill FX suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/urgharun_skill_fx_source_oracle.py" in workflow,
      "9bq6 CI must run the layer 1 / Q-W-E source oracle")
check(_us_path.is_file(), "9bq6 urgharun skill FX fixture must exist")
if _us_path.is_file():
    _us = json.loads(_us_path.read_text(encoding="utf-8"))
    check(urgharun_skill_fixture() == _us,
          "9bq6 urgharun skill FX fixture must not drift from bosses/level40.py")
    _us_groups = ["aura_frames", "ring_frames", "earthshock_ground_frames",
                  "earthshock_fx_frames", "overpower_frames", "furyswipes_frames"]
    check(sum(len(_us[key]) for key in _us_groups) == 27
          and sum(len(f["ops"]) for key in _us_groups for f in _us[key]) == 1236,
          "9bq6 oracle must pin 27 frames and 1236 draw ops")
    check([len(f["ops"]) for f in _us["aura_frames"]] == [54, 54, 62, 62, 62]
          and [len(f["ops"]) for f in _us["ring_frames"]] == [13, 13, 14, 14, 14],
          "9bq6 oracle must pin the 12/16-ember aura and the optional ring ellipse")
    check(len(_us["earthshock_ground_frames"][0]["ops"]) == 0
          and len(_us["furyswipes_frames"][0]["ops"]) == 0
          and len(_us["furyswipes_frames"][-1]["ops"]) == 0,
          "9bq6 oracle must pin the Q and E frames that draw nothing")
    check(all(f["target"] is None for f in _us["overpower_frames"]
              if f["label"] == "w_no_target")
          and any(f["target"] is not None for f in _us["overpower_frames"]),
          "9bq6 oracle must cover both source branches of the W/E target lookup")
check("def _draw_fury_aura(surface, x, y, phase, enraged=False):" in _us_urg
      and "def _draw_ground_ring(surface, x, y, phase, skill):" in _us_urg
      and "_NS_urgharun._draw_ground_ring(surface, x, y + 50, pulse, active_skill)"
      in _us_urg
      and "_NS_urgharun._draw_fury_aura(surface, x, y, pulse,\n                                      enraged=(active_skill == \"r\"))" in _us_urg,
      "9bq6 the source must still paint LAYER 1 first, with the ring 50 px below the anchor")
check("const Q_DURATION := 55" in _us_layout and "const W_DURATION := 50" in _us_layout
      and "const E_DURATION := 40" in _us_layout and "const RING_Y_OFFSET := 50" in _us_layout
      and "const RING_BLIT := [85, 27]" in _us_layout
      and "for radius in range(90, 5, -5)" in _us_layout
      and "float(index) * PI / half" in _us_layout
      and "_ellipse([left + 15, top + 12, 140, 38], FURY_HOT, _alpha(150.0 * pulse), 1)"
      in _us_layout
      and "while step < crack_len" in _us_layout
      and "fposmod(" in _us_layout and "if progress > 0.5 and target.size() >= 2:" in _us_layout
      and "if slash_t <= 0.0 or slash_t > 1.2:" in _us_layout,
      "9bq6 the skill layout must mirror the source aura, ring, Q, W and E formulas")
check("func urgharun_aura_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "func urgharun_skill_ground_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "func urgharun_skill_fg_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "func urgharun_target_point() -> Array:" in _bs_view
      and "world.boss_presentation_target()" in _bs_view,
      "9bq6 the view must build LAYER 1 and the Q/W/E layers from live state")
check("func boss_presentation_target() -> UnitState:" in _us_battle
      and "return _boss_target(_boss_enemies())" in _us_battle,
      "9bq6 the world must expose a read-only boss target query for the W/E layers")
check(not _us_view_preloads_unit_state,
      "9bq6 the view must not re-declare the parent's UnitState preload")
_us_draw = _bs_view[_bs_view.index("func _draw_boss(boss: BossState)"):
                    _bs_view.index("func _draw_boss_plain(")]
check("var aura_ops := urgharun_aura_draw_ops(boss)" in _us_draw
      and _us_draw.index("urgharun_aura_draw_ops(boss)")
      < _us_draw.index("nyxareth_realm_draw_ops(boss)")
      < _us_draw.index("urgharun_skill_ground_draw_ops(boss)")
      and _us_draw.index("urgharun_skill_ground_draw_ops(boss)")
      < _us_draw.index("var art := BossArt.frame(")
      and "var skill_fg_ops := urgharun_skill_fg_draw_ops(boss)" in _us_draw
      and _us_draw.index("urgharun_skill_fg_draw_ops(boss)")
      < _us_draw.index("urgharun_enrage_draw_ops(boss)")
      < _us_draw.index("var bar_position := Vector2("),
      "9bq6 the view must paint LAYER 1 below everything and the skill layers around the body")
check("view.boss_aura_fx_draws > aura_before" in _us_painter
      and "view.boss_skill_ground_draws > q_ground_before" in _us_painter
      and "view.boss_skill_fg_draws > q_fg_before" in _us_painter,
      "9bq6 the painter suite must paint the LAYER 1 and Q layers on the live boss")
check("_check_aura(check, data)" in _us_checks and "_check_ring(check, data)" in _us_checks
      and "_check_earthshock(check, data)" in _us_checks
      and "_check_overpower(check, data)" in _us_checks
      and "_check_furyswipes(check, data)" in _us_checks
      and "_check_view_wiring(check, data)" in _us_checks
      and "func _report(" in _us_checks,
      "9bq6 the skill suite must replay every group, the wiring and name a first mismatch")

# ── Layer 9bq7: the cached `Boss.draw` aura block (ability, enrage, true boss) ──
from boss_aura_fx_source_oracle import source_fixture as boss_aura_fixture
_ba_path = ROOT / "tests/fixtures/boss_aura_fx_source.json"
_ba_layout = (ROOT / "scripts/ui/boss_aura_fx_layout.gd").read_text(encoding="utf-8")
_ba_checks = (ROOT / "tests/boss_aura_fx_checks.gd").read_text(encoding="utf-8")
_ba_base = (ROOT.parent / "bosses/base_boss.py").read_text(encoding="utf-8")
check('const BossAuraFxChecks = preload("res://tests/boss_aura_fx_checks.gd")' in ai_tests
      and "BossAuraFxChecks.new().run(_check)" in ai_tests,
      "9bq7 boss aura suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/boss_aura_fx_source_oracle.py" in workflow,
      "9bq7 CI must run the cached aura source oracle")
check(_ba_path.is_file(), "9bq7 boss aura fixture must exist")
if _ba_path.is_file():
    _ba = json.loads(_ba_path.read_text(encoding="utf-8"))
    check(boss_aura_fixture() == _ba,
          "9bq7 boss aura fixture must not drift from bosses/base_boss.py")
    _ba_groups = ["ability_frames", "enrage_frames", "true_boss_frames"]
    check(sum(len(_ba[key]) for key in _ba_groups) == 12
          and sum(len(f["ops"]) for key in _ba_groups for f in _ba[key]) == 69,
          "9bq7 oracle must pin 12 source frames and 69 draw ops")
    check([len(f["ops"]) for f in _ba["ability_frames"]] == [6, 6, 6, 6]
          and [len(f["ops"]) for f in _ba["enrage_frames"]] == [5, 5, 5, 5, 4]
          and [len(f["ops"]) for f in _ba["true_boss_frames"]] == [7, 7, 7],
          "9bq7 oracle must pin the three ring bands, including the clamped tiny boss")
    check(all(_op["width"] == 2 for f in _ba["enrage_frames"] for _op in f["ops"])
          and all(_op["width"] == 0
                  for key in ("ability_frames", "true_boss_frames")
                  for f in _ba[key] for _op in f["ops"]),
          "9bq7 only the enrage aura strokes outlines; the other two fill their rings")
check("def _draw_enrage_aura(self, surface, x, y):" in _ba_base
      and "def _draw_true_boss_aura(self, surface, x, y):" in _ba_base
      and "def _aura_surface(key, builder):" in _ba_base,
      "9bq7 the source must still cache its three auras through `_aura_surface`")
_ba_draw = _ba_base[_ba_base.index("    def draw(self, surface"):]
_ba_draw = _ba_draw[:_ba_draw.index("    def _draw_enrage_aura(self")]
check("if self.ability_active:" in _ba_draw
      and _ba_draw.index("if self.ability_active:")
      < _ba_draw.index("self._draw_enrage_aura(surface, x, y)")
      < _ba_draw.index("self._draw_true_boss_aura(surface, x, y)"),
      "9bq7 `Boss.draw` must keep the ability -> enrage -> true aura order")
check("for radius in range(aura_radius, aura_radius - 20, -3):" in _ba_layout
      and "for offset in range(aura_radius, maxi(ENRAGE_MIN_RADIUS, aura_radius - 18), -3):"
      in _ba_layout
      and "for offset in range(aura_radius, aura_radius - 15, -2):" in _ba_layout
      and "* 8.0 * pulse), 0, 255)" in _ba_layout
      and "* 12.0 * pulse), 0, 200)" in _ba_layout
      and "* 5.0 * pulse), 0, 255)" in _ba_layout
      and "var aura_radius := radius + int(14.0 * pulse)" in _ba_layout,
      "9bq7 the aura layout must mirror the source bands, steps and alpha caps")
check("func boss_ability_aura_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "func boss_enrage_aura_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "func boss_true_aura_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "boss.ability_active" in _bs_view and "boss.is_enraged" in _bs_view,
      "9bq7 the view must build all three auras from live state")
_ba_boss_draw = _bs_view[_bs_view.index("func _draw_boss(boss: BossState)"):
                         _bs_view.index("func _draw_boss_plain(")]
check(_ba_boss_draw.index("boss_ability_aura_draw_ops(boss)")
      < _ba_boss_draw.index("boss_enrage_aura_draw_ops(boss)")
      < _ba_boss_draw.index("boss_true_aura_draw_ops(boss)")
      < _ba_boss_draw.index("urgharun_aura_draw_ops(boss)")
      < _ba_boss_draw.index("var art := BossArt.frame("),
      "9bq7 the view must paint the aura block before the body, in source order")
check("draw_arc(point, enrage_radius" not in _bs_view
      and "Color(boss.entrance_color, 0.30)" not in _bs_view
      and "Color(boss.color, 0.28 * true_pulse)" not in _bs_view,
      "9bq7 the flat one-arc aura approximations must be gone")
check("view.boss_ability_aura_draws > ability_before" in _us_painter
      and "view.boss_enrage_aura_draws > enrage_before" in _us_painter
      and "view.boss_true_aura_draws > true_before" in _us_painter,
      "9bq7 the painter suite must paint all three auras on the live boss")
check("_check_ability(check, data)" in _ba_checks and "_check_enrage(check, data)" in _ba_checks
      and "_check_true_boss(check, data)" in _ba_checks
      and "_check_view_wiring(check, data)" in _ba_checks
      and "func _report(" in _ba_checks,
      "9bq7 the aura suite must replay each band, the wiring and name a first mismatch")

# ── Layer 9bq8: urgharun's basic-attack FX and the per-frame swing clock ──
from urgharun_basic_attack_source_oracle import source_fixture as urgharun_basic_fixture
_ub_path = ROOT / "tests/fixtures/urgharun_basic_attack_source.json"
_ub_checks = (ROOT / "tests/urgharun_basic_attack_checks.gd").read_text(encoding="utf-8")
_ub_clock = (ROOT / "scripts/ui/urgharun_attack_clock.gd").read_text(encoding="utf-8")
_ub_src = (ROOT.parent / "bosses/level40.py").read_text(encoding="utf-8")
_ub_urg = _ub_src[_ub_src.index("class _NS_urgharun:"):_ub_src.index("class _NS_yhoranth:")]
check('const UrgharunBasicAttackChecks = preload("res://tests/urgharun_basic_attack_checks.gd")'
      in ai_tests and "UrgharunBasicAttackChecks.new().run(_check)" in ai_tests,
      "9bq8 urgharun basic-attack suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/urgharun_basic_attack_source_oracle.py" in workflow,
      "9bq8 CI must run the basic-attack / swing-clock source oracle")
check(_ub_path.is_file(), "9bq8 urgharun basic-attack fixture must exist")
if _ub_path.is_file():
    _ub = json.loads(_ub_path.read_text(encoding="utf-8"))
    check(urgharun_basic_fixture() == _ub,
          "9bq8 urgharun basic-attack fixture must not drift from bosses/level40.py")
    _ub_frames = _ub["fx_frames"]
    _ub_steps = sum(len(run["steps"]) for run in _ub["clock_runs"])
    check(len(_ub_frames) == 11
          and sum(len(frame["ops"]) for frame in _ub_frames) == 1132
          and len(_ub["clock_runs"]) == 5 and _ub_steps == 52
          and _ub["attack_duration"] == 28,
          "9bq8 oracle must pin 11 frames / 1132 ops and 5 clock runs / 52 steps")
    check([len(frame["ops"]) for frame in _ub_frames]
          == [6, 8, 10, 246, 246, 246, 31, 31, 31, 31, 246],
          "9bq8 oracle must pin the wind-up, slash and impact op counts")
    check(_ub_frames[0]["ops"][0]["color"][3] == 0
          and any(frame["target"] is None for frame in _ub_frames)
          and any(frame["target"] is not None for frame in _ub_frames),
          "9bq8 oracle must pin the transparent first wind-up frame and both target branches")
check("def _draw_basic_attack_fx(surface, boss, x, y):" in _ub_urg
      and "def _update_urg_attack_anim(boss):" in _ub_urg
      and "if attacking and not active_skill:" in _ub_urg
      and "_NS_urgharun._update_urg_attack_anim(boss)" in _ub_urg,
      "9bq8 the source must still advance the clock in draw and gate the FX on no cast")
_ub_layout = (ROOT / "scripts/ui/urgharun_skill_fx_layout.gd").read_text(encoding="utf-8")
check("const ATTACK_DURATION := 28" in _ub_layout
      and "const WHITE := [255, 255, 255]" in _ub_layout
      and "static func basic_attack_ops(" in _ub_layout
      and "if progress < 0.3:" in _ub_layout and "elif progress < 0.7:" in _ub_layout
      and "var rings := int(3.0 + windup * 3.0)" in _ub_layout
      and "var start_angle := deg_to_rad(-70.0 if facing == 1 else -110.0)" in _ub_layout
      and "for radius in range(4, 0, -1):" in _ub_layout
      and "var spark_r := float(arc_radius) + sin(phase * 3.0 + float(index)) * 8.0" in _ub_layout
      and "if distance > 80.0:" in _ub_layout,
      "9bq8 the layout must mirror the source wind-up, slash arc, sparks and melee clamp")
check("const ATTACK_DURATION := 28" in _ub_clock and "const MIN_COOLDOWN := 2" in _ub_clock
      and "var just_reset := previous > cooldown - 5 and timer < 3" in _ub_clock
      and "var near_max := timer >= cooldown - 1" in _ub_clock
      and "if (just_reset or near_max) and not active:" in _ub_clock
      and "if frame >= ATTACK_DURATION:" in _ub_clock,
      "9bq8 the swing clock must mirror `_update_urg_attack_anim`")
check("func urgharun_attack_clock(boss: BossState) -> UrgharunAttackClock:" in _bs_view
      and "func urgharun_attack_clock_step(boss: BossState) -> void:" in _bs_view
      and "func urgharun_basic_attack_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "urgharun_attack_clock(boss).advance(boss.timer, boss.attack_cooldown)" in _bs_view
      and "clock.active or not boss.active_skill.is_empty()" in _bs_view,
      "9bq8 the view must advance the clock and gate the FX from live state")
_ub_draw = _bs_view[_bs_view.index("func _draw_boss(boss: BossState)"):
                    _bs_view.index("func _draw_boss_plain(")]
check(_ub_draw.index("urgharun_attack_clock_step(boss)")
      < _ub_draw.index("boss_ability_aura_draw_ops(boss)")
      and "var basic_attack_ops := urgharun_basic_attack_draw_ops(boss)" in _ub_draw
      and _ub_draw.index("urgharun_basic_attack_draw_ops(boss)")
      < _ub_draw.index("urgharun_skill_fg_draw_ops(boss)")
      < _ub_draw.index("urgharun_enrage_draw_ops(boss)")
      and "boss_basic_attack_fg_ops += basic_attack_ops.size()" in _ub_draw,
      "9bq8 the view must advance the clock first and paint the FX before the skill layers")
check("view.boss_basic_attack_fg_draws > draws_before" in _us_painter
      and "view.boss_basic_attack_fg_draws == gated_before" in _us_painter,
      "9bq8 the painter suite must paint the swing and honour the cast gate")
check("_check_frames(check, data)" in _ub_checks and "_check_phases(check, data)" in _ub_checks
      and "_check_clock(check, data)" in _ub_checks
      and "_check_view_wiring(check, data)" in _ub_checks and "func _report(" in _ub_checks,
      "9bq8 the basic-attack suite must replay the frames, the clock and the view")

# ── Layer 9bq9: the debuff indicator `Boss.draw` paints (slow ring, flames, pips) ──
from boss_debuff_fx_source_oracle import source_fixture as boss_debuff_fixture
_bd_path = ROOT / "tests/fixtures/boss_debuff_fx_source.json"
_bd_layout = (ROOT / "scripts/ui/boss_debuff_fx_layout.gd").read_text(encoding="utf-8")
_bd_checks = (ROOT / "tests/boss_debuff_fx_checks.gd").read_text(encoding="utf-8")
_bd_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
check('const BossDebuffFxChecks = preload("res://tests/boss_debuff_fx_checks.gd")' in ai_tests
      and "BossDebuffFxChecks.new().run(_check)" in ai_tests,
      "9bq9 boss debuff suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/boss_debuff_fx_source_oracle.py" in workflow,
      "9bq9 CI must run the tower-debuff source oracle")
check(_bd_path.is_file(), "9bq9 boss debuff fixture must exist")
if _bd_path.is_file():
    _bd = json.loads(_bd_path.read_text(encoding="utf-8"))
    check(boss_debuff_fixture() == _bd,
          "9bq9 boss debuff fixture must not drift from _core.py")
    check(len(_bd["frames"]) == 8
          and sum(len(frame["ops"]) for frame in _bd["frames"]) == 69
          and [len(frame["ops"]) for frame in _bd["frames"]] == [0, 3, 8, 8, 17, 17, 16, 0],
          "9bq9 oracle must pin 8 frames and 69 ops, one per debuff combination")
    check(_bd["frames"][4]["ops"][0]["kind"] == "ellipse"
          and any(float(frame["anim_time"]).is_integer() for frame in _bd["frames"]),
          "9bq9 the slow ring must stay an ellipse and one frame must carry an integer clock")
check("def _draw_tower_debuff_fx(self, surface, x, y, radius=14," in _bd_core
      and "include_rings=True):" in _bd_core
      and "self._draw_tower_debuff_fx(surface, x, y, r)" in
      (ROOT.parent / "bosses/base_boss.py").read_text(encoding="utf-8"),
      "9bq9 the source must still share the indicator with `Boss.draw`")
check("const SLOW := [150, 220, 255]" in _bd_layout
      and "const ATK_SLOW := [90, 160, 255]" in _bd_layout
      and "const SKILL_DOWN := [200, 120, 255]" in _bd_layout
      and "const ANTI_HEAL := [255, 90, 140]" in _bd_layout
      and "const BURN_PIP := [255, 130, 40]" in _bd_layout
      and "var flick := int(1.5 + 1.5 * sin(anim_time * 0.6))" in _bd_layout
      and "var pip_y := y + radius + PIP_RADIUS_OFFSET" in _bd_layout
      and "var px := x - floori(float(total_w) / 2.0)" in _bd_layout,
      "9bq9 the layout must mirror the source ring, flames and pip row")
check("func boss_debuff_draw_ops(boss: BossState) -> Array:" in _bs_view
      and "boss.slow_timer," in _bs_view and "boss.anti_heal_timer," in _bs_view
      and "float(boss.anim_time)" in _bs_view,
      "9bq9 the view must build the indicator from the live debuff timers")
_bd_draw = _bs_view[_bs_view.index("func _draw_boss(boss: BossState)"):
                    _bs_view.index("func _draw_boss_plain(")]
check(_bd_draw.index("boss_true_aura_draw_ops(boss)")
      < _bd_draw.index("boss_debuff_draw_ops(boss)")
      < _bd_draw.index("urgharun_aura_draw_ops(boss)")
      and "boss_debuff_fx_ops += debuff_ops.size()" in _bd_draw,
      "9bq9 the view must paint the indicator after the auras and before the per-type layers")
check("view.boss_debuff_fx_draws > debuffed_before" in _us_painter
      and "view.boss_debuff_fx_draws == clean_before" in _us_painter,
      "9bq9 the painter suite must paint the indicator only while a debuff runs")
check("_check_frames(check, data)" in _bd_checks and "_check_shape(check, data)" in _bd_checks
      and "_check_view_wiring(check, data)" in _bd_checks and "func _report(" in _bd_checks,
      "9bq9 the debuff suite must replay the frames, the shape and the view")

# ── Layer 9bq10: the same indicator at the `_entity.py` hero and minion call sites ──
from entity_debuff_fx_source_oracle import source_fixture as entity_debuff_fixture
_ed_path = ROOT / "tests/fixtures/entity_debuff_fx_source.json"
_ed_checks = (ROOT / "tests/entity_debuff_fx_checks.gd").read_text(encoding="utf-8")
_ed_painter = (ROOT / "scripts/ui/debuff_fx_painter.gd").read_text(encoding="utf-8")
_ed_hero_painter = (ROOT / "scripts/ui/hero_painter.gd").read_text(encoding="utf-8")
_ed_minion_view = (ROOT / "scenes/combat/minion_view.gd").read_text(encoding="utf-8")
_ed_entity = (ROOT.parent / "_entity.py").read_text(encoding="utf-8")
check('const EntityDebuffFxChecks = preload("res://tests/entity_debuff_fx_checks.gd")' in ai_tests
      and "EntityDebuffFxChecks.new().run(_check)" in ai_tests,
      "9bq10 entity debuff suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/entity_debuff_fx_source_oracle.py" in workflow,
      "9bq10 CI must run the hero/minion debuff source oracle")
check(_ed_path.is_file(), "9bq10 entity debuff fixture must exist")
if _ed_path.is_file():
    _ed = json.loads(_ed_path.read_text(encoding="utf-8"))
    check(entity_debuff_fixture() == _ed,
          "9bq10 entity debuff fixture must not drift from _entity.py and _core.py")
    check(len(_ed["frames"]) == 8
          and sum(len(frame["ops"]) for frame in _ed["frames"]) == 54
          and [len(frame["ops"]) for frame in _ed["frames"]] == [0, 3, 8, 17, 2, 8, 16, 0],
          "9bq10 oracle must pin 8 frames, 54 ops and the hero/minion split")
    check(_ed["call_sites"]["Hero"]["args"] == ["surface", "x", "y", "self.radius"]
          and _ed["call_sites"]["Hero"]["kwargs"] == {}
          and int(_ed["call_sites"]["Hero"]["radius"]) == 16,
          "9bq10 `Hero.draw` must keep its own radius and the default ring flag")
    check(_ed["call_sites"]["Minion"]["kwargs"] == {"include_rings": "False"}
          and "_draw_hero_shape" in _ed["call_sites"]["Hero"]["after"]
          and "self.slow_timer > 0" in _ed["call_sites"]["Minion"]["before"],
          "9bq10 the call sites must keep their position and their ring flag")
check("self._draw_tower_debuff_fx(surface, x, y, self.radius)" in _ed_entity
      and "self._draw_tower_debuff_fx(surface, x, y, self.radius,\n                                   include_rings=False)"
      in _ed_entity,
      "9bq10 `_entity.py` must still call the shared indicator from both draws")
check("const HERO_DEBUFF_RADIUS := 16" in _bs_view
      and "func hero_debuff_draw_ops(hero: HeroState, anim: float) -> Array:" in _bs_view
      and "hero.anti_heal_timer," in _bs_view,
      "9bq10 the view must build the hero indicator from the live timers at radius 16")
_ed_hero_paint = _ed_hero_painter[_ed_hero_painter.index("static func paint("):]
check("debuff_ops: Array = []" in _ed_hero_paint
      and _ed_hero_paint.index("_ellipse(shadow)")
      < _ed_hero_paint.index("DebuffFxPainter.paint(canvas, debuff_ops)")
      < _ed_hero_paint.index("draw_texture_rect_region"),
      "9bq10 the hero painter must paint the indicator after the shadow, before the body")
check("func minion_debuff_draw_ops(unit: UnitState, anim: int) -> Array:" in _ed_minion_view
      and "int(unit.definition.radius_px)," in _ed_minion_view
      and _ed_minion_view.index("_draw_minion_slow(point, radius")
      < _ed_minion_view.index("DebuffFxPainter.paint(self, debuff_ops)")
      < _ed_minion_view.index("draw_texture_rect_region"),
      "9bq10 the minion view must paint the indicator after the ice aura, before the body")
check('"ellipse"' in _ed_painter and '"circle"' in _ed_painter
      and 'canvas.draw_polyline(path, color, float(width), true)' in _ed_painter,
      "9bq10 the shared painter must cover the layout's ellipse, circle and rect ops")
check("_check_call_sites(check, data)" in _ed_checks
      and "_check_hero_wiring(check, data)" in _ed_checks
      and "_check_minion_wiring(check, data)" in _ed_checks,
      "9bq10 the entity suite must replay the call sites and both wirings")

# ── Layer 9bq11: `Boss._draw_entrance` (entrance aura and wrapped title) ──
from boss_entrance_draw_source_oracle import source_fixture as boss_entrance_fixture
_be_path = ROOT / "tests/fixtures/boss_entrance_draw_source.json"
_be_layout = (ROOT / "scripts/ui/boss_entrance_layout.gd").read_text(encoding="utf-8")
_be_checks = (ROOT / "tests/boss_entrance_draw_checks.gd").read_text(encoding="utf-8")
_be_boss = (ROOT.parent / "bosses/base_boss.py").read_text(encoding="utf-8")
check('const BossEntranceDrawChecks = preload("res://tests/boss_entrance_draw_checks.gd")' in ai_tests
      and "BossEntranceDrawChecks.new().run(_check)" in ai_tests,
      "9bq11 entrance suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/boss_entrance_draw_source_oracle.py" in workflow,
      "9bq11 CI must run the entrance source oracle")
check(_be_path.is_file(), "9bq11 entrance fixture must exist")
if _be_path.is_file():
    _be = json.loads(_be_path.read_text(encoding="utf-8"))
    check(boss_entrance_fixture() == _be,
          "9bq11 entrance fixture must not drift from `Boss._draw_entrance`")
    check(len(_be["frames"]) == 8
          and sum(len(frame["ops"]) for frame in _be["frames"]) == 19
          and [len(frame["ops"]) for frame in _be["frames"]] == [2, 3, 1, 1, 2, 3, 4, 3],
          "9bq11 oracle must pin 8 frames, 19 ops and the aura/title gate")
    check(any(frame["entrance_text"].count(" ") > 8 and len(frame["ops"]) == 4
              for frame in _be["frames"]),
          "9bq11 one frame must prove the 1000 px word wrap")
check("self._draw_entrance(surface, x, y, max_entrance)" in _be_boss
      and "max_entrance = 180 if is_true else 120" in _be_boss
      and "if font.size(trial)[0] <= 1000:" in _be_boss
      and "start_y = 84 - (len(lines) - 1) * 18" in _be_boss,
      "9bq11 the source must keep the entrance gate, the wrap and the line origin")
check("const SCREEN_WIDTH := 1280" in _be_layout
      and "const TEXT_MAX_WIDTH := 1000" in _be_layout
      and "const TEXT_START_Y := 84" in _be_layout
      and "const LINE_STEP := 34" in _be_layout
      and "return int(float(radius) * entrance_progress * 2.0)" in _be_layout
      and "return sin(anim_time * 0.2) * 0.3 + 0.7" in _be_layout
      and "const TRUE_ENTRANCE := 180" in _be_layout,
      "9bq11 the layout must mirror the aura, the pulse and the 1000 px wrap")
check("func boss_entrance_draw_ops(boss: BossState, measure: Callable = Callable()) -> Array:"
      in _bs_view
      and "BossEntranceLayout.max_entrance(is_true)," in _bs_view
      and "measure if measure.is_valid() else _boss_text_measure" in _bs_view,
      "9bq11 the view must build the entrance ops from the live boss and the real font")
_be_draw = _bs_view[_bs_view.index("func _draw_boss_entrance("):]
check(_be_draw.index("boss_entrance_draw_ops(boss, measure)")
      < _be_draw.index("draw_string(")
      and _be_draw.index("draw_string(") < _be_draw.index("BossFont.get_ascent(size_px)")
      and "_draw_intro_op(op)" in _be_draw,
      "9bq11 the view must paint the aura as an op and the title on its baseline")
check("_check_frames(check, data)" in _be_checks and "_check_shape(check, data)" in _be_checks
      and "_check_view_wiring(check, data)" in _be_checks and "func _report(" in _be_checks,
      "9bq11 the entrance suite must replay the frames, the shape and the view")

# ── Layer 9bq12: no source recipe casts Urgharun's skills, so its FX stay unreachable ──
from urgharun_ai_reach_source_oracle import source_fixture as urgharun_reach_fixture
_ua_path = ROOT / "tests/fixtures/urgharun_ai_reach_source.json"
_ua_checks = (ROOT / "tests/urgharun_ai_reach_checks.gd").read_text(encoding="utf-8")
_ua_ai = (ROOT / "scripts/match/boss_ai.gd").read_text(encoding="utf-8")
check('const UrgharunAiReachChecks = preload("res://tests/urgharun_ai_reach_checks.gd")' in ai_tests
      and "UrgharunAiReachChecks.new().run(_check)" in ai_tests,
      "9bq12 urgharun reach suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/urgharun_ai_reach_source_oracle.py" in workflow,
      "9bq12 CI must run the urgharun reach source oracle")
check(_ua_path.is_file(), "9bq12 urgharun reach fixture must exist")
if _ua_path.is_file():
    _ua = json.loads(_ua_path.read_text(encoding="utf-8"))
    check(urgharun_reach_fixture() == _ua,
          "9bq12 urgharun reach fixture must not drift from base_boss.py and boss_data.py")
    check(int(_ua["dispatch_count"]) == 79
          and int(_ua["smart_ai_method_count"]) == 79
          and not _ua["dispatch_has_subject"]
          and not _ua["smart_ai_has_subject"],
          "9bq12 urgharun must stay outside the 79 arm dispatch chain and its recipes")
    check(_ua["subject_writers"] == []
          and int(_ua["subject_reset_count"]) == 2
          and _ua["stats"]["skill_count"] == 8,
          "9bq12 the boss must own skill stats but no active_skill writer")
check("urgharun" not in _ua_ai and "_generic(world, boss, enemies)" in _ua_ai,
      "9bq12 the native AI must keep the generic fallback and no urgharun arm")
check("BossAI.tick(world, boss, enemies, enemy, 40.0)" in _ua_checks
      and "casts == 0" in _ua_checks and "generic" in _ua_checks,
      "9bq12 the suite must run the live AI and prove it never casts")

# ── Layer 9bi2: tactical command visuals (gather marker, feedback banner, floating text) ──
from tactical_draw_source_oracle import source_fixture as tactical_draw_fixture
_td_path = ROOT / "tests/fixtures/tactical_draw_source.json"
_td_layout = (ROOT / "scripts/ui/tactical_layout.gd").read_text(encoding="utf-8")
_td_checks = (ROOT / "tests/tactical_draw_checks.gd").read_text(encoding="utf-8")
_td_sim = (ROOT / "scripts/match/tactical_commands.gd").read_text(encoding="utf-8")
_td_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
_td_scene = (ROOT / "scenes/prototype/PrototypeMatch.tscn").read_text(encoding="utf-8")
_td_src = (ROOT.parent / "tactical_commands.py").read_text(encoding="utf-8")
_td_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
check('const TacticalDrawChecks = preload("res://tests/tactical_draw_checks.gd")' in ai_tests
      and "TacticalDrawChecks.new().run(_check)" in ai_tests,
      "9bi2 tactical draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/tactical_draw_source_oracle.py" in workflow,
      "9bi2 CI must run the tactical draw_world / draw_ui source oracle")
check(_td_path.is_file(), "9bi2 tactical draw fixture must exist")
if _td_path.is_file():
    _td = json.loads(_td_path.read_text(encoding="utf-8"))
    check(tactical_draw_fixture() == _td,
          "9bi2 tactical draw fixture must not drift from tactical_commands.py")
    _td_world, _td_banner = _td["world_frames"], _td["feedback_frames"]
    check(len(_td_world) == 10 and len(_td_banner) == 8
          and sum(len(frame["ops"]) for frame in _td_world + _td_banner) == 105,
          "9bi2 oracle must pin 18 frames and 105 draw ops")
    check(all(op["radius"] in (42, 34, 26) and op["width"] == 2
              for frame in _td_world for op in frame["ops"]
              if op["kind"] == "circle" and op["radius"] > 6),
          "9bi2 oracle must pin the alpha-gated marker rings (r = 50 never shows)")
    check([sum(op["kind"] == "line" for op in frame["ops"]) for frame in _td_world]
          == [9, 9, 9, 3, 3, 6, 0, 0, 0, 0],
          "9bi2 oracle must pin three dashes per far hero for gather/tower/castle/boss only")
    check([frame["ops"][1]["color"][3] for frame in _td_banner if frame["ops"]]
          == [0, 85, 246, 255, 255, 246, 8],
          "9bi2 oracle must pin the banner sliding in over 30 ticks and fading out over 30")
_td_ui = _td_core[_td_core.index("self.effects.draw_ui(self.screen"):]
check(_td_ui.index("self.tactical.draw_ui(self.screen)")
      < _td_ui.index("self.level_intro.draw(self.screen)"),
      "9bi2 the source paints the tactical banner after effects.draw_ui, before the level intro")
check(re.search(r"add_damage_number\(\s*640, 100, text, is_critical=True\s*\)", _td_src)
      is not None
      and all('"%s", (255, 150, 100)' % text in _td_src
              for text in ("No tower to protect!", "No boss active!", "No enemy heroes!")),
      "9bi2 the source must still float feedback and warn in orange when nothing is targetable")
check("effects.add_damage_number(640.0, 100.0, text, true)" in _td_sim
      and "const REFUSAL_ORANGE := Color8(255, 150, 100)" in _td_sim
      and all('_refuse(world, "%s", silent, REFUSAL_ORANGE)' % text in _td_sim
              for text in ("No tower to protect!", "No boss active!", "No enemy heroes!")),
      "9bi2 feedback must float its text and keep the source refusal colours")
check("const SOLID_DRAWS := true" in _td_layout and "static func world_ops(" in _td_layout
      and "static func feedback_ops(" in _td_layout and "range(50, 20, -8)" in _td_layout
      and "const FEEDBACK_FONT_SIZE := 28" in _td_layout,
      "9bi2 the layout must mirror draw_world / draw_ui")
check('\t"achievement",\n\t"tactical_feedback",\n' in _bs_view
      and _bs_view.index('\t"tactical_feedback",\n') < _bs_view.index('\t"level_intro",\n')
      and "TacticalLayout.world_ops(" in _bs_view and "TacticalLayout.feedback_ops(" in _bs_view
      and "_draw_solid_op(op)" in _bs_view and "draw_style_box(" in _bs_view,
      "9bi2 the view must paint the solid marker and the banner in the draw_ui slot")
check("TacticalFeedback" not in _td_screen and "TacticalFeedback" not in _td_scene,
      "9bi2 the old 18 px HUD label must not return")
check("_check_world_frames(check" in _td_checks and "_check_feedback_frames(check" in _td_checks
      and "_check_view_wiring(check, data)" in _td_checks
      and "_check_feedback_side_effects(check)" in _td_checks,
      "9bi2 the tactical draw suite must replay frames, the view and the feedback side effects")

# ── Layer 9bv2: the source gold chip and mode badge (Game._draw_gold_hud) ──
from gold_hud_draw_source_oracle import source_fixture as gold_hud_draw_fixture
_gh_path = ROOT / "tests/fixtures/gold_hud_draw_source.json"
_gh_layout = (ROOT / "scripts/ui/gold_hud_layout.gd").read_text(encoding="utf-8")
_gh_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_gh_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
_gh_scene = (ROOT / "scenes/prototype/PrototypeMatch.tscn").read_text(encoding="utf-8")
_gh_hud = (ROOT / "tests/prototype_layout_checks.gd").read_text(encoding="utf-8")
_gh_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
check('const GoldHudDrawChecks = preload("res://tests/gold_hud_draw_checks.gd")' in ai_tests
      and "GoldHudDrawChecks.new().run(_check)" in ai_tests,
      "9bv2 gold HUD draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/gold_hud_draw_source_oracle.py" in workflow,
      "9bv2 CI must run the _draw_gold_hud source oracle")
check(_gh_path.is_file(), "9bv2 gold HUD fixture must exist")
if _gh_path.is_file():
    _gh = json.loads(_gh_path.read_text(encoding="utf-8"))
    check(gold_hud_draw_fixture() == _gh, "9bv2 gold HUD fixture must not drift from _core.py")
    check(len(_gh["frames"]) == 6 and sum(len(f["ops"]) for f in _gh["frames"]) == 102
          and {f["cheap_alpha"] for f in _gh["frames"]} == {True, False}
          and {f["difficulty"] for f in _gh["frames"]} >= {"easy", "normal", "hard"},
          "9bv2 fixture must pin 6 frames / 102 ops over both fill branches and every mode")
check("if not _PANEL_AKTIF():\n            self._draw_gold_hud(self.screen)" in _gh_core,
      "9bv2 source must still paint the gold HUD only while the side panel is off")
check("const ORIGIN := Vector2i(18, 22)" in _gh_layout
      and "maxi(CHIP_MIN_WIDTH, val_w + inc_w + 78)" in _gh_layout
      and "Economy.format_gold_rate(rate)" in _gh_layout,
      "9bv2 layout must keep the source origin, chip width rule and format_gold_rate")
check('const GoldHudLayout = preload("res://scripts/ui/gold_hud_layout.gd")' in _gh_view
      and re.search(r'const OVERLAY_ORDER := \[\s*"shop_hints",\s*"gold_hud",\s*"boss_intro",',
                    _gh_view) is not None
      and '"gold_hud":\n\t\t\t_draw_gold_hud(world)' in _gh_view
      and "if not gold_hud_visible:" in _gh_view
      and "func _draw_vgrad_op(" in _gh_view and "func _draw_round_rect_op(" in _gh_view,
      "9bv2 view must paint the gold HUD after the shop hints, gated by gold_hud_visible")
check('arena.set("gold_hud_visible", side_panel == null or not side_panel.is_active())'
      in _gh_screen and '%GoldLabel.text = "AI:%d" % world.economy.gold[1]' in _gh_screen,
      "9bv2 screen must hide the chip with the side panel and keep only the opponent gold")
check('[node name="TopBar" type="PanelContainer" parent="HUD"]\noffset_left = 240.0\n' in _gh_scene
      and "Gold chip %s and badge %s stay clear of the top bar %s" in _gh_hud,
      "9bv2 top bar must start right of the gold chip, proven by the live layout checks")

# ── Layer 9bv3: the floating ITEM FORGE / HERO SHOP hints (ShopHints.draw) ──
from shop_hint_draw_source_oracle import source_fixture as shop_hint_draw_fixture
_sh_path = ROOT / "tests/fixtures/shop_hint_draw_source.json"
_sh_layout = (ROOT / "scripts/ui/shop_hint_layout.gd").read_text(encoding="utf-8")
_sh_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_sh_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
check('const ShopHintDrawChecks = preload("res://tests/shop_hint_draw_checks.gd")' in ai_tests
      and "ShopHintDrawChecks.new().run(_check)" in ai_tests,
      "9bv3 shop hint draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/shop_hint_draw_source_oracle.py" in workflow,
      "9bv3 CI must run the ShopHints.draw source oracle")
check(_sh_path.is_file(), "9bv3 shop hint fixture must exist")
if _sh_path.is_file():
    _sh = json.loads(_sh_path.read_text(encoding="utf-8"))
    check(shop_hint_draw_fixture() == _sh, "9bv3 shop hint fixture must not drift from the source")
    check(len(_sh["frames"]) == 6 and sum(len(f["ops"]) for f in _sh["frames"]) == 36
          and {f["cheap_alpha"] for f in _sh["frames"]} == {True, False}
          and _sh["shops"] == {"dire_shop_pos": [940, 180], "radiant_shop_pos": [340, 540]},
          "9bv3 fixture must pin 6 frames / 36 ops over both fill branches and both shops")
check('self.ui.draw_shop_hints(self.screen)\n        _PH.mark("ui.gold")' in _sh_core,
      "9bv3 source must still open the UI pass with the shop hints, right before the gold HUD")
check("return int(sin(float(animation_time) * 0.06) * 2.0)" in _sh_layout
      and '[[340, 540], "ITEM FORGE", [82, -30]]' in _sh_layout
      and '[[940, 180], "HERO SHOP", [-82, 44]]' in _sh_layout,
      "9bv3 layout must keep the source bob and the two anchored labels")
check('const ShopHintLayout = preload("res://scripts/ui/shop_hint_layout.gd")' in _sh_view
      and '"shop_hints":\n\t\t\t_draw_shop_hints(world)' in _sh_view
      and "ShopHintLayout.ops(int(world.tick_count), metrics)" in _sh_view
      and "func _draw_hud_op(" in _sh_view,
      "9bv3 view must open the UI pass with the shop hints, bobbing on the world tick count")

# ── Layer 9bv4: the controller hint bar (Game._draw_input_hints / draw_hint_bar) ──
from input_hint_draw_source_oracle import source_fixture as input_hint_draw_fixture
_ih_path = ROOT / "tests/fixtures/input_hint_draw_source.json"
_ih_layout = (ROOT / "scripts/ui/input_hint_layout.gd").read_text(encoding="utf-8")
_ih_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_ih_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
_ih_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
check('const InputHintDrawChecks = preload("res://tests/input_hint_draw_checks.gd")' in ai_tests
      and "InputHintDrawChecks.new().run(_check)" in ai_tests,
      "9bv4 input hint draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/input_hint_draw_source_oracle.py" in workflow,
      "9bv4 CI must run the draw_hint_bar source oracle")
check(_ih_path.is_file(), "9bv4 input hint fixture must exist")
if _ih_path.is_file():
    _ih = json.loads(_ih_path.read_text(encoding="utf-8"))
    check(input_hint_draw_fixture() == _ih, "9bv4 input hint fixture must not drift from _core.py")
    check(len(_ih["frames"]) == 6 and sum(len(f["ops"]) for f in _ih["frames"]) == 89
          and any(not f["ops"] for f in _ih["frames"])
          and any(f["ops"] and f["ops"][0]["rect"][0] < 0 for f in _ih["frames"]),
          "9bv4 fixture must pin 6 frames / 89 ops incl. the empty and the overflowing bar")
_ih_draw = _ih_core[_ih_core.index("    def _draw_input_hints(self, surface):"):]
_ih_draw = _ih_draw[:_ih_draw.index("    def _input_label(")]
check("if mgr is None or not mgr.is_controller_mode():" in _ih_draw
      and "self.boss_death.celebration_active" in _ih_draw
      and "mgr.draw_hint_bar(surface, context=ctx)" in _ih_draw
      and _ih_core.index("self._draw_input_hints(self.screen)")
      < _ih_core.index("# ═══ LEVEL INTRO SCREEN (paling atas dari yang lain) ═══"),
      "9bv4 source must still gate the bar on controller mode and cinematics, before the intro")
check("var x := (SCREEN_WIDTH - total_w) >> 1" in _ih_layout and "const BAR_Y := 690" in _ih_layout,
      "9bv4 layout must keep the centred floor start and y = SCREEN_HEIGHT - 30")
check('const InputHintLayout = preload("res://scripts/ui/input_hint_layout.gd")' in _ih_view
      and re.search(r'"tactical_feedback",\s*"build_popup",\s*"hero_panel",\s*"end_overlay",\s*"input_hints",\s*"level_intro",',
                    _ih_view) is not None
      and '"input_hints":\n\t\t\t_draw_input_hints(world)' in _ih_view
      and "func input_hints_blocked(" in _ih_view,
      "9bv4 view must paint the hint bar between the tactical banner and the level intro")
check("controller_cursor.get_hints(hint_context) if controller_cursor.active else []" in _ih_screen
      and 'arena.set("input_hints", hints)' in _ih_screen,
      "9bv4 screen must feed the hint bar only in controller mode")

# ── Layer 9bv5: the victory / defeat overlay (Overlay.draw) and the result layout ──
from end_overlay_draw_source_oracle import source_fixture as end_overlay_draw_fixture
_eo_path = ROOT / "tests/fixtures/end_overlay_draw_source.json"
_eo_layout = (ROOT / "scripts/ui/end_overlay_layout.gd").read_text(encoding="utf-8")
_eo_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_eo_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
_eo_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
check('const EndOverlayDrawChecks = preload("res://tests/end_overlay_draw_checks.gd")' in ai_tests
      and "EndOverlayDrawChecks.new().run(_check)" in ai_tests,
      "9bv5 end overlay draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/end_overlay_draw_source_oracle.py" in workflow,
      "9bv5 CI must run the Overlay.draw source oracle")
check(_eo_path.is_file(), "9bv5 end overlay fixture must exist")
if _eo_path.is_file():
    _eo = json.loads(_eo_path.read_text(encoding="utf-8"))
    check(end_overlay_draw_fixture() == _eo, "9bv5 end overlay fixture must not drift from the source")
    check(len(_eo["frames"]) == 8 and sum(len(f["ops"]) for f in _eo["frames"]) == 2210
          and _eo["colors"] == {"victory": [255, 200, 50], "defeat": [220, 50, 50]},
          "9bv5 fixture must pin 8 frames / 2210 ops and the GOLD / RED titles")
    _eo_buttons = {f["label"]: (f["unlock"] or {}).get("button") for f in _eo["frames"]}
    check(_eo_buttons.get("unlock_steady") == [1275, 440, 310, 30]
          and _eo_buttons.get("unlock_full_hover") == [875, 440, 310, 30],
          "9bv6 fixture must pin the capped-timer and the slid-in PLAY NEXT LEVEL rects")
check('self.ui.draw_overlay(\n                self.screen,\n                f"VICTORY! LV.{self.level_number}"'
      in _eo_core and "self._draw_input_hints(self.screen)" in _eo_core
      and _eo_core.index('f"DEFEAT LV.{self.level_number}"')
      < _eo_core.index("self._draw_input_hints(self.screen)"),
      "9bv5 source must still paint the overlay before the input hint bar")
check("static func backdrop_rows()" in _eo_layout and "static func action_text(" in _eo_layout
      and "const UNLOCK_DELAY := 90" in _eo_layout and "static func play_button_rect(" in _eo_layout
      and "func _unlock_popup(" in _eo_layout,
      "9bv5/9bv6 layout must keep the backdrop rows, the action line and the unlock popup")
_eo_bundle = (ROOT.parent / "ui_components" / "_bundle.py").read_text(encoding="utf-8")
check("if self.unlock_popup_timer < self.unlock_popup_delay:\n                self.unlock_popup_timer += 1"
      in _eo_bundle and "g.ui_buttons['play_next_level'] = btn_rect" in _eo_bundle,
      "9bv6 source must still stop the unlock timer at the delay and register the PLAY button")
check("if unlock_popup_timer < EndOverlayLayout.UNLOCK_DELAY:" in _eo_view
      and "func unlock_play_rect() -> Rect2:" in _eo_view
      and 'var button: Rect2 = arena.call("unlock_play_rect")' in _eo_screen
      and "func _unlock_popup_state(world: Prototype) -> Dictionary:" in _eo_screen
      and "Control.MOUSE_FILTER_IGNORE if result else Control.MOUSE_FILTER_STOP" in _eo_screen,
      "9bv6 view/screen must cap the timer like pygame and route PLAY NEXT LEVEL clicks")
check('const EndOverlayLayout = preload("res://scripts/ui/end_overlay_layout.gd")' in _eo_view
      and re.search(r'"tactical_feedback",\s*"build_popup",\s*"hero_panel",\s*"end_overlay",\s*"input_hints",',
                    _eo_view) is not None
      and '"end_overlay":\n\t\t\t_draw_end_overlay(world)' in _eo_view
      and "state[\"animation_time\"] = world.tick_count" in _eo_view,
      "9bv5 view must paint the overlay between the tactical banner and the hint bar")
check('arena.set("end_overlay_state", {} if world.is_running() else _end_overlay_state(world))'
      in _eo_screen and "_set_result_layout(true)" in _eo_screen
      and "_set_result_layout(false)" in _eo_screen,
      "9bv5 screen must hand the end state to the arena and switch the pause card layout")

# ── Layer 9bv7: the build-tower popup (BuildPopup.draw) ──
from build_popup_draw_source_oracle import source_fixture as build_popup_draw_fixture
_bp_path = ROOT / "tests/fixtures/build_popup_draw_source.json"
_bp_layout = (ROOT / "scripts/ui/build_popup_layout.gd").read_text(encoding="utf-8")
_bp_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_bp_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
_bp_side_panel = (ROOT / "scripts/ui/side_panel.gd").read_text(encoding="utf-8")
_bp_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
_bp_platform_utils = (ROOT.parent / "mobile/platform_utils.py").read_text(encoding="utf-8")
check('const BuildPopupDrawChecks = preload("res://tests/build_popup_draw_checks.gd")' in ai_tests
      and "BuildPopupDrawChecks.new().run(_check)" in ai_tests,
      "9bv7 build popup draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/build_popup_draw_source_oracle.py" in workflow,
      "9bv7 CI must run the BuildPopup.draw source oracle")
check(_bp_path.is_file(), "9bv7 build popup fixture must exist")
if _bp_path.is_file():
    _bp = json.loads(_bp_path.read_text(encoding="utf-8"))
    check(build_popup_draw_fixture() == _bp, "9bv7 build popup fixture must not drift from the source")
    check(len(_bp["frames"]) == 11 and sum(len(f["ops"]) for f in _bp["frames"]) == 891
          and {f["cheap_alpha"] for f in _bp["frames"]} == {True, False}
          and any(f["label"] == "wide_panel_hover_tower" and f["target_surface"] == "side_panel"
                  for f in _bp["frames"])
          and any(f["label"] == "narrow_panel_flat" and f["panel"] == [1280, 0, 120, 720]
                  for f in _bp["frames"]),
          "9bv7 fixture must pin 11 frames / 891 ops, both fills, and compact mobile side-panel routes")
check("if self.build_popup_slot is not None:\n            self.ui.draw_build_popup(self.screen)"
      in _bp_core, "9bv7 source must still paint the build popup while a build slot is set")
check("static func origin(slot_x: int, slot_y: int) -> Vector2i:" in _bp_layout
      and "static func mobile_geometry(panel: Rect2i) -> Dictionary:" in _bp_layout
      and "static func state_button_rect(state: Dictionary, index: int) -> Rect2i:" in _bp_layout
      and "static func state_close_rect(state: Dictionary) -> Rect2i:" in _bp_layout
      and "func _fit_ellipsis(text: String, font_size: int, max_width: int) -> String:" in _bp_layout
      and "static func button_rect(slot_x: int, slot_y: int, index: int) -> Rect2i:" in _bp_layout
      and "const TOWER_TYPES :=" in _bp_layout
      and "def panel_popup_pos(w, h, atas=12):" in _bp_platform_utils,
      "9bv7 layout must keep fallback geometry and match the compact mobile panel helper")
check('const BuildPopupLayout = preload("res://scripts/ui/build_popup_layout.gd")' in _bp_view
      and '"tactical_feedback",\n\t"build_popup",\n\t"hero_panel",\n\t"end_overlay",' in _bp_view
      and '"build_popup":\n\t\t\t_draw_build_popup(world)' in _bp_view
      and "func build_popup_draw_ops(" in _bp_view
      and "build_popup_state.is_empty() or not world.is_running() or build_popup_state.has(\"panel_pos\")"
      in _bp_view,
      "9bv7 view must keep fallback order and leave the right-panel branch to SidePanel")
check('arena.set("build_popup_state", build_popup_state)' in _bp_screen
      and "var build_popup_state := _build_popup_state(world, match_session)" in _bp_screen
      and "_update_side_panel(world, hero_panel_state, build_popup_state)" in _bp_screen
      and "func _build_popup_state(world: Prototype, match_session: PrototypeSession) -> Dictionary:" in _bp_screen
      and "if not world.is_running():\n\t\treturn {}\n\tvar slot_id := match_session.selected_slot_id" in _bp_screen
      and "if slot == null or slot.structure_id != -1:" in _bp_screen
      and "BuildPopupLayout.mobile_geometry(side_panel.panel)" in _bp_screen,
      "9bv7 screen must supply the selected empty build slot and compact mobile anchor to both painters")
check('snapshot["build_popup_state"] = build_popup_state' in _bp_screen
      and "or not build_popup_state.is_empty()" in _bp_screen
      and 'var previous_build_state: Dictionary = snapshot.get("build_popup_state", {})' in _bp_side_panel
      and "or not next_build_state.is_empty()" in _bp_side_panel
      and "func _draw_build_popup_overlay() -> void:" in _bp_side_panel
      and 'not state.has("panel_pos")' in _bp_side_panel
      and 'String(snapshot.get("state", "")) != "playing"' in _bp_side_panel
      and "BuildPopupLayout.ops(" in _bp_side_panel
      and "BuildPopupBodyFont.has_char(0x2026)" in _bp_side_panel
      and "func _draw_build_popup_text(op: Dictionary) -> void:" in _bp_side_panel
      and 'if kind == "circle":' in _bp_side_panel
      and "draw_set_transform(-Vector2(panel.position)" in _bp_side_panel
      and "func _draw_build_popup_title(op: Dictionary) -> void:" in _bp_side_panel
      and _bp_side_panel.index("_draw_build_popup_overlay()") < _bp_side_panel.index("_draw_hero_panel_overlay()"),
      "9bv7 side dock must draw the compact popup above its opaque contents before HeroPanel")

# ── Layer 9bv8: selected hero panel and its six inventory slots ──
from hero_panel_draw_source_oracle import source_fixture as hero_panel_draw_fixture
_hp_path = ROOT / "tests/fixtures/hero_panel_draw_source.json"
_hp_layout = (ROOT / "scripts/ui/hero_panel_layout.gd").read_text(encoding="utf-8")
_hp_checks = (ROOT / "tests/hero_panel_draw_checks.gd").read_text(encoding="utf-8")
_hp_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
_hp_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
_hp_side_panel = (ROOT / "scripts/ui/side_panel.gd").read_text(encoding="utf-8")
_hp_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
_hp_bundle = (ROOT.parent / "ui_components/_bundle.py").read_text(encoding="utf-8")
_hp_items = (ROOT.parent / "hero_items.py").read_text(encoding="utf-8")
check('const HeroPanelDrawChecks = preload("res://tests/hero_panel_draw_checks.gd")' in ai_tests
      and "HeroPanelDrawChecks.new().run(_check)" in ai_tests,
      "9bv8 HeroPanel draw suite must be preloaded and run in the native suite")
check("python godot_rebuild/tests/hero_panel_draw_source_oracle.py" in workflow,
      "9bv8 CI must run the HeroPanel and HeroItemRenderer source oracle")
check(_hp_path.is_file(), "9bv8 HeroPanel source fixture must exist")
if _hp_path.is_file():
    _hp = json.loads(_hp_path.read_text(encoding="utf-8"))
    _hp_frames = _hp["frames"]
    check(hero_panel_draw_fixture() == _hp, "9bv8 HeroPanel fixture must not drift from its source")
    check(len(_hp_frames) == 6 and sum(len(f["ops"]) for f in _hp_frames) == 440
          and [f["label"] for f in _hp_frames] == [
              "ready_fallback", "low_hp_autocast", "locked_flat", "mobile_anchor_hover_close",
              "max_level_full_inventory_flat", "hover_upgrade"]
          and _hp["source"] == "ui_components/_bundle.py::HeroPanel.draw + hero_items.py::HeroItemRenderer.draw",
          "9bv8 fixture must pin the six representative source frames and 440 draw ops")
    check({f["cheap_alpha"] for f in _hp_frames} == {True, False}
          and any(f["state"].get("panel_pos") == [975, 420] for f in _hp_frames)
          and all(f["buttons"].get("hero_item_slot_5") is not None for f in _hp_frames),
          "9bv8 fixture must cover both panel fills, mobile anchoring, and all six item-slot rects")
check("if self.selected_hero and self.selected_hero.alive:\n            self.ui.draw_hero_info(self.screen)" in _hp_core
      and _hp_core.index("self.ui.draw_build_popup(self.screen)")
      < _hp_core.index("self.ui.draw_hero_info(self.screen)")
      and "HeroItemRenderer.draw(surface, h, px, y, panel_w)" in _hp_bundle
      and "for i in range(MAX_ITEM_SLOTS):" in _hp_items,
      "9bv8 source must draw the live selected hero after the build popup and use all six item slots")
check("static func panel_rect(state: Dictionary) -> Rect2i:" in _hp_layout
      and "static func mobile_panel_origin(panel: Rect2i) -> Variant:" in _hp_layout
      and "static func item_slot_rect(state: Dictionary, index: int) -> Rect2i:" in _hp_layout
      and "static func upgrade_rect(state: Dictionary) -> Rect2i:" in _hp_layout
      and "const PANEL_W := 280" in _hp_layout and "const PANEL_H := 276" in _hp_layout,
      "9bv8 layout must keep the source panel size and expose its panel, item, and upgrade geometry")
_hp_order_match = re.search(r"const OVERLAY_ORDER := \[(.*?)\]", _hp_view, re.S)
_hp_order = re.findall(r'"(\w+)"', _hp_order_match.group(1)) if _hp_order_match else []
check('const HeroPanelLayout = preload("res://scripts/ui/hero_panel_layout.gd")' in _hp_view
      and '"hero_panel":\n\t\t\t_draw_hero_panel(world)' in _hp_view
      and "func hero_panel_draw_ops(" in _hp_view
      and re.search(r'"build_popup",\s*"hero_panel",\s*"end_overlay"', _hp_view) is not None
      and bool(_hp_order) and _hp_order[-1] == "boss_death",
      "9bv8 view must paint after the build popup, before results, and leave boss death last")
check('arena.set("hero_panel_state", hero_panel_state)' in _hp_screen
      and "var hero_panel_state := _hero_panel_state(world, match_session)" in _hp_screen
      and "func _hero_panel_state(world: Prototype, match_session: PrototypeSession) -> Dictionary:" in _hp_screen
      and "selected == null or not selected.alive or selected.team != world.BLUE" in _hp_screen
      and "HeroPanelLayout.mobile_panel_origin(side_panel.panel)" in _hp_screen
      and 'state["panel_pos"] = [mobile_origin.x, mobile_origin.y]' in _hp_screen
      and "func _hero_panel_item_active(inventory: HeroItemInventory, item_id: String) -> bool:" in _hp_screen
      and "selected.upgrade_cost()" in _hp_screen,
      "9bv8 screen must hand the live hero snapshot and source mobile anchor to the view")
check('snapshot["hero_panel_state"] = hero_panel_state' in _hp_screen
      and 'snapshot["popup_open"] = (' in _hp_screen
      and "or not hero_panel_state.is_empty()" in _hp_screen
      and "side_panel.update_snapshot(snapshot)" in _hp_screen
      and "func _draw_hero_panel_overlay() -> void:" in _hp_side_panel
      and "HeroPanelLayout.ops(" in _hp_side_panel
      and "draw_set_transform(-Vector2(panel.position)" in _hp_side_panel
      and "var overlay_active := (" in _hp_side_panel
      and "or not previous_build_state.is_empty()" in _hp_side_panel
      and "if overlay_active:" in _hp_side_panel,
      "9bv8 wide-screen dock must redraw the source panel above its background at the mobile anchor")
check("Hero panel oracle pins 6 source frames and 440 draw ops" in _hp_checks
      and "mobile_panel_origin" in _hp_checks
      and "hero_panel_draw_ops" in _hp_checks
      and "for index in range(Layout.ITEM_COUNT):" in _hp_checks
      and 'order.back() == "boss_death"' in _hp_checks,
      "9bv8 draw checks must replay the fixture, pin all six slots, and keep the overlay order")

# ── Layer 9bv9: interactive BuildPopup and HeroPanel ──
_pi_screen = (ROOT / "scenes/prototype/prototype_screen.gd").read_text(encoding="utf-8")
_pi_side_panel = (ROOT / "scripts/ui/side_panel.gd").read_text(encoding="utf-8")
_pi_checks = (ROOT / "tests/popup_interaction_scene_checks.gd").read_text(encoding="utf-8")
check('const PopupInteractionSceneChecks = preload("res://tests/popup_interaction_scene_checks.gd")' in ai_tests
      and "PopupInteractionSceneChecks.new().run(root.get_tree(), app, _check)" in ai_tests,
      "9bv9 popup interaction suite must be preloaded and run in the native scene suite")
check("side_panel.overlay_pressed.connect(_handle_side_panel_overlay_press)" in _pi_screen
      and "signal overlay_pressed(screen_position: Vector2i, button_index: int)" in _pi_side_panel
      and "overlay_pressed.emit(screen_position, button_index)" in _pi_side_panel
      and "if action.is_empty() and popup_open:" in _pi_side_panel,
      "9bv9 dock pointer events must route only after SidePanel pause/tactical hit testing")
check("func _touch_target_rect(rect: Rect2i) -> Rect2i:" in _pi_screen
      and "maxi(rect.size.x + int(TOUCH_PADDING * 2.0), int(TOUCH_TARGET_MIN))" in _pi_screen
      and "BuildPopupLayout.state_button_rect(state, index)" in _pi_screen
      and "HeroPanelLayout.item_slot_rect(state, index)" in _pi_screen
      and "func _overlay_point(point: Vector2, state: Dictionary) -> Vector2i:" in _pi_screen,
      "9bv9 input must use source-sized hitboxes and resolve arena versus dock coordinates")
check('match_session.request_build(slot_id, action.replace("build_", ""))' in _pi_screen
      and "match_session.request_hero_upgrade(hero.id)" in _pi_screen
      and "match_session.request_autocast(hero.id)" in _pi_screen
      and "world.forge.set_selected(hero_id)" in _pi_screen
      and "world.forge.set_target(hero_id)" in _pi_screen
      and "shop.inspect_item = inspect_item" in _pi_screen,
      "9bv9 popup actions must reuse fixed-tick session and forge transactions")
check("_primary_action(event.position)" in _pi_screen
      and "_handle_overlay_pointer(event.position, MOUSE_BUTTON_RIGHT)" in _pi_screen
      and "_handle_overlay_pointer(point, MOUSE_BUTTON_RIGHT)" in _pi_screen
      and "func _overlay_target_screen_rect(entry: Dictionary, target: Rect2i) -> Rect2:" in _pi_screen
      and "if _overlay_action_rect_at(point) != null or _overlay_panel_captures_pointer(point):" in _pi_screen
      and "unreachable behind its button == 1 guard" in _pi_screen,
      "9bv9 mouse/touch/controller routing must retain priority, transform targets, and preserve the HeroPanel drop guard")
check('var paths := ["archer", "cannon", "ice", "mage"]' in _pi_checks
      and "Controller confirm recognizes a painted BuildPopup card" in _pi_checks
      and "SidePanel mouse input routes a docked BuildPopup card" in _pi_checks
      and "Occupied HeroPanel slot opens Forge" in _pi_checks
      and "HeroPanel ITEM FORGE button opens Forge" in _pi_checks
      and "HeroPanel long-press preserves the same unreachable item-drop guard" in _pi_checks
      and "Fixed tick activates HeroPanel autocast" in _pi_checks,
      "9bv9 scene checks must exercise build paths, controller/dock input, touch, Forge and commands")

# ── Layer 9br: UI skin from ui_theme.py (bake/bake_ui_theme.py) ──
_ui_path = ROOT / "data/art/ui_theme.json"
_ui_src = (ROOT.parent / "ui_theme.py").read_text(encoding="utf-8")
_ui_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
_ui_bake = (ROOT / "bake/bake_ui_theme.py").read_text(encoding="utf-8")
_ui_skin = (ROOT / "scripts/ui/ui_skin.gd").read_text(encoding="utf-8")
_ui_theme = (ROOT / "scripts/ui/rebuild_theme.gd").read_text(encoding="utf-8")
_ui_card = (ROOT / "scripts/ui/hero_shop_card.gd").read_text(encoding="utf-8")
_ui_project = (ROOT / "project.godot").read_text(encoding="utf-8")
_ui_button = (ROOT / "scripts/ui/source_ui_button.gd").read_text(encoding="utf-8")
_ui_toggle = (ROOT / "scripts/ui/ui_theme_toggle.gd").read_text(encoding="utf-8")
_ui_slider = (ROOT / "scripts/ui/ui_theme_slider.gd").read_text(encoding="utf-8")
_ui_audio = (ROOT / "scripts/ui/audio_settings_panel.gd").read_text(encoding="utf-8")
_ui_prefs = (ROOT / "scripts/settings/presentation_settings_store.gd").read_text(encoding="utf-8")
_ui_battle = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
_ui_app = (ROOT / "app/app.gd").read_text(encoding="utf-8")
check('const UiSkinChecks = preload("res://tests/ui_skin_checks.gd")' in ai_tests
      and "UiSkinChecks.new().run(_check)" in ai_tests,
      "9br UI skin suite must be preloaded and run in the native suite")
check(_ui_path.is_file(), "9br UI skin manifest must exist")
_ui_palette_src = {
    name: [int(r), int(g), int(b)]
    for name, r, g, b in re.findall(r"^([A-Z_]+)\s*=\s*\((\d+),\s*(\d+),\s*(\d+)\)", _ui_src, re.M)}
if _ui_path.is_file():
    _ui = json.loads(_ui_path.read_text(encoding="utf-8"))
    check(_ui["palette"] == _ui_palette_src and len(_ui_palette_src) >= 30,
          "9br the recorded palette must equal every colour constant of ui_theme.py")
    for _sheet_name, _png_name in (("panels", "panels.png"), ("pills", "pills.png")):
        _sheet = _ui[_sheet_name]
        _png = ROOT / "assets/art/ui" / _png_name
        check(_png.is_file(), f"9br {_png_name} must ship")
        if _png.is_file():
            _raw = _png.read_bytes()
            _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
            check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _sheet["size"]
                  and (_depth, _color) == (8, 6),
                  f"9br {_png_name} must be an RGBA8 PNG of its manifest size")
            check(len(_raw) == _sheet["bytes"] and hashlib.sha256(_raw).hexdigest() == _sheet["sha256"],
                  f"9br {_png_name} must match its manifest hash")
        check(all(w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= _sheet["size"][0]
                  and y + h <= _sheet["size"][1] for x, y, w, h in _sheet["frames"].values()),
              f"9br every {_sheet_name} frame must lie inside its sheet")
    _ui_controls = _ui.get("controls", {})
    for _control_name, _png_name in (("buttons", "buttons.png"), ("tabs", "tabs.png"),
                                    ("toggles", "toggles.png"), ("icons", "icons.png")):
        _sheet = _ui_controls.get(_control_name, {})
        _png = ROOT / "assets/art/ui" / _png_name
        check(_png.is_file(), f"9br {_png_name} must ship")
        if _png.is_file():
            _raw = _png.read_bytes()
            _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
            check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _sheet.get("size")
                  and (_depth, _color) == (8, 6),
                  f"9br {_png_name} must be RGBA8 and match the controls manifest")
            check(len(_raw) == _sheet.get("bytes")
                  and hashlib.sha256(_raw).hexdigest() == _sheet.get("sha256"),
                  f"9br {_png_name} must match its recorded hash")
        check(all(w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= _sheet.get("size", [0, 0])[0]
                  and y + h <= _sheet.get("size", [0, 0])[1]
                  for x, y, w, h in _sheet.get("frames", {}).values()),
              f"9br every {_control_name} state lies in its texture sheet")
    _glow = _ui_controls.get("slider_glow", {})
    _glow_png = ROOT / "assets/art/ui/slider_glow.png"
    check(_glow_png.is_file(), "9br the source radial slider glow must ship")
    if _glow_png.is_file():
        _raw = _glow_png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check([_width, _height] == _glow.get("size") == [36, 36]
              and (_depth, _color) == (8, 6)
              and len(_raw) == _glow.get("bytes")
              and hashlib.sha256(_raw).hexdigest() == _glow.get("sha256"),
              "9br the 36px slider glow matches the source radial bake")
    check(_ui_controls.get("buttons", {}).get("states") == ["normal", "hover"]
          and len(_ui_controls.get("buttons", {}).get("frames", {})) == 16
          and _ui_controls.get("tabs", {}).get("states") == ["active", "inactive", "hover"]
          and len(_ui_controls.get("tabs", {}).get("frames", {})) == 9
          and len(_ui_controls.get("toggles", {}).get("frames", {})) == 4,
          "9br control atlas must contain menu button, toggle and tab state variants")
    _button_accents = {
        "continue": [140, 225, 255], "play": [100, 220, 110], "hero": [255, 220, 100],
        "input": [100, 200, 220], "help": [110, 180, 255], "settings": [205, 180, 105],
        "credits": [200, 130, 210], "quit": [225, 90, 90],
    }
    _tab_accents = {"starter": [100, 200, 255], "mini": [255, 150, 100], "true": [255, 80, 100]}
    check(_ui_controls.get("buttons", {}).get("accents") == _button_accents
          and _ui_controls.get("tabs", {}).get("accents") == _tab_accents,
          "9br menu buttons and hero tabs retain the source accent colours")
    _icon_source = _ui_src[_ui_src.index("def draw_icon("): _ui_src.index("# ═══════════════════════════════════════════════════════════\n# KOMPONEN")]
    _icon_names = set(re.findall(r'name\s*==\s*"([^"]+)"', _icon_source))
    for _group in re.findall(r'name\s+in\s+\(([^)]+)\)', _icon_source):
        _icon_names.update(re.findall(r'"([^"]+)"', _group))
    check(set(_ui_controls.get("icons", {}).get("names", [])) == _icon_names,
          "9br the icon atlas contains every vector glyph in ui_theme.draw_icon")
    _ui_kinds = ["gold", "success", "danger", "locked", "owned", "neutral", "violet", "cyan"]
    check(sorted(_ui["panels"]["frames"]) == ["panel", "panel_bold"]
          and _ui["panels"]["rect"] == [4, 4, 72, 72] and _ui["panels"]["margin"] == 20
          and _ui["panels"]["expand"] == 4,
          "9br the panel sheet must hold the dialog and default panels on a 4 px shadow canvas")
    check(_ui["pills"]["kinds"] == _ui_kinds and _ui["pills"]["states"] == ["normal", "hover", "disabled"]
          and sorted(_ui["pills"]["frames"])
          == sorted(f"{kind}:{state}" for kind in _ui_kinds for state in ("normal", "hover", "disabled"))
          and _ui["pills"]["rect"] == [15, 12, 24, 24] and _ui["pills"]["margin"] == [23, 20]
          and _ui["pills"]["expand"] == [15, 12],
          "9br the pill sheet must hold every source kind in normal, hover and disabled state")
    check(_ui["pills"]["colors"]["neutral"]
          == {"top": [52, 58, 84], "bottom": [30, 35, 56], "edge": _ui_palette_src["SLATE"],
              "text": _ui_palette_src["TEXT_BODY"]}
          and _ui["pills"]["colors"]["gold"]["text"] == _ui_palette_src["GOLD_TEXT"]
          and _ui["pills"]["colors"]["locked"]["edge"] == _ui_palette_src["SLATE"],
          "9br the pill colour table must be the one read from pill()")
    _ui_consts = {
        name: ([int(r), int(g), int(b)], source)
        for name, r, g, b, source in re.findall(
            r"^const (\w+) := Color8\((\d+), (\d+), (\d+)\)\s*#\s*(\w+)", _ui_theme, re.M)}
    _ui_pins = {"INK": "TEXT_WHITE", "BODY": "TEXT_BODY", "MUTED": "TEXT_DIM", "FAINT": "TEXT_FAINT",
                "GOLD": "GOLD", "GOLD_TEXT": "GOLD_TEXT", "CYAN": "CYAN", "EDGE_GOLD": "EDGE_GOLD",
                "PANEL_FILL": "PANEL_FILL"}
    check(all(name in _ui_consts and _ui_consts[name][1] == source
              and _ui_consts[name][0] == _ui_palette_src[source] for name, source in _ui_pins.items()),
          "9br every palette constant of the theme must carry the value of its ui_theme.py name")
    check(_ui_consts["HOVER_FILL"][0] == [44, 52, 86] and "top = (44, 52, 86) if hover else (34, 41, 70)" in _ui_src
          and _ui_consts["TRACK"][0] == [16, 18, 30] and "pygame.draw.rect(screen, (16, 18, 30), r," in _ui_src
          and _ui_consts["TRACK_LINE"][0] == [86, 92, 120] and "pygame.draw.rect(screen, (86, 92, 120), r, 1," in _ui_src
          and _ui_consts["SCROLL_TRACK"][0] == [28, 32, 52]
          and "pygame.draw.rect(screen, (28, 32, 52), track, border_radius=3)" in _ui_src
          and "GOLD_BRIGHT,\n                               (196, 138, 40), radius=3)" in _ui_src,
          "9br the bar, popup and scrollbar colours must be the literals the source draws with")
    check("Color8(225, 185, 99)" in _ui_theme and "Color8(255, 233, 158)" in _ui_theme
          and _ui_palette_src["GOLD_BRIGHT"] == [255, 233, 158]
          and [(a + b) // 2 for a, b in zip(_ui_palette_src["GOLD_BRIGHT"], [196, 138, 40])] == [225, 185, 99],
          "9br the scroll thumb colours must be the GOLD_BRIGHT and mid gradient of scroll_indicator")
    _ui_clear = re.search(r"default_clear_color=Color\(([\d.]+), ([\d.]+), ([\d.]+), 1\)", _ui_project)
    check(_ui_clear is not None and all(
        abs(float(got) - want / 255) < 0.001
        for got, want in zip(_ui_clear.groups(), _ui_palette_src["BG_DEEP"])),
        "9br the window clear colour must be the BG_DEEP of ui_theme.py")
for _fragment in (
    "pygame.draw.rect(screen, border, r, border_w, border_radius=12)",
    "sh = _shadow(r.w, r.h, radius=12)", "screen.blit(sh, (r.x - 4, r.y - 4))",
    "corner_ticks(screen, r, GOLD)",
    "def corner_ticks(screen, rect, color, length=11, width=2, inset=2):",
    "pygame.draw.rect(screen, edge, r, 2 if enabled else 1, border_radius=7)",
    "screen.blit(_radial(r.w + 30, r.h + 24, edge, 66),", "(r.x - 15, r.y - 12))",
    "top = tuple(min(255, c + 18) for c in top)", "bot = tuple(min(255, c + 14) for c in bot)",
    '"neutral": ((52, 58, 84), (30, 35, 56), SLATE, TEXT_BODY),',
    '"gold":    ((86, 66, 22), (52, 40, 14), GOLD, GOLD_TEXT),',
    "screen.blit(_vgrad(r.w, r.h, top, bot, radius=7), (r.x, r.y))",
    "surf = pygame.transform.smoothscale(small, (w, h))",
):
    check(_fragment in _ui_src, f"9br the source UI skin must still read {_fragment!r}")
check("border=ui_theme.EDGE_GOLD, border_w=2)" in _ui_core,
      "9br the dialog panel the bake mirrors (border_w=2) must still be what the settings menu calls")
check("ui_theme.panel(canvas, PANEL_RECT, **kwargs)" in _ui_bake and "ui_theme.pill(" in _ui_bake
      and "assert ui_theme.cheap_alpha()" in _ui_bake and "def _pill_table(" in _ui_bake
      and "ui_theme.draw_text = lambda" in _ui_bake,
      "9br the bake must run the real panel() and pill() on transparent canvases")
check("ResourceLoader.exists(PANELS)" in _ui_skin and "ResourceLoader.exists(PILLS)" in _ui_skin
      and "box.region_rect = Rect2(" in _ui_skin and "box.texture_margin_left = margin.x" in _ui_skin
      and "box.expand_margin_left = expand.x" in _ui_skin and "return NO_COLOR" in _ui_skin,
      "9br the skin loader must cut nine-patches by manifest frame and tolerate a missing import")
check("pill_style(\"gold\", \"hover\", use_skin)" in _ui_theme
      and "pill_style(\"locked\", \"disabled\", use_skin)" in _ui_theme
      and "result.set_type_variation(variation, \"Button\")" in _ui_theme
      and "skin = UiSkin.panel_box(\"panel_bold\", PANEL_PAD)" in _ui_theme
      and "static func create_theme(use_skin: bool = true) -> Theme:" in _ui_theme,
      "9br the theme must map the pill states, variations and dialog panel with a flat fallback")
check("static func button_box(" in _ui_skin and "static func tab_box(" in _ui_skin
      and "static func toggle_box(" in _ui_skin and "static func icon_frame(" in _ui_skin
      and all(f'ResourceLoader.exists({name})' in _ui_skin
              for name in ("BUTTONS", "TABS", "TOGGLES", "ICONS", "SLIDER_GLOW")),
      "9br the skin loader must expose each baked interactive control and icon frame")
check("ui_theme.button(" in _ui_bake and "ui_theme.toggle(" in _ui_bake
      and "ui_theme.tab(" in _ui_bake and "ui_theme.draw_icon(" in _ui_bake
      and "ui_theme._radial(36, 36, ui_theme.GOLD, 80)" in _ui_bake,
      "9br the source baker must execute the real button, toggle, tab, icon and slider helpers")
check("UiSkin.button_box(source_style_key, \"normal\")" in _ui_button
      and "UiSkin.tab_box(source_style_key, \"active\")" in _ui_button
      and "_badge = IconBadge.new()" in _ui_button
      and "set_source_active(active: bool)" in _ui_button,
      "9br menu buttons and hero tabs must use the source frames and vector badge")
check("UiSkin.toggle_box(\"off\")" in _ui_toggle and "UiSkin.toggle_box(\"on\")" in _ui_toggle
      and "ThemeSlider.new()" in _ui_audio and "ThemeToggle.new()" in _ui_audio
      and "_build_presentation_row(column, \"Screen Shake\", \"screen_shake\")" in _ui_audio
      and "_build_presentation_row(column, \"Damage Numbers\", \"damage_numbers\")" in _ui_audio,
      "9br settings must use the baked toggle and slider presentation")
check("func apply_presentation_settings() -> void:" in _ui_battle
      and "session.apply_presentation_settings()" in _ui_app
      and "effects.set_quality_settings(" in _ui_battle,
      "9br persisted screen-shake and damage-number toggles must reach playable combat")
check('const PresentationSettingsChecks = preload("res://tests/presentation_settings_checks.gd")' in ai_tests
      and "PresentationSettingsChecks.new().run(_check)" in ai_tests
      and (ROOT / "tests/presentation_settings_checks.gd").is_file(),
      "9br visual preferences require native persistence checks")
check('UiSkin.palette("OPEN_BG_TOP")' in _ui_card and 'UiSkin.palette("LOCKED_EDGE")' in _ui_card
      and "162d34" not in _ui_card,
      "9br hero shop rows must use the source card colours instead of the old teal literals")

# ── Layer 9bq follow-up: the match view paints the live boss itself ──
_bf_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
check("var live_boss: BossState = world.active_boss" in _bf_view
      and "if live_boss != null and live_boss.alive:\n\t\t_draw_boss(live_boss)" in _bf_view,
      "9bq the match view must paint the live boss: the unit registry never holds it")
check(_bf_view.index("draw_circle(arrow.position, 3, ink)") < _bf_view.index("_draw_boss(live_boss)")
      < _bf_view.index("_draw_boss_death(snapshot)"),
      "9bq the boss is drawn after the heroes and their arrows and before the death presentations")

# ── Layer 9bs: baked main-menu background + recoloured scenes (bake/bake_menu_background.py) ──
_mn_path = ROOT / "data/art/menu.json"
_mn_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
_mn_ui = (ROOT.parent / "ui_theme.py").read_text(encoding="utf-8")
_mn_bake = (ROOT / "bake/bake_menu_background.py").read_text(encoding="utf-8")
_mn_back = (ROOT / "scripts/ui/menu_backdrop.gd").read_text(encoding="utf-8")
_mn_theme = (ROOT / "scripts/ui/rebuild_theme.gd").read_text(encoding="utf-8")
_mn_ambient = (ROOT / "scripts/ui/menu_ambient_fx.gd").read_text(encoding="utf-8")
_mn_layout = (ROOT / "scripts/ui/menu_ambient_layout.gd").read_text(encoding="utf-8")
_mn_ambient_bake = (ROOT / "bake/bake_menu_background.py").read_text(encoding="utf-8")
_mn_ambient_checks = (ROOT / "tests/menu_ambient_checks.gd").read_text(encoding="utf-8")
_mn_scene = (ROOT / "scenes/menu/MainMenu.tscn").read_text(encoding="utf-8")
check('const MenuArtChecks = preload("res://tests/menu_art_checks.gd")' in ai_tests
      and "MenuArtChecks.new().run(_check)" in ai_tests,
      "9bs menu art suite must be preloaded and run in the native suite")
check('const MenuAmbientChecks = preload("res://tests/menu_ambient_checks.gd")' in ai_tests
      and "MenuAmbientChecks.new().run(_check)" in ai_tests
      and "MenuAmbientChecks.new().run_scene(root.get_tree(), app.current_screen, _check)" in ai_tests,
      "9bs fog/particle source replay and live-scene suites must both run")
check('var backdrop = app.current_screen.get_node("Backdrop")' in ai_tests
      and "backdrop.background_draws > 0" in ai_tests,
      "9bs the real main menu must prove it drew the baked background")
check(_mn_path.is_file(), "9bs menu background manifest must exist")
if _mn_path.is_file():
    _mn = json.loads(_mn_path.read_text(encoding="utf-8"))
    _mn_bg = _mn["background"]
    _mn_png = ROOT / "assets/art/menu/main_background.png"
    check(_mn_png.is_file(), "9bs menu background must ship")
    if _mn_png.is_file():
        _raw = _mn_png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _mn_bg["size"] == [1280, 720]
              and (_depth, _color) == (8, 6),
              "9bs the menu background must be a 1280x720 RGBA8 PNG")
        check(len(_raw) == _mn_bg["bytes"] and hashlib.sha256(_raw).hexdigest() == _mn_bg["sha256"],
              "9bs the menu background must match its manifest hash")
    _mn_fog = _mn.get("fog", {})
    _mn_fog_png = ROOT / "assets/art/menu/menu_fog.png"
    check(_mn_fog_png.is_file(), "9bs the two baked source fog layers must ship")
    if _mn_fog_png.is_file():
        _raw = _mn_fog_png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _mn_fog.get("size") == [3000, 720]
              and (_depth, _color) == (8, 6),
              "9bs the fog atlas is a transparent RGBA8 pair of source surfaces")
        check(len(_raw) == _mn_fog.get("bytes")
              and hashlib.sha256(_raw).hexdigest() == _mn_fog.get("sha256"),
              "9bs the fog atlas must match its source-bake hash")
    check(_mn_fog.get("source_size") == [1500, 720]
          and _mn_fog.get("frames") == {"layer_0": [0, 0, 1500, 720],
                                         "layer_1": [1500, 0, 1500, 720]}
          and _mn_fog.get("layers") == [{"speed": 0.35, "alpha": 26}, {"speed": 0.6, "alpha": 18}],
          "9bs the fog manifest keeps source parallax, alpha and frame bounds")
    check(len(_mn["probes"]) >= 8 and all(0 <= x < 1280 and 0 <= y < 720 and len(rgb) == 3
                                          and all(0 <= c <= 255 for c in rgb)
                                          for x, y, *rgb in _mn["probes"]),
          "9bs the recorded source pixels must lie inside the frame")
for _fragment in (
    "def _build_main_background(self):", "rng = random.Random(2026)", "bg = pygame.Surface((W, H))",
    "for _ in range(170):",
    "moon_x, moon_y, moon_r = int(W * 0.22), int(H * 0.16), 48",
    "pygame.draw.circle(bg, (238, 230, 250), (moon_x, moon_y), moon_r)",
    "_mountains((11, 13, 28), 7, int(H * 0.74), 62, 46)",
    "_mountains((6, 8, 21), 21, int(H * 0.83), 44, 34)",
    "self._draw_portal(bg, 120, 612, (150, 130, 255), (95, 150, 255))",
    "self._draw_portal(bg, 1135, 168, (255, 205, 120), (255, 150, 90))",
):
    check(_fragment in _mn_core, f"9bs the source menu background must still read {_fragment!r}")
check("menu = core.Menu(screen)" in _mn_bake and "menu._build_main_background()" in _mn_bake
      and "menu._build_menu_fog()" in _mn_bake
      and 'pygame.image.tostring(surface, "RGB")' in _mn_bake and "surface.get_at((x, y))" in _mn_bake,
      "9bs the bake must run the real static and fog builders and record source pixels")
from menu_ambient_source_oracle import source_fixture as menu_ambient_source_fixture
_mn_fixture_path = ROOT / "tests/fixtures/menu_ambient_source.json"
check(_mn_fixture_path.is_file(), "9bs the menu particle source replay fixture must exist")
if _mn_fixture_path.is_file():
    check(menu_ambient_source_fixture() == json.loads(_mn_fixture_path.read_text(encoding="utf-8")),
          "9bs the menu particle fixture must replay the live _core.py methods")
check("ResourceLoader.exists(BACKGROUND)" in _mn_back
      and "draw_texture_rect(baked, cover_rect(size), false)" in _mn_back
      and "static func cover_rect(window: Vector2) -> Rect2:" in _mn_back
      and "var factor := maxf(window.x / SOURCE_SIZE.x, window.y / SOURCE_SIZE.y)" in _mn_back
      and "background_draws += 1" in _mn_back and "func _draw_fallback() -> void:" in _mn_back,
      "9bs the backdrop must cover the window with the baked frame and keep the old art as fallback")
check('const MENU_MANIFEST := "res://data/art/menu.json"' in _mn_ambient
      and "FileAccess.get_file_as_string(MENU_MANIFEST)" in _mn_ambient,
      "9bs the live fog overlay must read the menu atlas metadata, not the UI theme manifest")
check("func _draw_fog() -> void:" in _mn_ambient
      and "draw_texture_rect_region(" in _mn_ambient
      and "MenuAmbientLayout.advance(_particles, 1.0" in _mn_ambient
      and "MenuAmbientLayout.particle_alpha(particle, animation_time)" in _mn_ambient
      and "_draw_fog()\n\t_draw_particles()" in _mn_ambient,
      "9bs the overlay must animate two wrapped fog layers and source-glow particles above the background")
check("sin(phase) * 0.08" in _mn_layout and "phase += 0.01 * frames" in _mn_layout
      and "SOURCE_HEIGHT + 10.0" in _mn_layout and "SOURCE_WIDTH + 10.0" in _mn_layout
      and "tick * 0.05 + float(particle.get(\"ph\"" in _mn_layout
      and "tick * 0.008 + layer_index * 2.0" in _mn_layout,
      "9bs the native particle drift, wrapping and fog pulse mirror source equations")
check("[node name=\"Ambient\" type=\"Control\" parent=\".\"]" in _mn_scene
      and 'path="res://scripts/ui/menu_ambient_fx.gd" id="4"' in _mn_scene
      and _mn_scene.index('[node name="Backdrop"') < _mn_scene.index('[node name="Ambient"')
      < _mn_scene.index('[node name="Content"'),
      "9bs the ambient node must layer over the static art and underneath interactive menu content")
check("MenuAmbientChecks.new().run_scene(" in ai_tests
      and "ambient_draws" in _mn_ambient_checks and "particle_draws" in _mn_ambient_checks
      and "The live menu overlay draws" in _mn_ambient_checks,
      "9bs native tests must prove the animated overlay is actually drawn")
_mn_bright = [255, 233, 158]
check("def outline_text(screen, font, text, color, center, outline=(8, 9, 18)," in _mn_ui
      and "body = gradient_text(font, text, GOLD_BRIGHT, (196, 138, 40))" in _mn_ui
      and "const TITLE_OUTLINE := Color8(8, 9, 18)" in _mn_theme
      and "const GOLD_MID := Color8(225, 185, 99)" in _mn_theme
      and [(a + b) >> 1 for a, b in zip(_mn_bright, [196, 138, 40])] == [225, 185, 99]
      and 'label.add_theme_color_override("font_color", GOLD_MID)' in _mn_theme
      and 'label.add_theme_constant_override("outline_size", 2)' in _mn_theme,
      "9bs screen titles must be the outline_text gold (gradient mid) with its 2 px dark outline")
_mn_old = ("Color(0.59, 0.67, 0.66, 1)", "Color(0.68, 0.78, 0.75, 1)", "Color(0.55, 0.64, 0.63, 1)",
           "Color(0.47, 0.85, 0.76, 1)", "Color(0.83, 0.72, 0.46, 1)", "Color(0.015, 0.03, 0.04, 0.88)")
_mn_scenes = "\n".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "scenes").rglob("*.tscn")))
check(not any(literal in _mn_scenes for literal in _mn_old),
      "9bs no scene may keep the old teal text and dim literals")


def _mn_colour(name):
    r, g, b = _ui_palette_src[name]
    parts = [f"{channel / 255:.4f}".rstrip("0").rstrip(".") for channel in (r, g, b)]
    return f"Color({', '.join(parts)}, 1)"


check(_mn_scenes.count(_mn_colour("TEXT_DIM")) == 8 and _mn_scenes.count(_mn_colour("GOLD")) == 1
      and _mn_scenes.count(_mn_colour("CYAN")) == 1
      and _mn_scenes.count("Color(0.0392, 0.0392, 0.0784, 0.7843)") == 4
      and "overlay.fill((10, 10, 20, 200))" in _mn_core,
      "9bs the scenes must use the ui_theme.py muted, gold, cyan and the (10, 10, 20, 200) pause dim")

# ── Layer 9bt: source-baked minion slash and death effects ──
_mfx_path = ROOT / "data/art/minion_combat_fx.json"
_mfx_core = (ROOT.parent / "_core.py").read_text(encoding="utf-8")
_mfx_entity = (ROOT.parent / "_entity.py").read_text(encoding="utf-8")
_mfx_bundle = (ROOT.parent / "minions/_bundle.py").read_text(encoding="utf-8")
_mfx_bake = (ROOT / "bake/bake_minion_combat_fx.py").read_text(encoding="utf-8")
_mfx_art = (ROOT / "scripts/ui/minion_combat_fx_art.gd").read_text(encoding="utf-8")
_mfx_anim = (ROOT / "scripts/ui/minion_anim.gd").read_text(encoding="utf-8")
_mfx_view = (ROOT / "scenes/combat/minion_view.gd").read_text(encoding="utf-8")
_mfx_checks = (ROOT / "tests/minion_combat_fx_checks.gd").read_text(encoding="utf-8")
_mfx_painter = (ROOT / "tests/painter_scene_checks.gd").read_text(encoding="utf-8")
_mfx_siege = (ROOT / "scenes/siege/siege_view.gd").read_text(encoding="utf-8")
_mfx_prototype = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
check('const MinionCombatFxChecks = preload("res://tests/minion_combat_fx_checks.gd")' in ai_tests
      and "MinionCombatFxChecks.new().run(_check)" in ai_tests,
      "9bt FX checks must be registered in the native test suite")
check(workflow.count("      - '_entity.py'") == 2
      and workflow.count("      - 'minions/_bundle.py'") == 2,
      "9bt CI must run for both original minion-effect sources on push and pull_request")
check('const ROOT := "res://assets/art/minion_combat_fx/"' in _mfx_art
      and 'const MANIFEST := "res://data/art/minion_combat_fx.json"' in _mfx_art
      and "if ResourceLoader.exists(path):" in _mfx_art,
      "9bt loader must use a dynamic atlas root and guard PNG imports before load")
check("MinionCombatFxArt.draw_slash(" in _mfx_view
      and "MinionCombatFxArt.draw_death(" in _mfx_view
      and "take_death_snapshots" in _mfx_view,
      "9bt minion view must draw the baked effects and retain the source death snapshot")
check('extends "res://scenes/combat/minion_view.gd"' in _mfx_siege
      and 'extends "res://scenes/siege/siege_view.gd"' in _mfx_prototype,
      "9bt shared painter must reach siege and prototype views through inheritance")
check("view.minion_slash_draws > 0" in _mfx_painter
      and "view.minion_death_draws > 0" in _mfx_painter,
      "9bt painter scene must prove both baked FX paths execute")
check("_check_atlases(check, manifest)" in _mfx_checks
      and "_check_source_cases(check, manifest)" in _mfx_checks
      and "_check_clocks(check)" in _mfx_checks,
      "9bt native checks must validate atlas, source cases and clocks")
_mfx_types_match = re.search(r"^MINION_TYPES = \{\n(.*?)^\}", _mfx_core, re.S | re.M)
_mfx_source_types = []
_mfx_source_radii = {}
if _mfx_types_match is not None:
    _mfx_type_block = _mfx_types_match.group(1)
    _mfx_type_matches = list(re.finditer(r'^    "(\w+)": \{', _mfx_type_block, re.M))
    _mfx_source_types = [match.group(1) for match in _mfx_type_matches]
    for _index, _match in enumerate(_mfx_type_matches):
        _end = (_mfx_type_matches[_index + 1].start()
                if _index + 1 < len(_mfx_type_matches) else len(_mfx_type_block))
        _type_source = _mfx_type_block[_match.start():_end]
        _radius_match = re.search(r'^        "radius": (\d+),', _type_source, re.M)
        if _radius_match is not None:
            _mfx_source_radii[_match.group(1)] = int(_radius_match.group(1))
check(_mfx_source_types == ["goblin", "orc", "troll", "undead", "dark_rider"]
      and set(_mfx_source_radii) == set(_mfx_source_types),
      "9bt minion types and radii must come from _core.MINION_TYPES")
for _fragment in (
    "'life': 12,",
    "'max_life': 12,",
    "'distance': self.radius + 8,",
    "progress = 1.0 - (self.death_anim / 20.0)",
    "alpha = int((1 - progress) * 255)",
    "def _draw_death_animation(self, surface):",
):
    check(_fragment in _mfx_entity, f"9bt source minion animation must retain {_fragment!r}")
for _fragment in (
    "def draw_slash_effects(surface, cx, cy, slash_effects):",
    "if _RENDERING_TO_CACHE:",
    "alpha = int(220 * (1.0 - progress))",
    "span = 1.1",
    "steps = 7",
):
    check(_fragment in _mfx_bundle, f"9bt source slash painter must retain {_fragment!r}")
check("ANGLE_STEPS = 32" in _mfx_bake and "const ANGLE_STEPS := 32" in _mfx_art
      and "SLASH_LIFE = 12" in _mfx_bake and "DEATH_LIFE = 20" in _mfx_bake
      and "const SLASH_LIFE := 12" in _mfx_anim
      and "const DEATH_LIFE := 20" in _mfx_anim,
      "9bt bake, loader and presentation clocks must agree on their frame ranges")
check("_spawn_slash_effect()" in _mfx_bake
      and "draw_slash_effects(surface" in _mfx_bake
      and "_draw_death_animation(surface)" in _mfx_bake,
      "9bt bake must execute the original slash and death drawing functions")
check(_mfx_path.is_file(), "9bt minion combat FX manifest must exist")
if _mfx_path.is_file():
    import math as _mfx_math

    _mfx = json.loads(_mfx_path.read_text(encoding="utf-8"))
    check(_mfx["types"] == _mfx_source_types,
          "9bt manifest type order must match _core.MINION_TYPES")
    check(_mfx["angle_steps"] == 32 and _mfx["slash_life"] == 12
          and _mfx["death_life"] == 20,
          "9bt manifest must pin source slash/death lifetimes and atlas angles")
    _mfx_cases = _mfx["key_cases"]
    _mfx_slash_cases = [case for case in _mfx_cases if case["kind"] == "slash"]
    _mfx_death_cases = [case for case in _mfx_cases if case["kind"] == "death"]
    check(len(_mfx_slash_cases) == len(_mfx_source_types) * 12
          and len(_mfx_death_cases) == len(_mfx_source_types) * 3,
          "9bt manifest key_cases must come from both original effect functions")
    _mfx_bad_cases = []
    for _case in _mfx_slash_cases:
        _theta = 2.0 * _mfx_math.pi * _case["angle_index"] / _mfx["angle_steps"]
        _source_angle = _mfx_math.atan2(_mfx_math.sin(_theta), _mfx_math.cos(_theta))
        if (_case["type"] not in _mfx_source_radii
                or _case["max_life"] != 12
                or _case["distance"] != _mfx_source_radii.get(_case["type"], -100) + 8
                or abs(_case["angle"] - round(_source_angle, 8)) > 1e-7
                or _case["life"] not in (1, 6, 12)
                or not re.fullmatch(r"[0-9a-f]{64}", _case["rgba_sha256"])):
            _mfx_bad_cases.append(str(_case))
    for _case in _mfx_death_cases:
        if (_case["type"] not in _mfx_source_radii
                or _case["radius"] != _mfx_source_radii.get(_case["type"], -100)
                or _case["life"] not in (1, 11, 20)
                or not re.fullmatch(r"[0-9a-f]{64}", _case["rgba_sha256"])):
            _mfx_bad_cases.append(str(_case))
    check(not _mfx_bad_cases,
          "9bt source key_cases must preserve source params/render hashes: "
          + str(_mfx_bad_cases[:3]))
    _mfx_expected_keys = {f"slash{life:02d}:{angle:02d}"
                          for life in range(1, 13) for angle in range(32)}
    _mfx_expected_keys.update(f"death{life:02d}" for life in range(1, 21))
    _mfx_atlases = _mfx.get("atlases", {})
    check(set(_mfx_atlases) == set(_mfx_source_types),
          "9bt one atlas must exist for each source minion type")
    for _type_id in _mfx_source_types:
        _entry = _mfx_atlases.get(_type_id)
        if _entry is None:
            continue
        _png = ROOT / "assets/art/minion_combat_fx" / f"{_type_id}.png"
        check(_png.is_file(), f"9bt atlas PNG must ship: {_type_id}")
        if not _png.is_file():
            continue
        _raw = _png.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n" and [_width, _height] == _entry["size"]
              and (_depth, _color) == (8, 6),
              f"9bt atlas must be an RGBA8 PNG of its manifest size: {_type_id}")
        check(len(_raw) == _entry["bytes"]
              and hashlib.sha256(_raw).hexdigest() == _entry["sha256"],
              f"9bt atlas must match its manifest SHA-256: {_type_id}")
        check(_entry["radius"] == _mfx_source_radii[_type_id]
              and _entry["slash_distance"] == _mfx_source_radii[_type_id] + 8,
              f"9bt atlas radius and slash distance must match the source: {_type_id}")
        _rows = _entry["frames"]
        check(set(_rows) == _mfx_expected_keys,
              f"9bt atlas must hold every slash/death case: {_type_id}")
        check(all(w > 0 and h > 0 and x >= 0 and y >= 0
                  and x + w <= _entry["size"][0] and y + h <= _entry["size"][1]
                  and 0 <= ax <= w and 0 <= ay <= h
                  for x, y, w, h, ax, ay in _rows.values()),
              f"9bt every frame must fit its atlas and have a valid anchor: {_type_id}")

_hp_manifest_path = ROOT / "data/art/hero_projectiles.json"
check(_hp_manifest_path.is_file(), "9bu hero-projectile source manifest must ship")
if _hp_manifest_path.is_file():
    _hp = json.loads(_hp_manifest_path.read_text(encoding="utf-8"))
    _hp_atlases = _hp.get("atlases", {})
    _hp_specials = {
        "sylara": "arrow",
        "vex": "orb",
        "zephyr": "bolt",
        "morgath": "lightning",
        "ancient_apparition": "ice_shard",
    }
    _hp_ids = _hp.get("hero_types", [])
    _hp_data_ids = {path.stem for path in (ROOT / "data/heroes").glob("*.tres")}
    check(_hp.get("source") == "_entity.py:4976 Hero._draw_projectile",
          "9bu manifest must pin the source projectile painter")
    check(set(_hp_ids) == _hp_data_ids and len(_hp_ids) == 222,
          "9bu projectile styles must cover all 222 Godot/source heroes")
    check(_hp.get("special_types") == _hp_specials,
          "9bu must retain all five source-specific projectile branches")
    check(set(_hp.get("hero_meta", {})) == set(_hp_ids),
          "9bu source color/radius metadata must cover the full hero roster")
    _hp_source = (ROOT.parent / "_entity.py").read_text(encoding="utf-8")
    _hp_vex = (ROOT.parent / "heroes/vex_fx.py").read_text(encoding="utf-8")
    _hp_zephyr = (ROOT.parent / "heroes/zephyr_fx.py").read_text(encoding="utf-8")
    _hp_aa = (ROOT.parent / "heroes/ancient_apparition_fx.py").read_text(encoding="utf-8")
    _hp_bake = (ROOT / "bake/bake_hero_projectiles.py").read_text(encoding="utf-8")
    _hp_art = (ROOT / "scripts/ui/hero_projectile_art.gd").read_text(encoding="utf-8")
    _hp_view = (ROOT / "scenes/prototype/prototype_view.gd").read_text(encoding="utf-8")
    _hp_projectiles = (ROOT / "scripts/combat/hero_projectiles.gd").read_text(encoding="utf-8")
    _hp_battle = (ROOT / "scripts/match/prototype_battle.gd").read_text(encoding="utf-8")
    _hp_checks = (ROOT / "tests/hero_projectile_art_checks.gd").read_text(encoding="utf-8")
    _hp_painter = (ROOT / "tests/painter_scene_checks.gd").read_text(encoding="utf-8")
    _hp_run_all = (ROOT / "tests/run_all.gd").read_text(encoding="utf-8")
    check("hero._draw_projectile(surface, projectile)" in _hp_bake
          and "heroes_mod._reset_hero_render_budget()" in _hp_bake,
          "9bu baker must render the original pygame painter with its per-draw budget")
    check("_draw_arrow_projectile" in _hp_source
          and "_draw_magic_orb_projectile" in _hp_source
          and "_draw_magic_bolt_projectile" in _hp_source
          and "_draw_lightning_projectile" in _hp_source
          and "_draw_ice_shard_projectile" in _hp_source
          and "draw_arcane_orb" in _hp_vex
          and "draw_bolt" in _hp_zephyr
          and "draw_ice_shard" in _hp_aa,
          "9bu source branch and original FX helper keys must remain present")
    check("_entity.Hero._draw_projectile" in _hp_art
          and "func frame_for(" in _hp_art
          and "ResourceLoader.exists(path)" in _hp_art
          and "TEXTURE_PREFIX := \"res://assets/art/hero_projectiles/\"" in _hp_art,
          "9bu Godot loader must select source frames and retain import fallback")
    check("HeroProjectileArtScript.new()" in _hp_view
          and 'hero_projectile_art.call(' in _hp_view
          and "hero_projectile_draws += 1" in _hp_view
          and "draw_circle(arrow.position, 3, ink)" in _hp_view,
          "9bu prototype painter must draw baked art, count it, and keep fallback")
    check('"hero_type": hero.settings().id' in _hp_projectiles
          and '"is_crit": is_crit' in _hp_projectiles
          and "_hero_ranged_spawn(hero, target, raw, is_crit)" in _hp_battle
          and "HeroProjectiles.spawn(hero_projectiles, hero, target, damage, is_crit)" in _hp_battle,
          "9bu projectile metadata must preserve hero style and Zephyr crit visuals")
    check('const HeroProjectileArtChecks = preload("res://tests/hero_projectile_art_checks.gd")'
          in _hp_run_all
          and "HeroProjectileArtChecks.new().run(_check)" in _hp_run_all
          and "_seed_hero_projectile(world, hero)" in _hp_painter
          and "view.hero_projectile_draws > 0" in _hp_painter,
          "9bu frame and live painter draw-count tests must be registered")
    check(workflow.count("heroes/zephyr_fx.py") == 2
          and workflow.count("heroes/ancient_apparition_fx.py") == 2,
          "9bu helper source changes must trigger both workflow events")

    _hp_expected_frames = {
        "sylara": 32,
        "vex_attack": 73 * 32,
        "vex_skill": 73 * 32,
        "zephyr_basic": 73 * 32,
        "zephyr_crit": 73 * 32,
        "morgath": 73 * 32,
        "ancient_apparition": 32,
        "generic": 2 * (len(_hp_ids) - len(_hp_specials)),
    }
    _hp_expected_cells = {
        "sylara": 40,
        "vex_attack": 48,
        "vex_skill": 48,
        "zephyr_basic": 56,
        "zephyr_crit": 64,
        "morgath": 40,
        "ancient_apparition": 48,
        "generic": 48,
    }
    check(set(_hp_atlases) == set(_hp_expected_frames),
          "9bu atlas set must cover all five special styles and generic heroes")
    check(_hp.get("cell_sizes") == _hp_expected_cells,
          "9bu per-style cells must keep source bounds while limiting texture memory")
    for _atlas_name, _frame_count in _hp_expected_frames.items():
        _entry = _hp_atlases.get(_atlas_name)
        if _entry is None:
            continue
        _png_path = ROOT / "assets/art/hero_projectiles" / _entry.get("file", "")
        check(_png_path.is_file(), f"9bu projectile atlas PNG must ship: {_atlas_name}")
        _cell = _hp_expected_cells.get(_atlas_name, 0)
        check(_entry.get("frames") == _frame_count
              and _entry.get("cell") == _cell
              and _entry.get("columns") == 64,
              f"9bu atlas frame layout must be complete: {_atlas_name}")
        if not _png_path.is_file():
            continue
        _raw = _png_path.read_bytes()
        _width, _height, _depth, _color = struct.unpack(">IIBB", _raw[16:26])
        _size = _entry.get("size", [])
        _rows = (_frame_count + 63) // 64
        check(_raw[:8] == b"\x89PNG\r\n\x1a\n"
              and [_width, _height] == _size
              and [_width, _height] == [64 * _cell, _rows * _cell]
              and (_depth, _color) == (8, 6),
              f"9bu atlas must be a packed RGBA8 sheet: {_atlas_name}")
        check(len(_raw) == _entry.get("bytes")
              and hashlib.sha256(_raw).hexdigest() == _entry.get("sha256")
              and re.fullmatch(r"[0-9a-f]{64}", _entry.get("sha256", "")) is not None,
              f"9bu atlas SHA-256 must match its manifest: {_atlas_name}")
        _age_frames = 1 if _atlas_name in ("sylara", "ancient_apparition", "generic") else 73
        _directions = 1 if _atlas_name == "generic" else 32
        check(_entry.get("age_frames") == _age_frames
              and _entry.get("directions") == _directions,
              f"9bu atlas animation/direction metadata must fit: {_atlas_name}")

    _hp_generic = _hp_atlases.get("generic", {}).get("hero_frames", {})
    _hp_expected_generic = set(_hp_ids) - set(_hp_specials)
    check(set(_hp_generic) == _hp_expected_generic,
          "9bu generic frame table must cover every non-special hero")
    _hp_generic_indices = []
    for _hero_id in _hp_expected_generic:
        _frames = _hp_generic.get(_hero_id, {})
        check(set(_frames) == {"normal", "crit"}
              and _frames.get("crit") == _frames.get("normal", -2) + 1,
              f"9bu generic normal/crit frames must be paired: {_hero_id}")
        _hp_generic_indices.extend(_frames.values())
    check(sorted(_hp_generic_indices) == list(range(_hp_expected_frames["generic"])),
          "9bu generic frame indices must be unique and contiguous")

    _hp_expected_cases = {
        "sylara:arrow:age00:dir00", "sylara:arrow:age00:dir11",
        "vex:attack:age00:dir00", "vex:attack:age36:dir09", "vex:attack:age72:dir31",
        "vex:skill:age00:dir00", "vex:skill:age36:dir12", "vex:skill:age72:dir24",
        "zephyr:basic:age00:dir00", "zephyr:basic:age36:dir08", "zephyr:basic:age72:dir24",
        "zephyr:crit:age00:dir00", "zephyr:crit:age36:dir16", "zephyr:crit:age72:dir31",
        "morgath:lightning:age00:dir00", "morgath:lightning:age36:dir16",
        "morgath:lightning:age72:dir31",
        "ancient_apparition:ice_shard:age00:dir00",
        "ancient_apparition:ice_shard:age00:dir16",
        "kaizen:generic:normal", "kaizen:generic:crit", "abaddon:generic:normal",
    }
    _hp_cases = _hp.get("key_cases", [])
    check({case.get("key") for case in _hp_cases} == _hp_expected_cases
          and len(_hp_cases) == len(_hp_expected_cases),
          "9bu key cases must cover source families, ages, angles, and crit variants")
    for _case in _hp_cases:
        check(re.fullmatch(r"[0-9a-f]{64}", _case.get("pygame_rgb_sha256", "")) is not None
              and re.fullmatch(r"[0-9a-f]{64}", _case.get("rgba_sha256", "")) is not None,
              f"9bu source-render hashes must be pinned: {_case.get('key')}")

for error in errors:
    print("FAIL:", error, file=sys.stderr)
print(f"{'FAIL' if errors else 'PASS'}: {checks} static checks; runtime testing still required.")
sys.exit(bool(errors))
