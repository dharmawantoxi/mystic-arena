extends RefCounted
## Source Alchemist recipes; not the closed shared-source boss kit.
const Common = preload("res://scripts/combat/skill_common.gd")
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const BossTimers = preload("res://scripts/combat/boss_level_one_skills.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match key:
		"q":
			Common.hit(world, hero, target, 1.1)
		"w":
			hero.alchemy_target = target.position
			for enemy in Common.enemies(world, hero, structures):
				if hero.alchemy_target.distance_to(enemy.position) <= 100:
					Common.hit(world, hero, enemy, 1.5)
					world.apply_slow(enemy.id, 0.5, 180)
		"e":
			hero.rage_timer = 360
			hero.damage = int(hero.settings().catalog_damage * 1.5)
			hero.heal_hp(int(hero.max_hp * 0.15))
		"r":
			var kills := 0
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 200:
					Common.hit(world, hero, enemy, 2.5)
					if not enemy.alive:
						kills += 1
			if kills > 0:
				hero.heal_hp(kills * 100)
	Common.trigger(hero, key, {"q": 60, "w": 90, "e": 60, "r": 100}[key])
	return true


static func tick(world, hero: HeroState, structures: Array) -> void:
	# Same real BossHeroSkills.update_timers rage code as Drakar, including
	# the raw catalog reset after upgrade. No invented attack-speed buff.
	BossTimers.tick(world, hero, structures)
