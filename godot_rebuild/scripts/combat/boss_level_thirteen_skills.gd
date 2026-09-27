extends RefCounted
## Boss level 13 recipes: Kaeldris, Pyraklos, Velmyrth, Solvarin.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
## Source level-13 recipes call take_damage(dmg, team) without source/school,
## so every hit stays neutral and unattributed (Common.hit default).
## Visual timers: the shared BossHeroSkills.cast_* dispatcher overwrites the
## recipe active_skill_timer with 60/90/60/100 after the recipe runs.
## Attack delay: source attack_timer = max(attack_timer, n) -> Common.stun.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["kaeldris", "pyraklos", "velmyrth"]
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
		"kaeldris":
			_kaeldris(world, hero, target, key, structures)
		"pyraklos":
			_pyraklos(world, hero, target, key, structures)
		"velmyrth":
			_velmyrth(world, hero, target, key, structures)
		#DISPATCH
		_:
			return false
	Common.trigger(hero, key, VISUAL[key])
	return true


static func _kaeldris(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Overwhelming: target 1.2x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.2)
		"w":
			# Press: dash min(dist, 110) (d > 1), then target 1.3x skill.
			if target == null:
				return
			_dash(hero, target, 110.0)
			Common.hit(world, hero, target, 1.3)
		"e":
			# Moment: AOE 170 1.1x skill.
			_radial(world, hero, structures, 170.0, 1.1)
		"r":
			# Duel: AOE 220 1.8x skill, attack delay max(timer, 60).
			_radial(world, hero, structures, 220.0, 1.8, 60)


static func _pyraklos(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Spear of Mars: target 1.3x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
		"w":
			# Rebuke: AOE 170 1.1x skill.
			_radial(world, hero, structures, 170.0, 1.1)
		"e":
			# Bulwark: AOE 130 0.7x skill, heal 12%.
			_radial(world, hero, structures, 130.0, 0.7)
			hero.heal_hp(int(hero.max_hp * 0.12))
		"r":
			# Arena: AOE 230 1.8x skill, attack delay max(timer, 60).
			_radial(world, hero, structures, 230.0, 1.8, 60)


static func _velmyrth(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Dagger: target 1.2x skill, slow 0.5 for 90.
			if target == null:
				return
			Common.hit(world, hero, target, 1.2)
			world.apply_slow(target.id, 0.5, 90)
		"w":
			# Strike: teleport to (target.x, target.y - 20), then target 1.3x skill.
			if target == null:
				return
			hero.position = target.position - Vector2(0, 20)
			Common.hit(world, hero, target, 1.3)
		"e":
			# Blur: AOE 170 1.1x skill.
			_radial(world, hero, structures, 170.0, 1.1)
		"r":
			# Coup: AOE 220, dmg = int(skill * 1.8); strictly below 30% HP
			# (hp / max(1, max_hp), pre-hit) dmg = int(dmg * 1.6). No heal.
			var base := int(hero.skill_damage() * 1.8)
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 220.0:
					var damage := base
					if enemy.hp / maxf(1.0, _max_hp(enemy)) < 0.3:
						damage = int(damage * 1.6)
					world._deliver_hit(-1, hero.team, enemy, damage, "neutral", hero.position)


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
