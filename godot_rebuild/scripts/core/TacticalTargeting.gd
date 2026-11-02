class_name TacticalTargeting
extends RefCounted

## Target selection helpers from tactical_commands.py. Stable ordering matters:
## Python max/sort keep the first candidate on ties, so ties are index-broken.


static func mget(model: RefCounted, key: String, default: Variant = null) -> Variant:
	if model == null:
		return default
	var value: Variant = model.get(key)
	return default if value == null else value


static func alive_blue_heroes(model: RefCounted) -> Array[BattleUnit]:
	var out: Array[BattleUnit] = []
	for unit: Variant in mget(model, "heroes", []):
		if unit is BattleUnit and unit.alive:
			out.append(unit)
	return out


static func clear_retreat(heroes: Array) -> void:
	for hero: BattleUnit in heroes:
		hero.is_retreating = false
		hero.destination_auto = false


static func move_to(hero: BattleUnit, point: Vector2, auto := false) -> void:
	hero.destination = point
	hero.has_destination = true
	hero.destination_auto = auto
	hero.follow_target = null
	hero.is_retreating = false


static func clear_destination(hero: BattleUnit) -> void:
	hero.destination = Vector2.ZERO
	hero.has_destination = false
	hero.destination_auto = false


static func count_enemies_near(model: RefCounted, x: float, y: float, radius: float) -> int:
	var origin := Vector2(x, y)
	var count := 0
	for unit: Variant in mget(model, "minions", []):
		if unit is BattleUnit and unit.team == "red" and unit.alive:
			if unit.pos.distance_to(origin) <= radius:
				count += 1
	for unit: Variant in mget(model, "enemy_heroes", []):
		if unit is BattleUnit and unit.alive and unit.pos.distance_to(origin) <= radius:
			count += 1
	var boss: BattleUnit = mget(model, "active_boss")
	if (
		boss != null
		and boss.alive
		and boss.team == "red"
		and boss.pos.distance_to(origin) <= radius
	):
		count += 2
	return count


static func most_threatened_tower(model: RefCounted, cfg: Dictionary) -> BattleUnit:
	var blue_towers: Array[BattleUnit] = []
	for unit: Variant in mget(model, "towers", []):
		if unit is BattleUnit and unit.team == "blue" and unit.alive:
			blue_towers.append(unit)
	if blue_towers.is_empty():
		return null
	var scored: Array[Dictionary] = []
	for index in range(blue_towers.size()):
		var tower := blue_towers[index]
		var enemies := count_enemies_near(model, tower.pos.x, tower.pos.y, float(cfg.threat_radius))
		var hp_ratio := tower.hp / maxf(1.0, tower.max_hp)
		var score := (
			enemies * int(cfg.threat_enemy_weight) + (1.0 - hp_ratio) * float(cfg.threat_hp_weight)
		)
		if tower.pos.x < float(cfg.threat_outer_x):
			score += int(cfg.threat_outer_bonus)
		scored.append({"score": score, "tower": tower, "index": index})
	_insertion_sort(
		scored,
		func(a: Dictionary, b: Dictionary) -> bool:
			if a.score != b.score:
				return a.score > b.score
			return a.index < b.index
	)
	if float(scored[0].score) == 0.0:
		var by_hp := blue_towers.duplicate()
		_insertion_sort(
			by_hp,
			func(a: BattleUnit, b: BattleUnit) -> bool:
				return a.hp / maxf(1.0, a.max_hp) < b.hp / maxf(1.0, b.max_hp)
		)
		return by_hp[0]
	return scored[0].tower


static func nearest_enemy_target(
	model: RefCounted, cfg: Dictionary, x: float, y: float
) -> BattleUnit:
	var origin := Vector2(x, y)
	var best: BattleUnit = null
	var best_dist := float(cfg.nearest_init)
	var boss: BattleUnit = mget(model, "active_boss")
	if boss != null and boss.alive:
		var dist: float = boss.pos.distance_to(origin)
		if dist < best_dist:
			best_dist = dist
			best = boss
	for unit: Variant in mget(model, "towers", []):
		if unit is BattleUnit and unit.team == "red" and unit.alive:
			var dist: float = unit.pos.distance_to(origin)
			if dist < best_dist:
				best_dist = dist
				best = unit
	for unit: Variant in mget(model, "enemy_heroes", []):
		if unit is BattleUnit and unit.alive:
			var dist: float = unit.pos.distance_to(origin)
			if dist < best_dist:
				best_dist = dist
				best = unit
	if best == null:
		for unit: Variant in mget(model, "minions", []):
			if unit is BattleUnit and unit.team == "red" and unit.alive:
				var dist: float = unit.pos.distance_to(origin)
				if dist < best_dist:
					best_dist = dist
					best = unit
	if best == null:
		var red_base: BattleUnit = mget(model, "red_base")
		if red_base != null and red_base.alive:
			best = red_base
	return best


static func enemy_damage_dealer(model: RefCounted) -> BattleUnit:
	var best: BattleUnit = null
	for unit: Variant in mget(model, "enemy_heroes", []):
		if unit is BattleUnit and unit.alive:
			if best == null or unit.damage_dealt > best.damage_dealt:
				best = unit
	return best


static func sorted_heroes_by_distance(heroes: Array, point: Vector2) -> Array[BattleUnit]:
	var rows: Array[Dictionary] = []
	for index in range(heroes.size()):
		var hero: BattleUnit = heroes[index]
		rows.append({"hero": hero, "dist": hero.pos.distance_to(point), "index": index})
	_insertion_sort(
		rows,
		func(a: Dictionary, b: Dictionary) -> bool:
			if a.dist != b.dist:
				return a.dist < b.dist
			return a.index < b.index
	)
	var out: Array[BattleUnit] = []
	for row: Dictionary in rows:
		out.append(row.hero)
	return out


static func _insertion_sort(items: Array, less: Callable) -> void:
	for index in range(1, items.size()):
		var value: Variant = items[index]
		var position := index
		while position > 0 and less.call(value, items[position - 1]):
			items[position] = items[position - 1]
			position -= 1
		items[position] = value
