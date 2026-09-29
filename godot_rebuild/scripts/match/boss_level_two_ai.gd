extends RefCounted
## Layer 8d-2: source smart AI for level-2 bosses.

const BossState = preload("res://scripts/match/boss_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["razak", "khalros", "gorath", "alchemist"]
const RED := 1


static func step(world, boss: BossState, enemies: Array[UnitState], target: UnitState) -> void:
	if boss.boss_type not in IDS or target == null:
		return
	_tick_timers(boss)
	if boss.boss_type == "alchemist":
		_tick_alchemist(boss)
	elif boss.boss_type == "gorath":
		_tick_gorath(boss)
	var distance := boss.position.distance_to(target.position)
	match boss.boss_type:
		"razak":
			_razak(world, boss, enemies, target, distance)
		"khalros":
			_khalros(world, boss, enemies, target, distance)
		"gorath":
			_gorath(world, boss, enemies, target, distance)
		"alchemist":
			_alchemist(world, boss, enemies, target, distance)


static func _tick_timers(boss: BossState) -> void:
	for key in ["q_timer", "w_timer", "e_timer", "r_timer"]:
		if int(boss.get(key)) > 0:
			boss.set(key, int(boss.get(key)) - 1)
	if boss.active_skill_timer > 0:
		boss.active_skill_timer -= 1
		if boss.active_skill_timer <= 0:
			boss.active_skill = ""


static func _razak(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count(enemies, boss.position, 180.0)
	if nearby >= 3 and boss.r_timer == 0:
		boss.r_timer = _cooldown(boss, "skill_r_cooldown", 520)
		_activate(boss, "r", 90)
		_aoe(world, boss, enemies, boss.position, 180.0, _damage(boss, "skill_r_damage", 340))
	elif distance > 120.0 and distance < 260.0 and boss.e_timer == 0:
		boss.e_timer = _cooldown(boss, "skill_e_cooldown", 280)
		_activate(boss, "e", 35)
		_dash_to(boss, target, 40.0, 110.0, 50.0)
		_aoe(world, boss, enemies, boss.position, 80.0, _damage(boss, "skill_e_damage", 180))
	elif distance <= 220.0 and boss.w_timer == 0:
		boss.w_timer = _cooldown(boss, "skill_w_cooldown", 260)
		_activate(boss, "w", 50)
		var victims := _aoe(
			world, boss, enemies, target.position, 95.0, _damage(boss, "skill_w_damage", 220)
		)
		for victim in victims:
			_hold_attack(victim, 45)
	elif distance <= 260.0 and boss.q_timer == 0:
		boss.q_timer = _cooldown(boss, "skill_q_cooldown", 220)
		_activate(boss, "q", 40)
		var victims := _aoe(
			world, boss, enemies, target.position, 75.0, _damage(boss, "skill_q_damage", 160)
		)
		for victim in victims:
			world.apply_slow(victim.id, 0.35, 120)


static func _khalros(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count(enemies, boss.position, 140.0)
	var hp_ratio := boss.hp / float(boss.max_hp)
	if nearby >= 3 and boss.r_timer == 0:
		boss.r_timer = _cooldown(boss, "skill_r_cooldown", 560)
		_activate(boss, "r", 70)
		var victims := _aoe(
			world, boss, enemies, boss.position, 200.0, _damage(boss, "skill_r_damage", 380)
		)
		for victim in victims:
			_hold_attack(victim, 30)
	elif hp_ratio < 0.7 and boss.w_timer == 0:
		boss.w_timer = _cooldown(boss, "skill_w_cooldown", 300)
		_activate(boss, "w", 60)
		var victims := _aoe(
			world, boss, enemies, boss.position, 120.0, _damage(boss, "skill_w_damage", 160)
		)
		for victim in victims:
			world.apply_slow(victim.id, 0.5, 90)
		boss.hp = minf(float(boss.max_hp), boss.hp + int(float(boss.max_hp) * 0.08))
	elif distance > 110.0 and boss.e_timer == 0:
		boss.e_timer = _cooldown(boss, "skill_e_cooldown", 280)
		_activate(boss, "e", 45)
		_dash_to(boss, target, 35.0, 90.0, 45.0)
		var victims := _aoe(
			world, boss, enemies, boss.position, 85.0, _damage(boss, "skill_e_damage", 220)
		)
		for victim in victims:
			_hold_attack(victim, 40)
	elif distance <= 260.0 and boss.q_timer == 0:
		boss.q_timer = _cooldown(boss, "skill_q_cooldown", 220)
		_activate(boss, "q", 50)
		_aoe(world, boss, enemies, target.position, 70.0, _damage(boss, "skill_q_damage", 210))


static func _gorath(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count(enemies, boss.position, 150.0)
	var hp_ratio := boss.hp / float(boss.max_hp)
	var low_target := target.alive and target.hp / _max_hp(target) < 0.35
	if low_target and boss.r_timer == 0:
		_gorath_r(world, boss, enemies, target)
	elif not boss.rage_active and hp_ratio < 0.7 and boss.q_timer == 0:
		boss.q_timer = _cooldown(boss, "skill_q_cooldown", 420)
		boss.rage_active = true
		boss.rage_timer = 300
		boss.damage = int(float(boss.base_damage) * 1.4)
		boss.speed_px_per_tick = boss.base_speed * 1.2
		boss.hp = minf(float(boss.max_hp), boss.hp + int(float(boss.max_hp) * 0.08))
		_activate(boss, "q", 90)
	elif nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = _cooldown(boss, "skill_w_cooldown", 240)
		_activate(boss, "w", 60)
		var victims := _aoe(
			world, boss, enemies, boss.position, 150.0, _damage(boss, "skill_w_damage", 210)
		)
		for victim in victims:
			_hold_attack(victim, 50)
	elif distance > 90.0 and boss.e_timer == 0:
		boss.e_timer = _cooldown(boss, "skill_e_cooldown", 260)
		_activate(boss, "e", 35)
		_dash_to(boss, target, 45.0, 120.0, 35.0)
		_aoe(world, boss, enemies, boss.position, 85.0, _damage(boss, "skill_e_damage", 190))
	elif hp_ratio < 0.45 and boss.r_timer == 0:
		_gorath_r(world, boss, enemies, target)


static func _gorath_r(world, boss: BossState, enemies: Array[UnitState], target: UnitState) -> void:
	boss.r_timer = _cooldown(boss, "skill_r_cooldown", 560)
	_activate(boss, "r", 90)
	var damage := _damage(boss, "skill_r_damage", 420)
	_aoe(world, boss, enemies, boss.position, 190.0, damage)
	if target.alive:
		_hit(world, boss, target, int(damage / 2.0))


static func _tick_gorath(boss: BossState) -> void:
	if boss.rage_active:
		boss.rage_timer -= 1
		if boss.rage_timer <= 0:
			boss.rage_active = false
			boss.damage = boss.base_damage
			boss.speed_px_per_tick = boss.base_speed


static func _alchemist(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count(enemies, boss.position, 180.0)
	var hp_ratio := boss.hp / float(boss.max_hp)
	if hp_ratio < 0.4 and nearby >= 3 and boss.r_timer == 0:
		boss.r_timer = 720
		_activate(boss, "r", 90)
		var before := _alive_count(enemies)
		_aoe(world, boss, enemies, boss.position, 200.0, _damage(boss, "skill_r_damage", 550))
		var kills := before - _alive_count(enemies)
		if kills > 0:
			boss.hp = minf(float(boss.max_hp), boss.hp + kills * 100)
	elif hp_ratio < 0.6 and not boss.rage_active and boss.e_timer == 0:
		boss.e_timer = 480
		boss.rage_active = true
		boss.rage_timer = 360
		boss.damage = int(float(boss.damage) * 1.5)
		boss.hp = minf(float(boss.max_hp), boss.hp + int(float(boss.max_hp) * 0.15))
		_activate(boss, "e", 60)
	elif nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = 300
		_activate(boss, "w", 60)
		var victims := _aoe(
			world, boss, enemies, target.position, 100.0, _damage(boss, "skill_w_damage", 320)
		)
		for victim in victims:
			world.apply_slow(victim.id, 0.5, 180)
	elif distance < 200.0 and boss.q_timer == 0:
		boss.q_timer = 210
		_activate(boss, "q", 40)
		_hit(world, boss, target, _damage(boss, "skill_q_damage", 220))


static func _tick_alchemist(boss: BossState) -> void:
	if boss.rage_active:
		boss.rage_timer -= 1
		if boss.rage_timer <= 0:
			boss.rage_active = false


static func _activate(boss: BossState, key: String, duration: int) -> void:
	boss.active_skill = key
	boss.active_skill_timer = duration


static func _cooldown(boss: BossState, key: String, fallback: int) -> int:
	return int(boss.skills.get(key, fallback))


static func _damage(boss: BossState, key: String, fallback: int) -> int:
	return boss.smart_skill_damage(key, fallback)


static func _count(enemies: Array[UnitState], origin: Vector2, radius: float) -> int:
	var count := 0
	for enemy in enemies:
		if origin.distance_to(enemy.position) <= radius:
			count += 1
	return count


static func _alive_count(enemies: Array[UnitState]) -> int:
	var count := 0
	for enemy in enemies:
		if enemy.alive:
			count += 1
	return count


static func _aoe(
	world, boss: BossState, enemies: Array[UnitState], origin: Vector2, radius: float, damage: int
) -> Array[UnitState]:
	var victims: Array[UnitState] = []
	for enemy in enemies:
		if enemy.alive and origin.distance_to(enemy.position) <= radius:
			_hit(world, boss, enemy, damage)
			victims.append(enemy)
	return victims


static func _dash_to(
	boss: BossState, target: UnitState, minimum: float, maximum: float, stop_before: float
) -> void:
	var offset := target.position - boss.position
	if offset.length() <= 0.0:
		return
	var distance := minf(maximum, maxf(minimum, offset.length() - stop_before))
	boss.position += offset.normalized() * distance
	boss.direction = 1 if offset.x > 0.0 else -1
	boss.facing = float(boss.direction)


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
