extends RefCounted
## Exact BossHeroSkills._generic_cast target gate; not a kit or a fallback.
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key):
		return false
	var reach := maxi(int(hero.skill_range), 140)
	var nearby = null
	var best := INF
	for enemy in Common.enemies(world, hero, structures):
		var distance := hero.position.distance_to(enemy.position)
		if distance <= reach and distance < best:
			nearby = enemy
			best = distance
	if nearby == null:
		return false
	var target = Common.current(world, hero)
	if target == null or hero.position.distance_to(target.position) > reach:
		if nearby in world.units:
			hero.target_id = nearby.id
			hero.target_struct = null
		else:
			hero.target_id = -1
			hero.target_struct = nearby
	return true
