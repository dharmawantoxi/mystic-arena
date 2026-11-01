class_name EntityAI
extends RefCounted

## Native port of _entity.AIPlayer: draft, reserves, build/upgrade, items, lanes.
var model: RefCounted
var level_number := 1
var think_timer := 90
var purchase_target := ""
var purchase_cost := 0
var source_levels: Dictionary = {}
var total_built := 0
var total_upgraded := 0
var total_heroes_bought := 0
var total_hero_upgrades := 0
var total_nexus_upgrades := 0


func _init(match_model: RefCounted, level: int) -> void:
	model = match_model
	level_number = level
	think_timer = int(model.data.rule("AI_THINK_INTERVAL", 90))


func brain() -> float:
	return minf(1.0, float(maxi(1, level_number) - 1) / 19.0)


func elite() -> float:
	if level_number <= 20:
		return 0.0
	return minf(
		1.0,
		float(level_number - 20) / maxf(1.0, float(model.data.data.get("levels", []).size() - 20))
	)


func reserve() -> int:
	return purchase_cost if not purchase_target.is_empty() else 0


func update() -> void:
	_control_heroes()
	think_timer -= 1
	if think_timer > 0:
		return
	var b := brain()
	var e := elite()
	think_timer = maxi(
		8, int(float(model.data.rule("AI_THINK_INTERVAL", 90)) * (1.0 - 0.65 * b) - 22.0 * e)
	)
	for _action in range(1 + int(round(2.0 * e))):
		if not _step(b, e):
			break


func _roll(base: float, e: float) -> bool:
	return model.rng.randf() < minf(0.98, base + 0.45 * e)


func _step(b: float, e: float) -> bool:
	var empty: Array[Dictionary] = []
	for slot: Dictionary in model.build_slots_red:
		if not bool(slot.taken):
			empty.append(slot)
	if not empty.is_empty() and model.ai_gold >= 150 and _roll(0.4 + 0.45 * b, e):
		if _build(empty):
			return true
	if model.enemy_heroes.size() < int(model.data.rule("AI_MAX_HEROES", 5)):
		if _roll(float(model.data.rule("AI_HERO_BUY_PRIORITY", 0.45)) * (0.55 + 0.9 * b), e):
			if _buy_hero():
				return true
	if (
		not model.enemy_heroes.is_empty()
		and _roll(float(model.data.rule("AI_HERO_UPGRADE_PRIORITY", 0.4)) * (0.7 + 0.6 * b), e)
	):
		if _upgrade_hero():
			return true
	if not model.enemy_heroes.is_empty() and _roll(0.35 + 0.4 * b + 0.2 * e, e):
		if _buy_item():
			return true
	var towers: Array[BattleUnit] = []
	for tower: BattleUnit in model.towers:
		if tower.team == "red" and tower.alive:
			towers.append(tower)
	if (
		not towers.is_empty()
		and _roll(float(model.data.rule("AI_UPGRADE_TOWER_CHANCE", 0.3)) + 0.5 * b, e)
	):
		if _upgrade_tower(towers):
			return true
	if _regen_shield(towers):
		return true
	if _castle_shield():
		return true
	if _roll(float(model.data.rule("AI_NEXUS_UPGRADE_PRIORITY", 0.35)) * (0.7 + 0.6 * b), e):
		return _upgrade_nexus()
	return false


func _build(empty: Array[Dictionary]) -> bool:
	if model.ai_gold < 100 + reserve():
		return false
	var slot: Dictionary = empty[model.rng.randi_range(0, empty.size() - 1)]
	var types := ["archer", "cannon", "ice", "mage"]
	var weights := [0.35, 0.25, 0.20, 0.20]
	var roll: float = model.rng.randf()
	var acc := 0.0
	var chosen := "archer"
	for index in range(types.size()):
		acc += float(weights[index])
		if roll <= acc:
			chosen = str(types[index])
			break
	var tower := BattleUnit.new()
	tower.id = model._id()
	tower.world = model
	tower.setup_tower(model.data, slot.pos, "red", str(slot.lane))
	if chosen != "archer":
		tower.tower_type = chosen
		tower._apply_tower_stats(model.data)
	model.towers.append(tower)
	slot["taken"] = true
	model.ai_gold -= 100
	total_built += 1
	return true


func hero_pool() -> Array[String]:
	var result: Array[String] = []
	var starters: Array = model.data.rule("AI_HERO_PREFERENCES", [])
	source_levels.clear()
	if level_number >= 2:
		for level in range(1, level_number):
			var config: Dictionary = model.data.level(level)
			var bosses: Array = config.get("mini_bosses", {}).values()
			if not str(config.get("true_boss", "")).is_empty():
				bosses.append(config.true_boss)
			for boss_type: Variant in bosses:
				var key := str(boss_type)
				var stats: Dictionary = model.data.hero(key)
				if (
					bool(stats.get("is_boss_hero", false))
					and key not in result
					and key not in starters
				):
					result.append(key)
					source_levels[key] = level
	for hero_type: Variant in starters:
		result.append(str(hero_type))
	return result


func _buy_hero() -> bool:
	var owned: Array[String] = []
	for hero: BattleUnit in model.enemy_heroes:
		owned.append(hero.unit_type)
	var available: Array[String] = []
	for hero_type: String in hero_pool():
		if hero_type not in owned:
			available.append(hero_type)
	if available.is_empty():
		purchase_target = ""
		purchase_cost = 0
		return false
	if purchase_target.is_empty() or purchase_target not in available:
		purchase_target = _choose(available)
	purchase_cost = int(model.data.hero(purchase_target).get("cost", 400))
	if model.ai_gold < purchase_cost:
		return false
	var hero := BattleUnit.new()
	hero.id = model._id()
	hero.world = model
	var offset: float = model.enemy_heroes.size() * 40 - 40
	hero.setup_hero(
		model.data,
		purchase_target,
		"red",
		model.red_base.pos + Vector2(-60, 30 + offset),
		model.data.balance.boss_unlocks_for_purchases(model.purchased_heroes)
	)
	model.enemy_heroes.append(hero)
	model.ai_gold -= purchase_cost
	total_heroes_bought += 1
	purchase_target = ""
	purchase_cost = 0
	return true


func _choose(available: Array[String]) -> String:
	var starters: Array[String] = []
	var bosses: Array[String] = []
	for hero_type: String in available:
		if bool(model.data.hero(hero_type).get("is_boss_hero", false)):
			bosses.append(hero_type)
		else:
			starters.append(hero_type)
	var has_starter := false
	var has_boss := false
	for hero: BattleUnit in model.enemy_heroes:
		if bool(model.data.hero(hero.unit_type).get("is_boss_hero", false)):
			has_boss = true
		else:
			has_starter = true
	if not has_starter and not starters.is_empty():
		return starters[model.rng.randi_range(0, starters.size() - 1)]
	if not bosses.is_empty():
		if not has_boss:
			var newest := 0
			for hero_type: String in bosses:
				newest = maxi(newest, int(source_levels.get(hero_type, 0)))
			var options: Array[String] = []
			for hero_type: String in bosses:
				if int(source_levels.get(hero_type, 0)) == newest:
					options.append(hero_type)
			return options[model.rng.randi_range(0, options.size() - 1)]
		var total := 0
		for hero_type: String in bosses:
			total += maxi(1, int(source_levels.get(hero_type, 1)))
		var roll: int = model.rng.randi_range(1, total)
		for hero_type: String in bosses:
			roll -= maxi(1, int(source_levels.get(hero_type, 1)))
			if roll <= 0:
				return hero_type
	if not starters.is_empty():
		return starters[model.rng.randi_range(0, starters.size() - 1)]
	return available[0]


func _upgrade_hero() -> bool:
	var candidates: Array[BattleUnit] = []
	for hero: BattleUnit in model.enemy_heroes:
		if hero.level < int(model.data.rule("MAX_HERO_LEVEL", 15)):
			candidates.append(hero)
	candidates.sort_custom(func(a: BattleUnit, b: BattleUnit) -> bool: return a.kills > b.kills)
	for hero: BattleUnit in candidates:
		var cost := hero.hero_upgrade_cost(model.data)
		if model.ai_gold >= cost + reserve() and hero.upgrade_hero(model.data):
			model.ai_gold -= cost
			total_hero_upgrades += 1
			return true
	return false


func _buy_item() -> bool:
	var candidates: Array[BattleUnit] = []
	for hero: BattleUnit in model.enemy_heroes:
		if hero.alive and hero.items.used() < UnitInventory.MAX_SLOTS:
			candidates.append(hero)
	candidates.sort_custom(
		func(a: BattleUnit, b: BattleUnit) -> bool:
			return Vector2(a.kills, a.level) > Vector2(b.kills, b.level)
	)
	for hero: BattleUnit in candidates:
		var item_id := hero.items.suggest_for(hero)
		if item_id.is_empty():
			continue
		var cost: int = int(model.data.item(item_id).get("cost", 0))
		if (
			model.ai_gold >= cost + reserve()
			and hero.items.add(item_id, hero.attack_range, hero.is_magic_hero())
		):
			model.ai_gold -= cost
			hero._apply_hero_level(model.data)
			return true
	return false


func _upgrade_tower(towers: Array[BattleUnit]) -> bool:
	towers.sort_custom(func(a: BattleUnit, b: BattleUnit) -> bool: return a.kills > b.kills)
	for tower: BattleUnit in towers:
		if tower.level >= int(model.data.rule("TOWER_MAX_LEVEL", 6)):
			continue
		var path := ""
		if tower.level == 1:
			for candidate: String in ["cannon", "ice", "archer", "mage"]:
				var cost := tower.tower_upgrade_cost(model.data, candidate)
				if model.ai_gold >= cost + reserve():
					path = candidate
					break
			if path.is_empty():
				continue
		var cost := tower.tower_upgrade_cost(model.data, path)
		if cost > 0 and model.ai_gold >= cost + reserve() and tower.upgrade_tower(model.data, path):
			model.ai_gold -= cost
			total_upgraded += 1
			return true
	return false


func _regen_shield(towers: Array[BattleUnit]) -> bool:
	for tower: BattleUnit in towers:
		var cost := int(model.data.rule("TOWER_REGEN_SHIELD_COST", 850))
		if tower.can_activate_regen_shield(model.data) and model.ai_gold >= cost + reserve():
			if tower.activate_regen_shield(model.data):
				model.ai_gold -= cost
				return true
	return false


func _castle_shield() -> bool:
	var cost := int(model.data.rule("CASTLE_SHIELD_COST", 850))
	if model.red_base.can_activate_castle_shield(model.data) and model.ai_gold >= cost + reserve():
		if model.red_base.activate_castle_shield(model.data):
			model.ai_gold -= cost
			return true
	return false


func _upgrade_nexus() -> bool:
	var cost: int = model.red_base.castle_upgrade_cost(model.data)
	if cost > 0 and model.ai_gold >= cost + reserve() and model.red_base.upgrade_castle(model.data):
		model.ai_gold -= cost
		total_nexus_upgrades += 1
		return true
	return false


func _control_heroes() -> void:
	for hero: BattleUnit in model.enemy_heroes:
		if not hero.alive:
			continue
		if not hero.has_destination and hero.follow_target == null and hero.tactical_target == null:
			_assign_lane(hero)


func _assign_lane(hero: BattleUnit) -> void:
	var threats := {"top": 0, "mid": 0, "bot": 0}
	for minion: BattleUnit in model.minions:
		if minion.team == "blue" and minion.alive and threats.has(minion.lane):
			threats[minion.lane] = int(threats[minion.lane]) + 1
	var best_lane := "mid"
	var best_count := 0
	for lane: String in threats:
		if int(threats[lane]) > best_count:
			best_count = int(threats[lane])
			best_lane = lane
	if best_count > 0:
		var nearest: BattleUnit = null
		var best := INF
		for minion: BattleUnit in model.minions:
			if minion.team == "blue" and minion.alive and minion.lane == best_lane:
				var dist := hero.pos.distance_to(minion.pos)
				if dist < best:
					best = dist
					nearest = minion
		if nearest != null:
			hero.move_to_point(nearest.pos)
			hero.destination_auto = true
	else:
		var target: BattleUnit = model._nearest(hero.pos, model.enemies_of("red"), 2000.0)
		if target != null:
			var offset: Vector2 = (hero.pos - target.pos).normalized() * 60.0
			hero.move_to_point(target.pos + offset)
			hero.destination_auto = true
