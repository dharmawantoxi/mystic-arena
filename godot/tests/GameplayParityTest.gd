# Compare real Godot nodes with golden cases evaluated by the Pygame code.
# python tools/test_godot_match_parity.py   (fixture freshness)
# godot --headless --path godot res://tests/GameplayParityTest.tscn --quit-after 180
extends Node

const RendererRegistry = preload("res://scripts/render/RendererRegistry.gd")
const MainScene = preload("res://scenes/main.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

var _main = null
var _fixture: Dictionary = {}
var _save_before: Dictionary = {}
var _failures: int = 0
var _checks: int = 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	# Manual, deterministic clock. No wall-clock sleeps or player save writes.
	GameManager.set_process(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	_main = MainScene.instantiate()
	add_child(_main)
	_main.set_process(false)
	_main._ai.set_process(false)
	var containers: Node = GameManager.hero_container.get_parent()
	containers.process_mode = Node.PROCESS_MODE_DISABLED
	await get_tree().process_frame

	# Backfill never revokes previous unlocks, but a new/empty roster grants
	# only Kaizen, NOT all six catalog starters.
	SaveManager.data["unlocked_heroes"] = []
	SaveManager._backfill()
	_expect(SaveManager.data["unlocked_heroes"] == ["kaizen"], "Only Kaizen is granted by default")
	SaveManager.data["unlocked_heroes"] = ["kaizen", "abaddon"]
	SaveManager._backfill()
	_expect(SaveManager.is_unlocked("abaddon"), "Existing unlocks must survive backfill")
	SaveManager.data["unlocked_heroes"] = ["kaizen"]

	GameManager.start_level(1)
	await get_tree().process_frame
	await get_tree().process_frame
	_test_startup()
	_main._on_key(_key(KEY_SPACE))
	await get_tree().process_frame
	_expect(not get_tree().paused, "Intro skip must resume gameplay")
	_main._main_menu().close()
	var initial_gold := GameManager.gold
	var initial_difficulty := GameManager.difficulty
	var initial_theme: String = _main._arena_map.theme_name
	for code in [KEY_D, KEY_T, KEY_F1, KEY_SPACE]:
		_main._on_key(_key(code))
	_expect(GameManager.difficulty == initial_difficulty, "D cannot change difficulty in a normal match")
	_expect(_main._arena_map.theme_name == initial_theme, "T cannot change the normal match theme")
	_expect(GameManager.gold == initial_gold and GameManager.owned_heroes().is_empty(),
		"Debug shortcuts cannot summon heroes or restart the normal match")
	# FASE 18: D/T kini hotkey taktis (hold_start). Tuts sungguhan pasti
	# dilepas — KEYUP di sini mencegah hold "dipersenjatai" menembak
	# belakangan saat hero sudah dibeli di tes-tes berikutnya.
	for code in [KEY_D, KEY_T]:
		_main._on_key(_keyup(code))

	_test_economy()
	_test_purchases_and_respawn()
	_test_ai_ownership()
	_test_wave_and_minion_fixtures()
	_test_wave_queue()
	_test_boss_schedule()
	await _test_restart_and_menu()
	_finish()


func _test_startup() -> void:
	var rules: Dictionary = _fixture["rules"]
	_expect(RendererRegistry.hero_scene("kaizen") == RendererRegistry.BakedSpriteScene,
		"Default Kaizen uses the original Pygame bake, not the experimental rig")
	_expect(GameManager.owned_heroes("blue").is_empty(), "No free player roster")
	_expect(GameManager.owned_heroes("red").is_empty(), "AI must purchase its own roster")
	_expect(get_tree().get_nodes_in_group("nexus").size() == 2, "Both nexuses exist before wave 1")
	_expect(GameManager.build_slots.size() == 18, "18 empty build slots")
	_expect(get_tree().get_nodes_in_group("minions").is_empty(), "No minions during intro")
	_expect(GameManager.wave_number == 0, "Match begins at wave 0")
	_expect(get_tree().paused and GameManager.is_paused, "Intro pauses both clocks")
	_expect(not GameManager.can_buy_hero("kaizen"), "Cannot buy through the paused intro")
	_near(GameManager._wave_timer, rules["first_wave_delay"], "Initial 5-second preparation")
	_near(GameManager.HERO_RESPAWN_DELAY, rules["hero_respawn_delay"], "Pygame respawn delay")
	_near(GameManager.wave_interval, rules["wave_interval"], "Pygame wave interval")
	_near(GameManager.minion_spawn_delay, rules["spawn_delay"], "Pygame spawn cadence")
	_expect(GameManager.max_heroes_owned == int(rules["max_heroes_owned"]), "Pygame roster cap")
	_expect(GameManager.ai_gold == int(rules["ai_starting_gold"]), "AI starts with 350, not player gold")
	GameManager._process(100.0)
	_expect(GameManager.wave_number == 0, "Paused intro cannot advance waves")
	_near(GameManager._wave_timer, rules["first_wave_delay"], "Intro does not consume preparation")


func _test_economy() -> void:
	for c in _fixture["economy"]:
		var level_num := int(c["level"])
		var cfg: Dictionary = BossDB.get_level(level_num)
		_expect(GameManager.compute_starting_gold(cfg, level_num, c["difficulty"]) == int(c["gold"]),
			"Starting gold L%d %s" % [level_num, c["difficulty"]])
		_near(GameManager.compute_gold_per_second(level_num, c["difficulty"]), c["income"],
			"Player income L%d %s" % [level_num, c["difficulty"]])
	GameManager.waves_enabled = false
	for c in _fixture["ai_income"]:
		GameManager.wave_number = int(c["wave"])
		GameManager.ai_gold = 0
		GameManager._gold_timer = 0.0
		GameManager._process(1.0)
		_expect(GameManager.ai_gold == int(c["gold"]), "AI income includes wave bonus")
	GameManager.gold = 0
	GameManager.gold_per_second = 7.125
	GameManager._gold_income_milli = 0
	GameManager._gold_timer = 0.0
	GameManager._process(8.0)
	_expect(GameManager.gold == 57, "Fractional income and long frames must not lose gold")


func _test_purchases_and_respawn() -> void:
	GameManager.gold = 100000
	var balance := GameManager.gold
	_expect(not GameManager.try_buy_hero("not-a-hero"), "Reject unknown hero")
	_expect(not GameManager.try_buy_hero("grimjaw"), "Reject locked hero at API boundary")
	_expect(GameManager.gold == balance, "Rejected purchase cannot spend gold")
	var cost := int(HeroDB.get_hero("kaizen")["cost"])
	GameManager.gold = cost - 1
	_expect(not GameManager.try_buy_hero("kaizen"), "Reject insufficient gold")
	GameManager.gold = balance
	_expect(GameManager.try_buy_hero("kaizen"), "Unlocked hero can be purchased")
	_expect(GameManager.gold == balance - cost, "Purchase charges exact catalog cost")
	var hero = GameManager.owned_heroes()[0]
	_expect(hero.custom_visual != null and hero.custom_visual._built, "Purchased Kaizen has a loaded Pygame bake")
	_expect(hero.custom_visual.sprite.sprite_frames.get_frame_count(&"idle") > 0, "Kaizen idle frames exist at runtime")
	_expect(hero.global_position == _main._arena_map.radiant_shop_pos + Vector2(50, 10),
		"First purchase spawns in front of the Radiant shop")
	_expect(not GameManager.try_buy_hero("kaizen"), "Reject duplicate hero")
	SaveManager.data["unlocked_heroes"] = ["kaizen", "grimjaw", "sylara", "thorne", "vex", "zephyr"]
	for ht in ["grimjaw", "sylara", "thorne", "vex"]:
		_expect(GameManager.try_buy_hero(ht), "Fill roster: " + ht)
	_expect(GameManager.owned_heroes().size() == 5, "Five unique heroes purchased")
	_expect(not GameManager.try_buy_hero("zephyr"), "Reject sixth hero")

	_expect(hero.upgrade(), "Hero upgrade available before death")
	_expect(hero.buy_item("dead_edge"), "Persistent item equipped")
	_expect(hero.buy_item("holy_rapier"), "Drop-on-death item equipped")
	var inventory = hero.items
	var hero_level := int(hero.level)
	hero.kills = 7
	# State skill kini FIELD HERO berbasis frame (paritas _entity.py); mesin
	# lama (SkillBook.cds dalam detik) sudah jadi facade UI tanpa state.
	hero.r_cooldown = 540           # 9 s x 60 fps — cooldown R "sedang jalan"
	hero.active_skill = "r"
	hero.active_skill_timer = 60
	hero.kit["_powershot_charging"] = true   # nama field persis _bundle.py:4403
	hero.kit["_powershot_timer"] = 60
	hero.status.apply_stun(5.0)
	var tower = GameManager.spawn_tower("blue", Vector2(220, 500))
	var minion = GameManager.spawn_minion("goblin", "red", Vector2(900, 100))
	var nexus = GameManager.blue_nexus
	nexus.hp -= 123.0
	var nexus_hp := float(nexus.hp)
	_main.red_towers_destroyed = 4
	var wave_before := GameManager.wave_number
	for h in GameManager.owned_heroes():
		h.die()
	hero.die() # duplicate event must neither re-credit a kill nor reset the timer
	_expect(GameManager.owned_heroes().size() == 5, "Dead heroes remain owned")
	_expect(not GameManager.try_buy_hero("kaizen"), "Cannot repurchase a dead hero")
	_expect(not GameManager.try_buy_hero("zephyr"), "Dead heroes still consume roster capacity")
	_expect(not hero.visible and hero.collision_layer == 0, "Dead hero is hidden and nonblocking")
	_expect(not inventory.has("holy_rapier") and inventory.has("dead_edge"), "Only Holy Rapier drops")
	_expect(bool(hero.kit.get("_powershot_charging")),
		"Death freezes delayed casts (paritas: charge jalan lagi post-respawn)")

	GameManager.set_paused(true)
	GameManager._process(60.0)
	_near(GameManager.hero_respawn_remaining(hero), 10.0, "Pause freezes respawn")
	GameManager.set_paused(false)
	GameManager._process(9.9)
	_expect(hero.is_dead, "Hero must not respawn before 10 seconds")
	GameManager._process(0.1)
	_expect(not hero.is_dead and hero.visible, "Hero respawns after 10 seconds")
	_expect(hero.items == inventory and hero.level == hero_level and hero.kills == 7,
		"Same hero instance keeps level, items and kill statistics")
	_near(hero.hp, hero.max_hp, "Respawn restores full HP")
	_expect(hero.status.stun_timer == 0.0, "Respawn clears debuffs")
	_near(float(hero.r_cooldown), 540.0, "Death does not reset QWER cooldowns")
	_expect(hero.skill_timer <= 0, "Respawn resets Q ready (paritas respawn)")
	_expect(str(hero.active_skill) == "r",
		"Respawn keeps active_skill (pygame respawn tidak menyentuhnya)")
	_expect(hero.global_position == hero.own_base() + Vector2(60, -30), "Respawn at own base")
	_expect(hero.collision_layer == 2 and hero.is_physics_processing(), "Respawn restores physics")
	_expect(is_instance_valid(tower) and is_instance_valid(minion), "Team wipe does not erase the battlefield")
	_expect(GameManager.blue_nexus == nexus and nexus.hp == nexus_hp, "Team wipe does not heal/recreate nexus")
	_expect(GameManager.wave_number == wave_before and _main.red_towers_destroyed == 4,
		"Team wipe does not reset wave or boss progression")
	_expect(GameManager._hero_respawn_timers.is_empty(), "All independent respawn timers finish")


func _test_ai_ownership() -> void:
	_reset_field()
	var ai = _main._ai
	ai.reset()
	GameManager.ai_gold = 100000
	var dead_hero = GameManager.spawn_hero("grimjaw", "red", Vector2(1100, 150))
	dead_hero.die()
	_expect(ai._red_heroes().has(dead_hero), "AI roster includes heroes waiting to respawn")
	ai._hero_purchase_target = "grimjaw"
	_expect(ai._try_buy_hero(), "AI can purchase another available hero")
	var duplicates := 0
	for hero in GameManager.owned_heroes("red"):
		if hero.hero_type == "grimjaw":
			duplicates += 1
	_expect(duplicates == 1, "AI must not rebuy its dead draft target")
	for _i in range(3):
		_expect(ai._try_buy_hero(), "AI fills its own roster through purchases")
	for hero in GameManager.owned_heroes("red"):
		hero.die()
	var balance := GameManager.ai_gold
	_expect(not ai._try_buy_hero(), "AI cannot exceed five owned heroes after a wipe")
	_expect(GameManager.ai_gold == balance, "Rejected AI purchase is free of side effects")


func _test_wave_and_minion_fixtures() -> void:
	_reset_field()
	for c in _fixture["waves"]:
		for team in ["blue", "red"]:
			_set_nexus_level(GameManager.blue_nexus, int(c["castle_level"]) if team == "blue" else 5)
			_set_nexus_level(GameManager.red_nexus, int(c["castle_level"]) if team == "red" else 5)
			_expect(GameManager.wave_composition(int(c["wave"]), team) == c["composition"],
				"%s wave %d / castle %d matches Pygame" % [team, c["wave"], c["castle_level"]])
	for c in _fixture["ai_castle"]:
		_set_nexus_level(GameManager.red_nexus, 1)
		GameManager.wave_number = int(c["wave"])
		GameManager._auto_scale_ai_nexus()
		_expect(GameManager.red_nexus.level == int(c["level"]), "AI castle wave escalation matches Pygame")
	_set_nexus_level(GameManager.red_nexus, 5)
	GameManager.wave_number = 1
	GameManager._auto_scale_ai_nexus()
	_expect(GameManager.red_nexus.level == 5, "Wave escalation cannot downgrade an upgraded nexus")

	GameManager.enemy_scaling_enabled = false
	for c in _fixture["minions"]:
		for team in ["blue", "red"]:
			_set_nexus_level(GameManager.blue_nexus, int(c["castle_level"]) if team == "blue" else 5)
			_set_nexus_level(GameManager.red_nexus, int(c["castle_level"]) if team == "red" else 5)
			GameManager._spawn_wave_minion(team, {"type": c["type"], "lane": "top"})
			var minion = get_tree().get_nodes_in_group("minions").back()
			for field in ["max_hp", "damage", "move_speed", "attack_range", "attack_cooldown",
					"gold_reward", "regen_per_second", "ai_level"]:
				_near(minion.get(field), c[field], "%s %s castle %d: %s" % [team, c["type"], c["castle_level"], field])
			_expect(not minion.lane_path.is_empty(), "Wave spawn carries a real lane path")
			minion.free()

	# Enemy scaling is applied AFTER integer nexus scaling, only to red.
	_set_nexus_level(GameManager.blue_nexus, 3)
	_set_nexus_level(GameManager.red_nexus, 3)
	GameManager.enemy_scaling_enabled = true
	GameManager.enemy_hp_mult = 1.37
	GameManager.enemy_damage_mult = 1.21
	GameManager.enemy_speed_mult = 1.05
	for c in _fixture["minions"]:
		if c["type"] != "orc" or int(c["castle_level"]) != 3:
			continue
		for team in ["blue", "red"]:
			GameManager._spawn_wave_minion(team, {"type": "orc", "lane": "mid"})
			var minion = get_tree().get_nodes_in_group("minions").back()
			var hp := float(int(float(c["max_hp"]) * 1.37)) if team == "red" else float(c["max_hp"])
			var damage := float(int(float(c["damage"]) * 1.21)) if team == "red" else float(c["damage"])
			_near(minion.max_hp, hp, "Hard HP scaling applies only to red, after truncation")
			_near(minion.damage, damage, "Hard damage scaling applies only to red, after truncation")
			_near(minion.move_speed, float(c["move_speed"]) * (1.05 if team == "red" else 1.0), "Hard speed scaling")
			minion.free()
	GameManager.enemy_scaling_enabled = false

	# Path direction is behavioral, not merely a lane label on a diagonal mover.
	var path := PackedVector2Array([Vector2(100, 100), Vector2(100, 240), Vector2(250, 240)])
	for team in ["blue", "red"]:
		var pos := path[0] if team == "blue" else path[2]
		var minion = GameManager.spawn_minion("goblin", team, pos, 1.0, "top", path)
		# DISABLED containers remove CollisionObject bodies from their space.
		# Keep this manual path probe registered, but without automatic ticks.
		minion.process_mode = Node.PROCESS_MODE_ALWAYS
		minion.set_physics_process(false)
		minion._follow_lane(90.0) # reach spawn waypoint
		_expect(minion.waypoint_index == 1, "Both teams advance inward from their own path endpoint")
		minion._follow_lane(90.0)
		var expected := Vector2(0, 90) if team == "blue" else Vector2(-90, 0)
		_expect(minion.velocity.is_equal_approx(expected), "Minion follows lane, not enemy-base shortcut")
		minion.free()

	# Scene shape resources must not be shared between different minion sizes.
	var goblin = GameManager.spawn_minion("goblin", "blue", Vector2.ZERO)
	var troll = GameManager.spawn_minion("troll", "blue", Vector2(500, 500))
	var goblin_collider: CollisionShape2D = goblin.get_node(NodePath("CollisionShape2D"))
	var troll_collider: CollisionShape2D = troll.get_node(NodePath("CollisionShape2D"))
	_near(goblin_collider.shape.radius, 9.0, "A troll spawn cannot enlarge an existing goblin")
	_near(troll_collider.shape.radius, 14.0, "Troll keeps its own radius")
	_expect(goblin_collider.shape != troll_collider.shape, "Minion colliders are per-instance")
	goblin.free()
	troll.free()


func _test_wave_queue() -> void:
	_reset_field()
	GameManager.waves_enabled = true
	GameManager._reset_wave_state(GameManager.FIRST_WAVE_DELAY)
	GameManager._update_waves(4.99)
	_expect(GameManager.wave_number == 0, "Preparation is not skipped")
	GameManager._update_waves(0.01)
	_expect(GameManager.wave_number == 1, "First wave starts after preparation")
	for team in ["blue", "red"]:
		_expect(GameManager.count_alive("minions", team) == 1, "Only first minion arrives with wave banner")
	GameManager._update_waves(GameManager.minion_spawn_delay * 0.5)
	_expect(GameManager.count_alive("minions", "blue") == 1, "Spawn delay is respected")
	GameManager._update_waves(GameManager.minion_spawn_delay * 0.5 - 0.001)
	_expect(GameManager.count_alive("minions", "blue") == 1, "Idle time cannot shorten the second spawn interval")
	GameManager._update_waves(0.001)
	_expect(GameManager.count_alive("minions", "blue") == 2, "Second minion arrives after a full spawn interval")
	_drain_queues()
	for team in ["blue", "red"]:
		var counts := {"top": 0, "mid": 0, "bot": 0}
		for minion in get_tree().get_nodes_in_group("minions"):
			if minion.team != team:
				continue
			counts[minion.lane] += 1
			var endpoint: Array = _fixture["lane_endpoints"][minion.lane][team]
			_expect(minion.global_position == Vector2(endpoint[0], endpoint[1]), "Spawn at correct lane endpoint")
		_expect(counts == {"top": 3, "mid": 3, "bot": 3}, "Full initial composition on all three lanes")
	GameManager._update_waves(30.0)
	_expect(GameManager.wave_number == 1, "Living minions hold back next wave even after 25 seconds")
	for minion in get_tree().get_nodes_in_group("minions"):
		minion.is_dead = true
	GameManager._update_waves(1.0 / 60.0)
	_expect(GameManager.wave_number == 2, "Corpses cannot block the next wave")
	GameManager._wave_timer = 0.0
	for minion in get_tree().get_nodes_in_group("minions"):
		minion.is_dead = true
	_expect(not GameManager.next_wave(), "Nonempty spawn queues also block next wave")
	var queued: int = GameManager.spawn_queues["blue"].size()
	GameManager.set_paused(true)
	GameManager._process(30.0)
	_expect(GameManager.spawn_queues["blue"].size() == queued, "Pause freezes spawn queues")
	GameManager.set_paused(false)

	_reset_field()
	_set_nexus_level(GameManager.blue_nexus, 5)
	_set_nexus_level(GameManager.red_nexus, 5)
	GameManager.wave_number = 12
	_expect(GameManager.next_wave(), "Elite wave can start on a clear field")
	_drain_queues()
	_expect(GameManager.count_alive("minions", "blue") == 33, "Elite blue wave is not truncated at 24 minions")
	_expect(GameManager.count_alive("minions", "red") == 33, "Elite red wave is not truncated at 24 minions")
	GameManager.waves_enabled = false


func _test_boss_schedule() -> void:
	var previous := GameManager.difficulty
	for mode in ["easy", "normal", "hard"]:
		GameManager.difficulty = mode
		for level_num in [1, 20, 54]:
			GameManager.level_number = level_num
			var cfg: Dictionary = BossDB.get_level(level_num)
			for _i in range(12):
				var schedule: Dictionary = _main._roll_mini_boss_schedule()
				_expect(schedule.values() == cfg["mini_bosses"].values(), "Random schedule preserves boss order/types")
				for wave in schedule:
					var low := 20 if mode == "easy" else 11
					var high := 40 if mode == "easy" else 30
					_expect(int(wave) >= low and int(wave) <= high, "Boss wave respects difficulty bounds")
	GameManager.difficulty = previous
	GameManager.level_number = 1


func _test_restart_and_menu() -> void:
	var hero = GameManager.spawn_hero("kaizen", "blue", Vector2.ZERO)
	hero.die()
	GameManager.spawn_queues["blue"].append({"type": "goblin", "lane": "top"})
	GameManager.start_level(2)
	_expect(GameManager._hero_respawn_timers.is_empty(), "New match clears old respawn callbacks")
	_expect(GameManager.spawn_queues["blue"].is_empty(), "New match clears old spawn queue")
	await get_tree().process_frame
	await get_tree().process_frame
	_expect(not is_instance_valid(hero), "Old match hero is freed, not resurrected into the next match")
	_expect(GameManager.wave_number == 0 and GameManager.owned_heroes().is_empty(), "Restart has no demo roster/wave")
	_main._on_key(_key(KEY_SPACE))
	_main._on_menu_main_menu()
	_expect(GameManager.in_menu and GameManager.state == "idle", "Return to menu ends simulation")
	_expect(GameManager.spawn_queues["red"].is_empty(), "Menu clears both queues")
	GameManager._process(100.0)
	_expect(GameManager.wave_number == 0, "Menu cannot advance waves or respawn heroes")


func _reset_field() -> void:
	_main._clear_field()
	_main._reset_boss_schedule()
	_main._spawn_nexuses()
	_main._generate_build_slots()
	GameManager._hero_respawn_timers.clear()
	GameManager._reset_wave_state()
	GameManager.wave_number = 0


func _set_nexus_level(nexus, level_num: int) -> void:
	nexus.level = level_num
	nexus._apply_level_stats()


func _drain_queues() -> void:
	var guard := 0
	while guard < 100 and (not GameManager.spawn_queues["blue"].is_empty() \
			or not GameManager.spawn_queues["red"].is_empty()):
		GameManager._update_waves(GameManager.minion_spawn_delay)
		guard += 1
	_expect(guard < 100, "Spawn queues drain without blocking on the next-wave timer")


func _key(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = true
	return event


func _keyup(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = false
	return event


func _near(actual: float, expected: float, message: String) -> void:
	_expect(absf(actual - expected) < 0.0001, "%s (got %s, expected %s)" % [message, actual, expected])


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		push_error("[GameplayParityTest] " + message)


func _finish() -> void:
	get_tree().paused = false
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager._hero_respawn_timers.clear()
	GameManager._reset_wave_state()
	_main.free()
	SaveManager.data = _save_before
	GameManager.set_process(true)
	if _failures == 0:
		print("[GameplayParityTest] PASS: %d checks against Pygame + match lifecycle" % _checks)
	get_tree().quit(0 if _failures == 0 else 1)
