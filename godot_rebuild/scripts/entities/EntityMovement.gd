class_name EntityMovement
extends RefCounted

## Hero/minion/boss movement and targeting from _entity.py.


static func update(model: RefCounted, unit: BattleUnit) -> void:
	if not unit.alive:
		return
	if unit.kind == BattleUnit.Kind.BOSS:
		BossController.update(model, unit)
		return
	unit.anim_time += 1
	unit.pulse += 0.1
	unit.attack_anim_timer = maxi(0, unit.attack_anim_timer - 1)
	unit.hurt_flash_timer = maxi(0, unit.hurt_flash_timer - 1)
	unit.spawn_anim = maxi(0, unit.spawn_anim - 1)
	unit.upgrade_flash = maxi(0, unit.upgrade_flash - 1)
	unit.shoot_flash_timer = maxi(0, unit.shoot_flash_timer - 1)
	unit.active_skill_timer = maxi(0, unit.active_skill_timer - 1)
	if unit.active_skill_timer == 0:
		unit.active_skill = ""
	if unit.status.stun_timer > 0:
		unit.is_moving = false
		return
	match unit.kind:
		BattleUnit.Kind.HERO:
			_update_hero(model, unit)
		BattleUnit.Kind.MINION:
			_update_minion(model, unit)


static func _update_hero(model: RefCounted, hero: BattleUnit) -> void:
	var enemies: Array[BattleUnit] = model.enemies_of(hero.team)
	HeroSkills.shared().update_timers(
		hero, model.all_units(), model.towers, [model.blue_base, model.red_base]
	)
	EntityItems.update(hero, enemies, model)
	_hero_heal(model, hero)
	if hero.auto_cast_enabled:
		hero.auto_cast_check_timer += 1
		if hero.auto_cast_check_timer >= 20:
			hero.auto_cast_check_timer = 0
			_auto_cast(model, hero, enemies)
	if hero.is_retreating:
		var base: BattleUnit = model.blue_base if hero.team == "blue" else model.red_base
		_move(hero, base.pos)
		if hero.hp / maxf(1.0, hero.max_hp) >= hero.heal_target_ratio:
			hero.is_retreating = false
		return
	if hero.has_tactical_move:
		_move(hero, hero.tactical_move)
		if hero.pos.distance_to(hero.tactical_move) < 4.0:
			hero.has_tactical_move = false
		return
	if hero.tactical_target != null and hero.tactical_target.alive:
		_engage(model, hero, hero.tactical_target)
		return
	if hero.has_destination:
		_move(hero, hero.destination)
		if hero.pos.distance_to(hero.destination) < 4.0:
			hero.has_destination = false
			hero.destination_auto = false
		var aggro: BattleUnit = model._nearest(hero.pos, enemies, hero.aggro_range)
		if aggro != null and not hero.destination_auto:
			hero.has_destination = false
			hero.target = aggro
		return
	if hero.follow_target != null and hero.follow_target.alive:
		_move(hero, hero.follow_target.pos + Vector2(-hero.facing * 50, 20))
		return
	var target: BattleUnit = model._nearest(hero.pos, enemies, hero.attack_range + 40.0)
	if target == null:
		target = model._nearest(hero.pos, enemies, hero.hunt_range)
	if target != null:
		hero.target = target
		_engage(model, hero, target)
		return
	var base: BattleUnit = model.red_base if hero.team == "blue" else model.blue_base
	_move(hero, base.pos, 0.6)


static func _hero_heal(model: RefCounted, hero: BattleUnit) -> void:
	var base: BattleUnit = model.blue_base if hero.team == "blue" else model.red_base
	if hero.pos.distance_to(base.pos) <= 140.0:
		hero.heal(hero.base_heal_rate)
	else:
		hero.heal(hero.passive_heal_rate)
	if hero.hp / maxf(1.0, hero.max_hp) < hero.retreat_hp_ratio:
		hero.is_retreating = true
		hero.has_destination = false
		hero.follow_target = null


static func _auto_cast(model: RefCounted, hero: BattleUnit, enemies: Array[BattleUnit]) -> void:
	var near: BattleUnit = model._nearest(
		hero.pos, enemies, maxf(hero.skill_range, hero.attack_range) * 1.15
	)
	if near == null:
		return
	hero.target = near
	if hero.skill_cooldowns.r <= 0:
		model.cast_hero_skill(hero, "r")
		return
	if hero.skill_cooldowns.e <= 0 and enemies.size() >= 2:
		model.cast_hero_skill(hero, "e")
		return
	if hero.skill_cooldowns.w <= 0 and hero.hp / maxf(1.0, hero.max_hp) < 0.4:
		model.cast_hero_skill(hero, "w")
		return
	if hero.skill_cooldowns.q <= 0:
		model.cast_hero_skill(hero, "q")


static func _engage(model: RefCounted, hero: BattleUnit, target: BattleUnit) -> void:
	var dist := hero.pos.distance_to(target.pos)
	if dist <= hero.attack_range + target.radius:
		hero.facing = 1 if target.pos.x >= hero.pos.x else -1
		model._attack(hero, target)
	else:
		_move(hero, target.pos)


static func _update_minion(model: RefCounted, minion: BattleUnit) -> void:
	var enemies: Array[BattleUnit] = model.enemies_of(minion.team)
	var target := _minion_target(model, minion, enemies)
	minion.target = target
	if target != null and minion.pos.distance_to(target.pos) <= minion.attack_range + target.radius:
		minion.facing = 1 if target.pos.x >= minion.pos.x else -1
		model._attack(minion, target)
		return
	if target != null and minion.ai_level >= 2 and minion.pos.distance_to(target.pos) <= 180.0:
		_move(minion, target.pos)
		return
	_follow_path(minion)


static func _minion_target(
	model: RefCounted, minion: BattleUnit, enemies: Array[BattleUnit]
) -> BattleUnit:
	var tier := clampi(minion.ai_level, 1, 5)
	var best: BattleUnit = null
	var best_score := INF
	for enemy: BattleUnit in enemies:
		var dist := minion.pos.distance_to(enemy.pos)
		if dist > 260.0:
			continue
		var score := dist
		if tier >= 2 and enemy.lane != minion.lane:
			score += 120.0
		if tier >= 3:
			score += enemy.hp * 0.05
		if tier >= 4 and enemy.kind != BattleUnit.Kind.MINION:
			score += 80.0
		if tier >= 5 and enemy.kind in [BattleUnit.Kind.TOWER, BattleUnit.Kind.CASTLE]:
			score -= 100.0
		if score < best_score:
			best_score = score
			best = enemy
	if best == null:
		best = model._nearest(minion.pos, enemies, 120.0)
	return best


static func _follow_path(unit: BattleUnit) -> void:
	if unit.path.is_empty():
		unit.is_moving = false
		return
	var direction := 1 if unit.team == "blue" else -1
	var next := clampi(unit.waypoint + direction, 0, unit.path.size() - 1)
	_move(unit, unit.path[next])
	if unit.pos.distance_to(unit.path[next]) < 15.0:
		unit.waypoint = next


static func _move(unit: BattleUnit, point: Vector2, mult := 1.0) -> void:
	var old := unit.pos
	unit.pos = unit.pos.move_toward(point, unit.effective_speed() * mult)
	unit.is_moving = old.distance_to(unit.pos) > 0.05
	if unit.is_moving:
		unit.facing = 1 if unit.pos.x >= old.x else -1
