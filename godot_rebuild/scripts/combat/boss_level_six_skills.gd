extends RefCounted
## Boss level 6 recipes: Kunkka, Gravewake, Syrentha, Thalgryn.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["kunkka", "gravewake", "syrentha", "thalgryn"]
const VISUAL := {
	"kunkka": {"q": 60, "w": 90, "e": 60, "r": 100},
	"gravewake": {"q": 60, "w": 90, "e": 60, "r": 100},
	"syrentha": {"q": 60, "w": 90, "e": 60, "r": 100},
	"thalgryn": {"q": 60, "w": 90, "e": 60, "r": 100}
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
		"kunkka":
			_kunkka(world, hero, target, key, structures)
		"gravewake":
			_gravewake(world, hero, target, key, structures)
		"syrentha":
			_syrentha(world, hero, target, key, structures)
		"thalgryn":
			_thalgryn(world, hero, target, key, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _kunkka(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Tide: cone 250 width 70 towards target, damage 1.8x skill.
			if target == null:
				return
			var dist := hero.position.distance_to(target.position)
			if dist == 0.0:
				return
			var dir: Vector2 = (target.position - hero.position) / dist
			_cone(world, hero, dir, 250.0, 70.0, structures, 1.8)
		"w":
			# X-Mark: AOE 120 around target, damage 1.5x skill, stun 60.
			if target == null:
				return
			_radial(world, hero, structures, target.position, 120.0, 1.5, 60)
		"e":
			# Ghost: cone 300 width 80, damage 2.2x skill, stun 90, heal 15%.
			if target == null:
				return
			var dist := hero.position.distance_to(target.position)
			if dist == 0.0:
				return
			var dir: Vector2 = (target.position - hero.position) / dist
			_cone(world, hero, dir, 300.0, 80.0, structures, 2.2, 90)
			hero.heal_hp(int(hero.max_hp * 0.15))
		"r":
			# Torrent: AOE 200 around target (hero when absent), damage 3.0x skill,
			# stun 120, heal 20%.
			var center: Vector2 = target.position if target != null else hero.position
			_radial(world, hero, structures, center, 200.0, 3.0, 120)
			hero.heal_hp(int(hero.max_hp * 0.20))


static func _gravewake(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Anchor: cone 200 width 60, damage 1.4x skill, slow 0.5 for 180.
			if target == null:
				return
			var dist := hero.position.distance_to(target.position)
			if dist == 0.0:
				return
			var dir: Vector2 = (target.position - hero.position) / dist
			_cone(world, hero, dir, 200.0, 60.0, structures, 1.4, 0, 0.5, 180)
		"w":
			# Tide: AOE 120 around target (hero when absent), damage 1.3x skill, stun 60.
			var center: Vector2 = target.position if target != null else hero.position
			_radial(world, hero, structures, center, 120.0, 1.3, 60)
		"e":
			# Shell: defense flag 300 + heal 12%.
			hero.defense_timer = 300
			hero.heal_hp(int(hero.max_hp * 0.12))
		"r":
			# Ravage: AOE 200 around hero, damage 2.0x skill, slow 0.5 for 180, heal 10%.
			_radial(world, hero, structures, hero.position, 200.0, 2.0, 0, 0.5, 180)
			hero.heal_hp(int(hero.max_hp * 0.10))


static func _syrentha(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Riptide: cone 250 width 70, damage 1.3x skill, slow 0.5 for 180.
			if target == null:
				return
			var dist := hero.position.distance_to(target.position)
			if dist == 0.0:
				return
			var dir: Vector2 = (target.position - hero.position) / dist
			_cone(world, hero, dir, 250.0, 70.0, structures, 1.3, 0, 0.5, 180)
		"w":
			# Song: AOE 150 around hero, damage 1.0x skill, stun 120, slow 0.7 for 240.
			_radial(world, hero, structures, hero.position, 150.0, 1.0, 120, 0.7, 240)
		"e":
			# Mirror: rage 360 from RAW catalog damage x1.4, heal 12%.
			hero.rage_timer = 360
			hero.damage = int(hero.settings().catalog_damage * 1.4)
			hero.heal_hp(int(hero.max_hp * 0.12))
		"r":
			# Siren: AOE 220 around hero, damage 2.2x skill, stun 150, heal 10%.
			_radial(world, hero, structures, hero.position, 220.0, 2.2, 150)
			hero.heal_hp(int(hero.max_hp * 0.10))


static func _thalgryn(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Waveform: cone 250 width 50, damage 1.6x skill, then surge
			# min(dist, 200) towards the target from the PRE-SURGE position.
			if target == null:
				return
			var dist := hero.position.distance_to(target.position)
			if dist == 0.0:
				return
			var dir: Vector2 = (target.position - hero.position) / dist
			_cone(world, hero, dir, 250.0, 50.0, structures, 1.6)
			hero.position += dir * minf(dist, 200.0)
		"w":
			# Adaptive: target damage 2.0x skill, other enemies within 60 of the
			# target take 0.7x skill.
			if target == null:
				return
			Common.hit(world, hero, target, 2.0)
			for enemy in Common.enemies(world, hero, structures):
				if enemy.id != target.id and target.position.distance_to(enemy.position) <= 60:
					Common.hit(world, hero, enemy, 0.7)
		"e":
			# Morph: rage 300 from RAW catalog damage x1.35, heal 14%.
			hero.rage_timer = 300
			hero.damage = int(hero.settings().catalog_damage * 1.35)
			hero.heal_hp(int(hero.max_hp * 0.14))
		"r":
			# Replicate: AOE 200 around hero, damage 2.0x skill, slow 0.4 for 180, heal 10%.
			_radial(world, hero, structures, hero.position, 200.0, 2.0, 0, 0.4, 180)
			hero.heal_hp(int(hero.max_hp * 0.10))


static func tick(_world, hero: HeroState, _structures: Array) -> void:
	# Source BossHeroSkills.update_timers: rage decrements and resets damage
	# to the raw catalog value on expiry; defense decrements only.
	if hero.rage_timer > 0:
		hero.rage_timer -= 1
		if hero.rage_timer == 0:
			# Raw catalog damage, NOT level-adjusted damage. Preserve source quirk.
			hero.damage = hero.settings().catalog_damage
	if hero.defense_timer > 0:
		hero.defense_timer -= 1
	# Defense flag has NO mitigation consumer in source Hero.take_damage.


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
	for enemy in Common.enemies(world, hero, structures):
		if center.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, mult)
			if stun > 0:
				Common.stun(enemy, stun)
			if slow_amount > 0.0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)
