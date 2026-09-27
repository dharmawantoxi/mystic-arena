extends RefCounted
## Source hero_skills.ThorneSkills, empty inventory. Only Thorne dispatches here.
## world is the real MinionBattle/PrototypeBattle, not a parallel combat simulation.

const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const HeroDefinition = preload("res://scripts/data/hero_definition.gd")


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
			# Viscous Nose: full 60px cone (strict angle < 30 degrees),
			# not a generic radial Kaizen Q. Slows surviving units only.
			for enemy in _enemies(world, hero, structures):
				var delta: Vector2 = enemy.position - hero.position
				if delta.length() > 60.0:
					continue
				var angle := atan2(delta.y, delta.x)
				var face := 0.0 if hero.facing > 0 else PI
				var diff := absf(angle - face)
				if diff > PI:
					diff = TAU - diff
				if diff < PI / 6.0:
					world._deliver_hit(
						hero.id,
						hero.team,
						enemy,
						int(hero.skill_damage() * 0.8),
						hero.dmg_school,
						hero.position
					)
					if enemy is UnitState:
						world.apply_slow(enemy.id, 0.4, 180)
			hero.viscous_timer = 30
			hero.skill_timer = hero.skill_cd_max
			hero.active_skill_timer = 40
		"w":
			hero.bristleback_timer = 240
			world._deal_hero_aoe(
				hero, hero.position, 60.0, int(hero.skill_damage() * 0.5), structures
			)
			hero.hp = minf(hero.max_hp, hero.hp + 20)
			hero.w_cooldown = hero.w_cooldown_max
			hero.active_skill_timer = 100
		"e":
			hero.quill_timer = 30
			world._deal_hero_aoe(
				hero, hero.position, 100.0, int(hero.skill_damage() * 1.2), structures
			)
			hero.e_cooldown = hero.e_cooldown_max
			hero.active_skill_timer = 60
		"r":
			hero.warpath_timer = 300
			hero.warpath_original_attack_cd = hero.attack_cd_base
			hero.damage = int(hero.damage * 1.5)
			hero.attack_cd_base = maxi(15, int(hero.attack_cd_base / 1.5))
			world._deal_hero_aoe(
				hero, hero.position, 120.0, int(hero.skill_damage() * 1.5), structures
			)
			hero.hp = minf(hero.max_hp, hero.hp + 50)
			hero.r_cooldown = hero.r_cooldown_max
			hero.active_skill_timer = 120
	hero.active_skill = key
	return true


static func tick(hero: HeroState) -> void:
	if hero.viscous_timer > 0:
		hero.viscous_timer -= 1
	if hero.bristleback_timer > 0:
		hero.bristleback_timer -= 1
	if hero.quill_timer > 0:
		hero.quill_timer -= 1
	if hero.warpath_timer > 0:
		hero.warpath_timer -= 1
		if hero.warpath_timer == 0:
			# Source resets from CURRENT level, not snapshot damage if upgraded mid-buff.
			var level: Dictionary = HeroDefinition.level_data(hero.level)
			hero.damage = int(hero.base_damage * float(level["dmg_mult"]))
			hero.attack_cd_base = hero.warpath_original_attack_cd


static func _enemies(world, hero: HeroState, structures: Array) -> Array[UnitState]:
	var result: Array[UnitState] = []
	for unit in world.units:
		if unit.alive and unit.team != hero.team:
			result.append(unit)
	for entry in structures:
		var structure := entry as StructureState
		if structure != null and structure.alive and structure.team != hero.team:
			result.append(structure)
	return result
