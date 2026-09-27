extends RefCounted
## Boss level 12 recipes: Aurelix, Aurelyssa, Vargrath, Nazulmor.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
## Source level-12 recipes call take_damage(dmg, team) without source/school,
## so every hit stays neutral and unattributed (Common.hit default).
## Visual timers: the shared BossHeroSkills.cast_* dispatcher overwrites the
## recipe active_skill_timer with 60/90/60/100 after the recipe runs.
## Attack delay: source attack_timer = max(attack_timer, n) -> Common.stun.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["aurelix", "aurelyssa"]
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
		"aurelix":
			_aurelix(world, hero, target, key, structures)
		"aurelyssa":
			_aurelyssa(world, hero, target, key, structures)
		#DISPATCH
		_:
			return false
	Common.trigger(hero, key, VISUAL[key])
	return true


static func _aurelix(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Timebomb: target 1.2x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.2)
		"w":
			# Will: heal 12% only.
			hero.heal_hp(int(hero.max_hp * 0.12))
		"e":
			# Shockwave: AOE 170 1.1x skill, attack delay max(timer, 40).
			_radial(world, hero, structures, 170.0, 1.1, 40)
		"r":
			# Transcend: AOE 240 1.8x skill, slow 0.5 for 90.
			_radial(world, hero, structures, 240.0, 1.8, 0, 0.5, 90)


static func _aurelyssa(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Whirlwind: AOE 140 1.1x skill.
			_radial(world, hero, structures, 140.0, 1.1)
		"w":
			# Sweep: AOE 160 1.2x skill.
			_radial(world, hero, structures, 160.0, 1.2)
		"e":
			# Wings: dash min(dist, 100) (d > 1) when a target exists, then AOE 120
			# around the NEW position for 1.1x skill, even without a target.
			if target != null:
				_dash(hero, target, 100.0)
			_radial(world, hero, structures, 120.0, 1.1)
		"r":
			# Phantom: AOE 220 1.8x skill, attack delay max(timer, 60).
			_radial(world, hero, structures, 220.0, 1.8, 60)


#HEROES
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
	radius: float,
	mult: float,
	delay := 0,
	slow_amount := 0.0,
	slow_ticks := 0
) -> void:
	# Source radial around hero: inclusive distance <= radius.
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, mult)
			if delay > 0:
				Common.stun(enemy, delay)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
