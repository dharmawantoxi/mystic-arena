# gdlint:disable=max-file-lines
extends RefCounted
## Replays the source EffectManager coordinator through state/getter ports.
## No pygame drawing is part of this slice; only lifecycle, gates, caps and
## delegated state are compared.

const EffectManager = preload("res://scripts/ui/effect_manager.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/effect_manager_source.json"


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Effect manager fixture parses")
	if not (parsed is Dictionary):
		return
	var data: Dictionary = parsed
	check.call(
		int(data["max_floating"]) == EffectManager.MAX_FLOATING,
		"Effect manager floating cap matches source"
	)
	check.call(
		int(data["max_particles"]) == EffectManager.MAX_PARTICLES,
		"Effect manager particle cap matches source"
	)
	check.call(
		int(data["max_explosions"]) == EffectManager.MAX_EXPLOSIONS,
		"Effect manager explosion cap matches source"
	)
	for case_value in data["cases"]:
		_replay_case(case_value as Dictionary, check)
	_check_caps(check)
	_check_runtime_wiring(check)


func _replay_case(case_data: Dictionary, check: Callable) -> void:
	var manager := EffectManager.new()
	var settings: Dictionary = case_data["settings"]
	manager.set_quality_settings(
		bool(settings["damage_numbers_enabled"]),
		bool(settings["particles"]),
		float(settings["particle_ratio"]),
		int(settings["max_damage_numbers"]),
		bool(settings["screen_shake_enabled"])
	)
	var operations: Array = case_data["operations"]
	var outputs: Array = case_data["outputs"]
	var label: String = String(case_data["name"])
	for index in range(operations.size()):
		_apply_operation(manager, operations[index] as Dictionary, outputs[index]["replay"])
		check.call(
			_deep_equal(manager.get_state(), outputs[index]["snapshot"] as Dictionary),
			(
				"Effect manager state matches source: %s #%d %s"
				% [label, index, operations[index]["op"]]
			)
		)


func _apply_operation(manager: RefCounted, operation: Dictionary, replay: Variant) -> void:
	var op: String = String(operation["op"])
	match op:
		"settings":
			manager.set_quality_settings(
				bool(operation["damage_numbers_enabled"]),
				bool(operation["particles"]),
				float(operation["particle_ratio"]),
				int(operation["max_damage_numbers"]),
				bool(operation["screen_shake_enabled"]),
				bool(operation.get("sync", false))
			)
		"damage":
			if replay is Dictionary:
				var damage_replay: Dictionary = replay
				manager.add_damage_number(
					float(operation["x"]),
					float(operation["y"]),
					operation["damage"],
					bool(operation.get("is_critical", false)),
					String(operation.get("damage_type", "normal")),
					float(damage_replay["offset_x"]),
					float(damage_replay["offset_y"]),
					float(damage_replay["drift"])
				)
			else:
				manager.add_damage_number(
					float(operation["x"]),
					float(operation["y"]),
					operation["damage"],
					bool(operation.get("is_critical", false)),
					String(operation.get("damage_type", "normal"))
				)
		"gold":
			var gold_replay: Dictionary = replay
			manager.add_gold_popup(
				float(operation["x"]),
				float(operation["y"]),
				operation["amount"],
				float(gold_replay["drift"])
			)
		"particles":
			var particle_replay: Dictionary = replay if replay is Dictionary else {}
			manager.add_hit_particles(
				float(operation["x"]),
				float(operation["y"]),
				String(operation["team"]),
				int(operation["count"]),
				particle_replay.get("specs", [])
			)
		"explosion":
			var explosion_replay: Dictionary = replay
			manager.add_death_explosion(
				float(operation["x"]),
				float(operation["y"]),
				String(operation["team"]),
				String(operation["size"]),
				explosion_replay["specs"]
			)
		"shake":
			manager.shake_screen(float(operation["intensity"]))
		"path":
			manager.show_path_preview(operation["paths"] as Array)
		"wave":
			manager.announce_wave(int(operation["wave_num"]))
		"achievement":
			manager.unlock_achievement(
				String(operation["title"]),
				String(operation["description"]),
				String(operation["icon"])
			)
		"kill":
			manager.register_kill(
				String(operation["killer"]), String(operation["victim"]), String(operation["team"])
			)
		"update":
			for _step in range(int(operation["steps"])):
				manager.update()


func _check_caps(check: Callable) -> void:
	var manager := EffectManager.new()
	manager.set_quality_settings(true, true, 1.0, EffectManager.MAX_FLOATING, true)
	for index in range(EffectManager.MAX_FLOATING + 5):
		manager.add_damage_number(float(index), 0.0, index, false, "normal", 0.0, 0.0, 0.0)
	check.call(
		manager.floating_texts.size() == EffectManager.MAX_FLOATING,
		"Effect manager hard floating cap evicts oldest"
	)
	for index in range(EffectManager.MAX_PARTICLES + 5):
		manager.add_hit_particles(
			float(index),
			0.0,
			"red",
			1,
			[{"color": [255, 150, 100], "vx": 0.0, "vy": 0.0, "lifetime": 20, "size": 2}]
		)
	check.call(
		manager.particles.size() == EffectManager.MAX_PARTICLES,
		"Effect manager hard particle cap evicts oldest"
	)
	for index in range(EffectManager.MAX_EXPLOSIONS + 5):
		manager.add_death_explosion(
			float(index),
			0.0,
			"red",
			"small",
			[{"color": [255, 100, 100], "vx": 0.0, "vy": 0.0, "lifetime": 20, "size": 2}]
		)
	check.call(
		manager.explosions.size() == EffectManager.MAX_EXPLOSIONS,
		"Effect manager hard explosion cap evicts oldest"
	)


func _check_runtime_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	check.call(
		world.effects != null and world.effects is EffectManager,
		"Prototype owns a single EffectManager coordinator"
	)
	world.effects.set_quality_settings(true, true, 1.0, EffectManager.MAX_FLOATING, true)

	# Combo state delegates directly to effects.combo_counter without duplication.
	var goblin := world.spawn_unit(GOBLIN, world.RED, 1)
	var hero := world.blue_hero()
	check.call(goblin != null and hero != null, "Runtime wiring spawns test actors")
	if goblin == null or hero == null:
		return
	world._deliver_hit(hero.id, world.BLUE, goblin, 10, "physical", hero.position)
	check.call(
		not world.effects.floating_texts.is_empty() and not world.effects.particles.is_empty(),
		"Unit hit populates EffectManager floating texts and hit particles"
	)
	world._deliver_hit(hero.id, world.BLUE, goblin, 500, "physical", hero.position)
	check.call(
		(
			world.combo_count == 1
			and world.effects.combo_counter.count == 1
			and world.combo_timer == world.effects.combo_counter.timer
			and not world.effects.explosions.is_empty()
		),
		"Red minion death updates combo_counter, gold popup and death explosion via EffectManager"
	)
	world._step_combo_clock()
	check.call(
		world.combo_timer == 119 and world.effects.combo_counter.timer == 119,
		"_step_combo_clock advances EffectManager update without duplicate combo state"
	)

	# Wave 1 start announces wave and shows lane path preview, then ticks once in step_tick.
	var wave_world := Prototype.new()
	wave_world.setup_arena()
	wave_world.scheduler.timer = 1
	wave_world.step_tick()
	var wave_state: Dictionary = wave_world.effects.get_state()
	check.call(
		(
			bool(wave_state["wave_announcer_active"])
			and int(wave_state["wave_announcer_wave"]) == 1
			and int(wave_state["wave_announcer_timer"]) == 119
			and bool(wave_state["path_preview_active"])
			and int(wave_state["path_preview_timer"]) == 119
		),
		"Wave 1 start wires announce_wave, show_path_preview and per-tick update"
	)

	# Shield activation and item notify route through EffectManager floating texts.
	wave_world.economy.gold[wave_world.BLUE] = 5000
	var nexus := wave_world.nexuses[wave_world.BLUE]
	nexus.set_wave(11)
	var before_texts: int = wave_world.effects.floating_texts.size()
	check.call(
		wave_world.activate_player_castle_shield(nexus.id),
		"Castle shield activates for EffectManager wiring check"
	)
	var bus := wave_world._battle_item_effects(wave_world.blue_hero())
	bus.notify(Vector2(200.0, 200.0), "PROC!", "magic")
	check.call(
		wave_world.effects.floating_texts.size() == before_texts + 2,
		"Castle shield and BattleItemEffects.notify route floating texts to EffectManager"
	)

	# Hero death and boss defeat route kill feed, screen shake and achievements to EffectManager.
	var red_hero := wave_world.spawn_hero(KAIZEN, wave_world.RED, Vector2(400.0, 300.0))
	wave_world._on_hero_death(red_hero, wave_world.blue_hero().id)
	check.call(
		not wave_world.effects.kill_feed.entries.is_empty(),
		"Hero death registers kill in EffectManager kill_feed"
	)
	var boss := wave_world._spawn_boss("gornak")
	boss.team = wave_world.RED
	boss.position = Vector2(700.0, 300.0)
	boss.entrance_timer = 0
	boss.hp = 10.0
	wave_world._deliver_hit(
		wave_world.blue_hero().id, wave_world.BLUE, boss, 200, "physical", boss.position
	)
	check.call(
		is_equal_approx(wave_world.effects.screen_shake.intensity, 20.0),
		"Mini-boss death triggers EffectManager screen shake"
	)
	wave_world._process_boss_result()
	wave_world._auto_unlock_defeated_boss_heroes()
	wave_world.effects.update()
	var boss_state: Dictionary = wave_world.effects.get_state()
	check.call(
		(
			bool(boss_state["achievement_showing"])
			and String(boss_state["achievement_title"]) == "MINI BOSS SLAYER!"
			and int(boss_state["achievement_queue"]) >= 2
		),
		"Boss kill and unlock wire achievements into EffectManager popup queue"
	)


func _deep_equal(left: Variant, right: Variant) -> bool:
	var equal := false
	if left is Dictionary and right is Dictionary:
		var left_dict: Dictionary = left
		var right_dict: Dictionary = right
		equal = left_dict.size() == right_dict.size()
		if equal:
			for key in left_dict:
				if not right_dict.has(key) or not _deep_equal(left_dict[key], right_dict[key]):
					equal = false
					break
	elif left is Array and right is Array:
		var left_array: Array = left
		var right_array: Array = right
		equal = left_array.size() == right_array.size()
		if equal:
			for index in range(left_array.size()):
				if not _deep_equal(left_array[index], right_array[index]):
					equal = false
					break
	elif (left is int or left is float) and (right is int or right is float):
		equal = is_equal_approx(float(left), float(right))
	else:
		equal = left == right
	return equal
