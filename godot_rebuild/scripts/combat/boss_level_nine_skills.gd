extends RefCounted
## Boss level 9 recipes (batch 10-11): Kenshiro, Wiro, Khazan, Naraka.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
## Source level-9 recipes call take_damage(dmg, team) without source/school,
## so every hit stays neutral and unattributed (Common.hit default).
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["kenshiro", "wiro", "khazan", "naraka"]
const VISUAL := {
	"kenshiro": {"q": 35, "w": 45, "e": 55, "r": 70},
	"wiro": {"q": 30, "w": 45, "e": 40, "r": 80},
	"khazan": {"q": 40, "w": 50, "e": 60, "r": 75},
	"naraka": {"q": 40, "w": 50, "e": 60, "r": 90},
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
		"khazan":
			_khazan(world, hero, target, key, structures)
		"naraka":
			_naraka(world, hero, target, key, structures)
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


static func _khazan(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Chained: target 1.3x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
		"w":
			# Leap: dash min(dist, 110) towards the target (d > 1), then AOE 90
			# around the NEW position for 1.2x skill, even without a target.
			if target != null:
				_dash(hero, target, 110.0)
			_radial(world, hero, structures, hero.position, 90.0, 1.2)
		"e":
			# Spin: AOE 160 around hero, 1.1x skill.
			_radial(world, hero, structures, hero.position, 160.0, 1.1)
		"r":
			# Vanish: AOE 210 around hero, 1.9x skill, heal 8%.
			_radial(world, hero, structures, hero.position, 210.0, 1.9)
			hero.heal_hp(int(hero.max_hp * 0.08))


static func _naraka(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Chaos: target 1.3x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
		"w":
			# Shadowstep: dash min(dist, 120) (d > 1), then target 1.3x skill.
			if target == null:
				return
			_dash(hero, target, 120.0)
			Common.hit(world, hero, target, 1.3)
		"e":
			# Hammer: AOE 180 around hero, 1.1x skill, attack delay max(timer, 30)
			# (Common.stun skips source objects without attack_timer).
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 180.0:
					Common.hit(world, hero, enemy, 1.1)
					Common.stun(enemy, 30)
		"r":
			# Execution: AOE 230, dmg = int(skill * 1.8); strictly below 30% HP
			# (hp / max(1, max_hp), pre-hit) dmg = int(dmg * 1.6). Heal 10%.
			var base := int(hero.skill_damage() * 1.8)
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 230.0:
					var damage := base
					if enemy.hp / maxf(1.0, _max_hp(enemy)) < 0.3:
						damage = int(damage * 1.6)
					world._deliver_hit(-1, hero.team, enemy, damage, "neutral", hero.position)
			hero.heal_hp(int(hero.max_hp * 0.10))


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
