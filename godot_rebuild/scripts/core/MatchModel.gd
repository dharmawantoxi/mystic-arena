class_name MatchModel
extends RefCounted

## Native fixed-step match simulation migrated from _core.Game orchestration.
## Data-driven combat; bespoke hero skill handlers/rigs remain explicit gaps.
signal notification(text: String)
signal match_finished(victory: bool)

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
var notifications: Array[String] = []


func clear_unit_refs() -> void:
	# BattleUnit is RefCounted; break target/source cycles before replacing a match.
	for unit: BattleUnit in all_units():
		unit.tactical_target = null
		unit.follow_target = null
		unit.killed_by = null


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
	blue_base.setup_castle(data, "blue", int(config.get("starting_castle_level", 1)))
	red_base.setup_castle(data, "red", int(config.get("castle_start_level", 1)) if hard else 1)
	blue_base.set_wave(data, 0)
	red_base.set_wave(data, 0)
	for row: Array in data.rule("BLUE_TOWERS", []):
		var tower := BattleUnit.new()
		tower.id = _id()
		tower.setup_tower(data, Vector2(float(row[0]), float(row[1])), "blue", str(row[2]))
		towers.append(tower)
	for row: Array in data.rule("RED_TOWERS", []):
		var tower := BattleUnit.new()
		tower.id = _id()
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
	_update_boss()
	_update_ai()
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
	for team: String in ["blue", "red"]:
		var spawn := waves.pop_spawn(team, spawn_delay)
		if spawn.is_empty():
			continue
		var minion := BattleUnit.new()
		minion.id = _id()
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
	active_boss.setup_boss(data, boss_type, data.lane("mid"))
	active_boss.apply_scaling(enemy_hp_mult, enemy_damage_mult, enemy_speed_mult)
	_notify(str(active_boss.stats.get("entrance_text", active_boss.display_name)))


func _update_unit(unit: BattleUnit) -> void:
	if not unit.alive or unit.status.stun_timer > 0:
		return
	var enemies := enemies_of(unit.team)
	var target := _nearest(unit.pos, enemies, unit.attack_range + 40.0)
	if unit.kind == BattleUnit.Kind.HERO:
		if is_instance_valid(unit.tactical_target) and unit.tactical_target.alive:
			target = unit.tactical_target
		elif unit.has_tactical_move:
			unit.pos = unit.pos.move_toward(unit.tactical_move, unit.effective_speed())
			if unit.pos.distance_to(unit.tactical_move) < 4.0:
				unit.has_tactical_move = false
			return
		elif is_instance_valid(unit.follow_target) and unit.follow_target.alive:
			unit.pos = unit.pos.move_toward(unit.follow_target.pos, unit.effective_speed())
			return
		elif unit.has_destination:
			unit.pos = unit.pos.move_toward(unit.destination, unit.effective_speed())
			if unit.pos.distance_to(unit.destination) < 4.0:
				unit.has_destination = false
			return
	if target != null and unit.pos.distance_to(target.pos) <= unit.attack_range + target.radius:
		_attack(unit, target)
		return
	if unit.kind == BattleUnit.Kind.MINION or unit.kind == BattleUnit.Kind.BOSS:
		_follow_path(unit)
	elif unit.kind == BattleUnit.Kind.HERO and target != null:
		unit.pos = unit.pos.move_toward(target.pos, unit.effective_speed())


func _follow_path(unit: BattleUnit) -> void:
	if unit.path.is_empty():
		return
	var direction := 1 if unit.team == "blue" else -1
	var next := clampi(unit.waypoint + direction, 0, unit.path.size() - 1)
	unit.pos = unit.pos.move_toward(unit.path[next], unit.effective_speed())
	if unit.pos.distance_to(unit.path[next]) < 2.0:
		unit.waypoint = next


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
	if attacker.attack_timer > 0:
		return
	attacker.attack_timer = attacker.effective_attack_cd()
	var amount := attacker.damage
	var damage_type := "physical"
	if attacker.kind == BattleUnit.Kind.TOWER or attacker.kind == BattleUnit.Kind.CASTLE:
		damage_type = "projectile"
	if attacker.kind == BattleUnit.Kind.HERO and attacker.items != null:
		var crit := attacker.items.sum_stat("crit_chance")
		if crit > 0.0 and rng.randf() < crit:
			amount *= maxf(1.0, attacker.items.sum_stat("crit_mult"))
	var dealt := target.take_damage(amount, attacker.team, damage_type, attacker)
	if attacker.kind == BattleUnit.Kind.HERO and attacker.items != null:
		attacker.heal(dealt * attacker.items.lifesteal())
	if attacker.kind == BattleUnit.Kind.TOWER:
		_apply_tower_effects(attacker, target)


func _apply_tower_effects(tower: BattleUnit, target: BattleUnit) -> void:
	var s := tower.stats
	if float(s.get("burn_dps", 0)) > 0:
		target.apply_debuff("burn", float(s.burn_dps), int(s.get("burn_duration", 120)), tower.team)
		var radius := float(s.get("splash", 0))
		if radius > 0:
			for unit: BattleUnit in enemies_of(tower.team):
				if unit != target and unit.pos.distance_to(target.pos) <= radius:
					unit.take_damage(tower.damage * 0.6, tower.team, "normal", tower)
					unit.apply_debuff(
						"burn", float(s.burn_dps), int(s.get("burn_duration", 120)), tower.team
					)
	if float(s.get("slow", 0)) > 0:
		target.apply_debuff("slow", float(s.slow), int(s.get("slow_duration", 90)))
		target.apply_debuff(
			"atk_slow", float(s.get("atk_slow", 0)), int(s.get("slow_duration", 90))
		)
		var aoe := float(s.get("slow_aoe", 0))
		if aoe > 0:
			for unit: BattleUnit in enemies_of(tower.team):
				if unit != target and unit.pos.distance_to(target.pos) <= aoe:
					unit.apply_debuff("slow", float(s.slow), int(s.get("slow_duration", 90)))
	if float(s.get("skill_down", 0)) > 0:
		target.apply_debuff("skill_down", float(s.skill_down), int(s.get("debuff_duration", 120)))
		target.apply_debuff(
			"anti_heal", float(s.get("anti_heal", 0)), int(s.get("debuff_duration", 120))
		)
		var chain := int(s.get("chain", 1))
		var hit := 1
		for unit: BattleUnit in enemies_of(tower.team):
			if hit >= chain:
				break
			if unit != target and unit.pos.distance_to(target.pos) <= 120.0:
				unit.take_damage(tower.damage * 0.7, tower.team, "magic", tower)
				unit.apply_debuff(
					"skill_down", float(s.skill_down), int(s.get("debuff_duration", 120))
				)
				hit += 1
	if bool(s.get("double_shot", false)):
		var second := _nearest(tower.pos, enemies_of(tower.team), tower.attack_range)
		if second != null and second != target:
			second.take_damage(tower.damage, tower.team, "projectile", tower)


func _update_tower(tower: BattleUnit) -> void:
	if tower.attack_timer > 0:
		return
	var target := _nearest(tower.pos, enemies_of(tower.team), tower.attack_range)
	if target != null:
		_attack(tower, target)


func _update_boss() -> void:
	if active_boss == null or not active_boss.alive:
		return
	var boss := active_boss
	boss.attack_timer = maxi(0, boss.attack_timer - 1)
	var ability_cd := int(boss.stats.get("ability_cooldown", 240))
	if frame % maxi(1, ability_cd) == 0:
		var radius := float(boss.stats.get("ability_range", 150))
		var amount := float(boss.stats.get("ability_damage", 100))
		for unit: BattleUnit in enemies_of("red"):
			if unit.pos.distance_to(boss.pos) <= radius:
				unit.take_damage(amount, "red", "magic", boss)


func _update_ai() -> void:
	ai_timer += 1
	if ai_timer < int(data.rule("AI_THINK_INTERVAL", 30)):
		return
	ai_timer = 0
	var max_heroes := int(data.rule("AI_MAX_HEROES", 5))
	if enemy_heroes.size() < max_heroes:
		for hero_type: String in data.rule("AI_HERO_PREFERENCES", []):
			var stats := data.hero(hero_type)
			var cost := int(stats.get("cost", 500))
			if ai_gold >= cost + int(data.rule("AI_MIN_GOLD_RESERVE", 200)):
				ai_gold -= cost
				var hero := BattleUnit.new()
				hero.id = _id()
				hero.setup_hero(data, hero_type, "red", Vector2(1100, 150))
				enemy_heroes.append(hero)
				break
	for slot: Dictionary in build_slots_red:
		if not bool(slot.taken) and ai_gold >= 300:
			ai_gold -= 100
			slot.taken = true
			var tower := BattleUnit.new()
			tower.id = _id()
			tower.setup_tower(data, slot.pos, "red", str(slot.lane))
			towers.append(tower)
			break
	for tower: BattleUnit in towers:
		if tower.team == "red" and tower.alive and tower.level < 3:
			var cost := tower.tower_upgrade_cost(data, "cannon" if tower.level == 1 else "")
			if cost > 0 and ai_gold >= cost + 200:
				ai_gold -= cost
				tower.upgrade_tower(data, "cannon" if tower.level == 1 else "")
				break


func _process_rewards() -> void:
	for minion: BattleUnit in minions:
		if not minion.alive and not minion.rewarded:
			minion.rewarded = true
			if minion.team == "red":
				gold += minion.gold_reward
				score += minion.gold_reward
				total_kills += 1
				combo += 1
				combo_timer = 180
				max_combo = maxi(max_combo, combo)
			else:
				ai_gold += minion.gold_reward
	for tower: BattleUnit in towers:
		if not tower.alive and not tower.rewarded:
			tower.rewarded = true
			if tower.team == "red":
				gold += tower.gold_reward
				score += tower.gold_reward
				red_towers_destroyed += 1
			else:
				ai_gold += tower.gold_reward
	for hero: BattleUnit in heroes + enemy_heroes:
		if not hero.alive and not hero.rewarded:
			hero.rewarded = true
			hero.respawn_timer = 600
			if hero.team == "red":
				gold += 150
				score += 150
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
	return selected_hero.cast_skill(key, enemies_of("blue"))


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
