extends RefCounted
## Krobellus' level-five kit, ported from the four source recipe methods.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["krobellus"]
const VISUAL := {"krobellus": {"q": 60, "w": 90, "e": 60, "r": 100}}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id not in IDS:
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match key:
		"q":
			_q(world, hero, structures)
		"w":
			_w(world, hero, structures)
		"e":
			_e(world, hero, target)
		"r":
			_r(world, hero, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _q(world, hero: HeroState, structures: Array) -> void:
	# Exorcism: radius 150, skill damage x1.5.
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= 150.0:
			Common.hit(world, hero, enemy, 1.5)


static func _w(world, hero: HeroState, structures: Array) -> void:
	# Silence: radius 120, skill damage, minimum target attack clock 75.
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= 120.0:
			Common.hit(world, hero, enemy, 1.0)
			Common.stun(enemy, 75)


static func _e(world, hero: HeroState, target) -> void:
	# Siphon is restricted to the selected living target, not nearby enemies.
	if target == null:
		return
	Common.hit(world, hero, target, 1.3)
	hero.heal_hp(int(hero.skill_damage() * 0.5))


static func _r(world, hero: HeroState, structures: Array) -> void:
	# Crypt: radius 200, skill damage x2.5 and max-HP heal of 15%.
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= 200.0:
			Common.hit(world, hero, enemy, 2.5)
	hero.heal_hp(int(hero.max_hp * 0.15))
