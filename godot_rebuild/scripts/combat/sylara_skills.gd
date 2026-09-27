extends RefCounted
## SylaraSkills port. Gameplay hits are immediate except homing basic arrows;
## R's five skill arrows are purely visual in Python (damage is on release).

const HeroState = preload("res://scripts/combat/hero_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not world.is_running() or hero == null or not hero.alive:
		return false
	match key:
		"q":
			return hero.skill_timer <= 0 and world._has_q_target(hero, structures)
		"w":
			return hero.w_cooldown <= 0
		"e":
			return hero.e_cooldown <= 0 and _shackle_target(world, hero, structures) != null
		"r":
			return hero.r_cooldown <= 0 and world._has_q_target(hero, structures)
	return false


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	match key:
		"q":
			hero.focus_fire_timer = 180
			hero.attack_cd_base = maxi(20, int(hero.attack_cd_base / 1.7))
			var target := _current_target(world, hero)
			if target != null:
				var direction: Vector2 = target.position - hero.position
				if direction.length() > 0:
					_line_damage(world, hero, direction.normalized(), structures)
			hero.skill_timer = hero.skill_cd_max
			hero.active_skill_timer = 180
		"w":
			hero.windrun_timer = 180
			hero.windrun_original_speed = hero.speed
			hero.speed *= 2.0
			hero.hp = minf(hero.max_hp, hero.hp + 30)
			hero.w_cooldown = hero.w_cooldown_max
			hero.active_skill_timer = 180
		"e":
			var target := _shackle_target(world, hero, structures)
			if target == null:
				return false
			hero.shackle_timer = 150
			hero.shackle_target_id = target.id
			world._deliver_hit(
				-1,
				hero.team,
				target,
				int(hero.skill_damage() * 0.7),
				hero.dmg_school,
				hero.position
			)
			_stun(target, 45)
			hero.e_cooldown = hero.e_cooldown_max
			hero.active_skill_timer = 150
		"r":
			hero.powershot_timer = 60
			hero.r_cooldown = hero.r_cooldown_max
			hero.active_skill_timer = 60
	hero.active_skill = key
	return true


static func tick(world, hero: HeroState, structures: Array) -> void:
	if hero.focus_fire_timer > 0:
		hero.focus_fire_timer -= 1
		if hero.focus_fire_timer == 0:
			# Source resets from HERO_TYPES, not the potentially upgraded value.
			hero.attack_cd_base = hero.settings().attack_cooldown_ticks
	if hero.windrun_timer > 0:
		hero.windrun_timer -= 1
		if hero.windrun_timer == 0:
			hero.speed = hero.windrun_original_speed
	if hero.shackle_timer > 0:
		hero.shackle_timer -= 1
		var target = world.get_unit(hero.shackle_target_id)
		if target != null and target.alive:
			if hero.shackle_timer % 15 == 0:
				world._deliver_hit(
					-1,
					hero.team,
					target,
					int(hero.skill_damage() * 0.4),
					hero.dmg_school,
					hero.position
				)
				_stun(target, 30)
		else:
			hero.shackle_target_id = -1
		if hero.shackle_timer == 0:
			hero.shackle_target_id = -1
	if hero.powershot_timer > 0:
		hero.powershot_timer -= 1
		if hero.powershot_timer == 0:
			_release_powershot(world, hero, structures)


static func _current_target(world, hero: HeroState):
	if hero.target_struct != null and hero.target_struct.alive:
		return hero.target_struct
	var unit = world.get_unit(hero.target_id)
	return unit if unit != null and unit.alive else null


static func _enemies(world, hero: HeroState, structures: Array) -> Array:
	var enemies := []
	for unit in world.units:
		if unit.alive and unit.team != hero.team:
			enemies.append(unit)
	for entry in structures:
		var structure := entry as StructureState
		if structure != null and structure.alive and structure.team != hero.team:
			enemies.append(structure)
	return enemies


static func _shackle_target(world, hero: HeroState, structures: Array):
	# The outer source target gate uses skill_range * 1.15 (207px), but
	# the actual bind checks current target <=200, then fallback <200.
	if not world._has_q_target(hero, structures):
		return null
	var current = _current_target(world, hero)
	if current != null and hero.position.distance_to(current.position) <= 200.0:
		return current
	var closest = null
	var distance := 200.0
	for enemy in _enemies(world, hero, structures):
		var candidate := hero.position.distance_to(enemy.position)
		if candidate < distance:
			closest = enemy
			distance = candidate
	return closest


static func _line_damage(world, hero: HeroState, direction: Vector2, structures: Array) -> void:
	var hit_count := 0
	for enemy in _enemies(world, hero, structures):
		var offset: Vector2 = enemy.position - hero.position
		var projected := offset.dot(direction)
		if projected > 0 and projected < hero.skill_range:
			var perpendicular := absf(offset.cross(direction))
			if perpendicular < 15.0:
				var falloff := maxf(0.5, 1.0 - hit_count * 0.15)
				world._deliver_hit(
					-1,
					hero.team,
					enemy,
					int(hero.skill_damage() * falloff),
					hero.dmg_school,
					hero.position
				)
				hit_count += 1


static func _release_powershot(world, hero: HeroState, structures: Array) -> void:
	var target := _current_target(world, hero)
	var direction := Vector2(hero.facing, 0.0)
	if target != null and target.position != hero.position:
		direction = (target.position - hero.position).normalized()
	var base_angle := direction.angle()
	var hit := {}
	for arrow in range(5):
		var spread := (float(arrow) / 4.0 - 0.5) * (PI / 6.0)
		var arrow_direction := Vector2.from_angle(base_angle + spread)
		for enemy in _enemies(world, hero, structures):
			if hit.has(enemy.id):
				continue
			var offset: Vector2 = enemy.position - hero.position
			var projected := offset.dot(arrow_direction)
			if projected > 0 and projected < 300.0 and absf(offset.cross(arrow_direction)) < 20.0:
				var falloff := maxf(0.6, 1.0 - projected / 300.0 * 0.4)
				world._deliver_hit(
					-1,
					hero.team,
					enemy,
					int(hero.skill_damage() * falloff),
					hero.dmg_school,
					hero.position
				)
				hit[enemy.id] = true


static func _stun(target, duration: int) -> void:
	# Python's attack_timer maps to different native clocks by unit type.
	if target is HeroState:
		target.attack_timer = duration
	else:
		target.cooldown_ticks = duration
