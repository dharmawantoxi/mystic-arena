class_name BossController
extends RefCounted

## Native port of bosses/base_boss.py Boss.update (non-renderer half).
## Smart-AI Q/W/E/R remains the generated BossKit; this controller owns the
## source tick order, target selection, basic attack/cleave, kiting and lane walk.
const BossKit = preload("res://scripts/entities/generated/BossKit.gd")


static func update(model: RefCounted, boss: BattleUnit) -> void:
	if not boss.alive:
		return
	boss.anim_time += 1
	boss.pulse += 0.1
	boss.attack_anim_timer = maxi(0, boss.attack_anim_timer - 1)
	var moved := boss.pos.distance_to(boss.prev_pos)
	boss.prev_pos = boss.pos
	boss.is_moving = moved > 0.05
	if boss.attack_lock_timer > 0:
		boss.attack_lock_timer -= 1
		if boss.attack_lock_timer <= 0:
			boss.attack_facing = 0
	var burn := boss.status.tick()
	if burn > 0 and boss.alive:
		var burn_team := (
			boss.status.burn_team if not boss.status.burn_team.is_empty() else boss.team
		)
		boss.take_damage(float(burn), burn_team, "fire")
	if boss.status.stun_timer > 0:
		return
	boss.hurt_flash_timer = maxi(0, boss.hurt_flash_timer - 1)
	if boss.entrance_timer > 0:
		boss.entrance_timer -= 1
		return
	_enrage(model, boss)
	if boss.is_enraged:
		boss.enrage_pulse += 0.08
		if boss.anim_time % 2 == 0:
			boss.attack_timer = maxi(0, boss.attack_timer - 1)
			boss.ability_timer = maxi(0, boss.ability_timer - 1)
	boss.attack_timer = maxi(0, boss.attack_timer - 1)
	boss.ability_timer = maxi(0, boss.ability_timer - 1)
	boss.ability2_timer = maxi(0, boss.ability2_timer - 1)
	if boss.ability_active_timer > 0:
		boss.ability_active_timer -= 1
		if boss.ability_active_timer <= 0:
			boss.ability_active = false
	if boss.boss_class == "true" and boss.ability2_timer == 0 and boss.hp < boss.max_hp * 0.3:
		_heal(model, boss)
	var enemies: Array = boss.kit_enemies(
		model.all_units(), model.towers, [model.blue_base, model.red_base]
	)
	boss.target = _nearest(boss, enemies)
	if boss.target != null:
		var dist := boss.pos.distance_to(boss.target.pos)
		if dist <= boss.attack_range:
			_face(boss, boss.target.pos.x - boss.pos.x, boss.target.pos.y - boss.pos.y)
			if boss.attack_timer == 0:
				_basic_attack(model, boss, enemies)
			if model.data.bosses.has_smart_ai(boss.unit_type):
				BossKit.dispatch(boss, boss.unit_type, enemies, dist)
				_sync_kit_visual(boss)
			elif boss.ability_timer == 0:
				_ability(model, boss, enemies)
		else:
			_chase(boss, dist)
	else:
		_move_forward(model, boss)


static func _enrage(model: RefCounted, boss: BattleUnit) -> void:
	if boss.enrage_triggered:
		return
	var is_true := boss.boss_class == "true"
	var threshold := 0.50 if is_true else 0.40
	if boss.hp > boss.max_hp * threshold:
		return
	boss.enrage_triggered = true
	boss.is_enraged = true
	if is_true:
		boss.speed *= 1.25
		boss.damage = int(boss.damage * 1.25)
		boss.attack_cooldown = maxi(18, int(boss.attack_cooldown * 0.75))
		model.add_shake(25.0)
		model.add_popup(boss.pos + Vector2(0, -boss.radius - 30), "ENRAGED!", Color("ff5533"))
	else:
		boss.speed *= 1.15
		boss.damage = int(boss.damage * 1.20)
		boss.attack_cooldown = maxi(20, int(boss.attack_cooldown * 0.80))
		model.add_shake(15.0)
		model.add_popup(boss.pos + Vector2(0, -boss.radius - 30), "FRENZY!", Color("ff8c1e"))


static func _nearest(boss: BattleUnit, enemies: Array) -> BattleUnit:
	var best: BattleUnit = null
	var best_dist := boss.attack_range + 100.0
	for enemy: BattleUnit in enemies:
		var dist := boss.pos.distance_to(enemy.pos)
		if dist < best_dist:
			best_dist = dist
			best = enemy
	return best


static func _basic_attack(model: RefCounted, boss: BattleUnit, enemies: Array) -> void:
	boss.target.take_damage(boss.damage, boss.team, "normal", boss, "physical")
	var cleave := int(boss.damage * boss.cleave_ratio)
	if cleave > 0:
		for enemy: BattleUnit in enemies:
			if enemy != boss.target and boss.pos.distance_to(enemy.pos) <= boss.cleave_radius:
				enemy.take_damage(float(cleave), boss.team)
	boss.attack_timer = boss.effective_attack_cd()
	boss.attack_facing = boss.facing
	boss.basic_attack_seq += 1
	boss.attack_lock_timer = mini(15, maxi(6, int(boss.attack_cooldown / 3.0)))
	boss.attack_anim_timer = 18
	if model.has_signal("render_event"):
		model.render_event.emit("boss_attack", {"unit": boss})


static func _ability(model: RefCounted, boss: BattleUnit, enemies: Array) -> void:
	boss.ability_timer = boss.ability_cooldown_max
	boss.ability_active = true
	boss.ability_active_timer = 60
	for enemy: BattleUnit in enemies:
		if boss.pos.distance_to(enemy.pos) <= boss.ability_range:
			enemy.take_damage(boss.ability_damage, boss.team)
			enemy.attack_timer = maxi(enemy.attack_timer, 60)
	model.add_shake(15.0 if boss.boss_class == "true" else 12.0)
	if boss.unit_type == "krobellus":
		boss.kit_fx_cast("q")
		boss.kit_fx_impact(boss.pos.x, boss.pos.y, boss.ability_range, "q")


static func _heal(model: RefCounted, boss: BattleUnit) -> void:
	if boss.ability2_cooldown_max <= 0:
		return
	boss.ability2_timer = boss.ability2_cooldown_max
	var amount := int(boss.max_hp * boss.ability2_heal_pct)
	boss.hp = minf(boss.max_hp, boss.hp + amount)
	model.add_popup(boss.pos + Vector2(0, -30), "+%d" % amount, Color("66ff99"))
	model.add_shake(8.0)


static func _chase(boss: BattleUnit, dist: float) -> void:
	var delta := boss.target.pos - boss.pos
	var sp := boss.effective_speed()
	if dist <= 0.0 or sp <= 0.0:
		return
	if boss.world.data.bosses.kites(boss.unit_type):
		var min_dist := float(boss.stats.get("min_distance", 200))
		var prefer := float(boss.stats.get("prefer_distance", 280))
		var band := 12.0
		if dist < min_dist:
			boss.kite_mode = "back"
		elif dist > prefer:
			boss.kite_mode = "in"
		elif boss.kite_mode == "back" and dist < min_dist + band:
			pass
		elif boss.kite_mode == "in" and dist > prefer - band:
			pass
		else:
			boss.kite_mode = "hold"
		if boss.kite_mode == "back":
			var step := minf(sp, maxf(0.0, (min_dist + band) - dist))
			if step > 0.0:
				boss.pos -= delta / dist * step
				_face(boss, -delta.x, -delta.y)
		elif boss.kite_mode == "in":
			var step := minf(sp, maxf(0.0, dist - (prefer - band)))
			if step > 0.0:
				boss.pos += delta / dist * step
				_face(boss, delta.x, delta.y)
	else:
		var step := minf(sp, dist)
		boss.pos += delta / dist * step
		_face(boss, delta.x, delta.y)


static func _move_forward(model: RefCounted, boss: BattleUnit) -> void:
	var budget := boss.effective_speed()
	if budget <= 0.0:
		return
	var guard := 0
	while budget > 0.001 and guard < 16:
		guard += 1
		var target: Vector2 = model.blue_base.pos
		var has_next := not boss.path.is_empty() and boss.waypoint >= 0
		if has_next and boss.waypoint < boss.path.size():
			target = boss.path[boss.waypoint]
		var delta := target - boss.pos
		var dist := delta.length()
		if dist <= 0.000001:
			if not has_next:
				break
			boss.waypoint -= 1
			continue
		if dist <= budget:
			boss.pos = target
			budget -= dist
			_face(boss, delta.x, delta.y)
			if has_next:
				boss.waypoint -= 1
			continue
		boss.pos += delta / dist * budget
		_face(boss, delta.x, delta.y)
		budget = 0.0


static func _face(boss: BattleUnit, dx: float, dy: float) -> void:
	if boss.attack_lock_timer > 0:
		if boss.attack_facing != 0:
			boss.facing = boss.attack_facing
		return
	if absf(dx) < 0.35 * maxf(0.000001, absf(dy)):
		return
	boss.facing = 1 if dx > 0.0 else -1


static func _sync_kit_visual(boss: BattleUnit) -> void:
	var skill: Variant = boss.kit.get("active_skill")
	var timer := int(boss.kit.get("active_skill_timer", 0))
	boss.active_skill_timer = timer
	boss.active_skill = str(skill) if skill != null and timer > 0 else ""
