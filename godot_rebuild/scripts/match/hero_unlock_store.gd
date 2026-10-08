extends RefCounted
## Stateless main-menu Hero Shop catalog and pure unlock transaction. Match
## summoning remains in PrototypeBattle and spends match gold; this authority
## spends only permanent Hero Gold and never writes a save by itself.

const HeroDefinition = preload("res://scripts/data/hero_definition.gd")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS
const BOSS_DATA := "res://data/bosses/boss_stats.json"
const STARTERS: Array[String] = ["thorne", "grimjaw", "vex", "sylara", "kaizen", "zephyr"]
const DEFAULT_HERO := "kaizen"
const STARTER_UNLOCK_COST := 0
const MINI_BOSS_UNLOCK_COST := 4500
const TRUE_BOSS_UNLOCK_COST := 4500

static var _catalog_loaded := false
static var _catalog_valid := false
static var _boss_classes: Dictionary = {}
static var _boss_order: Array[String] = []


static func is_catalog_valid() -> bool:
	_ensure_catalog()
	return _catalog_valid


static func bootstrap_state(state: Dictionary) -> Dictionary:
	# Source Game.reset grants Kaizen only when permanent ownership is empty.
	# Progress fields are supplied so the first free unlock can be saved through
	# the same strict LevelProgressStore as earned Hero Gold.
	var result := state.duplicate(true)
	if not result.has("meta_gold"):
		result["meta_gold"] = 0
	if not result.has("completed_levels"):
		result["completed_levels"] = []
	if not result.has("replay_reward_counts"):
		result["replay_reward_counts"] = {}
	if not result.has("purchased_heroes"):
		result["purchased_heroes"] = []
	var purchased: Variant = result.get("purchased_heroes")
	if purchased is Array and purchased.is_empty():
		purchased.append(DEFAULT_HERO)
		result["purchased_heroes"] = purchased
	if not result.has("unlocked_bosses"):
		result["unlocked_bosses"] = []
	return result


static func entry(hero_type: String) -> Dictionary:
	_ensure_catalog()
	var definition: HeroDefinition = HERO_ROSTER.get(hero_type) as HeroDefinition
	if definition == null:
		return {}
	var boss_class := String(_boss_classes.get(hero_type, ""))
	var is_boss := definition.is_boss_hero
	if is_boss and boss_class not in ["mini", "true"]:
		return {}
	return {
		"id": hero_type,
		"definition": definition,
		"is_boss_hero": is_boss,
		"boss_class": boss_class,
		"unlock_require_boss": hero_type if is_boss else "",
		"unlock_cost":
		(
			TRUE_BOSS_UNLOCK_COST
			if boss_class == "true"
			else MINI_BOSS_UNLOCK_COST if is_boss else STARTER_UNLOCK_COST
		),
	}


static func ids_for_tab(tab: String) -> Array[String]:
	_ensure_catalog()
	var result: Array[String] = []
	if tab == "starter":
		for hero_type in STARTERS:
			if HERO_ROSTER.has(hero_type):
				result.append(hero_type)
		return result
	if tab not in ["mini", "true"]:
		return result
	for hero_type in _boss_order:
		if _boss_classes.get(hero_type) == tab and HERO_ROSTER.has(hero_type):
			result.append(hero_type)
	return result


static func try_unlock(state: Dictionary, hero_type: String) -> Dictionary:
	var current := bootstrap_state(state)
	if not _valid_profile(current):
		return {"state": state.duplicate(true), "error": "profile", "cost": 0}
	var item := entry(hero_type)
	if item.is_empty():
		return {"state": current, "error": "hero", "cost": 0}
	var purchased: Array = current["purchased_heroes"]
	var defeated: Array = current["unlocked_bosses"]
	var cost := int(item.unlock_cost)
	if hero_type in purchased:
		return {"state": current, "error": "owned", "cost": cost}
	if item.is_boss_hero and hero_type not in defeated:
		return {"state": current, "error": "locked", "cost": cost}
	if int(current.meta_gold) < cost:
		return {"state": current, "error": "gold", "cost": cost}
	current["meta_gold"] = int(current.meta_gold) - cost
	purchased.append(hero_type)
	current["purchased_heroes"] = purchased
	return {"state": current, "error": "", "cost": cost}


static func _valid_profile(state: Dictionary) -> bool:
	var gold: Variant = state.get("meta_gold")
	var purchased: Variant = state.get("purchased_heroes")
	var defeated: Variant = state.get("unlocked_bosses")
	if not (gold is int) or gold < 0 or not (purchased is Array) or not (defeated is Array):
		return false
	var seen := {}
	for hero_type in purchased:
		if not (hero_type is String) or not HERO_ROSTER.has(hero_type) or seen.has(hero_type):
			return false
		seen[hero_type] = true
	seen.clear()
	for hero_type in defeated:
		if (
			not (hero_type is String)
			or not HERO_ROSTER.has(hero_type)
			or not HERO_ROSTER[hero_type].is_boss_hero
			or seen.has(hero_type)
		):
			return false
		seen[hero_type] = true
	return true


static func _ensure_catalog() -> void:
	if _catalog_loaded:
		return
	_catalog_loaded = true
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(BOSS_DATA))
	if not (parsed is Dictionary):
		return
	var bosses: Variant = parsed.get("bosses")
	if not (bosses is Dictionary):
		return
	for value in bosses:
		var hero_type := String(value)
		var row: Variant = bosses[value]
		if not (row is Dictionary):
			return
		var boss_class := String(row.get("boss_class", ""))
		if boss_class not in ["mini", "true"] or _boss_classes.has(hero_type):
			return
		_boss_classes[hero_type] = boss_class
		_boss_order.append(hero_type)
	_catalog_valid = not _boss_order.is_empty()
