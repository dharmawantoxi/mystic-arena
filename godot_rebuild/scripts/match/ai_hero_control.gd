extends RefCounted
## Port of AIPlayer._control_heroes / _assign_hero_lane (layer 6a): the AI keeps
## every living red hero busy each tick through the same auto-cast path the
## player uses, and only assigns a lane when the hero has neither an attack
## target nor a destination. Layer 8h mirrors Hero._try_auto_cast's nearest
## target handoff for boss heroes before this lane gate.
##
## Source constants: lane y values LANE_Y_TOP/MID/BOT = 150/380/610, the lane
## tie-break is the dict insertion order top -> mid -> bot, the fallback park x
## is 600 and the tower approach stops 60 px short.
##
## The world is duck-typed: `units` (heroes and minions, each carrying
## is_hero/team/alive/lane/position), `try_auto_cast(hero)` and
## `move_to(hero, point, auto)`. The source AI is always the red side
## (`self.team == "red"`), so RED_TEAM mirrors MinionBattle.RED. `towers` is
## the caller's `all_towers` list
## (living towers only, like the source): the rebuild's structure list also
## carries nexuses, which the source never walks here.
## `total_skills_cast` counts attempts that actually raised the hero's
## `active_skill_timer`, exactly like the source counter.

# Source AIPlayer.team is always "red"; MinionBattle.RED is 1.
const RED_TEAM := 1
const LANE_Y := [150.0, 380.0, 610.0]
const LANE_COUNT := 3
const PARK_X := 600.0
const TOWER_STANDOFF := 60.0
const StructureState = preload("res://scripts/combat/structure_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")

var total_skills_cast := 0


func control_heroes(world: Object, towers: Array) -> void:
	# Source: hero.skill_timer == 0 gates the auto-cast attempt; the lane is
	# only assigned when `not hero.target and not hero.destination`.
	for unit in world.units:
		if not unit.is_hero or unit.team != RED_TEAM or not unit.alive:
			continue
		var hero: Object = unit
		var boss_hero_target: Object = null
		if hero.skill_timer == 0:
			if hero is HeroState and hero.settings().is_boss_hero:
				boss_hero_target = _nearest_skill_enemy(world, hero, towers)
				if boss_hero_target != null:
					hero.target_id = boss_hero_target.id
					hero.target_struct = (
						boss_hero_target as StructureState
						if boss_hero_target is StructureState
						else null
					)
			var before: int = hero.active_skill_timer
			world.try_auto_cast(hero)
			if hero.active_skill_timer > before:
				total_skills_cast += 1
		if (
			hero.target_id < 0
			and hero.target_struct == null
			and not hero.has_destination
			and boss_hero_target == null
		):
			assign_hero_lane(world, hero, towers)


func _nearest_skill_enemy(world: Object, hero: Object, towers: Array) -> Object:
	# Source Hero._try_auto_cast builds enemies in this order, then uses a stable
	# distance sort: all units (the active boss last), towers, then both bases.
	var candidates: Array = []
	var units: Variant = world.get("units")
	if units is Array:
		candidates.append_array(units)
	var active_boss: Object = world.get("active_boss")
	if active_boss != null and active_boss.alive:
		candidates.append(active_boss)
	candidates.append_array(towers)
	var bases: Variant = world.get("nexuses")
	if bases is Array:
		candidates.append_array(bases)
	var best: Object = null
	var best_distance := INF
	for enemy in candidates:
		if enemy == null or not enemy.alive or enemy.team == hero.team:
			continue
		var distance: float = hero.position.distance_to(enemy.position)
		if distance <= hero.skill_range and distance < best_distance:
			best = enemy
			best_distance = distance
	return best


func lane_threats(world: Object, hero: Object) -> Array:
	# Source counts every living enemy MINION per lane; heroes never count.
	var threats := [0, 0, 0]
	for unit in world.units:
		if unit.is_hero or not unit.alive or unit.team == hero.team:
			continue
		var lane: int = unit.lane
		if lane >= 0 and lane < LANE_COUNT:
			threats[lane] += 1
	return threats


func busiest_lane(threats: Array) -> int:
	# Python max() over the top/mid/bot dict keeps the first maximum, so a tie
	# always resolves to the lowest lane index.
	var best := 0
	for lane in range(1, LANE_COUNT):
		if int(threats[lane]) > int(threats[best]):
			best = lane
	return best


func assign_hero_lane(world: Object, hero: Object, towers: Array) -> void:
	var threats: Array = lane_threats(world, hero)
	var lane: int = busiest_lane(threats)
	if int(threats[lane]) > 0:
		var target_y: float = float(LANE_Y[lane])
		if hero.team == RED_TEAM:
			var nearest: Object = _nearest_lane_unit(world, hero, lane)
			if nearest != null:
				world.move_to(hero, Vector2(nearest.position.x, target_y), true)
			else:
				world.move_to(hero, Vector2(PARK_X, target_y), true)
		return
	if hero.team != RED_TEAM:
		return
	# No minion threat: walk to the nearest living blue tower, stopping 60 px
	# short of it (a zero distance leaves the hero where it stands).
	var tower: Object = _nearest_enemy_structure(hero, towers)
	if tower == null:
		return
	var tower_pos: Vector2 = tower.position
	var away: Vector2 = hero.position - tower_pos
	var dist: float = away.length()
	if dist > 0.0:
		world.move_to(hero, tower_pos + away / dist * TOWER_STANDOFF, true)


func _nearest_lane_unit(world: Object, hero: Object, lane: int) -> Object:
	# Source sorts by distance and takes [0]; Python's sort is stable, so an
	# equidistant pair keeps the list order.
	var best: Object = null
	var best_dist := INF
	for unit in world.units:
		if unit.is_hero or not unit.alive or unit.team == hero.team:
			continue
		if int(unit.lane) != lane:
			continue
		var dist: float = hero.position.distance_to(unit.position)
		if dist < best_dist:
			best_dist = dist
			best = unit
	return best


func _nearest_enemy_structure(hero: Object, towers: Array) -> Object:
	var best: Object = null
	var best_dist := INF
	for structure in towers:
		if not structure.alive or structure.team == hero.team:
			continue
		var dist: float = hero.position.distance_to(structure.position)
		if dist < best_dist:
			best_dist = dist
			best = structure
	return best
