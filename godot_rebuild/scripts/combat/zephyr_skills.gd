extends RefCounted
## ZephyrSkills: fixed ground trap, invulnerable healing realm, curse and Bedlam.
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key):
		return false
	if key == "w":
		return true
	if key == "e":
		return Common.bound_target(world, hero, structures) != null
	return world._has_q_target(hero, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	match key:
		"q":
			hero.bramble_origin = Common.current(world, hero).position
			hero.bramble_timer = 240
			for enemy in Common.enemies(world, hero, structures):
				if hero.bramble_origin.distance_to(enemy.position) <= 60:
					Common.hit(world, hero, enemy, 0.8)
					world.apply_slow(enemy.id, 0.5, 180)
		"w":
			hero.shadow_realm_timer = 180
			hero.hp = minf(hero.max_hp, hero.hp + 40)
		"e":
			var target = Common.bound_target(world, hero, structures)
			hero.curse_timer = 180
			hero.curse_target_id = target.id
			Common.hit(world, hero, target, 0.6)
		"r":
			hero.bedlam_timer = 240
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 80:
					Common.hit(world, hero, enemy, 1.8, true)
	Common.trigger(hero, key, {"q": 240, "w": 180, "e": 180, "r": 240}[key])
	return true


static func tick(world, hero: HeroState, structures: Array) -> void:
	if hero.bramble_timer > 0:
		hero.bramble_timer -= 1
		if hero.bramble_timer % 20 == 0:
			for enemy in Common.enemies(world, hero, structures):
				var distance := hero.bramble_origin.distance_to(enemy.position)
				if distance > 40 and distance <= 60:
					Common.hit(world, hero, enemy, 0.3, true)
					world.apply_slow(enemy.id, 0.5, 60)
		if hero.bramble_timer == 0:
			hero.bramble_origin = Vector2.ZERO
	if hero.shadow_realm_timer > 0:
		hero.shadow_realm_timer -= 1
		hero.hp = minf(hero.max_hp, hero.hp + 2)
	if hero.curse_timer > 0:
		hero.curse_timer -= 1
		var target = world.get_unit(hero.curse_target_id)
		if target != null and target.alive:
			if hero.curse_timer % 20 == 0:
				Common.hit(world, hero, target, 0.35, true)
		else:
			hero.curse_target_id = -1
		if hero.curse_timer == 0:
			hero.curse_target_id = -1
	if hero.bedlam_timer > 0:
		hero.bedlam_timer -= 1
		if hero.bedlam_timer % 15 == 0:
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 80:
					Common.hit(world, hero, enemy, 0.5, true)
