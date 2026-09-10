# FASE 24 — LAPISAN GAMEPAD vs oracle pygame (seksi fixture
# controller_input). python tools/test_godot_match_parity.py   (freshness)
# godot --headless --path godot res://tests/ControllerInputParityTest.tscn --quit-after 600
#
# Oracle-nya (tools/test_godot_match_parity.py) menjalankan:
#   * ControllerManager pygame ASLI dengan joystick PALSU ter-script
#     (pygame.joystick ditambal) — deteksi tipe, kursor, urutan aksi per
#     frame, rumble, label/hint, snap/find tombol UI.
#   * Blok routing controller main_desktop_legacy.py DI-EXEC apa adanya
#     dengan game/menu/fps_counter/splash palsu yang merekam panggilan.
#
# Replay di sini lewat JALUR PRODUKSI Godot:
#   * ControllerManager.gd dengan `scripted_device` (pola mouse_override /
#     ParityRng — produksi tak terpengaruh; tanpa scripted_device node ini
#     membaca singleton Input).
#   * ControllerRouter.route() — fungsi yang sama dipanggil _process() tiap
#     frame; jejak produksi direkam `trace_enabled` (pola hold_trace FASE 18).
#
# Yang dibandingkan per kasus: tipe deteksi + info, posisi kursor, daftar
# aksi per frame (URUTAN ikut), accum/axis scroll, hitungan repeat D-PAD,
# jejak rumble (low/high/ms) + frame sampai stop, label/hint, hasil
# find/snap, dan jejak panggilan routing (klik/tombol/pause/hold_end/skip/
# snap/next_level) + posisi kursor + menu.action.
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
# Data+file save di-snapshot lalu dipulihkan di akhir. Piksel kursor
# (glow/bracket) dan audio BELUM TERUJI — yang dikunci state + routing.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainScene = preload("res://scenes/main.tscn")
const ControllerScript = preload("res://scripts/systems/ControllerManager.gd")

## Peta nama tombol pygame (oracle) -> konstanta Godot. Hanya dipakai untuk
## membaca jejak; routing produksi memakai KEY_* sendiri.
const KEYMAP := {
	"q": KEY_Q, "w": KEY_W, "e": KEY_E, "r": KEY_R, "h": KEY_H,
	"n": KEY_N, "escape": KEY_ESCAPE,
}

var _fx: Dictionary = {}
var _failures := 0
var _checks := 0
var _save_before: Dictionary = {}
var _save_file_before = null
var _main = null


## Cinematic palsu untuk kasus `confirm` saat intro/banner/perayaan aktif.
class FakeCinematic:
	var active := true
	var skipped: Array = []

	func cinematic_active() -> bool:
		return active

	func skip_click() -> bool:
		skipped.append("click")
		active = false
		return true


## Host Node supaya cinematic palsu masuk grup "cinematic" seperti
## BossDeathFX produksi (dipakai Main._cinematic_kind/_cinematic_click).
class FakeCinematicHost:
	extends Node
	var fake = null

	func _ready() -> void:
		add_to_group("cinematic")

	func cinematic_active() -> bool:
		return bool(fake.active)

	func skip_click() -> bool:
		return bool(fake.skip_click())


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	if FileAccess.file_exists(SaveManager.SAVE_PATH):
		_save_file_before = FileAccess.get_file_as_string(SaveManager.SAVE_PATH)
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("controller_input"):
		_expect(false, "fixture controller_input belum ada — jalankan "
			+ "tools/test_godot_match_parity.py --write-fixture")
		_finish()
		return
	_fx = fixture["controller_input"]

	_test_constants()
	_test_detection()
	_test_labels()
	_test_cursor()
	_test_actions()
	_test_rumble()
	_test_ui_buttons()
	await _test_routing()

	_finish()


# ══════════════════════════════════════════════════════════
#  KONSTANTA + DETEKSI + LABEL
# ══════════════════════════════════════════════════════════

func _test_constants() -> void:
	var c: Dictionary = _fx["constants"]
	var mgr = _make_manager({})
	_compare(mgr.SCREEN_W, int(c["screen"][0]), "constants/screen_w")
	_compare(mgr.SCREEN_H, int(c["screen"][1]), "constants/screen_h")
	_compare(Vector2(mgr.cursor_x, mgr.cursor_y),
		_vec2(c["cursor_start"]), "constants/cursor_start")
	_compare(mgr.cursor_speed, float(c["cursor_speed"]), "constants/speed")
	_compare(mgr.cursor_max_speed, float(c["cursor_max_speed"]),
		"constants/max_speed")
	_compare(mgr.cursor_acceleration, float(c["cursor_acceleration"]),
		"constants/acceleration")
	_compare(mgr.deadzone, float(c["deadzone"]), "constants/deadzone")
	_compare(mgr.hat_repeat_delay, int(c["hat_repeat_delay"]),
		"constants/hat_repeat_delay")
	_compare(mgr.hat_repeat_rate, int(c["hat_repeat_rate"]),
		"constants/hat_repeat_rate")
	_compare(mgr.scroll_step, float(c["scroll_step"]), "constants/scroll_step")
	_compare(mgr.scroll_speed, float(c["scroll_speed"]),
		"constants/scroll_speed")
	_compare(mgr.scroll_deadzone, float(c["scroll_deadzone"]),
		"constants/scroll_deadzone")
	_compare(ControllerScript.MODE_KEYBOARD, str(c["mode_keyboard"]),
		"constants/mode_keyboard")
	_compare(ControllerScript.MODE_CONTROLLER, str(c["mode_controller"]),
		"constants/mode_controller")
	# Peta tombol SDL Godot: confirm=A, cancel=B, skill_q/w/e/r = X/Y/LB/RB,
	# start/back, L3/R3, axis stick + trigger (deviasi 1 di header manajer).
	var map_expect := {
		"confirm": JOY_BUTTON_A, "cancel": JOY_BUTTON_B,
		"skill_q": JOY_BUTTON_X, "skill_w": JOY_BUTTON_Y,
		"skill_e": JOY_BUTTON_LEFT_SHOULDER,
		"skill_r": JOY_BUTTON_RIGHT_SHOULDER,
		"start": JOY_BUTTON_START, "back": JOY_BUTTON_BACK,
		"stick_left": JOY_BUTTON_LEFT_STICK,
		"stick_right": JOY_BUTTON_RIGHT_STICK,
		"left_stick_x": JOY_AXIS_LEFT_X, "left_stick_y": JOY_AXIS_LEFT_Y,
		"right_stick_x": JOY_AXIS_RIGHT_X, "right_stick_y": JOY_AXIS_RIGHT_Y,
		"left_trigger": JOY_AXIS_TRIGGER_LEFT,
		"right_trigger": JOY_AXIS_TRIGGER_RIGHT,
	}
	for key in map_expect:
		_compare(int(ControllerScript.BUTTON_MAP[key]), int(map_expect[key]),
			"constants/map_" + str(key))
	mgr.free()


func _test_detection() -> void:
	for case in _fx["detection"]:
		var tag := "detection/" + str(case["name"])
		var empty_device := str(case["name"]) == "(tidak ada perangkat)"
		var device := {
			"ids": [] if empty_device else [0],
			"names": {0: str(case["name"])},
			"guids": {0: str(case["guid"])},
			"button_count": {0: int(case["buttons"])},
			"axis_count": {0: int(case["axes"])},
			"rumble": [], "stop_rumble": 0,
		}
		var mgr = _make_manager(device)
		mgr.init_joystick()
		var expect: Dictionary = case["expect"]
		_compare(mgr.connected, bool(expect["connected"]), tag + "/connected")
		_compare(str(mgr.controller_type), str(expect["type"]), tag + "/type")
		_compare(mgr._prev_buttons.size(), int(expect["prev_buttons"]),
			tag + "/prev_buttons")
		_compare(mgr.get_controller_info(), _dict(expect["info"]),
			tag + "/info")
		mgr.free()


func _test_labels() -> void:
	for case in _fx["button_labels"]:
		var mgr = _mode_manager(str(case["mode"]), case["type"])
		_compare(mgr.get_button_label(str(case["action"])),
			str(case["expect"]),
			"button_label/%s/%s/%s" % [case["mode"], case["type"],
				case["action"]])
		mgr.free()
	for case in _fx["action_labels"]:
		var mgr = _mode_manager(str(case["mode"]), case["type"])
		_compare(mgr.get_action_label(str(case["action"])),
			str(case["expect"]),
			"action_label/%s/%s/%s" % [case["mode"], case["type"],
				case["action"]])
		mgr.free()
	for case in _fx["hints"]:
		var mgr = _mode_manager(str(case["mode"]), case["type"])
		var got: Array = []
		for row in mgr.get_hints(str(case["context"])):
			got.append([str(row[0]), str(row[1])])
		var want: Array = []
		for row in case["expect"]:
			want.append([str(row[0]), str(row[1])])
		_compare(got, want,
			"hints/%s/%s/%s" % [case["mode"], case["type"], case["context"]])
		mgr.free()
	for case in _fx["controller_info"]:
		var mgr = _mode_manager(str(case["mode"]), case["type"])
		_compare(mgr.get_controller_info(), _dict(case["expect"]),
			"info/%s/%s" % [case["mode"], case["type"]])
		mgr.free()


# ══════════════════════════════════════════════════════════
#  KURSOR + AKSI + RUMBLE (perangkat ter-script per frame)
# ══════════════════════════════════════════════════════════

func _test_cursor() -> void:
	for scenario in _fx["cursor"]:
		var tag := "cursor/" + str(scenario["name"])
		var device := _xbox_device()
		var mgr = _controller_mode(device)
		mgr.cursor_x = float(int(scenario["start"][0]))
		mgr.cursor_y = float(int(scenario["start"][1]))
		var index := 0
		for step in scenario["steps"]:
			_apply_frame(device, step)
			mgr.update()
			mgr.get_pressed_actions()
			_compare(Vector2(mgr.cursor_x, mgr.cursor_y),
				_vec2(step["cursor"]), "%s/frame%d" % [tag, index], 0.02)
			index += 1
		mgr.free()


func _test_actions() -> void:
	for scenario in _fx["actions"]:
		var tag := "actions/" + str(scenario["name"])
		var device := _xbox_device()
		var mgr = _controller_mode(device)
		var index := 0
		for step in scenario["steps"]:
			_apply_frame(device, step)
			mgr.update()
			var got: Array = []
			for action in mgr.get_pressed_actions():
				got.append(str(action))
			var want: Array = []
			for action in step["actions"]:
				want.append(str(action))
			_compare(got, want, "%s/frame%d" % [tag, index])
			_compare(mgr._scroll_accum, float(step["scroll_accum"]),
				"%s/frame%d/scroll_accum" % [tag, index])
			var axis = mgr._scroll_axis
			_compare(-1 if axis == null else int(axis),
				-1 if step["scroll_axis"] == null else int(step["scroll_axis"]),
				"%s/frame%d/scroll_axis" % [tag, index])
			_compare(mgr._hat_hold_frames, int(step["hat_hold_frames"]),
				"%s/frame%d/hat_hold" % [tag, index])
			index += 1
		mgr.free()


func _test_rumble() -> void:
	for case in _fx["rumble"]:
		var tag := "rumble/%s_%s" % [case["intensity"], case["frames"]]
		var device := _xbox_device()
		var mgr = _controller_mode(device)
		if int(case["frames"]) == 30:
			# Kasus terakhir oracle: mode KEYBOARD (rumble harus diam).
			mgr.set_mode(ControllerScript.MODE_KEYBOARD)
		mgr.rumble(float(case["intensity"]), int(case["frames"]))
		var got_calls: Array = []
		for entry in device["rumble"]:
			got_calls.append([float(entry[0]), float(entry[1]), int(entry[2])])
		var want_calls: Array = []
		for entry in case["expect"]["calls"]:
			want_calls.append([float(entry[0]), float(entry[1]),
				int(entry[2])])
		_compare(got_calls, want_calls, tag + "/calls")
		_compare(mgr._rumble_timer, int(case["expect"]["timer"]),
			tag + "/timer")
		var frames := 0
		while mgr._rumble_timer > 0 and frames < int(case["frames"]) + 2:
			mgr.update()
			frames += 1
		_compare(frames, int(case["expect"]["frames_until_stop"]),
			tag + "/frames_until_stop")
		_compare(int(device["stop_rumble"]), int(case["expect"]["stop_calls"]),
			tag + "/stop_calls")
		mgr.free()


func _test_ui_buttons() -> void:
	for case in _fx["ui_buttons"]:
		var tag := "ui_buttons/" + str(case["name"])
		var device := _xbox_device()
		var mgr = _controller_mode(device)
		mgr.cursor_x = float(int(case["cursor"][0]))
		mgr.cursor_y = float(int(case["cursor"][1]))
		var rects := _rects(case["rects"])
		var found = mgr.find_ui_button_at_cursor(rects)
		var found_key = null
		if found != null:
			for key in rects:
				if rects[key] == found:
					found_key = str(key)
					break
		var want_found = case["expect"]["found"]
		_compare("" if want_found == null else str(want_found),
			"" if found_key == null else found_key, tag + "/found")
		mgr.snap_to_nearest_button(rects)
		_compare(mgr.get_cursor_pos(),
			Vector2i(int(case["expect"]["snap"][0]),
				int(case["expect"]["snap"][1])), tag + "/snap")
		mgr.free()


# ══════════════════════════════════════════════════════════
#  ROUTING (blok main_desktop_legacy.py vs ControllerRouter)
# ══════════════════════════════════════════════════════════

func _test_routing() -> void:
	var section: Dictionary = _fx["routing"]
	_expect(KEYMAP.has(str(section["key_esc"])),
		"key_esc oracle dikenal KEYMAP (%s)" % str(section["key_esc"]))
	_expect(section["actions_handled"].size() >= 18,
		"oracle merutekan >= 18 cabang aksi legacy (%d)"
		% section["actions_handled"].size())

	GameManager.set_process(false)
	GameManager.in_menu = false
	GameManager.state = "playing"
	GameManager.waves_enabled = false
	_main = MainScene.instantiate()
	add_child(_main)
	_main.set_process(false)
	_main._ai.set_process(false)
	_main._tactical.set_physics_process(false)
	_main.find_child("Containers", true, false).process_mode = \
		Node.PROCESS_MODE_DISABLED
	var menu = _main._main_menu()
	if menu != null:
		menu.close()
	await get_tree().process_frame
	await get_tree().process_frame
	_cleanup_field()

	var router = _main._router
	var controller = _main._controller
	_expect(router != null, "ControllerRouter dipasang Main")
	_expect(controller != null, "ControllerManager dipasang Main")
	_expect(menu != null and menu.controller_mgr == controller,
		"MainMenu.controller_mgr = ControllerManager (paritas menu.controller_mgr)")
	# Kursor virtual terpasang di CanvasLayer UI (paritas blit terakhir).
	_expect(_main.find_child("VirtualCursor", true, false) != null,
		"VirtualCursor ada di bawah UI")
	# Hint bar: tersembunyi tanpa controller mode, HIDUP saat controller
	# (paritas _draw_input_hints _core.py:2701-2736).
	var hud = _main.find_child("HUD", true, false)
	var hint_host = hud.find_child("HintLabel", true, false) if hud != null else null
	_expect(hint_host != null and not hint_host.visible,
		"hint bar tersembunyi saat mode keyboard")
	var hint_rows_keyboard: Array = hud._hint_rows("game")
	controller.scripted_device = _xbox_device()
	controller.init_joystick()
	controller.set_mode(ControllerScript.MODE_CONTROLLER)
	hud._sync_hint_visibility()
	_expect(hint_host != null and hint_host.visible,
		"hint bar tampil saat mode controller")
	var hint_rows_pad: Array = hud._hint_rows("game")
	_compare(hint_rows_pad.size(), 7,
		"hint bar controller = 7 baris (paritas get_hints 'game')")
	_expect(hint_rows_pad != hint_rows_keyboard,
		"label hint controller beda dari label keyboard")
	controller.set_mode(ControllerScript.MODE_KEYBOARD)
	hud._sync_hint_visibility()
	_expect(hint_host != null and not hint_host.visible,
		"hint bar sembunyi lagi saat kembali ke keyboard")

	# Tombol INPUT di menu utama = paritas btn_id "input_select".
	var input_button = _find_button_by_text(menu, "INPUT")
	_expect(input_button != null, "tombol INPUT ada di menu utama")

	# Router JANGAN jalan sendiri selama harness: perangkat ter-script di-step
	# manual (tick_frame/route dipanggil langsung), sama seperti oracle.
	router.set_process(false)
	controller.scripted_device = _xbox_device()
	controller.init_joystick()
	controller.set_mode(ControllerScript.MODE_CONTROLLER)
	hud._sync_hint_visibility()
	_expect(hint_host != null and hint_host.visible,
		"hint bar tampil saat mode controller (perangkat terpasang)")
	controller.set_mode(ControllerScript.MODE_KEYBOARD)
	hud._sync_hint_visibility()

	router.trace_enabled = true
	for scenario in section["scenarios"]:
		_route_case(router, controller, menu, scenario)

	# JALUR PRODUKSI PENUH: satu frame perangkat ter-script lewat tick_frame()
	# (device -> ControllerManager.get_pressed_actions -> route -> Main).
	controller.scripted_device = _xbox_device()
	controller.set_mode(ControllerScript.MODE_CONTROLLER)
	controller.cursor_x = 640.0
	controller.cursor_y = 360.0
	GameManager.state = "playing"
	GameManager.close_shop()
	GameManager.clear_selection()
	router.state_override = "game"
	router.reset_trace()
	controller.scripted_device["buttons"] = {0: {0: true}}
	router.tick_frame()
	_compare(_norm_calls(router.trace),
		[[ "click", 640, 360, 1 ]], "produksi/tick_frame confirm")
	controller.scripted_device["buttons"] = {0: {}}
	router.tick_frame()
	_compare(_norm_calls(router.trace),
		[["click", 640, 360, 1]], "produksi/tick_frame tepi (tahan = tanpa aksi)")
	router.state_override = ""
	_cleanup_field()
	router.trace_enabled = false


func _route_case(router, controller, menu, scenario: Dictionary) -> void:
	var tag := "routing/" + str(scenario["name"])
	var spec: Dictionary = scenario["spec"]
	var expect: Dictionary = scenario["expect"]

	# ── setel state produksi sesuai spec oracle ──
	var device := _xbox_device()
	controller.scripted_device = device
	controller.set_mode(ControllerScript.MODE_CONTROLLER)
	controller.controller_type = "xbox"
	controller._rumble_timer = 0
	var cursor: Array = spec.get("cursor", [640, 360])
	controller.cursor_x = float(int(cursor[0]))
	controller.cursor_y = float(int(cursor[1]))
	GameManager.state = str(spec.get("game_state", "playing"))
	GameManager.level_number = int(spec.get("level_number", 1))
	GameManager.close_shop()
	if bool(spec.get("shop_open", false)):
		GameManager.shop_open = true
	GameManager.clear_selection()
	var fake_hero = null
	var fake_tower = null
	if spec.get("selected_hero") != null:
		fake_hero = Node.new()
		fake_hero.name = "FakeHero"
		add_child(fake_hero)
		GameManager.selected_hero = fake_hero
	if spec.get("selected_tower") != null:
		fake_tower = Node.new()
		fake_tower.name = "FakeTower"
		add_child(fake_tower)
		GameManager.selected_tower = fake_tower
	_main._level_intro = null
	_main._boss_banner = null
	var fake_cine = null
	if bool(spec.get("level_intro", false)):
		fake_cine = FakeCinematic.new()
		_main._level_intro = fake_cine
	elif bool(spec.get("boss_intro", false)):
		fake_cine = FakeCinematic.new()
		_main._boss_banner = fake_cine
	elif bool(spec.get("boss_death", false)):
		fake_cine = FakeCinematic.new()
		add_child(fake_cine_node(fake_cine))
	router.state_override = str(spec["state"])
	router.ui_buttons_override = _rects(spec.get("menu_buttons",
		spec.get("ui_buttons", {})))
	if menu != null:
		var menu_state = spec.get("menu_state")
		if menu_state != null:
			menu.visible = true
			menu.state = int(menu.State[str(menu_state)])
	router.reset_trace()

	for action in spec["actions"]:
		router.route(str(action))

	# ── bandingkan jejak produksi dengan oracle ──
	var got: Array = []
	for entry in router.trace:
		var row: Array = []
		for value in entry:
			row.append(value)
		got.append(row)
	_compare(_norm_calls(got), _norm_calls(expect["calls"]), tag + "/calls")
	_compare(controller.get_cursor_pos(),
		Vector2i(int(expect["cursor"][0]), int(expect["cursor"][1])),
		tag + "/cursor")
	var rumble_got: Array = []
	for entry in device["rumble"]:
		rumble_got.append([float(entry[0]), float(entry[1]), int(entry[2])])
	var rumble_want: Array = []
	for entry in expect["rumble"]:
		rumble_want.append([float(entry[0]), float(entry[1]), int(entry[2])])
	_compare(rumble_got, rumble_want, tag + "/rumble")
	var menu_action_want = expect["menu_action"]
	var has_resume := _has_call(got, "menu_action")
	_compare(has_resume, menu_action_want != null and str(menu_action_want) \
		== "resume", tag + "/menu_action")
	if fake_cine != null:
		_expect(fake_cine.skipped.size() == 1,
			tag + "/cinematic di-skip tepat sekali")

	# ── bersihkan sisi efek (level berikutnya bisa benar-benar mulai) ──
	_cleanup_field()
	if fake_hero != null and is_instance_valid(fake_hero):
		fake_hero.free()
	if fake_tower != null and is_instance_valid(fake_tower):
		fake_tower.free()
	GameManager.close_shop()
	GameManager.clear_selection()
	GameManager.state = "playing"
	router.state_override = ""
	router.ui_buttons_override = {}


## Node pembungkus cinematic palsu — lihat class FakeCinematicHost.
func fake_cine_node(fake) -> Node:
	var host := FakeCinematicHost.new()
	host.name = "FakeCinematicHost"
	host.fake = fake
	add_child(host)
	return host


func _cleanup_field() -> void:
	get_tree().paused = false
	if _main == null or not is_instance_valid(_main):
		return
	if _main.has_method("_free_cinematics"):
		_main._free_cinematics()
	if _main.has_method("_clear_field"):
		_main._clear_field()
	for node in get_tree().get_nodes_in_group("cinematic"):
		if is_instance_valid(node) and node.name == "FakeCinematicHost":
			node.free()
	_main._level_intro = null
	_main._boss_banner = null


# ══════════════════════════════════════════════════════════
#  BANTU
# ══════════════════════════════════════════════════════════

func _xbox_device() -> Dictionary:
	return {
		"ids": [0],
		"names": {0: "Xbox Wireless Controller"},
		"guids": {0: "030000005e040000fd02000000000000"},
		"buttons": {},
		"axes": {},
		"hats": {0: [0, 0]},
		"button_count": {0: 15},
		"axis_count": {0: 6},
		"hat_count": {0: 1},
		"rumble": [],
		"stop_rumble": 0,
	}


## Return TIDAK bertipe (dan pemanggil memakai `var mgr = `): objek dibuat
## dari script hasil preload, jadi kalau diberi tipe Node, setiap panggilan
## `mgr.update()` jadi parse error ("Cannot find member ... in base Node").
func _make_manager(device: Dictionary):
	var mgr = ControllerScript.new()
	mgr.scripted_device = device
	add_child(mgr)
	return mgr


## Manajer dalam mode controller dengan perangkat Xbox ter-script.
func _controller_mode(device: Dictionary):
	var mgr = _make_manager(device)
	mgr.init_joystick()
	mgr.set_mode(ControllerScript.MODE_CONTROLLER)
	return mgr


func _mode_manager(mode: String, ctype):
	var device := _xbox_device()
	var mgr = _make_manager(device)
	mgr.init_joystick()
	mgr.set_mode(mode)
	mgr.controller_type = ctype
	return mgr


## Tuliskan satu frame perangkat ter-script (button/axis/hat). Field yang
## tidak ada di-step = kosong/netral, persis oracle (`frame.get(..., {})`).
func _apply_frame(device: Dictionary, step: Dictionary) -> void:
	var buttons: Dictionary = {}
	if step.has("buttons"):
		for key in step["buttons"]:
			buttons[int(key)] = bool(step["buttons"][key])
	device["buttons"] = {0: buttons}
	var axes: Dictionary = {}
	if step.has("axes"):
		for key in step["axes"]:
			axes[int(key)] = float(step["axes"][key])
	device["axes"] = {0: axes}
	var hat := [0, 0]
	if step.has("hat"):
		hat = [int(step["hat"][0]), int(step["hat"][1])]
	device["hats"] = {0: hat}


func _rects(source) -> Dictionary:
	var out: Dictionary = {}
	if source == null:
		return out
	var data: Dictionary = source
	for key in data:
		var v: Array = data[key]
		out[str(key)] = Rect2(float(v[0]), float(v[1]), float(v[2]), float(v[3]))
	return out


## PygameButton menggambar sendiri dan menyimpan label di `label_text`
## (Button.text-nya kosong) — keduanya diperiksa.
func _find_button_by_text(root: Node, text: String):
	if root == null or not is_instance_valid(root):
		return null
	for child in root.get_children():
		if child is Button:
			var label := str((child as Button).text)
			var custom = child.get("label_text")
			if custom != null:
				label += "|" + str(custom)
			if label.find(text) >= 0:
				return child
		var found = _find_button_by_text(child, text)
		if found != null:
			return found
	return null


func _has_call(calls: Array, name: String) -> bool:
	for entry in calls:
		if not (entry as Array).is_empty() and str(entry[0]) == name:
			return true
	return false


## Normalkan jejak: nama + argumen numerik sebagai int (posisi kursor pygame
## sudah int karena get_cursor_pos()).
func _norm_calls(calls) -> Array:
	var out: Array = []
	for entry in calls:
		var row: Array = []
		for value in entry:
			if value is float or value is int:
				row.append(int(round(float(value))))
			else:
				row.append(str(value))
		out.append(row)
	return out


func _vec2(value) -> Vector2:
	var v: Array = value
	return Vector2(float(v[0]), float(v[1]))


func _dict(value) -> Dictionary:
	var out: Dictionary = {}
	var data: Dictionary = value
	for key in data:
		out[str(key)] = data[key]
	return out


func _compare(actual, expected, label: String, tolerance: float = 0.0) -> void:
	_checks += 1
	var ok := false
	if tolerance > 0.0 and actual is Vector2 and expected is Vector2:
		ok = actual.distance_to(expected) <= tolerance
	elif actual is float and expected is float:
		ok = absf(actual - expected) <= 0.0001
	else:
		ok = _equal(actual, expected)
	if not ok:
		_failures += 1
		print("[ControllerInputParityTest] FAIL %s: got %s want %s"
			% [label, str(actual), str(expected)])
		push_error("[ControllerInputParityTest] " + label)


func _equal(a, b) -> bool:
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size():
			return false
		for key in a:
			if not b.has(key):
				return false
			if not _equal(a[key], b[key]):
				return false
		return true
	if a is Array and b is Array:
		if a.size() != b.size():
			return false
		for i in range(a.size()):
			if not _equal(a[i], b[i]):
				return false
		return true
	if a is float or b is float:
		return absf(float(a) - float(b)) <= 0.0001
	if (a is int or a is bool) and (b is int or b is bool):
		return int(a) == int(b)
	return str(a) == str(b)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		print("[ControllerInputParityTest] FAIL: " + message)
		push_error("[ControllerInputParityTest] " + message)


func _finish() -> void:
	if is_instance_valid(_main):
		if _main._router != null and is_instance_valid(_main._router):
			_main._router.trace_enabled = false
		if _main._controller != null and is_instance_valid(_main._controller):
			_main._controller.scripted_device = null
			_main._controller.set_mode(ControllerScript.MODE_KEYBOARD)
		_main.free()
	SaveManager.data = _save_before
	if _save_file_before == null:
		if FileAccess.file_exists(SaveManager.SAVE_PATH):
			DirAccess.remove_absolute(SaveManager.SAVE_PATH)
	else:
		var f := FileAccess.open(SaveManager.SAVE_PATH, FileAccess.WRITE)
		f.store_string(_save_file_before)
	GameManager.set_process(true)
	GameManager.waves_enabled = true
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.level_number = 1
	get_tree().paused = false
	if _failures == 0:
		print("[ControllerInputParityTest] PASS: %d checks lapisan gamepad vs oracle pygame" % _checks)
	else:
		print("[ControllerInputParityTest] FAIL: %d/%d checks gagal" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
