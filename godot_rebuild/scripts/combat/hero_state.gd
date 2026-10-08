extends "res://scripts/combat/unit_state.gd"
## Per-instance native hero identity, level math and source kit/cooldown state.
## Inherits hp/alive/facing/position plus the flat tower-debuff fields
## from UnitState. Battle wiring (spawn/strike/cast/tick) lives in
## minion_battle.gd; this file holds pure per-hero math only.

const HeroDefinition = preload("res://scripts/data/hero_definition.gd")
const HeroItemInventory = preload("res://scripts/match/hero_item_inventory.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const Damage = preload("res://scripts/combat/damage_rules.gd")

var level := 1
var base_hp := 0
var base_damage := 0
var skill_base := 0
var damage := 0
var skill_value := 0
var max_hp := 0.0
var speed := 0.0
var attack_range := 0.0
var attack_cd_base := 0
var attack_timer := 0
var skill_timer := 0
var skill_cd_max := 0
var skill_range := 0.0
var dmg_school := "physical"
var is_melee := true
var attack_seq := 0
var attack_facing := 1.0
var deaths := 0
var killed_by := -1
# Source Hero.kills: only incremented by Game._process_hero_kill/_process_boss_kill
# when an enemy HERO lands the killing blow. AI upgrade priority reads it.
var kills := 0
# Source credit_hero_damage: post-mitigation damage dealt by a known hero.
# Tactical ATTACK DAMAGE DEALER ranks living enemy heroes by this total.
var damage_dealt := 0
var stun_timer := 0
var w_cooldown := 0
var w_cooldown_max := 0
var e_cooldown := 0
var e_cooldown_max := 0
var r_cooldown := 0
var r_cooldown_max := 0
var active_skill := ""
var active_skill_timer := 0
# Thorne kit state is per hero instance, never stored in the shared .tres.
var viscous_timer := 0
var bristleback_timer := 0
var quill_timer := 0
var warpath_timer := 0
var warpath_original_attack_cd := 0
# Grimjaw kit state (per instance; never stored on a shared definition).
var blade_fury_timer := 0
var heal_ward_timer := 0
var heal_ward_position := Vector2.ZERO
var omnislash_timer := 0
var omnislash_target_id := -1
var grimjaw_crit_timer := 0
# Sylara state: only this hero uses projectile, Windrun and ranged timers.
var focus_fire_timer := 0
var windrun_timer := 0
var windrun_original_speed := 0.0
var shackle_timer := 0
var shackle_target_id := -1
var powershot_timer := 0
# Vex and Zephyr source kit state; timers intentionally survive source respawn.
var eclipse_timer := 0
var prison_timer := 0
var prison_target_id := -1
var essence_timer := 0
var bramble_timer := 0
var bramble_origin := Vector2.ZERO
var shadow_realm_timer := 0
var curse_timer := 0
var curse_target_id := -1
var bedlam_timer := 0
# Source BossHeroSkills state (level-one recipes).
var alchemy_target := Vector2.ZERO
var rage_timer := 0
var defense_timer := 0
var flux_timer := 0
var flux_target_id := -1
var clones_timer := 0
var blink_from := Vector2.ZERO
var mana_void_origin := Vector2.ZERO
# Level 3 recipes (Ancient Apparition + Nyzrak) + future shield/vortex.
var vortex_origin := Vector2.ZERO
var vortex_timer := 0
var shield_active := false
var shield_timer := 0
var w_dir := Vector2(1, 0)
var r_dir := Vector2(1, 0)
# Level 4 (Ignis Drachorn) dragon form.
var dragon_form_active := false
var dragon_form_timer := 0
var dragon_blood_active := false
var dragon_blood_timer := 0
var q_stack := 0
var q_reset_timer := 0
var is_dashing := false
var dash_timer := 0
var wind_wall_timer := 0
var ulti_active := false
var ulti_timer := 0
var target_struct: StructureState = null
var has_destination := false
var destination := Vector2.ZERO
# Layer 6a: destination ordered by the AI brain (`move_to(..., auto=True)`).
# A manual destination always wins; an auto one is dropped as soon as an enemy
# enters aggro range (source Hero.update destination_auto rule).
var destination_auto := false
var follow_id := -1
var respawn_timer := 0
# Layer 5f: Forge orders bought while the hero is dead (source
# hero._pending_forge_items). Delivered by forge.deliver_pending_forge_items()
# right after respawn.
var pending_items: Array = []
var is_retreating := false
var auto_cast_enabled := false
var auto_cast_check_timer := 0

# Source Hero.items (HeroItemInventory): six slots, melee/magic gates, rapier
# lost on death. Slot bookkeeping only - item stat effects are NOT ported, so
# slots never change max_hp/hp here (see hero_item_inventory.gd).
var items: HeroItemInventory = null


func _init() -> void:
	is_hero = true
	items = HeroItemInventory.new()


func settings() -> HeroDefinition:
	return definition as HeroDefinition


func apply_level_stats() -> void:
	# Port of Hero._apply_level_stats, items branch: real heroes always
	# carry an (empty) inventory, so hp is NEVER touched here. The oracle
	# locks this: a 1-hp hero stays at 1 hp through every upgrade.
	level = mini(level, HeroDefinition.MAX_HERO_LEVEL)
	var data: Dictionary = HeroDefinition.level_data(level)
	damage = int(base_damage * float(data["dmg_mult"]))
	skill_value = int(skill_base * float(data["skill_mult"]))
	max_hp = float(int(base_hp * float(data["hp_mult"])))
	# The source inventory reads role/range from the hero when equipping; the
	# definition is assigned after construction, so refresh the gate copies
	# here. Item HP bonuses stay out of max_hp until the stat phase is ported.
	var kit := settings()
	if kit != null:
		items.set_hero_gate(kit.role, attack_range)
	# Source Hero.is_melee_hero is exactly `range < 110` (_entity.py:3303), and
	# the item getters read base_hp/level for get_max_hp.
	items.set_hero_scaling(base_hp, level, 1 if attack_range < 110.0 else 0)
	# Source Hero._apply_level_stats ends with _recalc_item_stats(): the level
	# sets the base max HP, the inventory adds its flat + percent bonus.
	recalc_item_stats()


func recalc_item_stats() -> void:
	# Port of Hero._recalc_item_stats (_entity.py:3491): grow the current HP by
	# the max HP gain, shrink it only when it exceeds the new maximum.
	var new_max := float(items.get_max_hp())
	var old_max := max_hp
	max_hp = new_max
	if new_max > old_max:
		hp = minf(new_max, hp + (new_max - old_max))
	elif hp > new_max:
		hp = new_max


func apply_item_change() -> void:
	# Port of HeroItemInventory._on_item_changed. The inventory keeps no hero
	# reference (no RefCounted cycle), so the match transaction calls this
	# right after a successful equip or drop.
	recalc_item_stats()
	var amp := items.get_heal_amp()
	if amp > 0.0:
		apply_heal_amp(amp, 999999)


func apply_heal_amp(amount: float, duration: int) -> void:
	# Port of TowerDebuffMixin.apply_heal_amp (_core.py:900).
	if not alive:
		return
	if amount > heal_amp_amount or heal_amp_timer < duration:
		heal_amp_amount = amount
		heal_amp_timer = duration


func upgrade_cost() -> int:
	var price := int(HeroDefinition.level_data(level)["upgrade_cost"])
	return int(price * 1.6) if settings().is_boss_hero else price


func upgrade() -> bool:
	if level >= HeroDefinition.MAX_HERO_LEVEL:
		return false
	level += 1
	apply_level_stats()
	return true


func skill_damage() -> int:
	# Port of the Hero.skill_damage getter (layer 5b-5): the Astral Codex skill
	# amp is applied first, the Mage Tower skill-down factor after it.
	var base := float(skill_value)
	var amp := items.get_skill_amp()
	if amp > 0.0:
		base = float(Damage.rounded_like_python(base * (1.0 + amp)))
	if skill_down_timer > 0:
		var factor := maxf(0.0, 1.0 - skill_down_amount)
		return Damage.rounded_like_python(base * factor)
	return int(base)


func cdr_cooldown(cooldown_max: int) -> int:
	# Port of the Octarine Core slice of Hero.cast_skill: cooldowns are only
	# refreshed by the skill gates (cd <= 0), so the source's
	# `max(0, after - added * cdr)` with `before == 0` is `cd_max * (1 - cdr)`.
	var cdr := items.get_cooldown_reduction()
	if cdr <= 0.0:
		return cooldown_max
	return maxi(0, Damage.rounded_like_python(float(cooldown_max) * (1.0 - cdr)))


func spell_vamp_heal() -> int:
	# Port of the Octarine Core / Astral Codex spell vamp: an instant heal from
	# the hero's own skill damage, capped at max HP and NOT routed through
	# heal_hp (source sets `self.hp` directly, so heal amp does not apply).
	var vamp := items.get_spell_vamp()
	if vamp <= 0.0:
		return 0
	var heal := int(float(skill_damage()) * vamp)
	if heal <= 0:
		return 0
	hp = minf(max_hp, hp + float(heal))
	return heal


func eff_attack_cd(base_cd: int) -> int:
	# Port of Hero._eff_attack_cd: item attack speed first (Moon Shard,
	# Gale Pike active), then the Ice attack-slow divisor.
	if stun_timer > 0:
		return 9999
	var value := float(base_cd)
	var mult := items.get_attack_speed_mult()
	if mult > 0.0:
		value = value / mult
	if atk_slow_timer > 0:
		var factor := maxf(0.05, 1.0 - atk_slow_amount)
		value = value / factor
	return maxi(1, Damage.rounded_like_python(value))


func eff_attack_range() -> float:
	# Port of Hero._eff_attack_range: the item reach bonus only applies to a
	# ranged owner (inventory gate), so melee heroes stay at their base range.
	return attack_range + items.get_range_bonus()


func eff_speed() -> float:
	# Port of TowerDebuffMixin._eff_speed: movement slow, then the item move
	# speed bonus (Tempest Vane), then a stun pinning the hero in place.
	var value := speed
	if slow_timer > 0:
		value *= 1.0 - slow_amount
	value *= 1.0 + items.get_move_speed_pct()
	if stun_timer > 0:
		value = 0.0
	return value


func heal_hp(amount: float) -> void:
	# Source TowerDebuffMixin.hp setter: cap first, then reduce the gain.
	var desired := minf(max_hp, hp + amount)
	if desired > hp and anti_heal_timer > 0:
		desired = hp + (desired - hp) * (1.0 - anti_heal_amount)
	if desired > hp and heal_amp_timer > 0:
		desired = hp + (desired - hp) * (1.0 + heal_amp_amount)
	hp = desired
