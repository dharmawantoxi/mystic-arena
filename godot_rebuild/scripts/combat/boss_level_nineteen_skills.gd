extends RefCounted
## Boss level 19 recipes: Akahime, Nyxthrael, Sylvantheros, Vaelindra.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
## Source level-19 recipes call take_damage(dmg, team) without source/school,
## so every hit stays neutral and unattributed (Common.hit default).
## Visual timers: the shared BossHeroSkills.cast_* dispatcher overwrites the
## recipe active_skill_timer with 60/90/60/100 after the recipe runs.
## Attack delay: source attack_timer = max(attack_timer, n) -> Common.stun.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["akahime"]
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
		"akahime":
			_akahime(world, hero, target, key, structures)
		#DISPATCH
		_:
			return false
	Common.trigger(hero, key, VISUAL[key])
	return true


static func _akahime(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Target 1.25x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.25)
		"w":
			# AOE 195 1.15x skill, slow 0.4 for 90.
			_radial(world, hero, structures, 195.0, 1.15, 0, 0.4, 90)
		"e":
			# AOE 210 1.0x skill.
			_radial(world, hero, structures, 210.0, 1.0)
		"r":
			# AOE 270 1.95x skill, attack delay max(timer, 70).
			_radial(world, hero, structures, 270.0, 1.95, 70)


#HEROES
static func _execute_hit(world, hero: HeroState, target, mult: float, bonus: float) -> void:
	# Source: dmg = int(skill * mult); if hp / max(1, max_hp) < 0.3 (pre-hit):
	# dmg = int(dmg * bonus). Neutral, unattributed take_damage.
	var damage := int(hero.skill_damage() * mult)
	if target.hp / maxf(1.0, _max_hp(target)) < 0.3:
		damage = int(damage * bonus)
	world._deliver_hit(-1, hero.team, target, damage, "neutral", hero.position)


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
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
