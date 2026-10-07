extends RefCounted
## AIPlayer pool/draft/reserve policy. Metadata is NOT a playable hero kit.
## Production reaches this through the recruitment adapter; the purchase callback
## atomically validates, spawns, debits and registers the real AI-owned hero.

const METADATA := "res://data/ai/recruitment.json"

var level_number := 1
var purchase_target := ""
var purchase_target_cost := 0
var source_levels: Dictionary = {}
var total_heroes_bought := 0
var rng := RandomNumberGenerator.new()
var uniform_picker: Callable
var weighted_picker: Callable
var _metadata: Dictionary


func _init(metadata: Dictionary = {}) -> void:
	if metadata.is_empty():
		_metadata = JSON.parse_string(FileAccess.get_file_as_string(METADATA))
	else:
		_metadata = metadata.duplicate(true)
	uniform_picker = _uniform_choice
	weighted_picker = _weighted_choice


func hero_pool() -> Array:
	var starters: Array = _metadata.starters
	var bosses: Array = []
	source_levels = {}
	# Source iterates level numbers, not catalog order or boss price.
	for previous in range(1, level_number):
		var config: Dictionary = _metadata.levels.get(str(previous), {})
		for hero_type in config.get("bosses", []):
			if _is_boss(hero_type) and hero_type not in starters and hero_type not in bosses:
				bosses.append(hero_type)
				source_levels[hero_type] = previous
	return bosses + starters


func choose_target(available: Array, owned_types: Array) -> String:
	var starters: Array = []
	var bosses: Array = []
	for hero_type in available:
		if _is_boss(hero_type):
			bosses.append(hero_type)
		else:
			starters.append(hero_type)
	var has_starter := false
	var has_boss := false
	for hero_type in owned_types:
		if _is_boss(hero_type):
			has_boss = true
		else:
			has_starter = true
	if not has_starter and not starters.is_empty():
		return uniform_picker.call(starters)
	if not bosses.is_empty():
		if not has_boss:
			var newest := 0
			for hero_type in bosses:
				newest = maxi(newest, int(source_levels.get(hero_type, 0)))
			var options: Array = []
			for hero_type in bosses:
				if int(source_levels.get(hero_type, 0)) == newest:
					options.append(hero_type)
			return uniform_picker.call(options)
		var weights: Array = []
		for hero_type in bosses:
			weights.append(maxi(1, int(source_levels.get(hero_type, 1))))
		return weighted_picker.call(bosses, weights)
	if not starters.is_empty():
		return uniform_picker.call(starters)
	return ""


func try_buy(owned_types: Array, gold: int, purchase: Callable) -> bool:
	# Do not filter out dead heroes. The 5-hero cap belongs to AIPlayer._ai_step,
	# not this method; owned_types must reflect the authoritative complete roster.
	var available: Array = []
	for hero_type in hero_pool():
		if hero_type not in owned_types:
			available.append(hero_type)
	if available.is_empty():
		_clear_target()
		return false
	if purchase_target not in available:
		purchase_target = choose_target(available, owned_types)
	if purchase_target.is_empty():
		purchase_target_cost = 0
		return false
	var stats: Dictionary = _metadata.catalog.get(purchase_target, {})
	if stats.is_empty():
		stats = _metadata.fallback.get(purchase_target, {})
	purchase_target_cost = int(stats.get("cost", 400))
	if gold < purchase_target_cost:
		return false
	var origin: Array = _metadata.spawn_origin
	# Source ties placement to AIPlayer.heroes; scene-only red heroes do not
	# consume an AI-owned position slot.
	var point := Vector2(origin[0], origin[1] + owned_types.size() * 40 - 40)
	# Native adapter failure (e.g. capacity) must not release the saved draft.
	if not purchase.call(purchase_target, purchase_target_cost, point):
		return false
	total_heroes_bought += 1
	_clear_target()
	return true


func reserve() -> int:
	return maxi(0, purchase_target_cost) if not purchase_target.is_empty() else 0


func can_spend_nonhero(gold: int, cost: int) -> bool:
	return gold >= cost + reserve()


func _clear_target() -> void:
	purchase_target = ""
	purchase_target_cost = 0


func _is_boss(hero_type: String) -> bool:
	return bool(_metadata.catalog.get(hero_type, {}).get("is_boss_hero", false))


func _uniform_choice(options: Array) -> String:
	return options[rng.randi_range(0, options.size() - 1)]


func _weighted_choice(options: Array, weights: Array) -> String:
	return weighted_at(options, weights, rng.randf())


static func weighted_at(options: Array, weights: Array, draw: float) -> String:
	# Python random.choices uses bisect_right over cumulative weights.
	# Godot randf can return 1; the final fallback still chooses the last entry.
	var total := 0.0
	for weight in weights:
		total += float(weight)
	var point := draw * total
	var cumulative := 0.0
	for index in range(options.size() - 1):
		cumulative += float(weights[index])
		if point < cumulative:
			return options[index]
	return options.back()
