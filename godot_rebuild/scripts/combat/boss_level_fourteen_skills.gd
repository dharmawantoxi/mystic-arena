extends RefCounted
## Boss level 14 recipes: Azureth, Luminar, Solara, Pyraethis.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
## Source level-14 recipes call take_damage(dmg, team) without source/school,
## so every hit stays neutral and unattributed (Common.hit default).
## Visual timers: the shared BossHeroSkills.cast_* dispatcher overwrites the
## recipe active_skill_timer with 60/90/60/100 after the recipe runs.
## Attack delay: source attack_timer = max(attack_timer, n) -> Common.stun.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["azureth"]
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
		"azureth":
			_azureth(world, hero, target, key, structures)
		#DISPATCH
		_:
			return false
	Common.trigger(hero, key, VISUAL[key])
	return true


static func _azureth(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Arcane bolt: target 1.2x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.2)
		"w":
			# Concussive: AOE 170 1.15x skill.
			_radial(world, hero, structures, 170.0, 1.15)
		"e":
			# Ancient seal: AOE 200 1.0x skill, slow 0.5 for 100.
			_radial(world, hero, structures, 200.0, 1.0, 0, 0.5, 100)
		"r":
			# Mystic flare: AOE 240 1.9x skill, attack delay max(timer, 65).
			_radial(world, hero, structures, 240.0, 1.9, 65)


#HEROES
static func _max_hp(target) -> float:
	if target is HeroState:
		return float(target.max_hp)
	if "definition" in target:
		return float(target.definition.max_hp)
	return float(target.data.max_hp)


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
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
