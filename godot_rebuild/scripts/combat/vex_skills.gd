extends RefCounted
## VexSkills source port: instant orb/line, moving eclipse ring, prison, flux.
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key):
		return false
	if key == "e":
		return Common.bound_target(world, hero, structures) != null
	return world._has_q_target(hero, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var targets := Common.enemies(world, hero, structures)
	match key:
		"q":
			var target = Common.current(world, hero)
			Common.hit(world, hero, target, 1.2)
			var offset: Vector2 = target.position - hero.position
			var direction := offset.normalized()
			for enemy in targets:
				if enemy == target:
					continue
				var delta: Vector2 = enemy.position - hero.position
				var projected := delta.dot(direction)
				if (
					projected > 0
					and projected < offset.length()
					and absf(delta.cross(direction)) < 18
				):
					Common.hit(world, hero, enemy, 0.5)
		"w":
			hero.eclipse_timer = 180
			for enemy in targets:
				if hero.position.distance_to(enemy.position) <= 60:
					Common.hit(world, hero, enemy, 0.8)
					world.apply_slow(enemy.id, 0.5, 180)
		"e":
			var target = Common.bound_target(world, hero, structures)
			hero.prison_timer = 150
			hero.prison_target_id = target.id
			Common.hit(world, hero, target, 0.6)
		"r":
			hero.essence_timer = 60
			for enemy in targets:
				if hero.position.distance_to(enemy.position) <= 180:
					Common.hit(world, hero, enemy, 2.5, true)
	Common.trigger(hero, key, {"q": 40, "w": 100, "e": 60, "r": 80}[key])
	return true


static func tick(world, hero: HeroState, structures: Array) -> void:
	if hero.eclipse_timer > 0:
		hero.eclipse_timer -= 1
		if hero.eclipse_timer % 20 == 0:
			for enemy in Common.enemies(world, hero, structures):
				var distance := hero.position.distance_to(enemy.position)
				if distance > 30 and distance <= 55:
					Common.hit(world, hero, enemy, 0.4, true)
	if hero.prison_timer > 0:
		hero.prison_timer -= 1
		var target = world.get_unit(hero.prison_target_id)
		if target != null and target.alive:
			Common.stun(target, 15)
			if hero.prison_timer % 10 == 0:
				Common.hit(world, hero, target, 0.3, true)
		else:
			hero.prison_target_id = -1
		if hero.prison_timer == 0:
			hero.prison_target_id = -1
	if hero.essence_timer > 0:
		hero.essence_timer -= 1
