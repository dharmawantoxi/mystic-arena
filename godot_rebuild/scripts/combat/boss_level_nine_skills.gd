extends RefCounted
## Boss level 9 recipes (batch 10): Kenshiro, Wiro.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
## Source level-9 recipes call take_damage(dmg, team) without source/school,
## so every hit stays neutral and unattributed (Common.hit default).
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["kenshiro", "wiro"]
const VISUAL := {
	"kenshiro": {"q": 35, "w": 45, "e": 55, "r": 70},
	"wiro": {"q": 30, "w": 45, "e": 40, "r": 80},
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
		"kenshiro":
			_kenshiro(world, hero, target, key, structures)
		"wiro":
			_wiro(world, hero, target, key, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _kenshiro(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Swiftslash: target 1.2x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.2)
		"w":
			# Assault: dash min(dist, 90) towards the target only when dist > 1,
			# then hit the target for 1.4x skill.
			if target == null:
				return
			_dash(hero, target, 90.0)
			Common.hit(world, hero, target, 1.4)
		"e":
			# Gale: AOE 150 around hero, 1.1x skill.
			_radial(world, hero, structures, hero.position, 150.0, 1.1)
		"r":
			# Supremacy: AOE 190 around hero, 1.8x skill.
			_radial(world, hero, structures, hero.position, 190.0, 1.8)


static func _wiro(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Windcut: target 1.2x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.2)
		"w":
			# Whirl: AOE 140 around hero, 1.1x skill.
			_radial(world, hero, structures, hero.position, 140.0, 1.1)
		"e":
			# Dash: move min(dist, 100) towards the target only when dist > 1,
			# then hit the target for 1.1x skill.
			if target == null:
				return
			_dash(hero, target, 100.0)
			Common.hit(world, hero, target, 1.1)
		"r":
			# Typhoon: AOE 200 around hero, 1.8x skill, slow 0.5 for 90.
			_radial(world, hero, structures, hero.position, 200.0, 1.8, 0.5, 90)


static func _dash(hero: HeroState, target, max_step: float) -> void:
	# Source: d = hypot(dx, dy); if d > 1: step = min(d, max_step).
	var delta: Vector2 = target.position - hero.position
	var dist := delta.length()
	if dist > 1.0:
		hero.position += delta / dist * minf(dist, max_step)


static func _radial(
	world,
	hero: HeroState,
	structures: Array,
	center: Vector2,
	radius: float,
	mult: float,
	slow_amount := 0.0,
	slow_ticks := 0
) -> void:
	# Source radial: inclusive distance <= radius.
	for enemy in Common.enemies(world, hero, structures):
		if center.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, mult)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
