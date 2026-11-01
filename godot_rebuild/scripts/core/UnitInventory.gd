class_name UnitInventory
extends RefCounted

## Native port of hero_items.HeroItemInventory: slots, stat aggregation,
## active timers and passive getters. Runtime triggers live in EntityItems.
const MAX_SLOTS := 6
const TIMER_KEYS := [
	"blood_frenzy",
	"blood_frenzy_cd",
	"last_damage",
	"guard",
	"guard_cd",
	"veil",
	"veil_cd",
	"chains_cd",
	"rend",
	"rend_cd",
	"bash_cd",
	"overwhelm_cd",
	"static",
	"static_cd",
	"static_tick",
	"thorn",
	"thorn_cd",
	"arctic_cd",
	"gale",
	"gale_cd",
	"pierce_bash_cd",
	"searbrand_cd",
	"arcane_cd",
	"fulgur_cd",
	"hex_cd",
	"rift_cd",
	"pact_cd",
	"vine_cd",
	"ghost",
	"ghost_cd"
]

var slots: Array = [null, null, null, null, null, null]
var pending: Array[String] = []
var catalog: Dictionary = {}
var state: Dictionary = {}
var aura_armor := 0.0
var aura_attack_speed := 0.0
var aura_armor_reduction := 0.0
var aura_guard_block := 0.0
var hero: BattleUnit:
	get:
		return _hero_ref.get_ref() as BattleUnit if _hero_ref != null else null
	set(value):
		_hero_ref = weakref(value) if value != null else null
var _hero_ref: WeakRef = null


func _init(item_catalog: Dictionary = {}) -> void:
	catalog = item_catalog
	state["empower_charge"] = int(
		catalog.get("runic_gavel", {}).get("passive", {}).get("charge_time", 0)
	)


func timer(key: String) -> int:
	return int(state.get(key, 0))


func set_timer(key: String, value: int) -> void:
	state[key] = value


func tick_timers(dt := 1) -> void:
	for key: String in TIMER_KEYS:
		if timer(key) > 0:
			state[key] = timer(key) - dt
	if timer("rend") <= 0:
		state["rend_target"] = null
	if has("runic_gavel") and timer("empower_charge") > 0:
		state["empower_charge"] = maxi(0, timer("empower_charge") - dt)


func count(item_id: String) -> int:
	var total := 0
	for slot: Variant in slots:
		if slot == item_id:
			total += 1
	return total


func used() -> int:
	var count := 0
	for slot: Variant in slots:
		if slot != null:
			count += 1
	return count


func used_slots() -> int:
	return used()


func can_add(item_id: String, hero_range: float, magic_hero: bool) -> bool:
	var item: Dictionary = catalog.get(item_id, {})
	if item.is_empty() or used() >= MAX_SLOTS:
		return false
	if bool(item.get("melee_only", false)) and hero_range > 80.0:
		return false
	if bool(item.get("magic_only", false)) and not magic_hero:
		return false
	return true


func add(item_id: String, hero_range := 0.0, magic_hero := false) -> bool:
	if not can_add(item_id, hero_range, magic_hero):
		return false
	for index in range(MAX_SLOTS):
		if slots[index] == null:
			slots[index] = item_id
			_changed()
			return true
	return false


func remove(index: int) -> String:
	if index < 0 or index >= MAX_SLOTS or slots[index] == null:
		return ""
	var old := str(slots[index])
	slots[index] = null
	_changed()
	return old


func _changed() -> void:
	if hero != null and hero.world != null:
		hero._apply_hero_level(hero.world.data)


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
	var total := sum_stat("attack_speed") + aura_attack_speed + gale_as_bonus()
	return clampf(1.0 + total / 100.0, 0.2, 2.5)


func lifesteal() -> float:
	var total := sum_stat("lifesteal")
	if timer("blood_frenzy") > 0:
		total += 1.50
	return minf(1.75, total)


func crit() -> Array:
	var chance := 0.0
	var mult := 2.0
	for slot: Variant in slots:
		if slot == null:
			continue
		var stats: Dictionary = catalog.get(slot, {}).get("stats", {})
		if stats.has("crit_chance"):
			chance = maxf(chance, float(stats.crit_chance))
			mult = maxf(mult, float(stats.get("crit_mult", 2.25)))
	return [chance, mult]


func roll_crit(rng: RandomNumberGenerator) -> Array:
	var profile := crit()
	if float(profile[0]) <= 0.0:
		return [false, 1.0]
	if rng.randf() < float(profile[0]):
		return [true, float(profile[1])]
	return [false, 1.0]


func cleave() -> Array:
	for slot: Variant in slots:
		if slot == null:
			continue
		var passive: Dictionary = catalog.get(slot, {}).get("passive", {})
		if not passive.is_empty() and str(passive.get("name", "")) == "Cleave":
			return [float(passive.cleave_pct), float(passive.cleave_radius)]
	return []


func cooldown_reduction() -> float:
	return minf(0.5, sum_stat("cooldown_reduction"))


func spell_vamp() -> float:
	return sum_stat("spell_vamp")


func skill_amp() -> float:
	return minf(0.5, sum_stat("skill_amp"))


func evasion() -> float:
	if timer("ghost") > 0 and has("spectral_charm"):
		return 1.0
	return minf(0.5, sum_stat("evasion"))


func move_speed_pct() -> float:
	return minf(0.40, sum_stat("move_speed_pct"))


func heal_amp() -> float:
	return minf(0.5, sum_stat("heal_amp"))


func slow_resist() -> float:
	return minf(0.6, sum_stat("slow_resist"))


func range_bonus() -> float:
	var melee := false
	if hero != null:
		melee = hero.is_melee_hero
	else:
		melee = true
	if melee:
		return 0.0
	return sum_stat("range_bonus")


func has_true_strike() -> bool:
	return has("sundering_cudgel")


func reflect_pct() -> float:
	if timer("thorn") > 0 and has("razor_carapace"):
		return float(catalog.get("razor_carapace", {}).get("active", {}).get("reflect_pct", 0.0))
	return 0.0


func gale_as_bonus() -> float:
	if timer("gale") > 0 and has("gale_pike"):
		return float(catalog.get("gale_pike", {}).get("active", {}).get("as_bonus", 0.0))
	return 0.0


func consume_empower_strike() -> float:
	if has("runic_gavel") and timer("empower_charge") <= 0:
		var passive: Dictionary = catalog.get("runic_gavel", {}).get("passive", {})
		state["empower_charge"] = int(passive.get("charge_time", 0))
		return float(passive.get("damage", 0))
	return 0.0


func block_profile() -> Array:
	var melee := true
	if hero != null:
		melee = hero.attack_range <= 80.0
	var best: Array = []
	for slot: Variant in slots:
		if slot == null:
			continue
		var block: Dictionary = catalog.get(slot, {}).get("block", {})
		if block.is_empty():
			continue
		var amount := float(block.get("melee_block" if melee else "ranged_block", 0.0))
		var chance := float(block.get("chance", 0.0))
		if best.is_empty() or chance > float(best[0]) or amount > float(best[1]):
			best = [chance, amount]
	return best


func roll_block(rng: RandomNumberGenerator) -> float:
	var profile := block_profile()
	if profile.is_empty():
		return aura_guard_block
	if rng.randf() < float(profile[0]):
		return float(profile[1]) + aura_guard_block
	return aura_guard_block


func block_amount(_source: BattleUnit) -> float:
	var profile := block_profile()
	return (float(profile[1]) if not profile.is_empty() else 0.0) + aura_guard_block


func armor_shred() -> Array:
	for slot: Variant in slots:
		if slot == null:
			continue
		var passive: Dictionary = catalog.get(slot, {}).get("passive", {})
		if not passive.is_empty() and float(passive.get("armor_shred", 0.0)) != 0.0:
			return [float(passive.armor_shred), int(passive.get("duration", 300))]
	return []


func on_attack_chain() -> Dictionary:
	for slot: Variant in slots:
		if slot == null:
			continue
		var chain: Dictionary = catalog.get(slot, {}).get("on_attack", {})
		if chain.has_all(["chance", "targets", "radius", "damage"]):
			return chain
	return {}


func bash() -> Dictionary:
	if has("abyss_breaker"):
		return catalog.get("abyss_breaker", {}).get("bash", {})
	return {}


func is_veiled() -> bool:
	return timer("veil") > 0


func is_guarding() -> bool:
	return timer("guard") > 0


func rend_crit() -> Variant:
	if timer("rend") > 0 and has("sanguine_thorn"):
		return float(catalog.get("sanguine_thorn", {}).get("active", {}).get("crit_mult", 0.0))
	return null


func max_hp(base_hp: float) -> int:
	return int((base_hp + bonus_hp()) * (1.0 + hp_pct()))


func clear_on_death() -> bool:
	var dropped := false
	for index in range(MAX_SLOTS):
		if slots[index] == "holy_rapier":
			slots[index] = null
			dropped = true
	for key: String in TIMER_KEYS:
		state[key] = 0
	state["rend_target"] = null
	if has("runic_gavel"):
		state["empower_charge"] = int(
			catalog.get("runic_gavel", {}).get("passive", {}).get("charge_time", 0)
		)
	return dropped


func deliver_pending(hero_range: float, magic_hero: bool) -> Array[String]:
	var delivered: Array[String] = []
	while not pending.is_empty() and add(pending[0], hero_range, magic_hero):
		delivered.append(pending.pop_front())
	return delivered


func suggest_for(hero: BattleUnit) -> String:
	var role := str(hero.stats.get("role", "")).to_lower()
	var is_magic := hero.is_magic_hero()
	var magic := is_magic or "mage" in role or "trickster" in role
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
	elif magic:
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
		if can_add(item_id, hero.attack_range, is_magic):
			return item_id
	return ""


func has(item_id: String) -> bool:
	return item_id in slots
