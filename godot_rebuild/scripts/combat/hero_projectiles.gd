extends RefCounted
## Source Hero's ranged basic-attack homing arrows (9.5px/tick; 6 per hero).
## Skill arrows are visual-only and never add a second gameplay hit.

const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")


static func spawn(
	shots: Array[Dictionary], hero: HeroState, target: UnitState, damage: int
) -> void:
	# Source cap of six PER hero; evict oldest basic arrow if full.
	var own: Array[int] = []
	for index in range(shots.size()):
		if shots[index].source_id == hero.id:
			own.append(index)
	if own.size() >= 6:
		shots.remove_at(own[0])
	var origin := hero.position + Vector2(0, -5)
	shots.append(
		{
			"source_id": hero.id,
			"target_id": target.id,
			"team": hero.team,
			"school": hero.dmg_school,
			"damage": damage,
			"position": origin,
			"origin": origin,
			"last_target": target.position,
			"age": 0,
			"impact": false,
			"active": true
		}
	)


static func tick(world, hero: HeroState, shots: Array[Dictionary]) -> Array[Dictionary]:
	for shot in shots:
		if not shot.active or shot.source_id != hero.id:
			continue
		var target = world.get_unit(shot.target_id)
		var target_dead: bool = target == null or not target.alive
		var aim: Vector2 = shot.last_target
		if not target_dead:
			aim = target.position
			shot.last_target = aim
		shot.age += 1
		if shot.age > 72 or shot.position.distance_to(shot.origin) > 380.0:
			shot.active = false
			continue
		if target_dead and shot.age > 36:
			shot.active = false
			continue
		var offset: Vector2 = aim - shot.position
		if offset.length() < 14.5:  # speed 9.5 + 5px hit window
			if shot.impact:
				shot.active = false
				continue
			shot.position = aim
			shot.impact = true
			if not target_dead:
				world._deliver_hit(
					hero.id, hero.team, target, shot.damage, shot.school, aim, "projectile"
				)
		elif offset.length() > 0:
			shot.position += offset.normalized() * 9.5
	var active: Array[Dictionary] = []
	for shot in shots:
		if shot.active:
			active.append(shot)
	return active
