extends RefCounted
## Boss level 6 recipes: Kunkka, Gravewake, Syrentha and Thalgryn. Exact
## source BossHeroSkills._cast_* ports, not _fallback_cast and not one shared kit.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["kunkka", "gravewake", "syrentha", "thalgryn"]
# No per-hero override exists for these four in
# BossHeroSkills.BOSS_HERO_VISUAL_DURATION, so the shared default applies.
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
			# Tide: line 250 wide 70 towards the target, x1.8. No target, no cast.
			if target == null:
				return
			var dir := _direction(hero, target)
			if dir == Vector2.ZERO:
				return
			_line(world, hero, structures, dir, 250.0, 70.0, 1.8)
		"w":
			# X Mark: AOE 120 centred on the TARGET, x1.5, attack clock 60.
			if target == null:
				return
			_radial_at(world, hero, structures, target.position, 120.0, 1.5, 60)
		"e":
			# Ghost Ship: line 300 wide 80, x2.2, attack clock 90, heal 15%.
			if target == null:
				return
			var dir := _direction(hero, target)
			if dir == Vector2.ZERO:
				return
			_line(world, hero, structures, dir, 300.0, 80.0, 2.2, 90)
			_heal(hero, 0.15)
		"r":
			# Torrent: AOE 200 on the target (hero when there is none), x3.0,
			# attack clock 120 and a 20% heal.
			var center := target.position if target != null else hero.position
			_radial_at(world, hero, structures, center, 200.0, 3.0, 120)
			_heal(hero, 0.20)


static func _gravewake(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Anchor: line 200 wide 60, x1.4 and slow 0.5 for 180.
			if target == null:
				return
			var dir := _direction(hero, target)
			if dir == Vector2.ZERO:
				return
			_line(world, hero, structures, dir, 200.0, 60.0, 1.4, 0, 0.5, 180)
		"w":
			# Tide: AOE 120 on the target (hero when there is none), x1.3, clock 60.
			var center := target.position if target != null else hero.position
			_radial_at(world, hero, structures, center, 120.0, 1.3, 60)
		"e":
			# Shell: defense flag + 300 ticks and a 12% heal. Source Hero has no
			# mitigation consumer for defense_boost: never invent damage reduction.
			hero.defense_timer = 300
			_heal(hero, 0.12)
		"r":
			# Ravage: AOE 200, x2.0, slow 0.5 for 180 and a 10% heal.
			_radial(world, hero, structures, 200.0, 2.0, 0, 0.5, 180)
			_heal(hero, 0.10)


static func _syrentha(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Riptide: line 250 wide 70, x1.3 and slow 0.5 for 180.
			if target == null:
				return
			var dir := _direction(hero, target)
			if dir == Vector2.ZERO:
				return
			_line(world, hero, structures, dir, 250.0, 70.0, 1.3, 0, 0.5, 180)
		"w":
			# Song: AOE 150, x1.0, attack clock 120 and slow 0.7 for 240.
			_radial(world, hero, structures, 150.0, 1.0, 120, 0.7, 240)
		"e":
			# Mirror: rage 360 with damage 1.4x the RAW catalog value, heal 12%.
			hero.rage_timer = 360
			hero.damage = int(hero.settings().catalog_damage * 1.4)
			_heal(hero, 0.12)
		"r":
			# Siren: AOE 220, x2.2, attack clock 150 and a 10% heal.
			_radial(world, hero, structures, 220.0, 2.2, 150)
			_heal(hero, 0.10)


static func _thalgryn(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Waveform: line 250 wide 50 x1.6, then the hero surges up to 200px
			# along the SAME direction measured before the damage.
			if target == null:
				return
			var offset: Vector2 = target.position - hero.position
			if offset == Vector2.ZERO:
				return
			var dir := offset.normalized()
			_line(world, hero, structures, dir, 250.0, 50.0, 1.6)
			hero.position += dir * minf(offset.length(), 200.0)
		"w":
			# Adaptive: target x2.0 plus a 60px splash x0.7 around the target
			# that never re-hits the target itself.
			if target == null:
				return
			Common.hit(world, hero, target, 2.0)
			_splash_at(world, hero, structures, target, 60.0, 0.7)
		"e":
			# Morph: rage 300 with damage 1.35x the RAW catalog value, heal 14%.
			hero.rage_timer = 300
			hero.damage = int(hero.settings().catalog_damage * 1.35)
			_heal(hero, 0.14)
		"r":
			# Replicate: AOE 200, x2.0, slow 0.4 for 180 and a 10% heal.
			_radial(world, hero, structures, 200.0, 2.0, 0, 0.4, 180)
			_heal(hero, 0.10)


static func tick(_world, hero: HeroState, _structures: Array) -> void:
	# Source BossHeroSkills.update_timers: rage expires and resets damage to the
	# RAW catalog value (not the level-adjusted damage); defense only decays,
	# it never mitigates anything in source Hero.take_damage.
	if hero.rage_timer > 0:
		hero.rage_timer -= 1
		if hero.rage_timer == 0:
			hero.damage = hero.settings().catalog_damage
	if hero.defense_timer > 0:
		hero.defense_timer -= 1


static func _direction(hero: HeroState, target) -> Vector2:
	var offset: Vector2 = target.position - hero.position
	return Vector2.ZERO if offset == Vector2.ZERO else offset.normalized()


static func _radial(
	world,
	hero: HeroState,
	structures: Array,
	radius: float,
	mult: float,
	stun := 0,
	slow_amount := 0.0,
	slow_ticks := 0
) -> void:
	_radial_at(world, hero, structures, hero.position, radius, mult, stun, slow_amount, slow_ticks)


static func _radial_at(
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
			if slow_ticks > 0:
				world.apply_slow(enemy.id, slow_amount, slow_ticks)


static func _line(
	world,
	hero: HeroState,
	structures: Array,
	dir: Vector2,
	max_range: float,
	width: float,
	mult: float,
	stun := 0,
	slow_amount := 0.0,
	slow_ticks := 0
) -> void:
	for enemy in Common.enemies(world, hero, structures):
		var offset: Vector2 = enemy.position - hero.position
		var proj: float = offset.dot(dir)
		if proj > 0 and proj < max_range:
			var perp: float = absf(offset.x * -dir.y + offset.y * dir.x)
			if perp < width:
				Common.hit(world, hero, enemy, mult)
				if stun > 0:
					Common.stun(enemy, stun)
				if slow_ticks > 0:
					world.apply_slow(enemy.id, slow_amount, slow_ticks)


static func _splash_at(
	world, hero: HeroState, structures: Array, target, radius: float, mult: float
) -> void:
	for enemy in Common.enemies(world, hero, structures):
		if enemy != target and target.position.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, mult)


static func _heal(hero: HeroState, fraction: float) -> void:
	hero.heal_hp(int(hero.max_hp * fraction))
