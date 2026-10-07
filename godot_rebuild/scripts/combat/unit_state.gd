extends RefCounted

const Definition = preload("res://scripts/data/minion_definition.gd")

var id: int
var team: int
var lane: int
var definition: Definition
var position := Vector2.ZERO
var waypoint_index := 0
var hp := 0.0
var cooldown_ticks := 0
var target_id := -1
var alive := true
var is_hero := false
var facing := 1.0
var ai_level := 1
var burn_dps := 0.0
var burn_timer := 0
var burn_accum := 0.0
var burn_tick_cd := 0
var burn_team := -1
var slow_amount := 0.0
var slow_timer := 0
var atk_slow_amount := 0.0
var atk_slow_timer := 0
var skill_down_amount := 0.0
var skill_down_timer := 0
var anti_heal_amount := 0.0
var anti_heal_timer := 0
# Abyss Breaker heal amp (source TowerDebuffMixin heal_amp_* fields).
var heal_amp_amount := 0.0
var heal_amp_timer := 0
# Layer 5b-3: item debuffs that land on the TARGET (source TowerDebuffMixin).
var armor_shred_amount := 0.0
var armor_shred_timer := 0
var dmg_amp_amount := 0.0
var dmg_amp_timer := 0
# Source TowerDebuffMixin: blind (Scorched Earth aura) = chance an INCOMING
# physical hit misses; read from the ATTACKER in the evasion gate.
var blind_amount := 0.0
var blind_timer := 0
# Source `_entity.credit_hero_damage`: every take_damage path adds the
# post-mitigation damage to the attacker total. The tactical command
# ATTACK DAMAGE DEALER picks the red hero with the highest value, so the
# counter lives on UnitState exactly like the source's dynamic attribute
# (`getattr(source, "damage_dealt", 0)`).
var damage_dealt := 0


func apply_armor_shred(amount: float, duration: int) -> void:
	# Port of TowerDebuffMixin.apply_armor_shred (Corroder): strongest wins,
	# a longer duration refreshes both fields, a dead target is ignored.
	if not alive:
		return
	if amount > armor_shred_amount or armor_shred_timer < duration:
		armor_shred_amount = amount
		armor_shred_timer = duration


func apply_damage_amp(amount: float, duration: int) -> void:
	# Port of TowerDebuffMixin.apply_damage_amp (Soul Rend), same stacking.
	if not alive:
		return
	if amount > dmg_amp_amount or dmg_amp_timer < duration:
		dmg_amp_amount = amount
		dmg_amp_timer = duration


func apply_miss_chance(amount: float, duration: int) -> void:
	# Port of TowerDebuffMixin.apply_miss_chance (Solar Brand aura): strongest
	# wins, a longer duration refreshes both fields, a dead target is ignored.
	if not alive:
		return
	if amount > blind_amount or blind_timer < duration:
		blind_amount = amount
		blind_timer = duration


func tick_item_debuffs() -> void:
	# Port of the item slice of TowerDebuffMixin._tick_tower_debuffs: each
	# timer decays by one tick and clears its amount on the last tick.
	if armor_shred_timer > 0:
		armor_shred_timer -= 1
		if armor_shred_timer <= 0:
			armor_shred_amount = 0.0
	if dmg_amp_timer > 0:
		dmg_amp_timer -= 1
		if dmg_amp_timer <= 0:
			dmg_amp_amount = 0.0
	if heal_amp_timer > 0:
		heal_amp_timer -= 1
		if heal_amp_timer <= 0:
			heal_amp_amount = 0.0
	if blind_timer > 0:
		blind_timer -= 1
		if blind_timer <= 0:
			blind_amount = 0.0
