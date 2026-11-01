class_name UnitInventory
extends RefCounted

## Item slot/stat aggregation from hero_items.HeroItemInventory.
const MAX_SLOTS := 6
var slots: Array = [null, null, null, null, null, null]
var pending: Array[String] = []
var catalog: Dictionary = {}
var aura_armor := 0.0
var aura_attack_speed := 0.0
var aura_armor_reduction := 0.0


func _init(item_catalog: Dictionary = {}) -> void:
	catalog = item_catalog


func used() -> int:
	var count := 0
	for slot: Variant in slots:
		if slot != null:
			count += 1
	return count


func can_add(item_id: String, hero_range: float, magic_hero: bool) -> bool:
	var item: Dictionary = catalog.get(item_id, {})
	if item.is_empty() or used() >= MAX_SLOTS:
		return false
	if item.get("melee_only", false) and hero_range > 80.0:
		return false
	if item.get("magic_only", false) and not magic_hero:
		return false
	return true


func add(item_id: String, hero_range := 0.0, magic_hero := false) -> bool:
	if not can_add(item_id, hero_range, magic_hero):
		return false
	for index in range(MAX_SLOTS):
		if slots[index] == null:
			slots[index] = item_id
			return true
	return false


func remove(index: int) -> String:
	if index < 0 or index >= MAX_SLOTS or slots[index] == null:
		return ""
	var old := str(slots[index])
	slots[index] = null
	return old


func sum_stat(key: String) -> float:
	var total := 0.0
	for slot: Variant in slots:
		if slot != null:
			total += float(catalog.get(slot, {}).get("stats", {}).get(key, 0.0))
	return total


func bonus_damage() -> float:
	return sum_stat("damage")


func bonus_hp() -> float:
	return sum_stat("hp")


func hp_pct() -> float:
	return sum_stat("hp_pct")


func armor() -> float:
	return sum_stat("armor") + aura_armor - aura_armor_reduction


func hp_regen() -> float:
	return sum_stat("hp_regen")


func attack_speed_mult() -> float:
	return clampf(1.0 + (sum_stat("attack_speed") + aura_attack_speed) / 100.0, 0.2, 2.5)


func lifesteal() -> float:
	return minf(1.75, sum_stat("lifesteal"))


func cooldown_reduction() -> float:
	return minf(0.5, sum_stat("cooldown_reduction"))


func spell_vamp() -> float:
	return sum_stat("spell_vamp")


func move_speed_pct() -> float:
	return sum_stat("move_speed_pct")


func max_hp(base_hp: float) -> int:
	return int((base_hp + bonus_hp()) * (1.0 + hp_pct()))


func clear_on_death() -> bool:
	var dropped := false
	for index in range(MAX_SLOTS):
		if slots[index] == "holy_rapier":
			slots[index] = null
			dropped = true
	return dropped


func deliver_pending(hero_range: float, magic_hero: bool) -> Array[String]:
	var delivered: Array[String] = []
	for item_id: String in pending.duplicate():
		if add(item_id, hero_range, magic_hero):
			pending.erase(item_id)
			delivered.append(item_id)
	return delivered


func suggest_for(hero: BattleUnit) -> String:
	var role := str(hero.stats.get("role", "")).to_lower()
	var pool: Array[String] = []
	if "tank" in role or "bruiser" in role or "fighter" in role:
		pool.assign(
			[
				"leviathan_heart",
				"scarlet_bulwark",
				"searbrand",
				"razor_carapace",
				"everfrost_guard",
				"steel_aegis",
				"abyss_breaker",
				"solar_brand",
				"demon_maw",
				"corroder",
				"fenrir_chain",
				"octarine_core",
				"moon_shard"
			]
		)
	elif "marksman" in role or "assassin" in role:
		pool.assign(
			[
				"dead_edge",
				"basilisk_breath",
				"gale_pike",
				"frostbound_eye",
				"sundering_cudgel",
				"searbrand",
				"monarch_wings",
				"thunder_coil",
				"sanguine_thorn",
				"moon_shard",
				"runic_gavel",
				"corroder",
				"demon_maw",
				"octarine_core",
				"steel_aegis"
			]
		)
	elif hero.is_magic_hero():
		pool.assign(
			[
				"astral_codex",
				"fulgur_scepter",
				"sage_scepter",
				"hex_idol",
				"rift_veil",
				"vital_stone",
				"spectral_charm",
				"vine_rod",
				"octarine_core",
				"runic_gavel",
				"searbrand",
				"solar_brand",
				"frostbound_eye",
				"everfrost_guard",
				"tempest_vane",
				"corroder",
				"moon_shard",
				"thunder_coil",
				"steel_aegis",
				"demon_maw",
				"dead_edge"
			]
		)
	else:
		pool.assign(
			[
				"steel_aegis",
				"searbrand",
				"sundering_cudgel",
				"frostbound_eye",
				"razor_carapace",
				"moon_shard",
				"demon_maw",
				"leviathan_heart",
				"scarlet_bulwark",
				"solar_brand",
				"thunder_coil",
				"monarch_wings",
				"octarine_core",
				"gale_pike",
				"dead_edge",
				"corroder",
				"everfrost_guard"
			]
		)
	if hero.is_melee_hero:
		pool.push_front("cleave_axe")
	pool.append("holy_rapier")
	for item_id: String in pool:
		if item_id in slots:
			continue
		if can_add(item_id, hero.attack_range, hero.is_magic_hero()):
			return item_id
	return ""


func has(item_id: String) -> bool:
	return item_id in slots


func block_amount(source: BattleUnit) -> float:
	var total := 0.0
	for slot: Variant in slots:
		if slot == null:
			continue
		var block: Dictionary = catalog.get(slot, {}).get("block", {})
		if block.is_empty():
			continue
		var ranged := source != null and source.attack_range > 80.0
		total += float(block.get("ranged_block" if ranged else "melee_block", 0.0))
	return total
