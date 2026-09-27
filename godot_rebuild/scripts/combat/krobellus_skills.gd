extends RefCounted
## Exact Krobellus recipes. No persistent ghost/DOT/silence state in source.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
# Cooldown triggers replace recipe visual timers with BaseSkill defaults.
const VISUAL := {"q": 60, "w": 90, "e": 60, "r": 100}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id != "krobellus":
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	match key:
		"q":
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 150:
					Common.hit(world, hero, enemy, 1.5)
		"w":
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 120:
					Common.hit(world, hero, enemy, 1.0)
					Common.stun(enemy, 75)
		"e":
			var target = Common.current(world, hero)
			if target != null:
				Common.hit(world, hero, target, 1.3)
				hero.heal_hp(int(hero.skill_damage() * 0.5))
		"r":
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 200:
					Common.hit(world, hero, enemy, 2.5)
			hero.heal_hp(int(hero.max_hp * 0.15))
	Common.trigger(hero, key, VISUAL[key])
	return true
