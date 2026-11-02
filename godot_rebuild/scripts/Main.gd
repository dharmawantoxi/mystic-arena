class_name MysticMain
extends Control

## Native replacement for main.py's application loop, not for _core/_entity.
const Gesture := preload("res://scripts/core/GestureTracker.gd")
const Clock := preload("res://scripts/core/FixedClock.gd")
const State := preload("res://scripts/core/AppState.gd")
const TACTICAL_KEYS := {
	KEY_G: "gather",
	KEY_F: "gather",
	KEY_T: "protect_tower",
	KEY_C: "protect_castle",
	KEY_B: "attack_boss",
	KEY_D: "attack_damage_dealer",
}
const REVIEW_KEYS := {KEY_F7: "sylara", KEY_F9: "kaizen", KEY_F10: "vex", KEY_F11: "grimjaw"}

## Assign a native scene whose root extends GameplayPort. Empty = honest integration screen.
@export var game_scene: PackedScene
## Optional native service with poll() -> void. No Play Games plugin is bundled here.
@export var cloud_service_path: NodePath

var state := State.new()
var clock := Clock.new()
var gestures := Gesture.new()
var settings := GameSettings.new()
var diagnostics := Diagnostics.new()
var audio := AudioDirector.new()
var save_repo := SaveRepository.new()
var cloud_port := CloudSavePort.new()
var topup_port := TopupPort.new()
var voucher := VoucherService.new()
var controller := ControllerManager.new()
var controller_cursor: ColorRect
var splash: SplashView
var menu: MenuView
var hud: HudView
var debug_overlay: DebugView
var game: GameplayPort
var game_host: Control
var cloud_service: Node
var touch_mode := false
var debug_enabled := false
var background := false
var cloud_polls := 0
var held_sources: Dictionary = {}
var claimed_touches: Dictionary = {}
var pending_action := ""
var fps_counter := FpsCounter.new()
var adaptive_quality := AdaptiveQuality.new()
var _quality_timer := 0
var _pause_requested := false


func _ready() -> void:
	get_tree().auto_accept_quit = false
	get_tree().quit_on_go_back = false
	touch_mode = (
		OS.has_feature("android")
		or OS.has_feature("ios")
		or DisplayServer.is_touchscreen_available()
		or OS.get_environment("MYSTIC_FORCE_TOUCH") == "1"
	)
	settings.load_values()
	debug_enabled = (
		settings.values.debug
		or OS.get_environment("MYSTIC_DEBUG") == "1"
		or "--debug" in OS.get_cmdline_user_args()
	)
	Engine.max_fps = settings.effective_fps(touch_mode)
	add_child(audio)
	add_child(cloud_port)
	add_child(topup_port)
	add_child(controller)
	controller.enabled = str(settings.values.input_mode) == "controller"
	controller.action_pressed.connect(_controller_action)
	controller.cursor_moved.connect(_controller_cursor_moved)
	controller.device_changed.connect(_controller_device_changed)
	topup_port.settled.connect(_topup_settled)
	voucher.demo_mode = OS.get_environment("MYSTIC_VOUCHER_DEMO") == "1"
	voucher.load_allowlist(["res://voucher_codes.txt", "user://voucher_codes.txt"])
	controller_cursor = ColorRect.new()
	controller_cursor.color = Ui.GOLD
	controller_cursor.custom_minimum_size = Vector2(12, 12)
	controller_cursor.size = Vector2(12, 12)
	controller_cursor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	controller_cursor.visible = false
	controller_cursor.z_index = 100
	add_child(controller_cursor)
	audio.apply_settings(settings.values)
	audio.play_bgm("bgm_battle", 3.0)
	audio.play_ambient("ambient_forest", 0.8)
	if not audio.missing.is_empty():
		print(
			(
				"[AUDIO] %d stream opsional belum tersedia; jalankan tools/prepare_godot_main.py"
				% audio.missing.size()
			)
		)
	game_host = Control.new()
	game_host.name = "Gameplay"
	add_child(game_host)
	game_host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	game_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu = MenuView.new()
	menu.settings = settings
	menu.save_repo = save_repo
	menu.core_data = CoreData.new()
	menu.cloud_port = cloud_port
	menu.topup_port = topup_port
	menu.voucher = voucher
	add_child(menu)
	menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	menu.play_requested.connect(start_game)
	menu.resume_requested.connect(resume_game)
	menu.menu_requested.connect(return_to_menu)
	menu.quit_requested.connect(confirm_quit)
	menu.settings_changed.connect(_settings_changed)
	menu.sound_requested.connect(func(sound_name: String) -> void: audio.play_sfx(sound_name))
	hud = HudView.new()
	add_child(hud)
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.build_tactical_buttons()
	hud.apply_safe_area(_safe_rect())
	get_viewport().size_changed.connect(func() -> void: hud.apply_safe_area(_safe_rect()))
	hud.action_pressed.connect(_hud_action)
	splash = SplashView.new()
	add_child(splash)
	splash.finished.connect(_splash_finished)
	debug_overlay = DebugView.new()
	debug_overlay.fps_counter = fps_counter
	add_child(debug_overlay)
	debug_overlay.mode = 1 if debug_enabled else 0
	debug_overlay.visible = debug_enabled
	if not cloud_service_path.is_empty():
		cloud_service = get_node_or_null(cloud_service_path)
		if cloud_service != null and not cloud_service.has_method("poll"):
			diagnostics.report("cloud", "Service must implement poll()", Time.get_ticks_msec())
			cloud_service = null
	print(
		(
			"[GODOT] Mystic Arena | state=splash | input=%s | save=user://godot_settings.cfg"
			% ["touch" if touch_mode else "mouse/keyboard"]
		)
	)
	_sync_visibility()


func _sync_visibility() -> void:
	splash.visible = state.current == State.Kind.SPLASH
	menu.visible = state.current == State.Kind.MENU or state.current == State.Kind.PAUSE
	hud.visible = state.current == State.Kind.GAME
	game_host.visible = state.current == State.Kind.GAME or state.current == State.Kind.PAUSE
	if game != null:
		hud.sync_view(
			game.cinematic_active(),
			debug_enabled,
			(
				"LEVEL %02d • %s"
				% [game.level_number, "GAMEPLAY" if game.combat_ready() else "MODE INTEGRASI"]
			),
			game.combat_ready()
		)
		hud.show_tactical_buttons(game.combat_ready())


func _splash_finished() -> void:
	if state.transition(State.Kind.MENU):
		clock.reset()
		_sync_visibility()


func start_game(level: int, replay := false) -> void:
	if state.current != State.Kind.MENU and state.current != State.Kind.GAME:
		return
	if not menu.catalog.contains(level):
		diagnostics.report("level", "Level not in catalog: %d" % level, Time.get_ticks_msec())
		return
	_release_input()
	_dispose_game()
	if game_scene == null:
		game = IntegrationView.new()
	else:
		var instance := game_scene.instantiate()
		if instance == null:
			diagnostics.report(
				"game_scene",
				"Cannot instantiate scene; using integration screen",
				Time.get_ticks_msec()
			)
			game = IntegrationView.new()
		elif instance is GameplayPort:
			game = instance
		else:
			instance.free()
			diagnostics.report(
				"game_scene",
				"Root must extend GameplayPort; using integration screen",
				Time.get_ticks_msec()
			)
			game = IntegrationView.new()
	if game is CoreGame:
		game.attach_context(save_repo, settings, cloud_port, topup_port, voucher, controller)
	game.configure(level, replay)
	game_host.add_child(game)
	game.next_level_requested.connect(func() -> void: pending_action = "next")
	game.replay_requested.connect(func() -> void: pending_action = "replay")
	game.menu_requested.connect(func() -> void: pending_action = "menu")
	game.pause_requested.connect(func() -> void: pending_action = "pause")
	state.transition(State.Kind.GAME)
	clock.reset()
	pending_action = ""
	audio.play_bgm("bgm_battle", 1.5)
	_sync_visibility()


func _dispose_game() -> void:
	if game != null:
		game_host.remove_child(game)
		game.queue_free()
		game = null


func pause_game() -> void:
	if not state.transition(State.Kind.PAUSE):
		return
	_release_input()
	menu.show_pause()
	_sync_visibility()


func resume_game() -> void:
	if background or not state.transition(State.Kind.GAME):
		return
	_release_input()
	_sync_visibility()


func return_to_menu() -> void:
	if state.current != State.Kind.GAME and state.current != State.Kind.PAUSE:
		return
	_release_input()
	_dispose_game()
	state.transition(State.Kind.MENU)
	menu.show_main()
	pending_action = ""
	_sync_visibility()


func confirm_quit() -> void:
	_release_input()
	settings.save()
	audio.stop_all()
	get_tree().quit()


func _settings_changed() -> void:
	Engine.max_fps = settings.effective_fps(touch_mode)
	audio.apply_settings(settings.values)
	controller.enabled = str(settings.values.input_mode) == "controller"
	if not controller.enabled:
		controller_cursor.visible = false
	if menu != null and menu.core_data.localization != null:
		menu.core_data.localization.set_language(str(settings.values.language))
	if game is CoreGame:
		game.apply_language(str(settings.values.language))


func _release_input() -> void:
	gestures.cancel()
	claimed_touches.clear()
	held_sources.clear()
	_pause_requested = false
	if is_instance_valid(game):
		game.release_all_holds()
	if hud != null:
		hud.cancel()
	clock.reset()


func _process(delta: float) -> void:
	if background:
		return
	poll_cloud()
	controller.poll(delta)
	var now := Time.get_ticks_msec() / 1000.0
	gestures.update(now)
	if state.current == State.Kind.GAME:
		_dispatch_gestures()
		if _pause_requested:
			_pause_requested = false
			pause_game()
	if state.current == State.Kind.SPLASH:
		splash.advance(delta)
	elif state.current == State.Kind.GAME and game != null and game.combat_ready():
		for _step in range(clock.advance(delta)):
			game.simulation_step()
	_flush_pending_action()
	_sync_visibility()
	var frame_fps := Engine.get_frames_per_second()
	fps_counter.update(frame_fps)
	adaptive_quality.tick(frame_fps)
	_quality_timer += 1
	if (
		settings.values.auto_quality
		and _quality_timer >= 30
		and game != null
		and game.has_method("apply_render_quality")
	):
		_quality_timer = 0
		game.call("apply_render_quality", adaptive_quality.quality)
	debug_overlay.refresh(frame_fps, state.label(), clock, game)


func poll_cloud() -> void:
	if is_instance_valid(cloud_service) and cloud_service.has_method("poll"):
		cloud_service.call("poll")
		cloud_polls += 1
	cloud_port.poll()


func _topup_settled(transaction: Dictionary) -> void:
	var id := str(transaction.get("id", transaction.get("transaction_id", "")))
	var gold := int(transaction.get("gold", 0))
	var data := save_repo.load_slot()
	var result := SaveRepository.grant_topup(data, id, gold, Time.get_ticks_msec())
	if bool(result.get("ok", false)):
		save_repo.save_slot(data)


func _controller_device_changed(connected: bool, _device_name: String) -> void:
	controller_cursor.visible = connected and controller.enabled


func _controller_cursor_moved(position: Vector2) -> void:
	if controller_cursor != null:
		controller_cursor.position = position - Vector2(6, 6)


func _controller_action(action: String) -> void:
	if state.current in [State.Kind.MENU, State.Kind.PAUSE]:
		menu.controller_action(action)
		return
	if state.current != State.Kind.GAME or game == null:
		return
	match action:
		"confirm":
			game.pointer_action({"kind": "tap", "pos": controller.core.cursor, "id": 0})
		"cancel", "back":
			_back()
		"start":
			_pause_requested = true
		"shop":
			_hud_action("shop")
		"skill_q":
			game.key_pressed(KEY_Q)
		"skill_w":
			game.key_pressed(KEY_W)
		"skill_e":
			game.key_pressed(KEY_E)
		"skill_r":
			game.key_pressed(KEY_R)
		"stick_left":
			debug_overlay.toggle()
		"trigger_left", "trigger_right":
			game.pointer_action(
				{
					"kind": "scroll",
					"pos": controller.core.cursor,
					"id": 0,
					"value": -1.0 if action == "trigger_left" else 1.0
				}
			)
		_:
			if (
				action.begins_with("dpad_")
				and game is CoreGame
				and game.model.selected_hero != null
			):
				var direction := Vector2(
					float(action.get_slice("_", 1)), float(action.get_slice("_", 2))
				)
				game.model.selected_hero.move_toward_point(
					game.model.selected_hero.pos + direction * 80.0
				)


func _flush_pending_action() -> void:
	var action := pending_action
	pending_action = ""
	match action:
		"pause":
			pause_game()
		"menu":
			return_to_menu()
		"replay":
			if game != null:
				start_game(game.level_number, true)
		"next":
			if game != null:
				var next := menu.catalog.next_after(game.level_number)
				if next > 0:
					start_game(next)


func _input(event: InputEvent) -> void:
	if background or not event is InputEventKey:
		return
	_handle_key(event)


func _handle_key(event: InputEventKey) -> void:
	if event.echo:
		return
	var key: Key = event.physical_keycode if event.physical_keycode != 0 else event.keycode
	if not event.pressed:
		_end_hold("key:%d" % key)
		if state.current == State.Kind.GAME and game != null:
			game.key_released(key)
		return
	if state.current == State.Kind.SPLASH:
		splash.skip()
	elif (
		state.current == State.Kind.GAME
		and game != null
		and game.has_method("handle_dev_key")
		and game.call("handle_dev_key", key)
	):
		get_viewport().set_input_as_handled()
		return
	elif key == KEY_F8:
		debug_overlay.toggle()
	elif key == KEY_ESCAPE:
		_back()
	elif state.current == State.Kind.GAME and game != null:
		if REVIEW_KEYS.has(key):
			game.toggle_review(REVIEW_KEYS[key])
		elif key == KEY_SPACE and game.cinematic_active():
			game.skip_cinematic()
		elif TACTICAL_KEYS.has(key):
			_begin_hold("key:%d" % key, TACTICAL_KEYS[key])
		else:
			game.key_pressed(key)
	if state.current in [State.Kind.SPLASH, State.Kind.GAME] or key in [KEY_ESCAPE, KEY_F8]:
		get_viewport().set_input_as_handled()
	return


func _unhandled_input(event: InputEvent) -> void:
	if background:
		return
	if state.current == State.Kind.SPLASH:
		if (
			(event is InputEventMouseButton and event.pressed)
			or (event is InputEventScreenTouch and event.pressed)
		):
			splash.skip()
		return
	if state.current != State.Kind.GAME:
		return
	if event is InputEventScreenTouch:
		var position := _logical_position(event.position)
		if event.pressed:
			gestures.down(event.index, position, Time.get_ticks_msec() / 1000.0)
		else:
			gestures.up(event.index, position, Time.get_ticks_msec() / 1000.0)
	elif event is InputEventScreenDrag:
		gestures.motion(event.index, _logical_position(event.position))
	elif event is InputEventMouseButton:
		var position := _logical_position(event.position)
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				gestures.down(0, position, Time.get_ticks_msec() / 1000.0)
			else:
				gestures.up(0, position, Time.get_ticks_msec() / 1000.0)
		elif event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
			gestures._emit("long_press", position, 0)
		elif (
			event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]
		):
			gestures._emit(
				"scroll",
				position,
				0,
				Vector2.ZERO,
				-1.0 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0
			)
	elif event is InputEventMouseMotion and event.button_mask & MOUSE_BUTTON_MASK_LEFT:
		gestures.motion(0, _logical_position(event.position))


func _logical_position(window_position: Vector2) -> Vector2:
	return get_global_transform_with_canvas().affine_inverse() * window_position


func _dispatch_gestures() -> void:
	for action: Dictionary in gestures.collect():
		var id: int = action.id
		var kind: String = action.kind
		if kind == "long_press" and hud.hit_action(action.pos) == "pause":
			debug_overlay.toggle()
			_pause_requested = false
			continue
		if kind == "down":
			var hit := hud.hit_action(action.pos)
			if not hit.is_empty():
				claimed_touches[id] = true
				if hit in HudView.TACTICAL_COMMANDS:
					_begin_hold("touch:%d" % id, hit)
				else:
					_hud_action(hit)
			continue
		if claimed_touches.has(id):
			if kind == "release":
				claimed_touches.erase(id)
				_end_hold("touch:%d" % id)
			continue
		if kind in ["tap", "long_press", "double_tap", "scroll"]:
			if game != null:
				if game.cinematic_active() and kind == "tap":
					game.skip_cinematic()
				else:
					game.pointer_action(action)


func _hud_action(action: String) -> void:
	audio.play_sfx("ui_click")
	match action:
		"pause":
			_pause_requested = true
		"debug":
			debug_overlay.toggle()
		"skip":
			if game != null:
				game.skip_cinematic()
		_:
			if game != null:
				game.hud_action(action)


func _begin_hold(source: String, command: String) -> void:
	if game == null or held_sources.has(source):
		return
	var already_held := command in held_sources.values()
	held_sources[source] = command
	if not already_held:
		game.hold_begin(command)


func _end_hold(source: String) -> void:
	if not held_sources.has(source):
		return
	var command: String = held_sources[source]
	held_sources.erase(source)
	if game != null and not command in held_sources.values():
		game.hold_end(command)


func _back() -> void:
	if state.current == State.Kind.GAME:
		pause_game()
	elif state.current in [State.Kind.PAUSE, State.Kind.MENU]:
		menu.back()


func set_background(value: bool) -> void:
	if background == value:
		return
	background = value
	_release_input()
	if value and state.current == State.Kind.GAME:
		pause_game()
	audio.set_background_paused(value)
	if not value:
		clock.reset()


func _notification(what: int) -> void:
	if not is_node_ready():
		return
	match what:
		NOTIFICATION_APPLICATION_PAUSED:
			set_background(true)
		NOTIFICATION_APPLICATION_RESUMED:
			set_background(false)
		NOTIFICATION_WM_GO_BACK_REQUEST:
			_back()
		NOTIFICATION_WM_CLOSE_REQUEST:
			if state.current == State.Kind.GAME:
				pause_game()
			menu.confirm("quit")


func _exit_tree() -> void:
	if is_instance_valid(audio):
		audio.stop_all()
		audio.dispose_streams()
	if is_instance_valid(game):
		game.release_all_holds()
	Engine.max_fps = 60


func _safe_rect() -> Rect2:
	var logical := Rect2(0, 0, 1280, 720)
	if not touch_mode:
		return logical
	var safe := DisplayServer.get_display_safe_area()
	if safe.size.x <= 0 or safe.size.y <= 0:
		return Rect2(28, 10, 1224, 700)
	safe.position -= Vector2i(get_window().position)
	var transform := get_viewport().get_screen_transform().affine_inverse()
	var result := (transform * Rect2(safe)).intersection(logical)
	return result if result.size.x > 0 and result.size.y > 0 else logical
