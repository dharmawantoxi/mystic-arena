# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8d: source Boss smart ability dispatch for the level-1 boss roster.
## The generic Boss ability path is also retained for boss IDs without a native
## recipe in this active level. Entrance/enrage clocks and presentation stay in
## later layers.

const BossState = preload("res://scripts/match/boss_state.gd")
const Damage = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")


static func tick(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, target_distance: float
) -> void:
	if boss == null or not boss.alive:
		return
	# Boss.update checks the true-boss heal before it looks for a target.
	_heal_ability_if_ready(boss)
	if target == null:
		return
	_tick_smart_clocks(world, boss, target)
	match boss.boss_type:
		"gornak":
			_gornak(world, boss, enemies, target, target_distance)
		"morgath":
			_morgath(world, boss, enemies, target, target_distance)
		"drakar":
			_drakar(world, boss, enemies, target, target_distance)
		"abaddon":
			_abaddon(world, boss, enemies, target, target_distance)
		_:
			_generic(world, boss, enemies)


static func _tick_smart_clocks(world, boss: BossState, target: UnitState) -> void:
	if boss.q_timer > 0:
		boss.q_timer -= 1
	if boss.w_timer > 0:
		boss.w_timer -= 1
	if boss.e_timer > 0:
		boss.e_timer -= 1
	if boss.r_timer > 0:
		boss.r_timer -= 1
	if boss.active_skill_timer > 0:
		boss.active_skill_timer -= 1
		if boss.active_skill_timer <= 0:
			boss.active_skill = ""
	if boss.rage_active:
		boss.rage_timer -= 1
		if boss.rage_timer <= 0:
			boss.rage_active = false
			boss.damage = _source_damage(boss)
	if boss.defense_timer > 0:
		boss.defense_timer -= 1
		if boss.defense_timer <= 0:
			boss.defense_boost = false
	if boss.boss_type == "morgath":
		_tick_morgath_effects(world, boss, target)


static func _tick_morgath_effects(world, boss: BossState, target: UnitState) -> void:
	if boss.flux_active_timer > 0:
		boss.flux_active_timer -= 1
		if boss.flux_active_timer % 30 == 0:
			var flux_target: UnitState = world.get_unit(boss.flux_target_id)
			if flux_target != null and flux_target.alive:
				_hit(world, boss, flux_target, int(_skill_damage(boss, boss.skill_w_damage) / 4.0))
				_slow(flux_target, 0.4, 60)
	if boss.clones_active_timer > 0:
		boss.clones_active_timer -= 1
		if boss.clones_active_timer % 40 == 0 and target != null and target.alive:
			_hit(world, boss, target, int(float(boss.damage) * 0.5))


static func _heal_ability_if_ready(boss: BossState) -> void:
	if (
		boss.boss_class == "true"
		and boss.ability2_cooldown > 0
		and boss.ability2_timer == 0
		and boss.hp < boss.max_hp * 0.3
	):
		boss.ability2_timer = boss.ability2_cooldown
		var heal_amount := int(boss.max_hp * boss.ability2_heal_pct)
		boss.hp = minf(float(boss.max_hp), boss.hp + heal_amount)


static func _generic(world, boss: BossState, enemies: Array[UnitState]) -> void:
	# Exact source _use_ability fallback: one AOE, then the generic cooldown.
	if boss.ability_timer != 0:
		return
	boss.ability_timer = boss.ability_cooldown
	boss.ability_active = true
	boss.ability_active_timer = 60
	for enemy in enemies:
		if boss.position.distance_to(enemy.position) <= boss.ability_range:
			_hit(world, boss, enemy, boss.eff_ability_damage())
			_attack_lock(enemy, 60)


static func _gornak(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 150.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		boss.mana_void_origin = boss.position
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if distance > 120.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 25)
		var delta := target.position - boss.position
		var length := delta.length()
		if length > 0.0:
			boss.blink_from = boss.position
			boss.position += delta / length * maxf(0.0, length - 60.0)
			boss.blink_to = boss.position
		return
	if nearby_count >= 3 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
				_attack_lock(enemy, 60)
		return
	if distance < 200.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _morgath(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var close_count := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.5 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 60)
		boss.clones_active_timer = 480
		boss.clones_positions = [Vector2(-60, 0), Vector2(60, 0)]
		_heal(boss, 0.15)
		return
	if close_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 90.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
				_attack_lock(enemy, 45)
		_heal(boss, 0.08)
		return
	if distance < 300.0 and boss.w_timer == 0 and boss.flux_active_timer <= 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		boss.flux_target_id = target.id
		boss.flux_active_timer = 240
		_hit(world, boss, target, int(_skill_damage(boss, boss.skill_w_damage) / 2.0))
		_slow(target, 0.5, 240)
		return
	if distance < 350.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _drakar(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 120.0)
	var low_hp_target := false
	var target_max := _max_hp(target)
	if target.alive and target.hp / maxf(1.0, target_max) < 0.3:
		low_hp_target = true
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if low_hp_target and distance < 100.0 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 60)
		var damage := _skill_damage(boss, boss.skill_r_damage)
		if target.hp / maxf(1.0, target_max) < 0.3:
			damage *= 2
			boss.r_timer = 120
		_hit(world, boss, target, damage)
		return
	if hp_ratio < 0.4 and not boss.rage_active and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 90)
		boss.rage_active = true
		boss.rage_timer = 300
		boss.damage = int(float(_source_damage(boss)) * 1.5)
		_heal(boss, 0.1)
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return
	if hp_ratio < 0.6 and not boss.defense_boost and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		boss.defense_boost = true
		boss.defense_timer = 180
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 120.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
				_attack_lock(enemy, 30)


static func _abaddon(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 150.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.3 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		_heal(boss, float(boss.skill_w_shield) / maxf(1.0, float(boss.max_hp)))
		return
	if nearby_count >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if distance < 130.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 30)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))
		return
	if distance > 100.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 40)
		var delta := target.position - boss.position
		var length := delta.length()
		if length > 0.0:
			boss.position += delta / length * 80.0
		_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))


static func _set_skill(boss: BossState, key: String, duration: int) -> void:
	boss.active_skill = key
	boss.active_skill_timer = duration


static func _count_near(boss: BossState, enemies: Array[UnitState], radius: float) -> int:
	var result := 0
	for enemy in enemies:
		if boss.position.distance_to(enemy.position) <= radius:
			result += 1
	return result


static func _skill_damage(boss: BossState, base: int) -> int:
	var multiplier := 1.0
	if boss.skill_down_timer > 0:
		multiplier *= maxf(0.0, 1.0 - boss.skill_down_amount)
	multiplier *= boss.dmg_scaling_mult
	if boss.is_enraged:
		multiplier *= 1.25
	return Damage.rounded_like_python(float(base) * multiplier)


static func _source_damage(boss: BossState) -> int:
	var multiplier := 1.0
	if boss.skill_down_timer > 0:
		multiplier *= maxf(0.0, 1.0 - boss.skill_down_amount)
	if boss.is_enraged:
		multiplier *= 1.25
	return Damage.rounded_like_python(float(boss.base_damage) * multiplier)


static func _max_hp(target: UnitState) -> float:
	if target is HeroState:
		return (target as HeroState).max_hp
	return target.definition.max_hp


static func _heal(boss: BossState, fraction: float) -> void:
	boss.hp = minf(float(boss.max_hp), boss.hp + int(float(boss.max_hp) * fraction))


static func _hit(world, boss: BossState, target: UnitState, raw_damage: int) -> void:
	if target == null or not target.alive or raw_damage <= 0:
		return
	var school := "physical" if target is HeroState else "neutral"
	world._deliver_hit(boss.id, boss.team, target, raw_damage, school, boss.position)


static func _slow(target: UnitState, amount: float, duration: int) -> void:
	if target == null or not target.alive or target is StructureState:
		return
	if amount > target.slow_amount or target.slow_timer < duration:
		target.slow_amount = amount
		target.slow_timer = duration


static func _attack_lock(target: UnitState, duration: int) -> void:
	if target == null or not target.alive or target is StructureState:
		return
	if target is HeroState:
		var hero := target as HeroState
		hero.attack_timer = maxi(hero.attack_timer, duration)
	else:
		target.cooldown_ticks = maxi(target.cooldown_ticks, duration)
