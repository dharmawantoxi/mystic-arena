# gdlint:disable=max-public-methods
extends RefCounted
## Port of HeroItemInventory: six slots, the melee_only/magic_only gates,
## drop-on-death, and the PURE stat aggregation getters. The source instance
## lives on the hero as `hero.items`; the rebuild keeps one per HeroState.
##
## LIMITATION, NOT PARITY (layer 5a scope):
## - `_on_item_changed` (source add/remove hook) is NOT ported: equipping does
##   not recompute `hero.max_hp`/`hp` nor re-apply heal amp yet. `get_max_hp()`
##   below reports what the source would compute, but nothing consumes it.
## - The active/passive/aura timers the getters read (`blood_frenzy_timer`,
##   `ghost_timer`, `thorn_timer`, `gale_timer`, `veil_timer`, `guard_timer`,
##   `rend_timer`, `aura_*`) exist but nothing drives them, so every
##   timer-gated branch stays closed in this layer.
## - `update()`, `notify_damage_taken()`, `on_basic_attack_hit()`,
##   `_on_hit_common()`, `on_ranged_attack_hit()` and `update_auras()` are not
##   ported: no proc, no chain lightning, no miasma, no aura application.
## The source-side values are locked in `tests/fixtures/ai_items_source.json`
## ("stats"), so this contract has to be updated when those phases land.

const HeroItems = preload("res://scripts/match/hero_items.gd")
const HeroDefinition = preload("res://scripts/data/hero_definition.gd")
const RAPIER := "holy_rapier"

# Plain copies of the owner role/attack range/base HP/level (refreshed by
# HeroState). The source reads them from the hero on every call; copies keep
# hero and inventory free of a RefCounted reference cycle.
var hero_role := ""
var hero_range := 0.0
var hero_base_hp := 0
var hero_level := 1
# -1 = unknown, so get_range_bonus falls back to the source `range < 110`
# heuristic (Hero.is_melee_hero is that same rule, _entity.py:3303).
var hero_melee_flag := -1
var catalog: Dictionary
var slots: Array = []
# Read by the getters below, never advanced in this layer (see header).
var aura_armor := 0
var aura_as := 0
var aura_armor_reduction := 0
var aura_guard_block := 0
var blood_frenzy_timer := 0
var ghost_timer := 0
var thorn_timer := 0
var gale_timer := 0
var veil_timer := 0
var guard_timer := 0
var rend_timer := 0
var empower_charge := 0


func _init(metadata: Dictionary = {}) -> void:
	if metadata.is_empty():
		catalog = JSON.parse_string(FileAccess.get_file_as_string(HeroItems.METADATA))
	else:
		catalog = metadata.duplicate(true)
	slots.resize(max_slots())
	# Source __init__ preloads the Runic Gavel charge whether or not it is owned.
	empower_charge = int(item("runic_gavel").get("passive", {}).get("charge_time", 0))


func set_hero_gate(role: String, attack_range: float) -> void:
	hero_role = role
	hero_range = attack_range


func set_hero_scaling(base_hp: int, level: int, melee_flag: int) -> void:
	hero_base_hp = base_hp
	hero_level = level
	hero_melee_flag = melee_flag


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


# ── Agregasi stat (port getter murni) ─────────────────────────
func sum_stat(key: String) -> float:
	var total := 0.0
	for slot in slots:
		if slot == null:
			continue
		var stats: Dictionary = item(String(slot)).get("stats", {})
		total += float(stats.get(key, 0.0))
	return total


func level_hp_mult() -> float:
	var data: Dictionary = HeroDefinition.level_data(hero_level)
	return float(data["hp_mult"])


func is_melee_owner() -> bool:
	# Source get_range_bonus: explicit flag first, `range < 110` heuristic else.
	if hero_melee_flag >= 0:
		return hero_melee_flag == 1
	return hero_range < 110.0


func get_bonus_damage() -> float:
	return sum_stat("damage")


func get_bonus_hp() -> float:
	return sum_stat("hp")


func get_hp_pct() -> float:
	return sum_stat("hp_pct")


func get_armor() -> float:
	return sum_stat("armor") + float(aura_armor) - float(aura_armor_reduction)


func get_hp_regen() -> float:
	return sum_stat("hp_regen")


func get_max_hp() -> int:
	# Source: (base_hp * HERO_LEVELS hp_mult + item hp) * (1 + hp_pct).
	var base := int(float(hero_base_hp) * level_hp_mult())
	return int(float(base + get_bonus_hp()) * (1.0 + get_hp_pct()))


func get_attack_speed_mult() -> float:
	var total := sum_stat("attack_speed") + float(aura_as) + get_gale_as_bonus()
	return maxf(0.2, minf(2.5, 1.0 + total / 100.0))


func get_lifesteal_pct() -> float:
	var total := sum_stat("lifesteal")
	if blood_frenzy_timer > 0:
		total += 1.5
	return minf(1.75, total)


func get_crit() -> Array:
	# Source returns (chance, mult); the multiplier starts at 2.0.
	var chance := 0.0
	var mult := 2.0
	for slot in slots:
		if slot == null:
			continue
		var stats: Dictionary = item(String(slot)).get("stats", {})
		if stats.has("crit_chance"):
			chance = maxf(chance, float(stats["crit_chance"]))
			mult = maxf(mult, float(stats.get("crit_mult", 2.25)))
	return [chance, mult]


func get_cleave() -> Variant:
	for slot in slots:
		if slot == null:
			continue
		var passive: Dictionary = item(String(slot)).get("passive", {})
		if String(passive.get("name", "")) == "Cleave":
			return [float(passive["cleave_pct"]), float(passive["cleave_radius"])]
	return null


func get_cooldown_reduction() -> float:
	return minf(0.5, sum_stat("cooldown_reduction"))


func get_spell_vamp() -> float:
	return sum_stat("spell_vamp")


func get_skill_amp() -> float:
	return minf(0.5, sum_stat("skill_amp"))


func get_evasion() -> float:
	if ghost_timer > 0 and has("spectral_charm"):
		return 1.0
	return minf(0.5, sum_stat("evasion"))


func get_move_speed_pct() -> float:
	return minf(0.4, sum_stat("move_speed_pct"))


func get_heal_amp() -> float:
	return minf(0.5, sum_stat("heal_amp"))


func get_slow_resist() -> float:
	return minf(0.6, sum_stat("slow_resist"))


func get_range_bonus() -> float:
	if is_melee_owner():
		return 0.0
	return sum_stat("range_bonus")


func has_true_strike() -> bool:
	return has("sundering_cudgel")


func get_reflect_pct() -> float:
	if thorn_timer > 0 and has("razor_carapace"):
		return float(item("razor_carapace").get("active", {}).get("reflect_pct", 0.0))
	return 0.0


func get_gale_as_bonus() -> float:
	if gale_timer > 0 and has("gale_pike"):
		return float(item("gale_pike").get("active", {}).get("as_bonus", 0.0))
	return 0.0


func consume_empower_strike() -> int:
	if has("runic_gavel") and empower_charge <= 0:
		var passive: Dictionary = item("runic_gavel").get("passive", {})
		empower_charge = int(passive.get("charge_time", 0))
		return int(passive.get("damage", 0))
	return 0


func get_block() -> Variant:
	# Source: `rng or 100`, so range 0 counts as ranged here (unlike add()).
	var melee := HeroItems.source_range(hero_range) <= HeroItems.MELEE_RANGE_LIMIT
	var best: Variant = null
	for slot in slots:
		if slot == null:
			continue
		var block: Dictionary = item(String(slot)).get("block", {})
		if block.is_empty():
			continue
		var amount := float(block["melee_block"] if melee else block["ranged_block"])
		var chance := float(block["chance"])
		if best == null or chance > float(best[0]) or amount > float(best[1]):
			best = [chance, amount]
	return best


func get_armor_shred() -> Variant:
	for slot in slots:
		if slot == null:
			continue
		var passive: Dictionary = item(String(slot)).get("passive", {})
		if passive.has("armor_shred"):
			return [float(passive["armor_shred"]), float(passive.get("duration", 300))]
	return null


func get_on_attack_chain() -> Variant:
	# Source bugfix: only a real chain dict (chance + targets + radius + damage),
	# so Frostbite/Miasma on_attack blocks are never read as chain lightning.
	for slot in slots:
		if slot == null:
			continue
		var chain: Dictionary = item(String(slot)).get("on_attack", {})
		if (
			chain.has("chance")
			and chain.has("targets")
			and chain.has("radius")
			and chain.has("damage")
		):
			return chain
	return null


func get_bash() -> Variant:
	# Source bugfix: only Abyss Breaker, never Sundering Cudgel's bash block.
	if has("abyss_breaker"):
		return item("abyss_breaker").get("bash", {})
	return null


func is_veiled() -> bool:
	return veil_timer > 0


func is_guarding() -> bool:
	return guard_timer > 0


func get_rend_crit() -> Variant:
	if rend_timer > 0 and has("sanguine_thorn"):
		return float(item("sanguine_thorn").get("active", {}).get("crit_mult", 0.0))
	return null
