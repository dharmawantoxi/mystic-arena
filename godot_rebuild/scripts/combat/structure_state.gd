extends "res://scripts/combat/unit_state.gd"

const Damage = preload("res://scripts/combat/damage_rules.gd")
const StructureDefinition = preload("res://scripts/data/structure_definition.gd")
var shield := 0.0
var shield_max := 0.0
var shield_active := true
var free_shield_active := true
var castle_shield_purchased := false
var no_damage_ticks := 0


func settings() -> StructureDefinition:
	return definition as StructureDefinition


func set_wave(wave: int) -> void:
	if settings().structure_kind != "nexus" or not alive:
		return
	free_shield_active = wave <= settings().free_shield_waves
	if free_shield_active:
		shield_active = true
		if shield <= 0:
			shield = shield_max
	elif not castle_shield_purchased:
		shield_active = false
		shield = 0
	else:
		shield_active = true


func tick_regen() -> void:
	if not alive:
		return
	no_damage_ticks += 1
	var data := settings()
	if no_damage_ticks >= data.hp_regen_delay_ticks:
		hp = minf(data.max_hp, hp + data.regen_per_tick)
	if data.shield_regen_enabled and shield_active:
		if no_damage_ticks >= data.shield_regen_delay_ticks:
			shield = minf(shield_max, shield + data.shield_regen_per_tick)


func absorb(raw_damage: int, school: String) -> float:
	# Caller validates positive damage and recognized school before invoking this.
	no_damage_ticks = 0
	var data := settings()
	var remaining := float(raw_damage)
	if data.structure_kind == "tower":
		# Unlike minions, non-positive tower armor does NOT amplify damage.
		if school == "physical":
			var armor := maxf(0, data.armor)
			remaining = Damage.resolve(raw_damage, armor, 0, school)
		elif data.magic_resist > 0:
			remaining = Damage.resolve(raw_damage, 0, data.magic_resist, school)
	if shield_active:
		var absorbed := minf(shield, remaining)
		shield -= absorbed
		remaining -= absorbed
		if data.structure_kind == "nexus" and remaining > 0:
			remaining = int(remaining * (1.0 - data.shield_damage_reduction))
	return remaining
