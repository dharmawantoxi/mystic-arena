extends RefCounted
## Exact Vhalzun recipes: no invented DOT, execute, shield or ghost immunity.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
# Vhalzun explicitly overrides BaseSkill's W visual duration in the source.
const VISUAL := {"q": 60, "w": 80, "e": 60, "r": 100}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id != "vhalzun":
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	match key:
		"q":
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 130:
					Common.hit(world, hero, enemy, 1.5)
		"w":
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 150:
					Common.hit(world, hero, enemy, 1.0)
					Common.stun(enemy, 60)
		"e":
			var target = Common.current(world, hero)
			if target != null:
				Common.hit(world, hero, target, 1.8)
		"r":
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 150:
					Common.hit(world, hero, enemy, 1.4)
			hero.heal_hp(int(hero.max_hp * 0.18))
	Common.trigger(hero, key, VISUAL[key])
	return true
