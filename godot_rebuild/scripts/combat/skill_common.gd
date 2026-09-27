extends RefCounted
## Only source BaseSkill utilities, not a replacement hero kit.

const StructureState = preload("res://scripts/combat/structure_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")


static func enemies(world, hero: HeroState, structures: Array) -> Array:
	var result := []
	for enemy in world.units + structures:
		if enemy.alive and enemy.team != hero.team:
			result.append(enemy)
	return result


static func current(world, hero: HeroState):
	if hero.target_struct != null and hero.target_struct.alive:
		return hero.target_struct
	var target = world.get_unit(hero.target_id)
	return target if target != null and target.alive else null


static func bound_target(world, hero: HeroState, structures: Array):
	# Vex prison and Zephyr curse have identical source selection code.
	if not world._has_q_target(hero, structures):
		return null
	var target = current(world, hero)
	if target != null and hero.position.distance_to(target.position) <= 200.0:
		return target
	var distance := 200.0
	target = null
	for enemy in enemies(world, hero, structures):
		var candidate := hero.position.distance_to(enemy.position)
		if candidate < distance:
			distance = candidate
			target = enemy
	return target


static func stun(target, duration: int) -> void:
	# Tower/Castle source objects have no attack_timer: do not stun their fire clock.
	if target is StructureState:
		return
	# BaseSkill._apply_stun uses max, never shortens an existing clock.
	if target is HeroState:
		target.attack_timer = maxi(target.attack_timer, duration)
	else:
		target.cooldown_ticks = maxi(target.cooldown_ticks, duration)


static func hit(world, hero: HeroState, target, multiplier: float, attributed := false) -> void:
	world._deliver_hit(
		hero.id if attributed else -1,
		hero.team,
		target,
		int(hero.skill_damage() * multiplier),
		hero.dmg_school if attributed else "neutral",
		hero.position
	)


static func trigger(hero: HeroState, key: String, visual: int) -> void:
	match key:
		"q":
			hero.skill_timer = hero.skill_cd_max
		"w":
			hero.w_cooldown = hero.w_cooldown_max
		"e":
			hero.e_cooldown = hero.e_cooldown_max
		"r":
			hero.r_cooldown = hero.r_cooldown_max
	hero.active_skill = key
	hero.active_skill_timer = visual


static func ready(world, hero: HeroState, key: String) -> bool:
	if not world.is_running() or hero == null or not hero.alive:
		return false
	match key:
		"q":
			return hero.skill_timer <= 0
		"w":
			return hero.w_cooldown <= 0
		"e":
			return hero.e_cooldown <= 0
		"r":
			return hero.r_cooldown <= 0
	return false
