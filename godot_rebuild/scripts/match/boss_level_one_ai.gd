extends RefCounted
## Layer 8d-1: live Boss smart AI for level 1 plus the source generic ability.

const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const IDS := ["gornak", "morgath", "drakar", "abaddon"]
const RED := 1


static func step(world, boss: BossState, enemies: Array[UnitState], target: UnitState) -> void:
	if boss.boss_type not in IDS or target == null:
		return
	_tick_skill_timers(boss)
	if boss.boss_type == "morgath":
		_tick_morgath(world, boss, target)
	elif boss.boss_type == "drakar":
		_tick_drakar(boss)
	var distance := boss.position.distance_to(target.position)
	match boss.boss_type:
		"gornak":
			_gornak(world, boss, enemies, target, distance)
		"morgath":
			_morgath(world, boss, enemies, target, distance)
		"drakar":
			_drakar(world, boss, enemies, target, distance)
		"abaddon":
			_abaddon(world, boss, enemies, target, distance)


static func generic_ability(world, boss: BossState, enemies: Array[UnitState]) -> void:
	boss.ability_timer = boss.ability_cooldown
	boss.ability_active = true
	boss.ability_active_timer = 60
	for enemy in enemies:
		if enemy.alive and boss.position.distance_to(enemy.position) <= boss.ability_range:
			_hit(world, boss, enemy, boss.eff_ability_damage())
			_hold_attack(enemy, 60)


static func heal_ability(boss: BossState) -> void:
	if boss.ability2_cooldown <= 0:
		return
	boss.ability2_timer = boss.ability2_cooldown
	var heal := int(float(boss.max_hp) * boss.ability2_heal_pct)
	boss.hp = minf(float(boss.max_hp), boss.hp + heal)


static func _tick_skill_timers(boss: BossState) -> void:
	for key in ["q_timer", "w_timer", "e_timer", "r_timer"]:
		if int(boss.get(key)) > 0:
			boss.set(key, int(boss.get(key)) - 1)
	if boss.active_skill_timer > 0:
		boss.active_skill_timer -= 1
		if boss.active_skill_timer <= 0:
			boss.active_skill = ""


static func _gornak(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count(enemies, boss.position, 150.0)
	if boss.hp / float(boss.max_hp) < 0.4 and boss.r_timer == 0:
		boss.r_timer = 540
		_activate(boss, "r", 90)
		_aoe(world, boss, enemies, 180.0, boss.smart_skill_damage("skill_r_damage", 380))
	elif distance > 120.0 and boss.w_timer == 0:
		boss.w_timer = 240
		_activate(boss, "w", 25)
		var offset := target.position - boss.position
		if offset.length() > 0.0:
			boss.position += offset.normalized() * maxf(0.0, offset.length() - 60.0)
	elif nearby >= 3 and boss.e_timer == 0:
		boss.e_timer = 300
		_activate(boss, "e", 60)
		var victims := _aoe(
			world, boss, enemies, 100.0, boss.smart_skill_damage("skill_e_damage", 150)
		)
		for victim in victims:
			_hold_attack(victim, 60)
	elif distance < 200.0 and boss.q_timer == 0:
		boss.q_timer = 180
		_activate(boss, "q", 40)
		_hit(world, boss, target, boss.smart_skill_damage("skill_q_damage", 180))


static func _morgath(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count(enemies, boss.position, 200.0)
	if boss.hp / float(boss.max_hp) < 0.5 and boss.r_timer == 0:
		boss.r_timer = 720
		boss.clones_active_timer = 480
		boss.hp = minf(float(boss.max_hp), boss.hp + int(float(boss.max_hp) * 0.15))
		_activate(boss, "r", 60)
	elif nearby >= 2 and boss.e_timer == 0:
		boss.e_timer = 360
		var victims := _aoe(
			world, boss, enemies, 90.0, boss.smart_skill_damage("skill_e_damage", 100)
		)
		for victim in victims:
			_hold_attack(victim, 45)
		boss.hp = minf(float(boss.max_hp), boss.hp + int(float(boss.max_hp) * 0.08))
		_activate(boss, "e", 90)
	elif distance < 300.0 and boss.w_timer == 0 and boss.flux_active_timer <= 0:
		boss.w_timer = 300
		boss.flux_target_id = target.id
		boss.flux_active_timer = 240
		_hit(world, boss, target, int(boss.smart_skill_damage("skill_w_damage", 150) / 2.0))
		world.apply_slow(target.id, 0.5, 240)
		_activate(boss, "w", 40)
	elif distance < 350.0 and boss.q_timer == 0:
		boss.q_timer = 200
		_hit(world, boss, target, boss.smart_skill_damage("skill_q_damage", 200))
		_activate(boss, "q", 50)


static func _tick_morgath(world, boss: BossState, target: UnitState) -> void:
	if boss.flux_active_timer > 0:
		boss.flux_active_timer -= 1
		if boss.flux_active_timer % 30 == 0:
			var flux_target: UnitState = world.get_unit(boss.flux_target_id)
			if flux_target != null and flux_target.alive:
				_hit(
					world,
					boss,
					flux_target,
					int(boss.smart_skill_damage("skill_w_damage", 150) / 4.0)
				)
				world.apply_slow(flux_target.id, 0.4, 60)
	if boss.clones_active_timer > 0:
		boss.clones_active_timer -= 1
		if boss.clones_active_timer % 40 == 0 and target.alive:
			_hit(world, boss, target, int(float(boss.damage) * 0.5))


static func _drakar(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var target_ratio := target.hp / _max_hp(target)
	var hp_ratio := boss.hp / float(boss.max_hp)
	var nearby := _count(enemies, boss.position, 120.0)
	if target_ratio < 0.3 and distance < 100.0 and boss.r_timer == 0:
		boss.r_timer = 120
		_activate(boss, "r", 60)
		_hit(world, boss, target, boss.smart_skill_damage("skill_r_damage", 450) * 2)
	elif hp_ratio < 0.4 and not boss.rage_active and boss.q_timer == 0:
		boss.q_timer = 420
		boss.rage_active = true
		boss.rage_timer = 300
		boss.damage = int(float(boss.base_damage) * 1.5)
		boss.hp = minf(float(boss.max_hp), boss.hp + int(float(boss.max_hp) * 0.1))
		_activate(boss, "q", 90)
	elif nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = 240
		_activate(boss, "w", 45)
		_aoe(world, boss, enemies, 100.0, boss.smart_skill_damage("skill_w_damage", 220))
	elif hp_ratio < 0.6 and not boss.defense_boost and boss.e_timer == 0:
		boss.e_timer = 360
		boss.defense_boost = true
		boss.defense_timer = 180
		var victims := _aoe(
			world, boss, enemies, 120.0, boss.smart_skill_damage("skill_e_damage", 150)
		)
		for victim in victims:
			_hold_attack(victim, 30)
		_activate(boss, "e", 60)


static func _tick_drakar(boss: BossState) -> void:
	if boss.rage_active:
		boss.rage_timer -= 1
		if boss.rage_timer <= 0:
			boss.rage_active = false
			boss.damage = boss.base_damage
	if boss.defense_boost:
		boss.defense_timer -= 1
		if boss.defense_timer <= 0:
			boss.defense_boost = false


static func _abaddon(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count(enemies, boss.position, 150.0)
	if boss.hp / float(boss.max_hp) < 0.3 and boss.w_timer == 0:
		boss.w_timer = 360
		_aoe(world, boss, enemies, 100.0, boss.smart_skill_damage("skill_w_damage", 300))
		boss.hp = minf(float(boss.max_hp), boss.hp + int(boss.skills.get("skill_w_shield", 500)))
		_activate(boss, "w", 90)
	elif nearby >= 3 and boss.r_timer == 0:
		boss.r_timer = 600
		_aoe(world, boss, enemies, 180.0, boss.smart_skill_damage("skill_r_damage", 500))
		_activate(boss, "r", 60)
	elif distance < 130.0 and boss.q_timer == 0:
		boss.q_timer = 240
		_hit(world, boss, target, boss.smart_skill_damage("skill_q_damage", 250))
		_activate(boss, "q", 30)
	elif distance > 100.0 and boss.e_timer == 0:
		boss.e_timer = 300
		var offset := target.position - boss.position
		if offset.length() > 0.0:
			boss.position += offset.normalized() * 80.0
		_hit(world, boss, target, boss.smart_skill_damage("skill_e_damage", 200))
		_activate(boss, "e", 40)


static func _activate(boss: BossState, key: String, duration: int) -> void:
	boss.active_skill = key
	boss.active_skill_timer = duration


static func _count(enemies: Array[UnitState], origin: Vector2, radius: float) -> int:
	var result := 0
	for enemy in enemies:
		if origin.distance_to(enemy.position) <= radius:
			result += 1
	return result


static func _aoe(
	world, boss: BossState, enemies: Array[UnitState], radius: float, damage: int
) -> Array[UnitState]:
	var victims: Array[UnitState] = []
	for enemy in enemies:
		if enemy.alive and boss.position.distance_to(enemy.position) <= radius:
			_hit(world, boss, enemy, damage)
			victims.append(enemy)
	return victims


static func _hit(world, boss: BossState, target: UnitState, damage: int) -> void:
	world._deliver_hit(-1, RED, target, damage, "neutral", boss.position)


static func _hold_attack(target: UnitState, duration: int) -> void:
	if target is HeroState:
		(target as HeroState).attack_timer = maxi((target as HeroState).attack_timer, duration)
	else:
		target.cooldown_ticks = maxi(target.cooldown_ticks, duration)


static func _max_hp(target: UnitState) -> float:
	if target is HeroState:
		return maxf(1.0, (target as HeroState).max_hp)
	return maxf(1.0, float(target.definition.max_hp))
