extends RefCounted
## Actual source Kunkka recipes; X Mark and Ghost Ship are instantaneous.
## No invented return teleport, ship projectile, rum mitigation or torrent delay.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const VISUAL := {"q": 60, "w": 90, "e": 60, "r": 100}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id != "kunkka":
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match key:
		"q":
			_tide(world, hero, target, structures)
		"w":
			if target != null:
				for enemy in Common.enemies(world, hero, structures):
					if target.position.distance_to(enemy.position) <= 120:
						Common.hit(world, hero, enemy, 1.5)
						Common.stun(enemy, 60)
		"e":
			_ghost(world, hero, target, structures)
		"r":
			var origin: Vector2 = target.position if target != null else hero.position
			for enemy in Common.enemies(world, hero, structures):
				if origin.distance_to(enemy.position) <= 200:
					Common.hit(world, hero, enemy, 3.0)
					Common.stun(enemy, 120)
			hero.heal_hp(int(hero.max_hp * 0.20))
	Common.trigger(hero, key, VISUAL[key])
	return true


static func _tide(world, hero: HeroState, target, structures: Array) -> void:
	if target == null or target.position == hero.position:
		return
	var direction: Vector2 = (target.position - hero.position).normalized()
	for enemy in Common.enemies(world, hero, structures):
		var offset: Vector2 = enemy.position - hero.position
		var projection: float = offset.dot(direction)
		var perpendicular: float = absf(offset.x * -direction.y + offset.y * direction.x)
		if 0 < projection and projection < 250 and perpendicular < 70:
			Common.hit(world, hero, enemy, 1.8)


static func _ghost(world, hero: HeroState, target, structures: Array) -> void:
	# The source returns before healing when the selected target overlaps caster.
	if target == null or target.position == hero.position:
		return
	var direction: Vector2 = (target.position - hero.position).normalized()
	for enemy in Common.enemies(world, hero, structures):
		var offset: Vector2 = enemy.position - hero.position
		var projection: float = offset.dot(direction)
		var perpendicular: float = absf(offset.x * -direction.y + offset.y * direction.x)
		if 0 < projection and projection < 300 and perpendicular < 80:
			Common.hit(world, hero, enemy, 2.2)
			Common.stun(enemy, 90)
	hero.heal_hp(int(hero.max_hp * 0.15))
