extends RefCounted
## Fixed-tick port of tactical_commands.TacticalCommandManager. This state
## object never owns the battle; every mutation receives the live world so the
## PrototypeBattle -> TacticalCommands reference cannot form a cycle.

const HeroState = preload("res://scripts/combat/hero_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")

const GATHER := "gather"
const PROTECT_TOWER := "protect_tower"
const PROTECT_CASTLE := "protect_castle"
const ATTACK_BOSS := "attack_boss"
const ATTACK_DAMAGE_DEALER := "attack_damage_dealer"
const COMMANDS: Array[String] = [
	GATHER, PROTECT_TOWER, PROTECT_CASTLE, ATTACK_BOSS, ATTACK_DAMAGE_DEALER
]
const COMMAND_TICKS := 600
const COOLDOWN_TICKS := 30
const HOLD_TAP_MAX_TICKS := 20
const HOLD_RELEASE_TAIL := 30
const GATHER_PUSH_DELAY_TICKS := 240
const POINT_TICKS := 150
const FEEDBACK_TICKS := 180
const BLUE := 0
const RED := 1
const RED_BASE := Vector2(1180, 100)

var active_command := ""
var command_timer := 0
var command_target_id := -1
var gather_point := Vector2.ZERO
var gather_point_active := false
var gather_point_timer := 0
var feedback_timer := 0
var feedback_text := ""
var feedback_color := Color.WHITE
var cooldown := 0

var held_command := ""
var hold_point := Vector2.ZERO
var hold_has_point := false
var hold_target_id := -1
var hold_selected_hero_id := -1
var hold_follow_cursor := false
var hold_elapsed := 0
var hold_has_fired := false
var gather_push_fired := false

var cursor_point := Vector2.ZERO
var cursor_valid := false
var auto_check_timer := 0
var boss_auto_roll_override: Callable
var rng := RandomNumberGenerator.new()


func _init() -> void:
	rng.seed = 20261008


func set_cursor(point: Vector2, valid: bool) -> void:
	cursor_point = point
	cursor_valid = valid and point.is_finite()


func can_issue(world: Object) -> bool:
	return cooldown <= 0 and world != null and world.is_running()


func hold_start(
	world: Object,
	name: String,
	point: Vector2 = Vector2.ZERO,
	has_point: bool = false,
	target_id: int = -1,
	selected_hero_id: int = -1,
	follow_cursor: bool = false
) -> bool:
	if name not in COMMANDS:
		return false
	if name == held_command and hold_elapsed > 0:
		return true
	held_command = name
	hold_point = point
	hold_has_point = has_point
	hold_target_id = target_id
	hold_selected_hero_id = selected_hero_id
	hold_follow_cursor = follow_cursor
	hold_elapsed = 0
	hold_has_fired = false
	gather_push_fired = false
	var accepted := _issue_held(world, true)
	if accepted:
		hold_has_fired = true
	return accepted


func hold_end(name: String = "") -> void:
	if held_command.is_empty() or (not name.is_empty() and name != held_command):
		return
	var elapsed := hold_elapsed
	held_command = ""
	hold_point = Vector2.ZERO
	hold_has_point = false
	hold_target_id = -1
	hold_selected_hero_id = -1
	hold_follow_cursor = false
	hold_elapsed = 0
	hold_has_fired = false
	if elapsed >= HOLD_TAP_MAX_TICKS and command_timer > 0:
		command_timer = mini(command_timer, HOLD_RELEASE_TAIL)


func hold_active() -> bool:
	return not held_command.is_empty()


func issue(
	world: Object,
	name: String,
	point: Vector2 = Vector2.ZERO,
	has_point: bool = false,
	target_id: int = -1,
	selected_hero_id: int = -1,
	silent: bool = false
) -> bool:
	match name:
		GATHER:
			return _command_gather(world, point, has_point, selected_hero_id, silent)
		PROTECT_TOWER:
			return _command_protect_tower(world, target_id, silent)
		PROTECT_CASTLE:
			return _command_protect_castle(world, silent)
		ATTACK_BOSS:
			return _command_attack_boss(world, silent)
		ATTACK_DAMAGE_DEALER:
			return _command_attack_damage_dealer(world, silent)
	return false


func step_tick(world: Object) -> void:
	if cooldown > 0:
		cooldown -= 1
	if command_timer > 0:
		command_timer -= 1
		if command_timer <= 0:
			active_command = ""
			command_target_id = -1
	if gather_point_timer > 0:
		gather_point_timer -= 1
		if gather_point_timer <= 0:
			gather_point_active = false
	if feedback_timer > 0:
		feedback_timer -= 1

	if not held_command.is_empty() and world.is_running():
		hold_elapsed += 1
		if cooldown <= 0:
			var accepted := _issue_held(world, false)
			if accepted and not hold_has_fired:
				cooldown = 0
				_issue_held(world, true)
			if accepted:
				hold_has_fired = true

	if active_command == GATHER and gather_point_active:
		if held_command == GATHER:
			if not gather_push_fired and hold_elapsed >= GATHER_PUSH_DELAY_TICKS:
				_try_gather_push(world)
		elif command_timer == 300:
			_try_gather_push(world)

	if active_command.is_empty() and cooldown <= 0:
		auto_check_timer += 1
		if auto_check_timer >= 90:
			auto_check_timer = 0
			_auto_evaluate_protect(world)


func status_text(world: Object) -> String:
	var hold_tag := " [HOLD]" if hold_active() else ""
	if not active_command.is_empty():
		var target_name := ""
		var target: Object = world.get_unit(command_target_id)
		if target != null:
			target_name = _display_name(target).left(15)
		return (
			"%s %s (%ds)%s"
			% [active_command.to_upper(), target_name, floori(command_timer / 60.0), hold_tag]
		)
	if hold_active():
		return "%s [HOLD] (menunggu syarat)" % held_command.to_upper()
	return "No tactical command"


func command_color() -> Color:
	return (
		{
			GATHER: Color("64dcff"),
			PROTECT_TOWER: Color("64ff64"),
			PROTECT_CASTLE: Color("ffdc32"),
			ATTACK_BOSS: Color("ff6464"),
			ATTACK_DAMAGE_DEALER: Color("ff82ff"),
		}
		. get(active_command, Color("ffdc64"))
	)


func _issue_held(world: Object, loud: bool) -> bool:
	if held_command.is_empty():
		return false
	if held_command == GATHER and not loud and gather_push_fired:
		var pushed := _gather_hold_push(world)
		cooldown = COOLDOWN_TICKS
		return pushed
	var point := hold_point
	var has_point := hold_has_point
	if held_command == GATHER and hold_follow_cursor and cursor_valid:
		point = cursor_point
		has_point = true
	var accepted := issue(
		world, held_command, point, has_point, hold_target_id, hold_selected_hero_id, not loud
	)
	if not accepted:
		cooldown = maxi(cooldown, int(COOLDOWN_TICKS / 2.0))
	return accepted


func _command_gather(
	world: Object, point: Vector2, has_point: bool, selected_hero_id: int, silent: bool
) -> bool:
	if not can_issue(world):
		return false
	var heroes := _alive_blue_heroes(world)
	if heroes.is_empty():
		_refuse("No heroes alive!", silent)
		return false
	if not has_point:
		var selected := world.get_unit(selected_hero_id) as HeroState
		if selected != null and selected.alive and selected.team == BLUE:
			point = selected.position
		elif heroes.size() >= 2:
			point = Vector2.ZERO
			for hero in heroes:
				point += hero.position
			point /= heroes.size()
			point = point.lerp(RED_BASE, 0.35)
			point.x = clampf(point.x, 200.0, 1080.0)
			point.y = clampf(point.y, 100.0, 620.0)
		else:
			point = Vector2(640, 360)
	active_command = GATHER
	command_timer = COMMAND_TICKS
	gather_point = point
	gather_point_active = true
	gather_point_timer = POINT_TICKS
	cooldown = COOLDOWN_TICKS
	if not silent:
		gather_push_fired = false
	_clear_retreat(heroes)
	for index in range(heroes.size()):
		var hero: HeroState = heroes[index]
		var angle := float(index) / maxi(1, heroes.size()) * TAU
		var spread := 35.0 + float(index % 3) * 15.0
		world.move_to(hero, point + Vector2.from_angle(angle) * spread, false)
		hero.follow_id = -1
		hero.target_id = -1
	if not silent:
		AudioRuntime.play("ui_click")
		_feedback("GATHER! %d heroes regrouping!" % heroes.size(), Color("64dcff"))
	return true


func _command_protect_tower(world: Object, target_id: int, silent: bool) -> bool:
	if not can_issue(world):
		return false
	var heroes := _alive_blue_heroes(world)
	if heroes.is_empty():
		_refuse("No heroes alive!", silent)
		return false
	var target := world.get_unit(target_id) as StructureState
	if not _is_blue_tower(target):
		target = _find_most_threatened_tower(world)
	if target == null:
		_refuse("No tower to protect!", silent)
		return false
	active_command = PROTECT_TOWER
	command_timer = COMMAND_TICKS
	command_target_id = target.id
	gather_point = target.position
	gather_point_active = true
	gather_point_timer = POINT_TICKS
	cooldown = COOLDOWN_TICKS
	var protectors: Array = heroes
	if heroes.size() > 3:
		protectors = _stable_distance_sort(heroes, target.position)
		var count := 3 if _count_enemies_near(world, target.position, 250.0) >= 3 else 2
		protectors = protectors.slice(0, count)
	_clear_retreat(protectors)
	for index in range(protectors.size()):
		var hero: HeroState = protectors[index]
		var angle := float(index) / protectors.size() * TAU if protectors.size() > 1 else 0.0
		var spread := 30.0 + float(index) * 10.0
		world.move_to(hero, target.position + Vector2.from_angle(angle) * spread, false)
		hero.follow_id = -1
		hero.target_id = -1
	if not silent:
		AudioRuntime.play("ui_click")
		_feedback(
			"PROTECT TOWER! %d heroes defending %s!" % [protectors.size(), _display_name(target)],
			Color("64ff64")
		)
	return true


func _command_protect_castle(world: Object, silent: bool) -> bool:
	if not can_issue(world):
		return false
	var heroes := _alive_blue_heroes(world)
	if heroes.is_empty():
		_refuse("No heroes alive!", silent)
		return false
	var castle := world.nexuses[BLUE] as StructureState
	if castle == null or not castle.alive:
		_refuse("Castle destroyed!", silent)
		return false
	active_command = PROTECT_CASTLE
	command_timer = COMMAND_TICKS
	command_target_id = castle.id
	gather_point = castle.position
	gather_point_active = true
	gather_point_timer = POINT_TICKS
	cooldown = COOLDOWN_TICKS
	_clear_retreat(heroes)
	for index in range(heroes.size()):
		var hero: HeroState = heroes[index]
		var angle := float(index) / heroes.size() * TAU
		var radius := 80.0 + float(index % 2) * 30.0
		var destination := castle.position + Vector2.from_angle(angle) * radius
		destination.x = clampf(destination.x, 50.0, 1230.0)
		destination.y = clampf(destination.y, 50.0, 670.0)
		world.move_to(hero, destination, false)
		hero.follow_id = -1
		hero.target_id = -1
	if not silent:
		AudioRuntime.play("ui_click")
		_feedback("PROTECT CASTLE! %d heroes defending base!" % heroes.size(), Color("ffdc32"))
	return true


func _command_attack_boss(world: Object, silent: bool) -> bool:
	if not can_issue(world):
		return false
	var heroes := _alive_blue_heroes(world)
	if heroes.is_empty():
		_refuse("No heroes alive!", silent)
		return false
	var boss: Object = world.active_boss
	if boss == null or not boss.alive:
		_refuse("No boss active!", silent)
		return false
	_attack_target(world, heroes, boss, ATTACK_BOSS)
	if not silent:
		AudioRuntime.play("hero_skill")
		_feedback("ATTACK BOSS! All heroes attack %s!" % _display_name(boss), Color("ff6464"))
	return true


func _command_attack_damage_dealer(world: Object, silent: bool) -> bool:
	if not can_issue(world):
		return false
	var heroes := _alive_blue_heroes(world)
	if heroes.is_empty():
		_refuse("No heroes alive!", silent)
		return false
	var dealer := _find_enemy_damage_dealer(world)
	if dealer == null:
		_refuse("No enemy heroes!", silent)
		return false
	_attack_target(world, heroes, dealer, ATTACK_DAMAGE_DEALER)
	if not silent:
		AudioRuntime.play("hero_skill")
		_feedback(
			(
				"ATTACK DAMAGE DEALER! Focus %s (%d dmg)!"
				% [_display_name(dealer), dealer.damage_dealt]
			),
			Color("ff82ff")
		)
	return true


func _attack_target(world: Object, heroes: Array, target: Object, command_name: String) -> void:
	active_command = command_name
	command_timer = COMMAND_TICKS
	command_target_id = target.id
	gather_point = target.position
	gather_point_active = true
	gather_point_timer = POINT_TICKS
	cooldown = COOLDOWN_TICKS
	_clear_retreat(heroes)
	for index in range(heroes.size()):
		var hero: HeroState = heroes[index]
		var angle := float(index) / heroes.size() * TAU
		var spread := hero.attack_range * 0.5 + float(index) * 8.0
		world.move_to(hero, target.position + Vector2.from_angle(angle) * spread, false)
		hero.follow_id = target.id
		hero.target_id = target.id


func _gather_hold_push(world: Object) -> bool:
	var heroes := _alive_blue_heroes(world)
	if heroes.is_empty() or not gather_point_active:
		return false
	var target := _find_nearest_enemy_target(world, gather_point)
	if target == null:
		var fallback_point := hold_point if hold_has_point else gather_point
		return _command_gather(world, fallback_point, true, hold_selected_hero_id, true)
	for hero in heroes:
		hero.follow_id = target.id
		hero.has_destination = false
		hero.destination_auto = false
		hero.is_retreating = false
		hero.target_id = target.id
	command_timer = COMMAND_TICKS
	gather_point_timer = POINT_TICKS
	gather_point_active = true
	return true


func _try_gather_push(world: Object) -> bool:
	var heroes := _alive_blue_heroes(world)
	if heroes.is_empty() or not gather_point_active:
		return false
	var arrived := 0
	for hero in heroes:
		if hero.position.distance_to(gather_point) < 100.0:
			arrived += 1
	if arrived < heroes.size() * 0.6:
		return false
	var target := _find_nearest_enemy_target(world, gather_point)
	if target == null:
		return false
	for hero in heroes:
		hero.follow_id = target.id
		hero.has_destination = false
	gather_push_fired = true
	_feedback("GATHER ATTACK! %d heroes push together!" % heroes.size(), Color("64dcff"))
	return true


func _auto_evaluate_protect(world: Object) -> void:
	if not world.is_running():
		return
	var castle := world.nexuses[BLUE] as StructureState
	if castle != null and castle.alive:
		var castle_ratio := castle.hp / maxf(1.0, castle.definition.max_hp)
		if castle_ratio < 0.4 and _count_enemies_near(world, castle.position, 300.0) >= 2:
			_command_protect_castle(world, false)
			return
	var threatened: Array = []
	for tower in _blue_towers(world):
		var ratio := tower.hp / maxf(1.0, tower.definition.max_hp)
		var enemies := _count_enemies_near(world, tower.position, 250.0)
		if (ratio < 0.6 and enemies >= 2) or enemies >= 4:
			threatened.append({"enemies": enemies, "ratio": ratio, "tower": tower})
	if not threatened.is_empty():
		threatened.sort_custom(
			func(a: Dictionary, b: Dictionary) -> bool:
				if a.enemies == b.enemies:
					return a.ratio < b.ratio
				return a.enemies > b.enemies
		)
		_command_protect_tower(world, threatened[0].tower.id, false)
		return
	var boss: Object = world.active_boss
	if boss != null and boss.alive and boss.hp / maxf(1.0, boss.max_hp) < 0.8:
		var roll := (
			float(boss_auto_roll_override.call())
			if boss_auto_roll_override.is_valid()
			else rng.randf()
		)
		if world.wave_count >= 11 and roll < 0.2:
			_command_attack_boss(world, false)


func _find_most_threatened_tower(world: Object) -> StructureState:
	var towers := _blue_towers(world)
	if towers.is_empty():
		return null
	var best: StructureState = towers[0]
	var best_score := -INF
	for tower in towers:
		var enemies := _count_enemies_near(world, tower.position, 220.0)
		var ratio := tower.hp / maxf(1.0, tower.definition.max_hp)
		var score := enemies * 10.0 + (1.0 - ratio) * 15.0
		if tower.position.x < 400.0:
			score += 2.0
		if score > best_score:
			best_score = score
			best = tower
	if best_score == 0.0:
		for tower in towers:
			if (
				tower.hp / maxf(1.0, tower.definition.max_hp)
				< best.hp / maxf(1.0, best.definition.max_hp)
			):
				best = tower
	return best


func _count_enemies_near(world: Object, point: Vector2, radius: float) -> int:
	var count := 0
	for unit in world.units:
		if unit.alive and unit.team == RED and not unit.is_hero:
			if unit.position.distance_to(point) <= radius:
				count += 1
	for hero in world._ai_roster():
		if hero.alive and hero.position.distance_to(point) <= radius:
			count += 1
	var boss: Object = world.active_boss
	if boss != null and boss.alive and boss.team == RED:
		if boss.position.distance_to(point) <= radius:
			count += 2
	return count


func _find_nearest_enemy_target(world: Object, point: Vector2) -> Object:
	var best: Object = null
	var best_distance := 9999.0
	var boss: Object = world.active_boss
	if boss != null and boss.alive:
		best = boss
		best_distance = boss.position.distance_to(point)
	for structure in world.structures:
		if (
			structure.alive
			and structure.team == RED
			and structure.settings().structure_kind == "tower"
		):
			var distance := structure.position.distance_to(point)
			if distance < best_distance:
				best_distance = distance
				best = structure
	for hero in world._ai_roster():
		if hero.alive:
			var distance := hero.position.distance_to(point)
			if distance < best_distance:
				best_distance = distance
				best = hero
	if best == null:
		for unit in world.units:
			if unit.alive and unit.team == RED and not unit.is_hero:
				var distance := unit.position.distance_to(point)
				if distance < best_distance:
					best_distance = distance
					best = unit
	if best == null:
		var red_castle := world.nexuses[RED] as StructureState
		if red_castle != null and red_castle.alive:
			best = red_castle
	return best


func _find_enemy_damage_dealer(world: Object) -> HeroState:
	var best: HeroState = null
	for value in world._ai_roster():
		var hero := value as HeroState
		if hero == null or not hero.alive:
			continue
		if best == null or hero.damage_dealt > best.damage_dealt:
			best = hero
	return best


func _alive_blue_heroes(world: Object) -> Array:
	var result: Array = []
	for hero in world.player_roster():
		if hero.alive:
			result.append(hero)
	return result


func _blue_towers(world: Object) -> Array:
	var result: Array = []
	for structure in world.structures:
		if _is_blue_tower(structure):
			result.append(structure)
	return result


func _is_blue_tower(value: Object) -> bool:
	var tower := value as StructureState
	return (
		tower != null
		and tower.alive
		and tower.team == BLUE
		and tower.settings().structure_kind == "tower"
	)


func _stable_distance_sort(heroes: Array, point: Vector2) -> Array:
	var result: Array = []
	for hero in heroes:
		var inserted := false
		for index in range(result.size()):
			if hero.position.distance_to(point) < result[index].position.distance_to(point):
				result.insert(index, hero)
				inserted = true
				break
		if not inserted:
			result.append(hero)
	return result


func _clear_retreat(heroes: Array) -> void:
	for hero in heroes:
		hero.is_retreating = false
		hero.destination_auto = false


func _feedback(text: String, color: Color) -> void:
	feedback_text = text
	feedback_timer = FEEDBACK_TICKS
	feedback_color = color


func _refuse(text: String, silent: bool) -> void:
	if not silent:
		_feedback(text, Color("ff6464"))


func _display_name(target: Object) -> String:
	if target is HeroState:
		return (target as HeroState).settings().display_name
	if target is StructureState:
		return (target as StructureState).settings().display_name
	var name_value: Variant = target.get("display_name")
	return String(name_value) if name_value != null else "BOSS"
