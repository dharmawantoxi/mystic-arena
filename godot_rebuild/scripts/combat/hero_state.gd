extends "res://scripts/combat/unit_state.gd"
## Kaizen-1 hero state: identity, level math, skill/cooldown helpers.
## Inherits hp/alive/facing/position plus the flat tower-debuff fields
## from UnitState. Battle wiring (spawn/strike/cast/tick) lives in
## minion_battle.gd; this file holds pure per-hero math only.

const HeroDefinition = preload("res://scripts/data/hero_definition.gd")
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
var stun_timer := 0
var w_cooldown := 0
var w_cooldown_max := 0
var e_cooldown := 0
var e_cooldown_max := 0
var r_cooldown := 0
var r_cooldown_max := 0
var active_skill := ""
var active_skill_timer := 0
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
var follow_id := -1
var respawn_timer := 0
var is_retreating := false


func _init() -> void:
	is_hero = true


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


func upgrade_cost() -> int:
	return int(HeroDefinition.level_data(level)["upgrade_cost"])


func upgrade() -> bool:
	if level >= HeroDefinition.MAX_HERO_LEVEL:
		return false
	level += 1
	apply_level_stats()
	return true


func skill_damage() -> int:
	# Port of the Hero.skill_damage getter (no-item amp in Kaizen-1).
	if skill_down_timer > 0:
		var factor := maxf(0.0, 1.0 - skill_down_amount)
		return Damage.rounded_like_python(skill_value * factor)
	return skill_value


func eff_attack_cd(base_cd: int) -> int:
	# Port of Hero._eff_attack_cd with an empty inventory (AS mult 1.0).
	if stun_timer > 0:
		return 9999
	var value := float(base_cd) / 1.0
	if atk_slow_timer > 0:
		var factor := maxf(0.05, 1.0 - atk_slow_amount)
		value = value / factor
	return maxi(1, Damage.rounded_like_python(value))


func eff_attack_range() -> float:
	return attack_range
