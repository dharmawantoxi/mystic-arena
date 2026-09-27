extends RefCounted
## Boss level 7 recipes: Akashari, Malzareth, Nyxarath, Vorenmarr.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["akashari", "malzareth", "nyxarath", "vorenmarr"]
const VISUAL := {
	"akashari": {"q": 60, "w": 90, "e": 60, "r": 100},
	"malzareth": {"q": 60, "w": 90, "e": 60, "r": 100},
	"nyxarath": {"q": 60, "w": 90, "e": 60, "r": 100},
	"vorenmarr": {"q": 60, "w": 90, "e": 60, "r": 100}
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
		"akashari":
			_akashari(world, hero, target, key, structures)
		"malzareth":
			_malzareth(world, hero, target, key, structures)
		"nyxarath":
			_nyxarath(world, hero, target, key, structures)
		"vorenmarr":
			_vorenmarr(world, hero, target, key, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _akashari(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Strike: target 1.6x skill, slow 0.4 for 120.
			if target == null:
				return
			Common.hit(world, hero, target, 1.6)
			world.apply_slow(target.id, 0.4, 120)
		"w":
			# Blink: move min(dist, 150) towards the target, then AOE 80 around
			# the NEW position for 1.3x skill. Heal 8% even without a target.
			if target != null:
				var dist := hero.position.distance_to(target.position)
				if dist > 0.0:
					hero.position += (target.position - hero.position) / dist * minf(dist, 150.0)
			_radial(world, hero, structures, hero.position, 80.0, 1.3)
			hero.heal_hp(int(hero.max_hp * 0.08))
		"e":
			# Scream: AOE 150 around hero, damage 1.5x skill.
			_radial(world, hero, structures, hero.position, 150.0, 1.5)
		"r":
			# Sonic: AOE 220 around hero, damage 2.3x skill, slow 0.5 for 240, heal 10%.
			_radial(world, hero, structures, hero.position, 220.0, 2.3, 0, 0.5, 240)
			hero.heal_hp(int(hero.max_hp * 0.10))


static func _malzareth(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Disruption: AOE 100 around target (x+100 offset when absent), 1.5x skill.
			var center: Vector2 = (
				target.position if target != null else hero.position + Vector2(100, 0)
			)
			_radial(world, hero, structures, center, 100.0, 1.5)
		"w":
			# Soul: target 1.4x skill, other enemies within 60 of the target 0.7x.
			if target == null:
				return
			Common.hit(world, hero, target, 1.4)
			for enemy in Common.enemies(world, hero, structures):
				if enemy.id != target.id and target.position.distance_to(enemy.position) <= 60:
					Common.hit(world, hero, enemy, 0.7)
		"e":
			# Poison: target 1.1x skill, slow 0.5 for 180.
			if target == null:
				return
			Common.hit(world, hero, target, 1.1)
			world.apply_slow(target.id, 0.5, 180)
		"r":
			# Disillusion: AOE 200 around hero, damage 2.0x skill, stun 90, heal 10%.
			_radial(world, hero, structures, hero.position, 200.0, 2.0, 90)
			hero.heal_hp(int(hero.max_hp * 0.10))


static func _nyxarath(world, hero: HeroState, _target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Shadowraze: auto-targets the NEAREST enemy, ignoring hero.target;
			# cone 280 width 50, damage 1.8x skill, stun 45.
			var closest = null
			var closest_dist := 9999.0
			for enemy in Common.enemies(world, hero, structures):
				var d := hero.position.distance_to(enemy.position)
				if d < closest_dist:
					closest_dist = d
					closest = enemy
			if closest == null or closest_dist > 300.0:
				return
			if closest_dist == 0.0:
				return
			var dir: Vector2 = (closest.position - hero.position) / closest_dist
			_cone(world, hero, dir, 280.0, 50.0, structures, 1.8, 45)
		"w":
			# Necro: AOE 180 around hero, damage 1.7x skill; rage 480 from RAW
			# catalog damage x1.4; heal 8% plus 30 per kill.
			var victims := []
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 180.0:
					victims.append(enemy)
			var kills := 0
			for enemy in victims:
				Common.hit(world, hero, enemy, 1.7)
				if not enemy.alive:
					kills += 1
			hero.rage_timer = 480
			hero.damage = int(hero.settings().catalog_damage * 1.4)
			hero.heal_hp(int(hero.max_hp * 0.08) + kills * 30)
		"e":
			# Presence: AOE 200 around hero: stun 90 + slow 0.5 for 240, no damage,
			# heal 12%.
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 200.0:
					Common.stun(enemy, 90)
					world.apply_slow(enemy.id, 0.5, 240)
			hero.heal_hp(int(hero.max_hp * 0.12))
		"r":
			# Requiem: AOE 220 around hero, damage 3.0x skill, stun 120, heal 15%.
			_radial(world, hero, structures, hero.position, 220.0, 3.0, 120)
			hero.heal_hp(int(hero.max_hp * 0.15))


static func _vorenmarr(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Bonds: target 1.3x skill, other enemies within 80 of the target 0.6x.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
			for enemy in Common.enemies(world, hero, structures):
				if enemy.id != target.id and target.position.distance_to(enemy.position) <= 80:
					Common.hit(world, hero, enemy, 0.6)
		"w":
			# Power: heal 14% only.
			hero.heal_hp(int(hero.max_hp * 0.14))
		"e":
			# Upheaval: AOE 120 around target (hero when absent), 1.8x skill, stun 60.
			var center: Vector2 = target.position if target != null else hero.position
			_radial(world, hero, structures, center, 120.0, 1.8, 60)
		"r":
			# Golem: AOE 200 around hero, damage 2.2x skill, stun 90, heal 12%.
			_radial(world, hero, structures, hero.position, 200.0, 2.2, 90)
			hero.heal_hp(int(hero.max_hp * 0.12))


static func tick(_world, hero: HeroState, _structures: Array) -> void:
	# Source BossHeroSkills.update_timers: rage (Nyxarath W) decrements and
	# resets damage to the raw catalog value on expiry.
	if hero.rage_timer > 0:
		hero.rage_timer -= 1
		if hero.rage_timer == 0:
			# Raw catalog damage, NOT level-adjusted damage. Preserve source quirk.
			hero.damage = hero.settings().catalog_damage


static func _cone(
	world,
	hero: HeroState,
	dir: Vector2,
	max_range: float,
	width: float,
	structures: Array,
	mult: float,
	stun := 0,
	slow_amount := 0.0,
	slow_ticks := 0
) -> void:
	# Source cone: strict 0 < proj < range and strict perp < width.
	for enemy in Common.enemies(world, hero, structures):
		var ex: float = enemy.position.x - hero.position.x
		var ey: float = enemy.position.y - hero.position.y
		var proj: float = ex * dir.x + ey * dir.y
		if proj > 0 and proj < max_range:
			var perp: float = absf(ex * -dir.y + ey * dir.x)
			if perp < width:
				Common.hit(world, hero, enemy, mult)
				if stun > 0:
					Common.stun(enemy, stun)
				if slow_amount > 0.0:
					world.apply_slow(enemy.id, slow_amount, slow_ticks)


static func _radial(
	world,
	hero: HeroState,
	structures: Array,
	center: Vector2,
	radius: float,
	mult: float,
	stun := 0,
	slow_amount := 0.0,
	slow_ticks := 0
) -> void:
	# Source radial: inclusive distance <= radius (zero multiplier means no hit).
	if mult > 0.0:
		for enemy in Common.enemies(world, hero, structures):
			if center.distance_to(enemy.position) <= radius:
				Common.hit(world, hero, enemy, mult)
				if stun > 0:
					Common.stun(enemy, stun)
				if slow_amount > 0.0:
					world.apply_slow(enemy.id, slow_amount, slow_ticks)
