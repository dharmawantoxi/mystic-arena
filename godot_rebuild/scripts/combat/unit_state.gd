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
# Source `Minion.nexus_level`: the owner's nexus tier at spawn. Presentation only: it
# picks the baked sprite (`minions/_bundle.py` keys its cache on it), never a rule.
var nexus_level := 1
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


func apply_slow(amount: float, duration: int) -> void:
	# Layer 9ae: port of `TowerDebuffMixin.apply_slow` (`_core.py:853-867`), the
	# polymorphic method every item slow arm calls (`target.apply_slow(...)` in
	# Frostbite `hero_items.py:2594-2595`, Vine Rod Entangle `:2662`, Arctic
	# Blast `:2290-2291`). A dead victim is ignored, the victim's item slow
	# resist scales the incoming payload, and the store rewrites BOTH fields on
	# `amount > slow_amount or slow_timer < duration`. The pre-9ae bus write
	# (`maxf`/`maxi`, no resist, no alive guard) skipped all three for any
	# victim that had no `apply_slow` method of its own - which was every unit
	# but the boss.
	if not alive:
		return
	var resist := slow_resist()
	if resist > 0.0:
		amount *= 1.0 - resist
	if amount > slow_amount or slow_timer < duration:
		slow_amount = amount
		slow_timer = duration


func slow_resist() -> float:
	# Source reads the victim's inventory (`inv.get_slow_resist()`); only heroes
	# carry one, so the base entity resists nothing.
	return 0.0


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
