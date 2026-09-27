extends RefCounted
## Port of source GrimjawSkills: persistent Blade Fury, ward, crit and Omnislash.
## Every hit/heal is applied to authoritative world units, never to a receipt roster.

const HeroState = preload("res://scripts/combat/hero_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not world.is_running() or hero == null or not hero.alive:
		return false
	match key:
		"q":
			return hero.skill_timer <= 0 and world._has_q_target(hero, structures)
		"w":
			return hero.w_cooldown <= 0
		"e":
			return hero.e_cooldown <= 0 and world._has_q_target(hero, structures)
		"r":
			return hero.r_cooldown <= 0 and world._has_q_target(hero, structures)
	return false


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	match key:
		"q":
			# Source: no immediate damage. Timer first decrements, hits at
			# 165,150,...,0 (12 hits when enemies remain in 70px).
			hero.blade_fury_timer = 180
			hero.skill_timer = hero.skill_cd_max
			hero.active_skill_timer = 180
		"w":
			hero.heal_ward_timer = 360
			hero.heal_ward_position = hero.position
			hero.hp = minf(hero.max_hp, hero.hp + 30)
			hero.w_cooldown = hero.w_cooldown_max
			hero.active_skill_timer = 90
		"e":
			# Buff is NOT consumed by the next hit; expires after 300 ticks.
			hero.grimjaw_crit_timer = 300
			world._deal_hero_aoe(
				hero, hero.position, 60.0, int(hero.skill_damage() * 1.5), structures
			)
			hero.e_cooldown = hero.e_cooldown_max
			hero.active_skill_timer = 60
		"r":
			hero.omnislash_timer = 90
			var target_id := hero.target_id
			if hero.target_struct != null:
				target_id = hero.target_struct.id
			var target = world.get_unit(target_id)
			if target != null and target.alive:
				hero.omnislash_target_id = target.id
				# Immediate source hit has no source=hero; timed follow-ups do.
				world._deliver_hit(
					-1,
					hero.team,
					target,
					int(hero.skill_damage() * 2.5),
					hero.dmg_school,
					hero.position
				)
			else:
				world._deal_hero_aoe(
					hero, hero.position, 150.0, int(hero.skill_damage() * 2.0), structures
				)
			hero.r_cooldown = hero.r_cooldown_max
			hero.active_skill_timer = 90
	hero.active_skill = key
	return true


static func tick(world, hero: HeroState, structures: Array) -> void:
	if hero.blade_fury_timer > 0:
		hero.blade_fury_timer -= 1
		if hero.blade_fury_timer % 15 == 0:
			world._deal_hero_aoe(
				hero, hero.position, hero.skill_range, hero.skill_damage(), structures
			)
	if hero.heal_ward_timer > 0:
		hero.heal_ward_timer -= 1
		if hero.position.distance_to(hero.heal_ward_position) <= 100.0:
			hero.hp = minf(hero.max_hp, hero.hp + 2)
		for unit in world.units:
			if unit == hero or not unit.alive or unit.team != hero.team:
				continue
			if unit.position.distance_to(hero.heal_ward_position) <= 100.0:
				var limit: float = (
					(unit as HeroState).max_hp if unit is HeroState else unit.definition.max_hp
				)
				unit.hp = minf(limit, unit.hp + 1)
	if hero.omnislash_timer > 0:
		hero.omnislash_timer -= 1
		if hero.omnislash_timer % 8 == 0:
			var locked = world.get_unit(hero.omnislash_target_id)
			if locked != null and locked.alive:
				world._deliver_hit(
					hero.id,
					hero.team,
					locked,
					int(hero.skill_damage() * 0.6),
					hero.dmg_school,
					hero.position
				)
		if hero.omnislash_timer == 0:
			hero.omnislash_target_id = -1
	if hero.grimjaw_crit_timer > 0:
		hero.grimjaw_crit_timer -= 1
