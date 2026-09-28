extends RefCounted
## Port of the module-level `hero_items.update_auras()` (layer 5d): the aura
## pass the source runs once per frame, after every hero/minion/boss update.
##
## Scope: the four per-hero aura fields are recomputed from scratch on every
## call (aura_armor, aura_as, aura_armor_reduction, aura_guard_block), Scarlet
## Bulwark's Bulwark Guard blocks allies inside its radius, Everfrost Guard /
## Solar Brand / Searbrand debuff every enemy unit (heroes, minions and the
## live boss), and Steel Aegis buffs nearby allies while shredding enemy armor.
##
## The source helper `_collect_all_units()` reaches into `__main__.game_instance`
## to append minions and the active boss; the rebuild keeps no global game
## singleton, so the caller passes the same unit list in `units` and this file
## stays pure. Debuff sends go through the ItemEffects bus, exactly like the
## 5c-2 auto-triggers, so the aura pass never mutates a foreign unit directly.

const HeroItems = preload("res://scripts/match/hero_items.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const ItemEffects = preload("res://scripts/match/item_effects.gd")
# Every debuff the source aura block sends is refreshed with this flat
# duration (hero_items.py: 30 frames), including the Solar Brand blind.
const AURA_DURATION := 30

var catalog: Dictionary


func _init(metadata: Dictionary = {}) -> void:
	# The source reads the module-level ITEM_CATALOG; one instance per match
	# caches the same JSON instead of re-parsing it on every tick.
	if metadata.is_empty():
		catalog = HeroItems.new().catalog
	else:
		catalog = metadata.duplicate(true)


func item(item_id: String) -> Dictionary:
	var items: Dictionary = catalog.get("items", {})
	return items.get(item_id, {})


func update_auras(heroes: Array[HeroState], units: Array[UnitState], effects: ItemEffects) -> void:
	# Reset every aura field first: the source wipes them each call so an aura
	# never lingers once the item, the radius or the owner is gone. Dead heroes
	# are reset too (they only skip the buff/debuff application below).
	for hero in heroes:
		var inv := hero.items
		if inv != null:
			inv.aura_armor = 0
			inv.aura_as = 0
			inv.aura_armor_reduction = 0
			inv.aura_guard_block = 0
	# SCARLET BULWARK: Bulwark Guard, computed BEFORE Steel Aegis because the
	# source keeps the two independent (guards do not need a Steel holder).
	var guards: Array[HeroState] = []
	for holder in _holders(heroes, "scarlet_bulwark"):
		if holder.items.guard_timer > 0:
			guards.append(holder)
	if not guards.is_empty():
		var act: Dictionary = item("scarlet_bulwark").get("active", {})
		var guard_radius := float(act.get("ally_radius", 0))
		var base_block := int(act.get("base_block", 0))
		var hp_block_pct := float(act.get("max_hp_block_pct", 0.0))
		for hero in heroes:
			if not hero.alive or hero.items == null:
				continue
			for src in guards:
				if src.team != hero.team:
					continue
				if src.position.distance_to(hero.position) <= guard_radius:
					# Strongest guard wins, computed from the SOURCE max HP.
					var block := base_block + int(float(src.max_hp) * hp_block_pct)
					if block > hero.items.aura_guard_block:
						hero.items.aura_guard_block = block
	# EVERFROST GUARD / SOLAR BRAND / SEARBRAND: auras that hit EVERY enemy
	# unit (minion, hero, boss), not just heroes, so they run over `units`.
	var frost := _holders(heroes, "everfrost_guard")
	var solar := _holders(heroes, "solar_brand")
	var sear := _holders(heroes, "searbrand")
	if not (frost.is_empty() and solar.is_empty() and sear.is_empty()):
		var frost_data: Dictionary = item("everfrost_guard").get("aura", {})
		var solar_data: Dictionary = item("solar_brand").get("aura", {})
		var sear_data: Dictionary = item("searbrand").get("aura", {})
		var frost_radius := float(frost_data.get("enemy_radius", 0))
		var frost_slow := float(frost_data.get("enemy_atk_slow", 0.0))
		var frost_heal := float(frost_data.get("enemy_anti_heal", 0.0))
		var solar_radius := float(solar_data.get("enemy_radius", 0))
		var solar_burn := float(solar_data.get("burn_dps", 0.0))
		var solar_blind := float(solar_data.get("blind", 0.0))
		var sear_radius := float(sear_data.get("enemy_radius", 0))
		var sear_heal := float(sear_data.get("enemy_anti_heal", 0.0))
		var sear_burn := float(sear_data.get("burn_dps", 0.0))
		for unit in units:
			if not unit.alive:
				continue
			# The first source in range wins for each aura (source `break`),
			# so a unit can only be hit once per holder list and tick.
			for src in frost:
				if unit.team == src.team:
					continue
				if src.position.distance_to(unit.position) <= frost_radius:
					effects.apply_debuff(unit.id, "atk_slow", frost_slow, AURA_DURATION)
					effects.apply_debuff(unit.id, "anti_heal", frost_heal, AURA_DURATION)
					break
			for src in solar:
				if unit.team == src.team:
					continue
				if src.position.distance_to(unit.position) <= solar_radius:
					effects.apply_debuff(unit.id, "burn", solar_burn, AURA_DURATION, src.team)
					effects.apply_miss_chance(unit.id, solar_blind, AURA_DURATION)
					break
			for src in sear:
				if unit.team == src.team:
					continue
				if src.position.distance_to(unit.position) <= sear_radius:
					effects.apply_debuff(unit.id, "anti_heal", sear_heal, AURA_DURATION)
					effects.apply_debuff(unit.id, "burn", sear_burn, AURA_DURATION, src.team)
					break
	# STEEL AEGIS: allies gain armor/attack speed per source (the holder never
	# buffs itself) and enemy heroes lose armor per source. Only heroes carry
	# an inventory, so minions are outside this block in both codebases.
	var sources := _holders(heroes, "steel_aegis")
	if sources.is_empty():
		return
	var data: Dictionary = item("steel_aegis").get("aura", {})
	var ally_radius := float(data.get("ally_radius", 0))
	var enemy_radius := float(data.get("enemy_radius", 0))
	var ally_armor := int(data.get("ally_armor", 0))
	var ally_as := int(data.get("ally_attack_speed", 0))
	var enemy_reduction := int(data.get("enemy_armor_reduction", 0))
	for hero in heroes:
		if not hero.alive or hero.items == null:
			continue
		for src in sources:
			if is_same(src, hero):
				continue
			var distance := src.position.distance_to(hero.position)
			if hero.team == src.team:
				if distance <= ally_radius:
					# Both values STACK per source, like the source loop.
					hero.items.aura_armor += ally_armor
					hero.items.aura_as += ally_as
			elif distance <= enemy_radius:
				hero.items.aura_armor_reduction += enemy_reduction


func _holders(heroes: Array[HeroState], item_id: String) -> Array[HeroState]:
	# Source: `[h for h in all_heroes if h.alive and h.items is not None and
	# h.items.has(item_id)]`.
	var holders: Array[HeroState] = []
	for hero in heroes:
		if hero.alive and hero.items != null and hero.items.has(item_id):
			holders.append(hero)
	return holders
