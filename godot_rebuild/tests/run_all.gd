class_name MysticTestRunner
extends SceneTree

## Native regression tests. Run after --editor --import, not as a gameplay demo.
const State := preload("res://scripts/core/AppState.gd")
const Clock := preload("res://scripts/core/FixedClock.gd")
const Gesture := preload("res://scripts/core/GestureTracker.gd")
var checks := 0
var failures := 0


func _initialize() -> void:
	call_deferred("_run")


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)


func near(a: float, b: float) -> bool:
	return absf(a - b) < 0.000001


func _run() -> void:
	_test_state()
	_test_clock()
	_test_gestures()
	_test_settings()
	_test_core_data()
	_test_core_rules()
	_test_core_save()
	_test_core_services()
	_test_core_match()
	_test_hud()
	await _test_app()
	await _test_audio()
	await _test_core_game()
	print(
		(
			"PASS: %d checks; fixed ticks, input ownership, lifecycle, audio and UI (%d failures)"
			% [checks, failures]
		)
	)
	quit(1 if failures else 0)


func _test_state() -> void:
	var state := State.new()
	check(state.current == State.Kind.SPLASH, "initial splash")
	check(not state.transition(State.Kind.GAME), "no splash -> game shortcut")
	check(state.transition(State.Kind.MENU), "splash -> menu")
	check(state.transition(State.Kind.GAME), "menu -> game")
	check(state.simulates_game(), "game runs simulation")
	check(state.transition(State.Kind.PAUSE), "game -> pause")
	check(not state.simulates_game(), "pause stops simulation")
	check(not state.transition(State.Kind.SPLASH), "no invalid pause -> splash")
	check(state.transition(State.Kind.GAME), "pause -> game")
	check(state.transition(State.Kind.MENU), "game -> menu")
	check(not state.simulates_game(), "menu does not simulate")


func _test_clock() -> void:
	var clock := Clock.new()
	check(clock.advance(1.0 / 120.0) == 0, "120 Hz render accumulates")
	check(clock.advance(1.0 / 120.0) == 1, "two render frames = one tick")
	clock.reset()
	check(clock.advance(1.0 / 15.0) == 4, "15 FPS catches up four ticks")
	check(near(clock.accumulator, 0.0), "exact catch-up has no residual")
	clock.reset()
	check(clock.advance(10.0) == 4, "long stall capped at four")
	check(clock.capped_frames == 2, "both catch-up limits counted")
	check(clock.accumulator <= Clock.STEP * 3.0, "bounded residual")
	clock.reset()
	check(clock.advance(-1.0) == 0, "negative delta ignored")
	var slow := Clock.new()
	var fast := Clock.new()
	for _frame in range(30):
		slow.advance(1.0 / 30.0)
	for _frame in range(60):
		fast.advance(1.0 / 60.0)
	check(slow.total_steps == fast.total_steps, "30/60 FPS simulate one second equally")
	var paused_ticks := slow.total_steps
	for _frame in range(60):
		pass
	check(slow.total_steps == paused_ticks, "no advance calls = no simulation")


func _test_gestures() -> void:
	var touch := Gesture.new()
	touch.down(1, Vector2(100, 100), 0.0)
	touch.up(1, Vector2(105, 105), 0.1)
	var actions := touch.collect()
	check(actions[1].kind == "tap", "small movement remains tap")
	touch.down(1, Vector2(100, 100), 0.2)
	touch.up(1, Vector2(100, 100), 0.3)
	check(touch.collect()[1].kind == "double_tap", "double tap threshold")
	touch.down(2, Vector2(400, 400), 1.0)
	touch.update(1.449)
	check(touch.collect().size() == 1, "no early long press")
	touch.update(1.45)
	actions = touch.collect()
	check(actions[0].kind == "long_press", "450 ms long press")
	touch.up(2, Vector2(400, 400), 1.6)
	check(touch.collect()[0].kind == "release", "long press does not become tap")
	touch.down(3, Vector2(100, 100), 2.0)
	touch.motion(3, Vector2(100, 190))
	actions = touch.collect()
	check(
		actions.any(func(a: Dictionary) -> bool: return a.kind == "scroll" and a.value == -1.0),
		"drag scrolls"
	)
	touch.up(3, Vector2(100, 190), 2.1)
	check(
		touch.collect().any(func(a: Dictionary) -> bool: return a.kind == "fling"),
		"fast drag flings"
	)
	touch.down(4, Vector2.ZERO, 3.0)
	touch.cancel()
	check(touch.points.is_empty() and touch.collect().is_empty(), "cancel clears touch state")
	touch.up(4, Vector2.ZERO, 3.1)
	check(touch.collect().is_empty(), "cancelled release is harmless")


func _test_hud() -> void:
	var hud := HudView.new()
	root.add_child(hud)
	hud.build_tactical_buttons()
	hud.sync_view(false, true, "test", true)
	hud.show_tactical_buttons(true)
	check(hud.hit_action(Vector2(50, 180)) == "pause", "pause hit target")
	check(hud.hit_action(Vector2(130, 180)) == "debug", "debug hit target")
	check(hud.hit_action(Vector2(890, 650)) == "q", "touch skill Q")
	check(hud.hit_action(Vector2(1170, 650)) == "r", "touch skill R")
	check(hud.hit_action(Vector2(50, 650)) == "shop", "touch shop")
	hud.apply_safe_area(Rect2(28, 10, 1224, 700))
	check(
		hud.pause_button.get_rect().encloses(Rect2(34, 158, 64, 56)),
		"safe-area pause remains tappable"
	)
	check(hud.skill_buttons.r.get_rect().end.x <= 1252, "safe-area skill bounds")
	hud.sync_view(true, true, "cinematic", true)
	check(hud.hit_action(Vector2(50, 180)) == "", "cinematic hides pause")
	check(not hud.skill_buttons.q.visible, "cinematic hides skills")
	check(hud.hit_action(Vector2(1150, 660)) == "skip", "cinematic skip button")
	hud.free()


func _test_settings() -> void:
	var settings := GameSettings.new()
	settings.path = "user://test_settings_%d.cfg" % Time.get_ticks_usec()
	settings.set_value("master_volume", 0.4)
	settings.set_value("fps_limit", 120)
	var loaded := GameSettings.new()
	loaded.path = settings.path
	loaded.load_values()
	check(near(loaded.values.master_volume, 0.4), "settings persist")
	check(loaded.effective_fps(true) == 60, "mobile quality cap enforced")
	check(loaded.effective_fps(false) == 120, "desktop can raise limit")
	loaded.values.fps_limit = 30
	check(loaded.effective_fps(false) == 30, "user can lower limit")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(settings.path))
	var catalog := LevelCatalog.new()
	check(catalog.entries.size() == 54, "all 54 source levels exported")
	check(catalog.contains(1) and catalog.contains(54), "catalog endpoints")
	check(catalog.next_after(1) == 2 and catalog.next_after(54) == 0, "next level boundaries")
	check(not catalog.contains(999), "invalid level rejected")


func _press(app: MysticMain, key: Key, pressed := true) -> void:
	var event := InputEventKey.new()
	event.keycode = key
	event.physical_keycode = key
	event.pressed = pressed
	app._input(event)


func _touch(app: MysticMain, id: int, position: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.index = id
	event.position = position
	event.pressed = pressed
	app._unhandled_input(event)


func _test_app() -> void:
	var app: MysticMain = load("res://scenes/Main.tscn").instantiate()
	app.game_scene = load("res://tests/fakes/FakeGame.tscn")
	app.settings.path = "user://test_app_%d.cfg" % Time.get_ticks_usec()
	var cloud: Node = load("res://tests/fakes/FakeCloud.gd").new()
	app.add_child(cloud)
	app.cloud_service = cloud
	root.add_child(app)
	await process_frame
	check(app.state.current == State.Kind.SPLASH, "scene boots to splash")
	_press(app, KEY_SPACE)
	for _frame in range(6):
		app.splash.advance(0.05)
	app._process(0.0)
	check(app.state.current == State.Kind.MENU, "splash skips to menu")
	app.menu.show_help()
	check(app.menu.page == "help", "native help menu")
	app.menu.show_credits()
	check(app.menu.page == "credits", "native credits menu")
	app.menu.show_settings(app.settings)
	var sliders := app.menu.root.find_children("*", "HSlider", true, false)
	check(sliders.size() == 5, "all audio settings rendered")
	sliders[0].value = 0.5
	check(app.settings.values.master_volume == 0.5, "slider updates shared settings")
	check(app.audio.settings.master_volume == 0.5, "slider updates audio director")
	app.menu.show_main()
	var before: int = cloud.polls
	app._process(0.016)
	check(cloud.polls > before, "cloud polls in menu")
	app.start_game(7)
	var fake: FakeGame = app.game
	check(
		app.state.current == State.Kind.GAME and fake.level_number == 7,
		"selected level reaches adapter"
	)
	app._process(0.1)
	check(fake.ticks == 4, "main forwards capped fixed updates")
	fake.cinematic = true
	_press(app, KEY_SPACE)
	check(not fake.cinematic, "space skips cinematic")
	_press(app, KEY_G)
	_press(app, KEY_F)
	check(fake.holds == ["gather"], "duplicate gather source starts once")
	_press(app, KEY_G, false)
	check(fake.holds == ["gather"], "G release preserves F hold")
	_press(app, KEY_F, false)
	check(fake.holds.is_empty(), "last gather source releases command")
	_press(app, KEY_T)
	_press(app, KEY_ESCAPE)
	check(
		app.state.current == State.Kind.PAUSE and fake.holds.is_empty(), "pause releases every hold"
	)
	var paused_ticks: int = fake.ticks
	app._process(0.25)
	check(fake.ticks == paused_ticks, "pause cannot tick combat")
	check(cloud.polls > before + 1, "cloud polls during pause")
	_press(app, KEY_T, false)
	check(fake.events.count("end:protect_tower") == 1, "stale keyup does not end twice")
	_press(app, KEY_ESCAPE)
	check(app.state.current == State.Kind.GAME, "escape resumes")
	_touch(app, 5, Vector2(50, 180), true)
	app._process(0.0)
	check(app.state.current == State.Kind.PAUSE, "pause button pauses after gesture dispatch")
	_touch(app, 5, Vector2(900, 600), false)
	app._process(0.0)
	check(app.claimed_touches.is_empty(), "claimed release outside button cleans up")
	check(not fake.events.has("pointer:tap"), "HUD click never leaks to arena")
	app.resume_game()
	app._process(0.016)
	_touch(app, 6, Vector2(1140, 270), true)
	app._process(0.0)
	check(fake.holds == ["gather"], "touch tactical starts hold")
	app.set_background(true)
	check(app.background and app.state.current == State.Kind.PAUSE, "background freezes game")
	check(fake.holds.is_empty() and app.gestures.points.is_empty(), "background releases ownership")
	var background_ticks: int = fake.ticks
	var background_polls: int = cloud.polls
	app._process(0.25)
	check(
		fake.ticks == background_ticks and cloud.polls == background_polls,
		"background does not tick or poll"
	)
	app.set_background(false)
	check(app.state.current == State.Kind.PAUSE, "foreground requires explicit resume")
	app.resume_game()
	fake.replay_requested.emit()
	app._process(0.0)
	check(
		app.game != fake and app.game.is_replay and app.game.level_number == 7,
		"replay replaces adapter"
	)
	fake = app.game
	fake.next_level_requested.emit()
	app._process(0.0)
	check(app.game.level_number == 8 and not app.game.is_replay, "next level resets replay flag")
	fake.menu_requested.emit()
	app._process(0.0)
	check(app.state.current == State.Kind.MENU and app.game == null, "menu disposes gameplay")
	app.start_game(54)
	app.game.next_level_requested.emit()
	app._process(0.0)
	check(
		app.game.level_number == 54 and app.pending_action.is_empty(),
		"final level does not loop or spam requests"
	)
	app.pause_game()
	app.menu.show_settings(app.settings)
	app.menu._settings_back()
	check(app.menu.page == "pause", "settings returns to pause")
	app.menu.confirm("menu")
	app.menu._cancel()
	check(
		app.menu.page == "pause" and app.state.current == State.Kind.PAUSE,
		"cancel leaves pause intact"
	)
	app.return_to_menu()
	app.game_scene = null
	app.start_game(1)
	check(
		app.game is IntegrationView and not app.game.combat_ready(), "missing gameplay is explicit"
	)
	var integration_ticks: int = app.clock.total_steps
	app._process(0.25)
	check(app.clock.total_steps == integration_ticks, "integration screen does not fake simulation")
	app.set_background(true)
	app.set_background(false)
	app.return_to_menu()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(app.settings.path))
	app.audio.stop_all()
	app.free()
	for _frame in range(12):
		await process_frame


func _test_audio() -> void:
	var audio := AudioDirector.new()
	root.add_child(audio)
	await process_frame
	audio.play_bgm("test_missing", 0.0)
	audio.play_ambient("test_missing")
	check(audio.missing.has("test_missing"), "missing audio is nonfatal")
	audio.play_bgm("bgm_battle", 0.0)
	audio.play_ambient("ambient_forest", 0.8)
	check(audio.bgm.playing and audio.ambient.playing, "BGM and ambient start")
	audio.bgm.stream_paused = true
	audio.set_background_paused(true)
	audio.set_background_paused(false)
	check(audio.bgm.stream_paused, "resume preserves pre-existing pause")
	check(not audio.ambient.stream_paused, "resume restores own paused streams")
	audio.set_background_paused(true)
	check(audio.bgm.stream_paused and audio.ambient.stream_paused, "background pauses both loops")
	audio.set_background_paused(false)
	check(audio.play_sfx("ui_click", 1.0, 1000), "SFX plays")
	check(not audio.play_sfx("ui_click", 1.0, 1010), "SFX throttled")
	check(audio.play_sfx("ui_click", 1.0, 1060), "SFX throttle expires")
	audio.stop_all()
	check(not audio.bgm.playing and not audio.ambient.playing, "quit stops audio")
	audio.streams.clear()
	audio.free()
	for _frame in range(12):
		await process_frame


func _test_core_data() -> void:
	var data := CoreData.new()
	check(data.valid(), "core data loads")
	check(data.data.get("levels", []).size() == 54, "core has 54 levels")
	check(data.data.get("heroes", {}).size() >= 222, "core hero catalog exported")
	check(data.data.get("bosses", {}).get("mini", {}).size() == 162, "162 mini bosses")
	check(data.data.get("bosses", {}).get("true", {}).size() == 54, "54 true bosses")
	check(data.data.get("items", {}).size() == 33, "33 forge items")
	check(data.lane("top").size() > 100 and data.lane("river").size() > 50, "lanes exported")
	check(data.hero("kaizen").get("hp", 0) == 550, "hero balance applied")
	check(not data.text("menu_play", "id").is_empty(), "localization exported")


func _test_core_rules() -> void:
	check(Economy.starting_gold({"starting_gold": 1000}, 1, "easy") == 1250, "easy starting gold")
	check(Economy.starting_gold({"starting_gold": 1000}, 2, "hard") == 825, "hard level gold")
	var income := Economy.add_income(0, 0, 3.3)
	check(income.gold == 3 and income.milli == 300, "milli-gold income")
	var status := StatusEffects.new()
	status.apply("slow", 0.25, 60)
	status.apply("slow", 0.1, 30)
	check(near(status.slow_amount, 0.25) and status.slow_timer == 60, "strongest slow wins")
	status.apply("anti_heal", 0.5, 60)
	check(near(status.modified_heal(100, 200), 150), "anti-heal modifies healing")
	status.apply("burn", 30, 60, "red")
	var burn := 0
	for _tick in range(30):
		burn += status.tick()
	check(burn == 15, "burn ticks integer damage")
	var inv := UnitInventory.new(
		{"sword": {"stats": {"damage": 10}}, "rapier": {"stats": {"damage": 5}}}
	)
	check(inv.add("sword") and inv.used() == 1, "item slot add")
	check(inv.bonus_damage() == 10, "item stat aggregation")
	var unit := BattleUnit.new()
	var data := CoreData.new()
	unit.setup_tower(data, Vector2.ZERO, "blue", "mid", true)
	var before := unit.hp + unit.shield
	unit.take_damage(100, "red", "physical")
	check(unit.hp + unit.shield < before, "tower takes damage")
	check(unit.upgrade_tower(data, "cannon") and unit.level == 2, "tower path upgrade")
	check(unit.sell_value(data) > 0, "player tower sell refund")
	var castle := BattleUnit.new()
	castle.setup_castle(data, "blue", 1)
	castle.set_wave(data, 11)
	check(not castle.free_shield_active, "free castle shield expires")
	check(castle.activate_castle_shield(data), "castle shield purchasable")
	var waves := WaveDirector.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	var schedule := waves.roll_schedule(
		{"mini_bosses": {"10": "a", "15": "b", "25": "c"}}, "normal", rng
	)
	var keys := schedule.keys()
	keys.sort()
	check(keys[0] >= 11 and keys[2] <= 30, "normal mini-boss range")
	var rng2 := RandomNumberGenerator.new()
	rng2.seed = 42
	var waves2 := WaveDirector.new()
	check(
		(
			waves2.roll_schedule({"mini_bosses": {"10": "a", "15": "b", "25": "c"}}, "normal", rng2)
			== schedule
		),
		"schedule deterministic with seed"
	)
	check(waves.composition(1, 13, data.data.rules).count("troll") == 2, "late wave composition")
	var tactical := TacticalCommands.new()
	tactical.hold_begin("gather", 0.0)
	tactical.hold_end("gather", 0.1)
	check(tactical.command_timer > 9.0, "quick tap keeps full duration")
	tactical.hold_begin("gather", 1.0)
	tactical.hold_end("gather", 2.0)
	check(tactical.command_timer <= 0.5, "long hold release tail")


func _test_core_save() -> void:
	var repo := SaveRepository.new("user://test_core_save_%d" % Time.get_ticks_usec())
	var data := repo.empty_save(100.0)
	check(repo.save_slot(data, 1, 100.0), "slot write")
	check(repo.exists(1) and not repo.exists(2), "slot isolation")
	var loaded := repo.load_slot(1)
	check(loaded.meta_gold == 0, "slot roundtrip")
	var config := {"meta_gold_reward_win": 3000, "meta_gold_reward_replay": 1500}
	var stats := {
		"won": true,
		"score": 100,
		"time_seconds": 60,
		"kills": 10,
		"combo": 3,
		"playtime_seconds": 60
	}
	var result := SaveRepository.grant_match_result(
		data, 1, config, true, false, "normal", stats, ["gornak"], 54, 200.0
	)
	check(result.reward == 3000 and data.meta_gold == 3000, "first win reward")
	check("gornak" in data.purchased_heroes, "boss hero free unlock")
	check(data.run_difficulty == "normal", "difficulty lock set")
	result = SaveRepository.grant_match_result(
		data, 1, config, true, true, "normal", stats, [], 54, 300.0
	)
	check(result.reward == 1500, "first replay reward")
	result = SaveRepository.grant_match_result(
		data, 1, config, true, true, "normal", stats, [], 54, 400.0
	)
	check(result.reward == 200, "repeat replay reward")
	result = SaveRepository.grant_match_result(
		data,
		2,
		config,
		false,
		false,
		"normal",
		{
			"won": false,
			"score": 0,
			"time_seconds": 10,
			"kills": 0,
			"combo": 0,
			"playtime_seconds": 10
		},
		[],
		54,
		500.0
	)
	check(
		result.reward == 0 and data.level_stats["2"].total_attempts == 1, "defeat stats no reward"
	)
	check(SaveRepository.purchase_hero(data, "vex", 500), "meta hero purchase")
	check(not SaveRepository.purchase_hero(data, "vex", 500), "no duplicate purchase")
	var voucher := SaveRepository.grant_voucher(data, "MA-123456", 50000, 1)
	check(voucher.ok and data.meta_gold >= 50000, "voucher grant")
	check(not SaveRepository.grant_voucher(data, "MA-123456", 50000, 2).ok, "voucher dedupe")
	check(SaveRepository.grant_topup(data, "TX-1", 1000, 3).ok, "topup grant")
	check(not SaveRepository.grant_topup(data, "TX-1", 1000, 4).ok, "topup dedupe")
	check(repo.delete_slot(1) and not repo.exists(1), "slot delete")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(repo.directory))


func _test_core_services() -> void:
	var fixture := FileAccess.get_file_as_string("res://tests/fixtures/cloud_payload.json")
	var parsed := CloudSaveCodec.parse_payload(fixture)
	check(parsed.ok, "Python cloud checksum validates")
	if parsed.ok:
		var summary := CloudSaveCodec.summarize(parsed.payload)
		check(summary.highest_level == 2 and summary.meta_gold == 4700, "cloud summary")
	var bad := CloudSaveCodec.parse_payload(
		'{"magic":"MYSTIC_ARENA_BACKUP","version":1,"slots":{"1":{}},"checksum":"bad"}'
	)
	check(not bad.ok, "bad checksum rejected")
	var repo := SaveRepository.new("user://test_cloud_%d" % Time.get_ticks_usec())
	repo.save_slot(repo.empty_save(), 1)
	var settings := GameSettings.new()
	settings.path = "user://test_cloud_settings_%d.cfg" % Time.get_ticks_usec()
	var payload := CloudSaveCodec.build_payload(repo, settings.values, 1761955200.25)
	check(
		not payload.is_empty() and CloudSaveCodec.parse_payload(JSON.stringify(payload)).ok,
		"native payload roundtrip"
	)
	repo.save_slot(repo.empty_save(), 2)
	check(CloudSaveCodec.apply_payload(repo, parsed.payload, settings), "cloud apply")
	check(repo.exists(1) and not repo.exists(2), "cloud restore deletes missing slot")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(repo.directory))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(settings.path))
	var voucher := VoucherService.new()
	check(voucher.valid_format("MA-123456") and not voucher.valid_format("XX-1"), "voucher format")
	var repo2 := SaveRepository.new("user://test_voucher_%d" % Time.get_ticks_usec())
	repo2.save_slot(repo2.empty_save(), 1)
	check(not voucher.redeem(repo2, "MA-123456", 1).ok, "production requires allowlist")
	var allow_path := "user://test_vouchers_%d.txt" % Time.get_ticks_usec()
	var file := FileAccess.open(allow_path, FileAccess.WRITE)
	file.store_line("MA-123456=75000")
	file.close()
	check(voucher.load_allowlist([allow_path]), "allowlist loads")
	check(voucher.redeem(repo2, "MA-123456", 1).get("gold", 0) == 75000, "allowlist amount")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(allow_path))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(repo2.directory))
	var currency := CurrencyFormat.new(CoreData.new().data.get("currency", {}))
	check(currency.currency_for("ID", "id") == "IDR", "region currency")
	check(currency.format_idr(10000, "IDR") == "Rp 10000", "IDR format")
	var controller := ControllerCore.new()
	controller.configure(CoreData.new().data.get("rules", {}), "Xbox Controller")
	check(controller.family == "xbox", "controller family")
	check(ControllerCore.apply_deadzone(0.1) == 0.0, "controller deadzone")
	var actions := controller.update({0: 1.0, 1: 0.0}, {0: true}, 0.1, Rect2(0, 0, 1280, 720))
	check(actions.has("confirm"), "controller button edge")
	check(controller.cursor.x > 640, "controller cursor moves")
	actions = controller.update({0: 1.0, 1: 0.0}, {0: true}, 0.1, Rect2(0, 0, 1280, 720))
	check(not actions.has("confirm"), "controller no repeat edge")
	var cloud := CloudSavePort.new()
	check(not cloud.upload({}).ok, "empty upload rejected")
	check(cloud.download().code == "unavailable", "cloud unavailable is explicit")
	cloud.free()
	var topup := TopupPort.new()
	check(not topup.available(), "topup unavailable without server")
	check(
		topup.create(0, "gopay", CoreData.new().data.get("rules", {})).code == "unavailable",
		"no fake payment success"
	)
	topup.free()


func _test_core_match() -> void:
	var model := MatchModel.new()
	var data := CoreData.new()
	model.setup(
		data.level(1), {"purchased_heroes": ["kaizen"], "completed_levels": []}, "normal", false, 42
	)
	check(model.gold == 1000 and model.heroes.size() == 1, "match setup")
	check(model.towers.size() == 18, "source tower layout")
	check(model.build_slots_blue.size() == 9, "generated build slots")
	for _tick in range(360):
		model.step()
	check(model.wave_number >= 1 and model.minions.size() > 0, "waves spawn")
	check(model.gold > 1000, "passive income accrues")
	check(model.build_tower(0, "archer"), "player build")
	check(
		model.selected_tower != null and model.selected_tower.player_built, "built tower selected"
	)
	model.selected_hero = model.heroes[0]
	model.selected_hero.pos = model.red_base.pos
	check(model.cast_skill("q"), "hero skill casts")
	model.tactical.hold_begin("protect_castle", 0.0)
	model.tactical.update(0.5, model)
	check(model.heroes[0].has_tactical_move, "tactical command moves hero")
	model.red_base.take_damage(model.red_base.max_hp + model.red_base.shield + 1, "blue", "true")
	model.step()
	check(model.state == "victory", "victory detected")
	var dev := DevMode.new()
	dev.allowed = true
	var model2 := MatchModel.new()
	model2.setup(data.level(1), {}, "normal", false, 1)
	check(dev.handle_hotkey(KEY_F1, model2) and dev.enabled, "dev toggle")
	var gold := model2.gold
	check(dev.handle_hotkey(KEY_F5, model2) and model2.gold == gold + 500, "dev gold cheat")
	dev.enabled = false
	check(not dev.handle_hotkey(KEY_F5, model2), "cheats require dev mode")


func _test_core_game() -> void:
	var game: CoreGame = load("res://scenes/CoreGame.tscn").instantiate()
	var repo := SaveRepository.new("user://test_core_game_%d" % Time.get_ticks_usec())
	var settings := GameSettings.new()
	settings.path = "user://test_core_game_settings_%d.cfg" % Time.get_ticks_usec()
	var cloud := CloudSavePort.new()
	var topup := TopupPort.new()
	game.attach_context(repo, settings, cloud, topup, VoucherService.new(), null)
	root.add_child(game)
	game.configure(1, false)
	await process_frame
	check(game.combat_ready(), "CoreGame is combat-ready")
	game.simulation_step()
	check(game.model.frame > 0, "CoreGame advances fixed simulation")
	game.hud_action("shop")
	check(game.shop_open and not game.button_rects.is_empty(), "hero shop opens")
	game.hud_action("shop")
	game.pointer_action({"kind": "tap", "pos": game.model.heroes[0].pos, "id": 0})
	check(game.model.selected_hero != null, "pointer selects hero")
	game.handle_dev_key(KEY_F1)
	check(game.dev.enabled, "CoreGame dev hotkey")
	game.model.red_base.take_damage(
		game.model.red_base.max_hp + game.model.red_base.shield + 1, "blue", "true"
	)
	game.simulation_step()
	check(game.result_visible and game.result_victory, "CoreGame result overlay")
	var gold: int = int(repo.load_slot().get("meta_gold", 0))
	game._on_match_finished(true)
	check(int(repo.load_slot().get("meta_gold", 0)) == gold, "reward guard prevents double grant")
	game.free()
	cloud.free()
	topup.free()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(repo.directory))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(settings.path))
	for _frame in range(12):
		await process_frame
