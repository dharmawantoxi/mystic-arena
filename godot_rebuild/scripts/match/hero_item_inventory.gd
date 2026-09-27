extends RefCounted
## Port of HeroItemInventory SLOT bookkeeping: six slots, the melee_only and
## magic_only gates, drop-on-death. The source instance lives on the hero as
## `hero.items`; the rebuild keeps one per HeroState too.
##
## LIMITATION, NOT PARITY: the source `add` and `remove` call
## `_on_item_changed`, which recomputes `hero.max_hp` (`get_max_hp` =
## base_hp * HERO_LEVELS hp_mult + item hp/hp_pct) and re-applies heal amp
## (`apply_heal_amp`, Abyss Breaker). Hero stat aggregation, item passives,
## actives and auras are not ported, so here a purchase only fills a slot and
## never touches max_hp/hp. The source-side numbers are locked in
## `tests/fixtures/ai_items_source.json` ("inventory") so the gap stays visible
## and this contract has to be updated when the stats are ported.
## The source also resets per-item timers in `clear_on_death`; timers belong to
## the stat/active phase and are absent here.

const HeroItems = preload("res://scripts/match/hero_items.gd")
const RAPIER := "holy_rapier"

# Plain copies of the owner role/attack range (refreshed by HeroState). The
# source reads them from the hero on every equip; both values are fixed once
# the definition is assigned, and copies keep hero/inventory free of a
# RefCounted reference cycle.
var hero_role := ""
var hero_range := 0.0
var catalog: Dictionary
var slots: Array = []


func _init(metadata: Dictionary = {}) -> void:
	if metadata.is_empty():
		catalog = JSON.parse_string(FileAccess.get_file_as_string(HeroItems.METADATA))
	else:
		catalog = metadata.duplicate(true)
	slots.resize(max_slots())


func set_hero_gate(role: String, attack_range: float) -> void:
	hero_role = role
	hero_range = attack_range


func max_slots() -> int:
	return int(catalog.get("max_slots", 6))


func item(item_id: String) -> Dictionary:
	var items: Dictionary = catalog.get("items", {})
	return items.get(item_id, {})


func count(item_id: String) -> int:
	var total := 0
	for slot in slots:
		if slot == item_id:
			total += 1
	return total


func has(item_id: String) -> bool:
	return slots.has(item_id)


func used_slots() -> int:
	var used := 0
	for slot in slots:
		if slot != null:
			used += 1
	return used


func owned() -> Array:
	# Source builds `set(s for s in slots if s is not None)` before suggesting.
	var result: Array = []
	for slot in slots:
		if slot != null:
			result.append(String(slot))
	return result


func add(item_id: String) -> bool:
	# Fill the first empty slot. Source returns False on unknown id, on a
	# melee_only item for a ranged hero (`rng and rng > 80`, so range 0 passes)
	# and on a magic_only item for a non-magic role.
	var data := item(item_id)
	if data.is_empty():
		return false
	if bool(data.get("melee_only", false)) and hero_range > HeroItems.MELEE_RANGE_LIMIT:
		return false
	if bool(data.get("magic_only", false)) and not HeroItems.is_magic_hero(hero_role):
		return false
	for index in range(max_slots()):
		if slots[index] == null:
			slots[index] = item_id
			return true
	return false


func remove(slot_index: int) -> String:
	# Source drop: no gold refund. Returns the dropped id or an empty string.
	if slot_index < 0 or slot_index >= max_slots():
		return ""
	var old = slots[slot_index]
	if old == null:
		return ""
	slots[slot_index] = null
	return String(old)


func clear_on_death() -> bool:
	# Source: Holy Rapier is destroyed, never dropped on the ground.
	var dropped := false
	for index in range(max_slots()):
		if slots[index] == RAPIER:
			slots[index] = null
			dropped = true
	return dropped
