extends RefCounted
## Boss level 11 recipes: Aeralith, Aurex, Nyxareva, Thalakryon.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
## Source level-11 recipes call take_damage(dmg, team) without source/school,
## so every hit stays neutral and unattributed (Common.hit default).
## Visual timers: the shared BossHeroSkills.cast_* dispatcher overwrites the
## recipe active_skill_timer with 60/90/60/100 after the recipe runs.
## Attack delay: source attack_timer = max(attack_timer, n) -> Common.stun.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["aeralith", "aurex", "nyxareva", "thalakryon"]
const VISUAL := {"q": 60, "w": 90, "e": 60, "r": 100}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id not in IDS:
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match hero.settings().id:
		"aeralith":
			_aeralith(world, hero, target, key, structures)
		"aurex":
			_aurex(world, hero, target, key, structures)
		"nyxareva":
			_nyxareva(world, hero, target, key, structures)
		"thalakryon":
			_thalakryon(world, hero, target, key, structures)
		_:
			return false
	Common.trigger(hero, key, VISUAL[key])
	return true


static func _aeralith(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Tailwind: target 1.2x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.2)
		"w":
			# Windblade: AOE 190 1.1x skill.
			_radial(world, hero, structures, 190.0, 1.1)
		"e":
			# Vacuum: AOE 170 1.1x skill, slow 0.5 for 90.
			_radial(world, hero, structures, 170.0, 1.1, 0, 0.5, 90)
		"r":
			# Skyrider: AOE 240 1.8x skill.
			_radial(world, hero, structures, 240.0, 1.8)


static func _aurex(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Shieldcrash: target 1.3x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
		"w":
			# Voltblast: target 1.4x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.4)
		"e":
			# Aegis: AOE 130 0.9x skill, heal 10%.
			_radial(world, hero, structures, 130.0, 0.9)
			hero.heal_hp(int(hero.max_hp * 0.10))
		"r":
			# Spin: AOE 210 1.8x skill, attack delay max(timer, 60).
			_radial(world, hero, structures, 210.0, 1.8, 60)


static func _nyxareva(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Darkslash: target 1.2x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.2)
		"w":
			# Mortal wound: target 1.4x skill, slow 0.5 for 90.
			if target == null:
				return
			Common.hit(world, hero, target, 1.4)
			world.apply_slow(target.id, 0.5, 90)
		"e":
			# Sacrifice: AOE 170 1.1x skill.
			_radial(world, hero, structures, 170.0, 1.1)
		"r":
			# Avatar: AOE 220 1.8x skill, attack delay max(timer, 60).
			_radial(world, hero, structures, 220.0, 1.8, 60)


static func _thalakryon(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Bolt: target 1.3x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
		"w":
			# Aquashield: AOE 150 0.8x skill, heal 12%.
			_radial(world, hero, structures, 150.0, 0.8)
			hero.heal_hp(int(hero.max_hp * 0.12))
		"e":
			# Tidal rage: AOE 190 1.2x skill, attack delay max(timer, 40).
			_radial(world, hero, structures, 190.0, 1.2, 40)
		"r":
			# Metamorph: AOE 260 2.0x skill, attack delay max(timer, 75), heal 10%.
			_radial(world, hero, structures, 260.0, 2.0, 75)
			hero.heal_hp(int(hero.max_hp * 0.10))


static func _dash(hero: HeroState, target, max_step: float) -> void:
	# Source: d = hypot(dx, dy); if d > 1: step = min(d, max_step).
	var delta: Vector2 = target.position - hero.position
	var dist := delta.length()
	if dist > 1.0:
		hero.position += delta / dist * minf(dist, max_step)


static func _radial(
	world, hero: HeroState, structures: Array, radius: float, mult: float, delay := 0
) -> void:
	# Source radial around hero: inclusive distance <= radius.
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, mult)
			if delay > 0:
				Common.stun(enemy, delay)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
