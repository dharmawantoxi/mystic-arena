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
	_test_hud()
	await _test_app()
	await _test_audio()
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
	check(sliders.size() == 4, "all audio settings rendered")
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
