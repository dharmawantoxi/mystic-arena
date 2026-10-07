extends "res://scripts/combat/unit_state.gd"

const Damage = preload("res://scripts/combat/damage_rules.gd")
const StructureDefinition = preload("res://scripts/data/structure_definition.gd")
const REGEN_SHIELD_MIN_LEVEL := 4
const REGEN_SHIELD_COST := 850
const CASTLE_SHIELD_COST := REGEN_SHIELD_COST

# Source Tower.kills exists but nothing in the Python game ever increments it,
# so AI kill-priority over towers degenerates to a stable order-preserving sort.
var kills := 0
var regen_shield_active := false
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


func can_activate_regen_shield() -> bool:
	return (
		alive
		and settings().structure_kind == "tower"
		and settings().level >= REGEN_SHIELD_MIN_LEVEL
		and not regen_shield_active
	)


func activate_regen_shield() -> bool:
	if not can_activate_regen_shield():
		return false
	regen_shield_active = true
	shield = shield_max
	# Source does NOT reset the tower's shared HP/shield regen clock here.
	return true


func regen_shield_cost() -> int:
	return REGEN_SHIELD_COST


func castle_shield_cost() -> int:
	return CASTLE_SHIELD_COST


func can_activate_castle_shield() -> bool:
	# Extra native alive/kind guard; Python assumes Game only supplies its live castle.
	return (
		alive
		and settings().structure_kind == "nexus"
		and not free_shield_active
		and not castle_shield_purchased
	)


func activate_castle_shield() -> bool:
	if not can_activate_castle_shield():
		return false
	castle_shield_purchased = true
	free_shield_active = false
	shield_active = true
	shield_max = settings().shield_capacity
	shield = shield_max
	no_damage_ticks = 0
	return true


func sale_value() -> int:
	var shield_refund := int(REGEN_SHIELD_COST / 2.0) if regen_shield_active else 0
	return settings().sale_refund + shield_refund


func tick_regen() -> void:
	if not alive or (settings().structure_kind == "nexus" and not shield_active):
		return
	no_damage_ticks += 1
	var data := settings()
	if no_damage_ticks >= data.hp_regen_delay_ticks:
		hp = minf(data.max_hp, hp + data.regen_per_tick)
	var regen_enabled := (
		regen_shield_active if data.structure_kind == "tower" else data.shield_regen_enabled
	)
	if regen_enabled and shield_active:
		if no_damage_ticks >= data.shield_regen_delay_ticks:
			shield = minf(shield_max, shield + data.shield_regen_per_tick)


func absorb(raw_damage: int, school: String) -> float:
	# Caller validates positive damage and recognized school before invoking this.
	if settings().structure_kind == "tower" or shield_active:
		no_damage_ticks = 0
	var data := settings()
	var remaining := float(raw_damage)
	if data.structure_kind == "tower":
		# Unlike minions, non-positive tower armor does NOT amplify damage.
		if school == "physical":
			var armor := maxf(0, data.armor)
			remaining = Damage.resolve(raw_damage, armor, 0, school)
		elif school == "magic" and data.magic_resist > 0:
			remaining = Damage.resolve(raw_damage, 0, data.magic_resist, school)
	if shield_active:
		var absorbed := minf(shield, remaining)
		shield -= absorbed
		remaining -= absorbed
		if data.structure_kind == "nexus" and remaining > 0:
			remaining = int(remaining * (1.0 - data.shield_damage_reduction))
	return remaining
