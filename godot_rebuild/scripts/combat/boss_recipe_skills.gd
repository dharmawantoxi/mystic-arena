extends RefCounted
## Own-recipe BossHeroSkills handlers beyond the level-one group.
## Every ID here has its OWN four source methods (AST-audited to be unique
## across all 61 remaining bosses) and its own source oracle + native suite.
## This is never a fallback: unknown IDs return false and stay rejected.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const Shapes = preload("res://scripts/combat/boss_recipe_shapes.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["ignis_drachorn"]


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id not in IDS:
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	match hero.settings().id:
		"ignis_drachorn":
			_ignis(world, hero, Common.current(world, hero), key, structures)
	# Source generic cooldown trigger overwrites each recipe's visual duration.
	# No BOSS_HERO_VISUAL_DURATION entry exists for these IDs, so the BaseSkill
	# defaults 60/90/60/100 apply.
	Common.trigger(hero, key, {"q": 60, "w": 90, "e": 60, "r": 100}[key])
	return true


static func _ignis(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Q - Dragon Breath: widening cone 250/60, half width scaling from
			# 0.3 to 1.0 of the cone width along the reach, 1.6x, stun 45.
			Shapes.cone(world, hero, structures, target, 250.0, 60.0, 1.6, 45)
		"w":
			# W - Dragon Tail: 360 sweep r130, 1.9x, stun 60.
			Shapes.burst(world, hero, structures, hero.position, 130.0, 1.9, 0.0, 0, 60)
		"e":
			# E - Dragon Blood: 480 tick flag, RAW catalog damage x1.3 (not the
			# level-adjusted damage) and a 20% heal.
			hero.dragon_blood_active = true
			hero.dragon_blood_timer = 480
			hero.damage = int(hero.settings().catalog_damage * 1.3)
			Shapes.heal(hero, int(hero.max_hp * 0.2))
		"r":
			# R - Elder Dragon Form: 600 tick flag, catalog damage x1.8, then the
			# r220 nova at 3.0x with stun 90 and a 25% heal.
			hero.dragon_form_active = true
			hero.dragon_form_timer = 600
			hero.damage = int(hero.settings().catalog_damage * 1.8)
			Shapes.burst(world, hero, structures, hero.position, 220.0, 3.0, 0.0, 0, 90)
			Shapes.heal(hero, int(hero.max_hp * 0.25))


static func tick(_world, hero: HeroState, _structures: Array) -> void:
	# Real BossHeroSkills.update_timers order: dragon form first, then blood.
	if hero.dragon_form_active:
		hero.dragon_form_timer -= 1
		if hero.dragon_form_timer <= 0:
			hero.dragon_form_active = false
			# Raw catalog damage, not the level-adjusted or blood value.
			hero.damage = hero.settings().catalog_damage
	if hero.dragon_blood_active:
		hero.dragon_blood_timer -= 1
		if hero.dragon_blood_timer <= 0:
			# Source quirk: the blood flag clears but the damage it applied is
			# never rolled back. Do not "fix" this.
			hero.dragon_blood_active = false
