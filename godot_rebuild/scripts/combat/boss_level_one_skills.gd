extends RefCounted
## BossHeroSkills registry recipes for the four level-1 unlocks ONLY.
## Not _fallback_cast; unported boss IDs remain rejected.
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["gornak", "morgath", "drakar", "abaddon"]


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id not in IDS:
		return false
	# BossHeroSkills._generic_cast differs from BaseSkill target slack:
	# max(int(skill_range or 100), 140), stable FIRST nearest on ties.
	var reach := maxi(int(hero.skill_range), 140)
	var nearby = null
	var best := INF
	for enemy in Common.enemies(world, hero, structures):
		var distance := hero.position.distance_to(enemy.position)
		if distance <= reach and distance < best:
			nearby = enemy
			best = distance
	if nearby == null:
		return false
	var target = Common.current(world, hero)
	if target == null or hero.position.distance_to(target.position) > reach:
		if nearby is HeroState or nearby in world.units:
			hero.target_id = nearby.id
			hero.target_struct = null
		else:
			hero.target_id = -1
			hero.target_struct = nearby
	return true


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match hero.settings().id:
		"gornak":
			_gornak(world, hero, target, key, structures)
		"morgath":
			_morgath(world, hero, target, key, structures)
		"drakar":
			_drakar(world, hero, target, key, structures)
		"abaddon":
			_abaddon(world, hero, target, key, structures)
	# Source generic cooldown trigger overwrites each recipe's visual duration.
	Common.trigger(hero, key, {"q": 60, "w": 90, "e": 60, "r": 100}[key])
	return true


static func _gornak(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			Common.hit(world, hero, target, 1.2)
		"w":
			hero.blink_from = hero.position
			var delta: Vector2 = target.position - hero.position
			hero.position += delta.normalized() * maxf(0, delta.length() - 60)
		"e":
			_radial(world, hero, structures, 100, 0.8, 60)
		"r":
			hero.mana_void_origin = hero.position
			_radial(world, hero, structures, 180, 2.0)


static func _morgath(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			Common.hit(world, hero, target, 1.3)
		"w":
			hero.flux_target_id = target.id
			hero.flux_timer = 240
			Common.hit(world, hero, target, 0.5)
			world.apply_slow(target.id, 0.5, 240)
		"e":
			_radial(world, hero, structures, 90, 0.7, 45)
			_heal(hero, 0.08)
		"r":
			hero.clones_timer = 480
			_heal(hero, 0.15)


static func _drakar(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			hero.rage_timer = 300
			hero.damage = int(hero.settings().catalog_damage * 1.5)
			_heal(hero, 0.1)
		"w":
			_radial(world, hero, structures, 100, 1.5)
		"e":
			hero.defense_timer = 180
			_radial(world, hero, structures, 120, 1.0, 30)
		"r":
			var damage := int(hero.skill_damage() * 2.5)
			var maximum: float = target.max_hp if target is HeroState else target.definition.max_hp
			if target.hp / maximum < 0.3:
				damage *= 2
			world._deliver_hit(-1, hero.team, target, damage, hero.dmg_school, hero.position)


static func _abaddon(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			Common.hit(world, hero, target, 1.3)
		"w":
			_radial(world, hero, structures, 100, 1.5)
			_heal(hero, 0.25)
		"e":
			var delta: Vector2 = target.position - hero.position
			# Source travels a full 80px even if this overshoots the target.
			hero.position += delta.normalized() * 80
			Common.hit(world, hero, target, 1.0)
		"r":
			_radial(world, hero, structures, 180, 2.5)


static func tick(world, hero: HeroState, _structures: Array) -> void:
	if hero.rage_timer > 0:
		hero.rage_timer -= 1
		if hero.rage_timer == 0:
			# Raw catalog damage, NOT level-adjusted damage. Preserve source quirk.
			hero.damage = hero.settings().catalog_damage
	if hero.defense_timer > 0:
		hero.defense_timer -= 1
	# Defense flag has NO mitigation consumer in source Hero.take_damage.
	if hero.flux_timer > 0:
		hero.flux_timer -= 1
		if hero.flux_timer % 30 == 0:
			var target = world.get_unit(hero.flux_target_id)
			if target != null and target.alive:
				Common.hit(world, hero, target, 0.3)
				world.apply_slow(target.id, 0.4, 60)
	if hero.clones_timer > 0:
		hero.clones_timer -= 1
		if hero.clones_timer % 40 == 0:
			var target = Common.current(world, hero)
			if target != null:
				world._deliver_hit(
					-1, hero.team, target, int(hero.damage * 0.5), hero.dmg_school, hero.position
				)


static func _radial(
	world, hero: HeroState, structures: Array, radius: float, mult: float, stun := 0
) -> void:
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, mult)
			if stun > 0:
				Common.stun(enemy, stun)


static func _heal(hero: HeroState, fraction: float) -> void:
	hero.hp = minf(hero.max_hp, hero.hp + int(hero.max_hp * fraction))
