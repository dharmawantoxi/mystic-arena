extends RefCounted
## Boss level 5 recipes: Vhalzun and Krobellus. Exact source
## BossHeroSkills._cast_* ports, not _fallback_cast and not a shared kit.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["vhalzun", "krobellus"]
# Vhalzun owns a per-hero visual override in the source (60/80/60/100);
# Krobellus falls through to the shared default (60/90/60/100).
const VISUAL := {
	"vhalzun": {"q": 60, "w": 80, "e": 60, "r": 100},
	"krobellus": {"q": 60, "w": 90, "e": 60, "r": 100}
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
		"vhalzun":
			_vhalzun(world, hero, target, key, structures)
		"krobellus":
			_krobellus(world, hero, target, key, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _vhalzun(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Death Pulse: AOE 130 skill x1.5.
			_radial(world, hero, structures, 130.0, 1.5)
		"w":
			# Heartstopper: AOE 150 skill x1.0, attack clock floor 60.
			_radial(world, hero, structures, 150.0, 1.0, 60)
		"e":
			# Reaper's Scythe: single target x1.8, no AOE, no heal.
			if target == null:
				return
			Common.hit(world, hero, target, 1.8)
		"r":
			# Ghost Shroud: AOE 150 x1.4 plus an 18% max-HP heal.
			_radial(world, hero, structures, 150.0, 1.4)
			_heal(hero, 0.18)


static func _krobellus(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Exorcism: AOE 150 x1.5.
			_radial(world, hero, structures, 150.0, 1.5)
		"w":
			# Silence: AOE 120 x1.0, attack clock floor 75.
			_radial(world, hero, structures, 120.0, 1.0, 75)
		"e":
			# Siphon: target x1.3, heal is HALF THE SKILL VALUE, not max HP.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
			hero.heal_hp(int(hero.skill_damage() * 0.5))
		"r":
			# Crypt: AOE 200 x2.5 plus a 15% max-HP heal.
			_radial(world, hero, structures, 200.0, 2.5)
			_heal(hero, 0.15)


static func _radial(
	world, hero: HeroState, structures: Array, radius: float, mult: float, stun := 0
) -> void:
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, mult)
			if stun > 0:
				Common.stun(enemy, stun)


static func _heal(hero: HeroState, fraction: float) -> void:
	hero.heal_hp(int(hero.max_hp * fraction))


static func tick(_world, _hero: HeroState, _structures: Array) -> void:
	# Source BossHeroSkills.update_timers only ticks rage/defense/vortex/flux/
	# clones/dragon state. No level-5 recipe sets any of them, so the source
	# really does nothing here: do not invent a decay for these two kits.
	pass
