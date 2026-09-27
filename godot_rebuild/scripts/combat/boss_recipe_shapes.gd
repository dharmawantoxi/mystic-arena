extends RefCounted
## Geometry primitives lifted 1:1 from the source recipe bodies.
## Every shape here is a literal transcription of one source loop; none of them
## decides what a hero's numbers are. Each call site passes the source values
## and the source ordering, and the source oracle proves the result per ID.
## NEVER a fallback or a generic kit: heroes without a ported recipe stay out.
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")


## Source 'for e in enemies: if dist <= radius' loop. Damage, slow and stun all
## share ONE pass over the pre-filtered enemy list, exactly like the source
## body, so a lethal hit still applies the source slow and stun to that unit
## instead of skipping it on a second alive-only sweep.
static func burst(
	world,
	hero: HeroState,
	structures: Array,
	origin: Vector2,
	radius: float,
	mult: float,
	slow := 0.0,
	slow_ticks := 0,
	stun_ticks := 0
) -> void:
	for enemy in Common.enemies(world, hero, structures):
		if origin.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, mult)
			if slow > 0.0:
				world.apply_slow(enemy.id, slow, slow_ticks)
			if stun_ticks > 0:
				Common.stun(enemy, stun_ticks)


## Source line aimed through the live target, with 'dist == 0 -> return'.
## Returns the fired unit direction, or ZERO when the source returned early,
## so the caller can keep its previous direction exactly like the source does.
static func line(
	world,
	hero: HeroState,
	structures: Array,
	target,
	reach: float,
	width: float,
	mult: float,
	slow := 0.0,
	slow_ticks := 0,
	stun_ticks := 0
) -> Vector2:
	if target == null:
		return Vector2.ZERO
	var delta: Vector2 = target.position - hero.position
	if delta == Vector2.ZERO:
		return Vector2.ZERO
	var direction := delta / delta.length()
	for enemy in Common.enemies(world, hero, structures):
		var offset: Vector2 = enemy.position - hero.position
		var projection := offset.dot(direction)
		if projection > 0.0 and projection < reach and absf(offset.cross(direction)) < width:
			Common.hit(world, hero, enemy, mult)
			if slow > 0.0:
				world.apply_slow(enemy.id, slow, slow_ticks)
			if stun_ticks > 0:
				Common.stun(enemy, stun_ticks)
	return direction


## Source 'math.hypot(...) or 1.0' beam: a zero-length aim points nowhere and
## therefore hits nobody, which is a real source quirk, not a guard.
static func beam(
	world,
	hero: HeroState,
	structures: Array,
	origin: Vector2,
	reach: float,
	width: float,
	mult: float,
	slow := 0.0,
	slow_ticks := 0,
	stun_ticks := 0
) -> void:
	var delta: Vector2 = origin - hero.position
	var span := delta.length()
	if span == 0.0:
		span = 1.0
	var direction := delta / span
	for enemy in Common.enemies(world, hero, structures):
		var offset: Vector2 = enemy.position - hero.position
		var projection := offset.dot(direction)
		if projection > 0.0 and projection < reach and absf(offset.cross(direction)) < width:
			Common.hit(world, hero, enemy, mult)
			if slow > 0.0:
				world.apply_slow(enemy.id, slow, slow_ticks)
			if stun_ticks > 0:
				Common.stun(enemy, stun_ticks)


## Source widening cone: the allowed half width grows along the reach, so the
## shape is narrow at the caster and widest at max range. Same early return as
## the line shape, because the source guards this recipe the same way.
static func cone(
	world,
	hero: HeroState,
	structures: Array,
	target,
	reach: float,
	cone_width: float,
	mult: float,
	stun_ticks := 0
) -> void:
	if target == null:
		return
	var delta: Vector2 = target.position - hero.position
	if delta == Vector2.ZERO:
		return
	var direction := delta / delta.length()
	for enemy in Common.enemies(world, hero, structures):
		var offset: Vector2 = enemy.position - hero.position
		var projection := offset.dot(direction)
		if projection <= 0.0 or projection >= reach:
			continue
		if absf(offset.cross(direction)) < cone_width * (0.3 + projection / reach * 0.7):
			Common.hit(world, hero, enemy, mult)
			if stun_ticks > 0:
				Common.stun(enemy, stun_ticks)


## Source 'h.target.take_damage(...)' guarded on a live target, with the
## source slow and stun applied to that same target.
static func single(
	world, hero: HeroState, target, mult: float, slow := 0.0, slow_ticks := 0, stun_ticks := 0
) -> void:
	if target == null:
		return
	Common.hit(world, hero, target, mult)
	if slow > 0.0:
		world.apply_slow(target.id, slow, slow_ticks)
	if stun_ticks > 0:
		Common.stun(target, stun_ticks)


## Source 'h.hp = min(h.max_hp, h.hp + amount)': cap first, then the real HP
## setter applies anti-heal to the gain.
static func heal(hero: HeroState, amount: float) -> void:
	hero.heal_hp(amount)
