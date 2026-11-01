class_name MatchModel
extends RefCounted

## Native fixed-step match simulation migrated from _core.Game and _entity.py.
## Combat, projectiles, AI, items and baked entity visuals run in GDScript.
signal notification(text: String)
signal match_finished(victory: bool)
signal render_event(kind: String, data: Dictionary)

var data := CoreData.new()
var level_number := 1
var level_config: Dictionary = {}
var difficulty := "normal"
var is_replay := false
var rng := RandomNumberGenerator.new()
var state := "playing"
var frame := 0
var gold := 0
var ai_gold := 0
var gold_milli := 0
var gold_timer := 0
var gold_per_second := 0.0
var wave_number := 0
var wave_timer := 300
var wave_interval := 1500
var spawn_delay := 20
var waves := WaveDirector.new()
var tactical := TacticalCommands.new()
var minions: Array[BattleUnit] = []
var towers: Array[BattleUnit] = []
var heroes: Array[BattleUnit] = []
var enemy_heroes: Array[BattleUnit] = []
var blue_base := BattleUnit.new()
var red_base := BattleUnit.new()
var active_boss: BattleUnit
var build_slots_blue: Array[Dictionary] = []
var build_slots_red: Array[Dictionary] = []
var selected_tower: BattleUnit
var selected_hero: BattleUnit
var selected_slot := -1
var red_towers_destroyed := 0
var true_boss_spawned := false
var bosses_defeated: Array[String] = []
var total_kills := 0
var score := 0
var max_combo := 0
var combo := 0
var combo_timer := 0
var enemy_hp_mult := 1.0
var enemy_damage_mult := 1.0
var enemy_speed_mult := 1.0
var purchased_heroes: Array = []
var unlocked_bosses: Array = []
var next_id := 1
var ai_timer := 0
var ai: EntityAI
var projectiles: Array[Dictionary] = []
var effects: Array[Dictionary] = []
var popups: Array[Dictionary] = []
var shake := 0.0
var notifications: Array[String] = []
var first_blood := false
var spatial := SpatialGrid.new()


func clear_unit_refs() -> void:
	# BattleUnit is RefCounted; break target/source cycles before replacing a match.
	var units := all_units()
	units.append_array(towers)
	units.append_array([blue_base, red_base])
	for unit: BattleUnit in units:
		unit.tactical_target = null
		unit.follow_target = null
		unit.killed_by = null
		unit.target = null
		unit.world = null
		for key: String in unit.kit:
			if unit.kit[key] is BattleUnit:
				unit.kit[key] = null
	selected_tower = null
	selected_hero = null
	active_boss = null
	projectiles.clear()
	spatial.clear()
	effects.clear()
	popups.clear()
	ai = null


func setup(
	config: Dictionary,
	save_data: Dictionary,
	settings_difficulty: String,
	replay: bool,
	seed_value := 0
) -> void:
	clear_unit_refs()
	level_config = config
	level_number = int(config.get("level_number", 1))
	is_replay = replay
	purchased_heroes = save_data.get("purchased_heroes", []).duplicate()
	unlocked_bosses = save_data.get("unlocked_bosses", []).duplicate()
	if purchased_heroes.is_empty():
		purchased_heroes.append("kaizen")
	var locked: Variant = save_data.get("run_difficulty", null)
	difficulty = (
		str(locked)
		if (
			locked != null
			and (
				int(save_data.get("completed_levels", []).size())
				< data.data.get("levels", []).size()
			)
		)
		else settings_difficulty
	)
	if seed_value != 0:
		rng.seed = seed_value
	else:
		rng.randomize()
	gold = Economy.starting_gold(config, level_number, difficulty)
	gold_per_second = Economy.gold_per_second(level_number, difficulty)
	var hard := difficulty == "hard"
	enemy_hp_mult = float(config.get("enemy_hp_mult", 1.0)) * (1.15 if hard else 1.0)
	enemy_damage_mult = float(config.get("enemy_damage_mult", 1.0)) * (1.10 if hard else 1.0)
	enemy_speed_mult = float(config.get("enemy_speed_mult", 1.0))
	wave_interval = int(data.rule("MINION_WAVE_INTERVAL", 1500))
	spawn_delay = int(data.rule("MINION_SPAWN_DELAY", 20))
	waves.roll_schedule(config, difficulty, rng)
	blue_base.world = self
	red_base.world = self
	ai = EntityAI.new(self, level_number)
	blue_base.setup_castle(data, "blue", int(config.get("starting_castle_level", 1)))
	red_base.setup_castle(data, "red", int(config.get("castle_start_level", 1)) if hard else 1)
	blue_base.set_wave(data, 0)
	red_base.set_wave(data, 0)
	for row: Array in data.rule("BLUE_TOWERS", []):
		var tower := BattleUnit.new()
		tower.id = _id()
		tower.world = self
		tower.setup_tower(data, Vector2(float(row[0]), float(row[1])), "blue", str(row[2]))
		towers.append(tower)
	for row: Array in data.rule("RED_TOWERS", []):
		var tower := BattleUnit.new()
		tower.id = _id()
		tower.world = self
		tower.setup_tower(data, Vector2(float(row[0]), float(row[1])), "red", str(row[2]))
		towers.append(tower)
	_generate_build_slots()
	buy_hero("kaizen", true)


func _id() -> int:
	next_id += 1
	return next_id


func _generate_build_slots() -> void:
	var positions := {
		"top": {"blue": [0.15, 0.30, 0.45], "red": [0.85, 0.70, 0.55]},
		"mid": {"blue": [0.10, 0.25, 0.40], "red": [0.90, 0.75, 0.60]},
		"bot": {"blue": [0.15, 0.30, 0.45], "red": [0.85, 0.70, 0.55]},
	}
	for lane: String in ["top", "mid", "bot"]:
		var path := data.lane(lane)
		if path.is_empty():
			continue
		for team: String in ["blue", "red"]:
			for pct: float in positions[lane][team]:
				var index := mini(int(path.size() * pct), path.size() - 1)
				var slot := {"pos": path[index], "lane": lane, "taken": false}
				if team == "blue":
					build_slots_blue.append(slot)
				else:
					build_slots_red.append(slot)


func all_units() -> Array[BattleUnit]:
	var result: Array[BattleUnit] = []
	result.append_array(minions)
	result.append_array(heroes)
	result.append_array(enemy_heroes)
	if active_boss != null and active_boss.alive:
		result.append(active_boss)
	return result


func _update_spatial_grid() -> void:
	spatial.clear()
	for unit: BattleUnit in all_units():
		if unit.alive:
			spatial.insert(unit)


func query_enemies_in_range(pos: Vector2, radius: float, team: String) -> Array[BattleUnit]:
	return spatial.query_range(pos.x, pos.y, radius, team)


func nearest_enemy_in_range(pos: Vector2, radius: float, team: String) -> BattleUnit:
	var best := _nearest(pos, query_enemies_in_range(pos, radius, team), radius)
	for tower: BattleUnit in towers:
		if tower.team != team and tower.alive and pos.distance_to(tower.pos) <= radius:
			if best == null or pos.distance_to(tower.pos) < pos.distance_to(best.pos):
				best = tower
	var base := red_base if team == "blue" else blue_base
	if base.alive and pos.distance_to(base.pos) <= radius:
		if best == null or pos.distance_to(base.pos) < pos.distance_to(best.pos):
			best = base
	return best


func enemies_of(team: String) -> Array[BattleUnit]:
	var result: Array[BattleUnit] = []
	for unit: BattleUnit in all_units():
		if unit.team != team and unit.alive:
			result.append(unit)
	for tower: BattleUnit in towers:
		if tower.team != team and tower.alive:
			result.append(tower)
	var base := red_base if team == "blue" else blue_base
	if base.alive:
		result.append(base)
	return result


func step() -> void:
	if state != "playing":
		return
	frame += 1
	gold_timer += 1
	if gold_timer >= 60:
		gold_timer = 0
		var income := Economy.add_income(gold, gold_milli, gold_per_second)
		gold = income.gold
		gold_milli = income.milli
		ai_gold += int(data.rule("GOLD_PER_SECOND", 3)) + maxi(0, wave_number)
	_update_waves()
	_update_spatial_grid()
	var units := all_units()
	for unit: BattleUnit in units:
		unit.tick_timers(data)
		_update_unit(unit)
	for tower: BattleUnit in towers:
		if tower.alive:
			tower.tick_timers(data)
			_update_tower(tower)
	for base: BattleUnit in [blue_base, red_base]:
		if base.alive:
			base.tick_timers(data)
			_update_tower(base)
	EntityProjectiles.update(self)
	_update_ai()
	_update_effects()
	_process_rewards()
	_respawn_heroes()
	tactical.update(1.0 / 60.0, self)
	combo_timer = maxi(0, combo_timer - 1)
	if combo_timer == 0:
		combo = 0
	_cleanup()
	if not blue_base.alive:
		state = "defeat"
		match_finished.emit(false)
	elif not red_base.alive:
		state = "victory"
		match_finished.emit(true)


func _update_waves() -> void:
	if wave_timer > 0:
		wave_timer -= 1
	elif waves.queue_blue.is_empty() and waves.queue_red.is_empty():
		wave_number += 1
		wave_timer = wave_interval
		blue_base.set_wave(data, wave_number)
		red_base.set_wave(data, wave_number)
		waves.queue_mini(wave_number)
		_try_spawn_mini()
		var target := WaveDirector.ai_castle_target(wave_number)
		while red_base.level < target:
			red_base.upgrade_castle(data)
		waves.enqueue_wave(blue_base.level, red_base.level, wave_number, data.data.get("rules", {}))
		_notify("Wave %d" % wave_number)
	render_event.emit("wave", {"number": wave_number})
	render_event.emit(
		"path_preview", {"paths": [data.lane("top"), data.lane("mid"), data.lane("bot")]}
	)
	for team: String in ["blue", "red"]:
		var spawn := waves.pop_spawn(team, spawn_delay)
		if spawn.is_empty():
			continue
		var minion := BattleUnit.new()
		minion.id = _id()
		minion.world = self
		minion.ai_level = clampi(1 + int(wave_number / 5.0), 1, 5)
		var castle_level := blue_base.level if team == "blue" else red_base.level
		minion.setup_minion(
			data, str(spawn.type), team, str(spawn.lane), castle_level, data.lane(str(spawn.lane))
		)
		if team == "red":
			minion.apply_scaling(enemy_hp_mult, enemy_damage_mult, enemy_speed_mult)
		minions.append(minion)
	if not true_boss_spawned and red_towers_destroyed >= 6 and active_boss == null:
		var boss_type := str(level_config.get("true_boss", ""))
		if not boss_type.is_empty():
			_spawn_boss(boss_type)
			true_boss_spawned = true


func _try_spawn_mini() -> void:
	if active_boss != null and active_boss.alive:
		return
	var entry := waves.pop_mini()
	if not entry.is_empty():
		_spawn_boss(str(entry.type))


func _spawn_boss(boss_type: String) -> void:
	active_boss = BattleUnit.new()
	active_boss.id = _id()
	active_boss.world = self
	active_boss.setup_boss(data, boss_type, data.lane("mid"))
	active_boss.apply_scaling(enemy_hp_mult, enemy_damage_mult, enemy_speed_mult)
	_notify(str(active_boss.stats.get("entrance_text", active_boss.display_name)))
	render_event.emit("boss_intro", {"unit": active_boss})


func _update_unit(unit: BattleUnit) -> void:
	EntityMovement.update(self, unit)


func _nearest(origin: Vector2, candidates: Array[BattleUnit], max_distance: float) -> BattleUnit:
	var best: BattleUnit = null
	var best_dist := max_distance
	for candidate: BattleUnit in candidates:
		var dist := origin.distance_to(candidate.pos)
		if dist <= best_dist:
			best_dist = dist
			best = candidate
	return best


func _attack(attacker: BattleUnit, target: BattleUnit) -> void:
	if attacker.attack_timer > 0 or attacker.attack_lock_timer > 0:
		return
	attacker.attack_timer = attacker.effective_attack_cd()
	attacker.attack_anim_timer = 18
	attacker.attack_facing = attacker.facing
	var amount := attacker.damage
	var is_crit := false
	if attacker.kind == BattleUnit.Kind.HERO and attacker.items != null:
		var crit := attacker.items.sum_stat("crit_chance")
		if crit > 0.0 and rng.randf() < crit:
			amount *= maxf(1.0, attacker.items.sum_stat("crit_mult"))
			is_crit = true
	if (
		attacker.kind == BattleUnit.Kind.HERO
		and attacker.attack_range > 80.0
		and attacker.unit_type != "morgath"
	):
		EntityProjectiles.spawn_hero(self, attacker, target, amount, is_crit)
		return
	var dealt := target.take_damage(
		amount, attacker.team, "physical", attacker, attacker.dmg_school
	)
	if attacker.kind == BattleUnit.Kind.HERO:
		if attacker.items != null:
			var lifesteal := attacker.items.lifesteal()
			if attacker.item_timer("blood_frenzy") > 0:
				lifesteal += float(
					attacker.items.catalog.get("demon_maw", {}).get("active", {}).get(
						"lifesteal_bonus", 0.0
					)
				)
			attacker.heal(dealt * lifesteal)
			EntityItems.on_attack(attacker, target, amount, enemies_of(attacker.team), self)
		add_effect(target.pos, "hit", attacker.color, 10)
		add_damage_number(target.pos, int(dealt), is_crit, attacker.dmg_school)


func _update_tower(tower: BattleUnit) -> void:
	if tower.attack_timer > 0:
		return
	var target := nearest_enemy_in_range(tower.pos, tower.attack_range, tower.team)
	if target == null:
		return
	tower.attack_timer = tower.effective_attack_cd()
	tower.shoot_flash_timer = 10
	tower.facing = 1 if target.pos.x >= tower.pos.x else -1
	var bullet_type := tower.tower_type if tower.kind == BattleUnit.Kind.TOWER else "normal"
	if bullet_type == "archer":
		bullet_type = "normal"
	EntityProjectiles.spawn_tower(
		self, tower, target, bullet_type, tower.pos + Vector2(0, -20), tower.stats
	)
	if bool(tower.stats.get("double_shot", false)):
		var second := nearest_enemy_in_range(tower.pos, tower.attack_range, tower.team)
		if second != null and second != target:
			EntityProjectiles.spawn_tower(
				self, tower, second, bullet_type, tower.pos + Vector2(0, -20), tower.stats
			)


func _update_ai() -> void:
	if ai != null:
		ai.update()


func _process_rewards() -> void:
	for minion: BattleUnit in minions:
		if not minion.alive and not minion.rewarded:
			minion.rewarded = true
			render_event.emit("death", {"pos": minion.pos, "team": minion.team, "size": "small"})
			if minion.team == "red":
				gold += minion.gold_reward
				score += minion.gold_reward
				total_kills += 1
				combo += 1
				combo_timer = 180
				max_combo = maxi(max_combo, combo)
				render_event.emit("gold", {"pos": minion.pos, "amount": minion.gold_reward})
				render_event.emit("combo_kill", {})
				if not first_blood:
					first_blood = true
					render_event.emit(
						"achievement",
						{"title": "First Blood", "description": "Kill pertama diraih!"}
					)
			else:
				ai_gold += minion.gold_reward
	for tower: BattleUnit in towers:
		if not tower.alive and not tower.rewarded:
			tower.rewarded = true
			render_event.emit("death", {"pos": tower.pos, "team": tower.team, "size": "medium"})
			if tower.team == "red":
				gold += tower.gold_reward
				score += tower.gold_reward
				red_towers_destroyed += 1
				render_event.emit("gold", {"pos": tower.pos, "amount": tower.gold_reward})
			else:
				ai_gold += tower.gold_reward
	for hero: BattleUnit in heroes + enemy_heroes:
		if not hero.alive and not hero.rewarded:
			hero.rewarded = true
			hero.respawn_timer = 600
			render_event.emit("death", {"pos": hero.pos, "team": hero.team, "size": "medium"})
			if hero.team == "red":
				gold += 150
				score += 150
				render_event.emit("gold", {"pos": hero.pos, "amount": 150})
			else:
				ai_gold += 150
	if active_boss != null and not active_boss.alive and active_boss.defeated:
		gold += active_boss.gold_reward
		score += active_boss.gold_reward
		if active_boss.unit_type not in bosses_defeated:
			bosses_defeated.append(active_boss.unit_type)
		if active_boss.unit_type not in unlocked_bosses:
			unlocked_bosses.append(active_boss.unit_type)
		_notify("%s defeated!" % active_boss.display_name)
		render_event.emit("boss_death", {"unit": active_boss})
		render_event.emit("gold", {"pos": active_boss.pos, "amount": active_boss.gold_reward})
		render_event.emit(
			"achievement",
			{"title": "Boss Slayer", "description": "%s dikalahkan!" % active_boss.display_name}
		)
		active_boss = null
		_try_spawn_mini()


func _respawn_heroes() -> void:
	for hero: BattleUnit in heroes + enemy_heroes:
		if not hero.alive and hero.respawn_timer > 0:
			hero.respawn_timer -= 1
			if hero.respawn_timer <= 0:
				hero.respawn(data)


func _cleanup() -> void:
	minions = minions.filter(
		func(unit: BattleUnit) -> bool: return unit.alive or unit.death_anim > 0
	)
	for minion: BattleUnit in minions:
		if not minion.alive:
			minion.death_anim -= 1
	towers = towers.filter(func(unit: BattleUnit) -> bool: return unit.alive)
	if selected_tower != null and not selected_tower.alive:
		selected_tower = null


func _notify(text: String) -> void:
	notifications.append(text)
	if notifications.size() > 8:
		notifications.pop_front()
	notification.emit(text)


func buy_hero(hero_type: String, free := false) -> bool:
	if heroes.size() >= int(data.rule("MAX_HEROES_OWNED", 5)):
		return false
	for hero: BattleUnit in heroes:
		if hero.unit_type == hero_type:
			return false
	var stats := data.hero(hero_type)
	if stats.is_empty():
		return false
	var cost := int(stats.get("cost", 500))
	if not free:
		if hero_type not in purchased_heroes and hero_type not in unlocked_bosses:
			return false
		if gold < cost:
			return false
		gold -= cost
	var hero := BattleUnit.new()
	hero.id = _id()
	hero.world = self
	hero.setup_hero(data, hero_type, "blue", Vector2(180, 560))
	heroes.append(hero)
	selected_hero = hero
	return true


func build_tower(slot_index: int, tower_type: String) -> bool:
	if slot_index < 0 or slot_index >= build_slots_blue.size():
		return false
	var slot := build_slots_blue[slot_index]
	if bool(slot.taken) or gold < 100:
		return false
	gold -= 100
	slot.taken = true
	var tower := BattleUnit.new()
	tower.id = _id()
	tower.world = self
	tower.setup_tower(data, slot.pos, "blue", str(slot.lane), true)
	if tower_type != "archer":
		tower.tower_type = tower_type
		tower._apply_tower_stats(data)
	towers.append(tower)
	selected_tower = tower
	selected_slot = -1
	return true


func upgrade_selected_tower(path := "") -> bool:
	if selected_tower == null or not selected_tower.alive:
		return false
	var cost := selected_tower.tower_upgrade_cost(data, path)
	if cost <= 0 or gold < cost:
		return false
	gold -= cost
	return selected_tower.upgrade_tower(data, path)


func sell_selected_tower() -> bool:
	if selected_tower == null or not selected_tower.player_built:
		return false
	gold += selected_tower.sell_value(data)
	selected_tower.alive = false
	selected_tower = null
	return true


func upgrade_base() -> bool:
	var cost := blue_base.castle_upgrade_cost(data)
	if cost <= 0 or gold < cost:
		return false
	gold -= cost
	return blue_base.upgrade_castle(data)


func buy_castle_shield() -> bool:
	var cost := int(data.rule("CASTLE_SHIELD_COST", 850))
	if gold < cost or not blue_base.activate_castle_shield(data):
		return false
	gold -= cost
	return true


func buy_tower_regen_shield() -> bool:
	if selected_tower == null:
		return false
	var cost := int(data.rule("TOWER_REGEN_SHIELD_COST", 850))
	if gold < cost or not selected_tower.activate_regen_shield(data):
		return false
	gold -= cost
	return true


func upgrade_selected_hero() -> bool:
	if selected_hero == null:
		return false
	var cost := selected_hero.hero_upgrade_cost(data)
	if cost <= 0 or gold < cost:
		return false
	gold -= cost
	return selected_hero.upgrade_hero(data)


func buy_item(item_id: String) -> bool:
	if selected_hero == null or not selected_hero.alive:
		return false
	var item := data.item(item_id)
	var cost := int(item.get("cost", 0))
	if item.is_empty() or gold < cost:
		return false
	if selected_hero.items.used() >= UnitInventory.MAX_SLOTS:
		selected_hero.items.pending.append(item_id)
	elif not selected_hero.items.add(
		item_id, selected_hero.attack_range, selected_hero.is_magic_hero()
	):
		return false
	gold -= cost
	selected_hero._apply_hero_level(data)
	return true


func cast_skill(key: String) -> bool:
	if selected_hero == null:
		return false
	return cast_hero_skill(selected_hero, key)


func cast_hero_skill(hero: BattleUnit, key: String) -> bool:
	return hero.cast_skill(key, enemies_of(hero.team))


func add_damage_number(
	position: Vector2, amount: int, critical := false, damage_type := "normal"
) -> void:
	render_event.emit(
		"damage", {"pos": position, "amount": amount, "critical": critical, "type": damage_type}
	)


func add_effect(position: Vector2, effect_type: String, effect_color: Color, radius: int) -> void:
	render_event.emit(
		"effect", {"pos": position, "type": effect_type, "color": effect_color, "radius": radius}
	)
	effects.append(
		{
			"pos": position,
			"type": effect_type,
			"color": effect_color,
			"radius": radius,
			"age": 0,
			"ttl": 24
		}
	)
	if effects.size() > 120:
		effects.pop_front()


func add_popup(position: Vector2, text: String, popup_color: Color) -> void:
	render_event.emit("popup", {"pos": position, "text": text, "color": popup_color})
	popups.append({"pos": position, "text": text, "color": popup_color, "age": 0, "ttl": 60})
	if popups.size() > 40:
		popups.pop_front()


func add_shake(amount: float) -> void:
	shake = maxf(shake, amount)
	render_event.emit("shake", {"amount": amount})


func _update_effects() -> void:
	shake = maxf(0.0, shake - 1.0)
	var keep: Array[Dictionary] = []
	for effect: Dictionary in effects:
		effect["age"] = int(effect.age) + 1
		if int(effect.age) < int(effect.ttl):
			keep.append(effect)
	effects = keep
	var keep_popups: Array[Dictionary] = []
	for popup: Dictionary in popups:
		popup["age"] = int(popup.age) + 1
		if int(popup.age) < int(popup.ttl):
			keep_popups.append(popup)
	popups = keep_popups


func apply_tactical(command: String, _delta: float) -> void:
	if command.is_empty():
		for hero: BattleUnit in heroes:
			hero.tactical_target = null
			hero.has_tactical_move = false
		return
	for hero: BattleUnit in heroes:
		if not hero.alive:
			continue
		match command:
			"gather", "gather_push":
				hero.tactical_target = null
				hero.has_tactical_move = true
				hero.tactical_move = Vector2(640, 360) if command == "gather" else Vector2(900, 300)
			"protect_castle", "auto_protect":
				hero.tactical_target = null
				hero.has_tactical_move = true
				hero.tactical_move = blue_base.pos + Vector2(60, -40)
			"protect_tower":
				var blue_towers: Array[BattleUnit] = []
				for tower: BattleUnit in towers:
					if tower.team == "blue" and tower.alive:
						blue_towers.append(tower)
				var tower := _nearest(blue_base.pos, blue_towers, 2000.0)
				if tower != null:
					hero.has_tactical_move = true
					hero.tactical_move = tower.pos
			"attack_boss":
				if active_boss != null and active_boss.alive:
					hero.tactical_target = active_boss
			"attack_damage_dealer":
				var best: BattleUnit = null
				for enemy: BattleUnit in enemy_heroes:
					if enemy.alive and (best == null or enemy.damage_dealt > best.damage_dealt):
						best = enemy
				hero.tactical_target = best


func match_stats() -> Dictionary:
	return {
		"won": state == "victory",
		"score": score,
		"time_seconds": int(frame / 60.0),
		"kills": total_kills,
		"combo": max_combo,
		"playtime_seconds": int(frame / 60.0),
	}
