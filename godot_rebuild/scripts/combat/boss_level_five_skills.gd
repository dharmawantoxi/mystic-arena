extends RefCounted
## Boss level 5 recipes: Krobellus + Vhalzun.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["krobellus", "vhalzun"]
const VISUAL := {
	"krobellus": {"q": 60, "w": 90, "e": 60, "r": 100},
	"vhalzun": {"q": 60, "w": 80, "e": 60, "r": 100}
}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id not in IDS:
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match hero.settings().id:
		"krobellus":
			_krobellus(world, hero, target, key, structures)
		"vhalzun":
			_vhalzun(world, hero, target, key, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _krobellus(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Exorcism: AOE 150 around hero, damage 1.5x skill.
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 150:
					Common.hit(world, hero, enemy, 1.5)
		"w":
			# Silence: AOE 120, damage 1.0x skill, stun 75 (attack clock max).
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 120:
					Common.hit(world, hero, enemy, 1.0)
					Common.stun(enemy, 75)
		"e":
			# Siphon: target damage 1.3x skill, heal 0.5x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
			hero.heal_hp(int(hero.skill_damage() * 0.5))
		"r":
			# Crypt: AOE 200, damage 2.5x skill, heal 15% max hp.
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 200:
					Common.hit(world, hero, enemy, 2.5)
			hero.heal_hp(int(hero.max_hp * 0.15))


static func _vhalzun(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Death Pulse: AOE 130 around hero, damage 1.5x skill.
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 130:
					Common.hit(world, hero, enemy, 1.5)
		"w":
			# Heartstopper: AOE 150, damage 1.0x skill, stun 60 (attack clock max).
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 150:
					Common.hit(world, hero, enemy, 1.0)
					Common.stun(enemy, 60)
		"e":
			# Reaper's Scythe: target damage 1.8x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.8)
		"r":
			# Ghost Shroud: AOE 150, damage 1.4x skill, heal 18% max hp.
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 150:
					Common.hit(world, hero, enemy, 1.4)
			hero.heal_hp(int(hero.max_hp * 0.18))
