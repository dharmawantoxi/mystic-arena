extends RefCounted
## Layer 9bv21: replays `touch_hud_source_oracle.py`'s fixture through
## `scripts/ui/touch_hud_layout.gd`. The oracle runs the REAL
## `mobile/hud.py::TouchHUD` under a pygame/platform shim, so the button
## rects, 80 px hit padding, visibility rules, press decay, hit answers and
## action intents below come from the Pygame source.

const Hud = preload("res://scripts/ui/touch_hud_layout.gd")
const Platform = preload("res://scripts/platform/mobile_platform.gd")
const FIXTURE := "res://tests/fixtures/touch_hud_source.json"

const SAFE_TOUCH := Rect2i(28, 10, 1224, 700)
const SAFE_DESKTOP := Rect2i(0, 0, 1280, 720)


static func _rect(values: Array) -> Rect2i:
	return Rect2i(int(values[0]), int(values[1]), int(values[2]), int(values[3]))


static func _color(values: Array) -> Color:
	return Color8(int(values[0]), int(values[1]), int(values[2]))


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Touch HUD fixture parses")
	if not (data is Dictionary):
		return
	_constant_checks(data, check)
	_layout_checks(data, check)
	_sync_checks(data, check)
	_hit_checks(data, check)
	_action_checks(data, check)


func _constant_checks(data: Dictionary, check: Callable) -> void:
	check.call(Hud.MIN_TAP == int(data["min_tap"]), "the HUD keeps the source 80 px minimum tap")
	check.call(Hud.PRESS_DECAY == float(data["press_decay"]), "press animation decays by 0.12")
	check.call(
		Hud.LOGICAL_WIDTH == int(data["logical_width"]) and Hud.LOGICAL_WIDTH / 2 == 640,
		"the end capsules centre on the 1280 px logical width"
	)
	var tetris: bool = Hud.KEYS.size() == 7 and Hud.KEYS[0] == "pause" and Hud.KEYS[6] == "back"
	check.call(tetris, "the button order matches the source dict order")
	var tactical: Array = [
		"gather", "protect_tower", "protect_castle", "attack_boss", "attack_damage_dealer"
	]
	var tactical_matches: bool = Hud.TACTICAL_ACTIONS.size() == tactical.size()
	for index in range(mini(Hud.TACTICAL_ACTIONS.size(), tactical.size())):
		if Hud.TACTICAL_ACTIONS[index] != String(tactical[index]):
			tactical_matches = false
	check.call(tactical_matches, "tactical actions keep the source tuple")


func _layout_checks(data: Dictionary, check: Callable) -> void:
	for row in data["layout"]:
		var safe := SAFE_TOUCH if bool(row["touch_mode"]) else SAFE_DESKTOP
		var built := Hud.build(safe)
		var tag := "[%s/%s] " % [
			"touch" if bool(row["touch_mode"]) else "desktop",
			"panel" if bool(row["panel_present"]) else "no-panel",
		]
		var expected: Dictionary = row["buttons"]
		check.call(built.size() == expected.size(), tag + "button count matches")
		for key in expected:
			var want: Dictionary = expected[key]
			if not built.has(key):
				check.call(false, tag + "missing button %s" % key)
				continue
			var got: Dictionary = built[key]
			check.call(got["rect"] == _rect(want["rect"]), tag + "%s rect matches" % key)
			check.call(
				got["hit_rect"] == _rect(want["hit_rect"]),
				tag + "%s hit rect matches (24 px pad, 80 px floor)" % key
			)
			check.call(
				String(got["label"]) == String(want["label"])
				and String(got["shape"]) == String(want["shape"])
				and int(got["font_size"]) == int(want["font_size"]),
				tag + "%s label/shape/size match" % key
			)
			check.call(
				got["color"] == _color(want["color"])
				and bool(got["visible"]) == bool(want["visible"]),
				tag + "%s colour and initial visibility match" % key
			)
	# The dock moves PAUSE/FPS out of the arena but never reshapes anything.
	for row in data["layout"]:
		if not bool(row["panel_present"]):
			continue
		var safe := SAFE_TOUCH if bool(row["touch_mode"]) else SAFE_DESKTOP
		var built := Hud.build(safe)
		check.call(
			built["pause"]["hit_rect"] == _rect(row["buttons"]["pause"]["hit_rect"]),
			"a present right panel keeps the HUD geometry"
		)


func _sync_checks(data: Dictionary, check: Callable) -> void:
	for row in data["sync"]:
		var built := Hud.build(SAFE_DESKTOP)
		built["pause"]["press_anim"] = 1.0
		Hud.sync(
			built,
			String(row["state"]),
			String(row["game_state"]),
			bool(row["cinematic"]),
			bool(row["panel_present"]),
			_next_level(String(row["game_state"]), int(row["level"]))
		)
		var tag := "[%s] " % row["label"]
		var expected: Dictionary = row["visible"]
		for key in expected:
			check.call(
				bool(built[key]["visible"]) == bool(expected[key]),
				tag + "%s visibility matches (%s)" % [key, str(expected[key])]
			)
		check.call(
			is_equal_approx(float(built["pause"]["press_anim"]), float(row["press_anim"])),
			tag + "press animation decays once per sync"
		)


func _next_level(game_state: String, level: int) -> bool:
	# `levels.get_next_level(level) is not None` for the oracle stub.
	return game_state == "victory" and level < 3


func _hit_checks(data: Dictionary, check: Callable) -> void:
	for row in data["hits"]:
		var built := Hud.build(SAFE_DESKTOP)
		Hud.sync(
			built,
			String(row["state"]),
			String(row["game_state"]),
			bool(row["cinematic"]),
			bool(row["panel_present"]),
			_next_level(String(row["game_state"]), int(row["level"]))
		)
		var pos := Vector2i(int(row["pos"][0]), int(row["pos"][1]))
		var action := Hud.hit_test(built, pos)
		var want := String(row["action"]) if row["action"] != null else ""
		check.call(action == want, "[%s] hit_test returns '%s'" % [row["label"], want])
		var pressed: Array = []
		for key in built:
			if float(built[key]["press_anim"]) > 0.0:
				pressed.append(key)
		check.call(
			pressed == Array(row["pressed"]),
			"[%s] pressed buttons match (%s)" % [row["label"], str(row["pressed"])]
		)
		check.call(
			Hud.blocks(built, pos) == bool(row["blocks"]),
			"[%s] blocks() matches" % row["label"]
		)


func _action_checks(data: Dictionary, check: Callable) -> void:
	for row in data["actions"]:
		var tower_team := String(row["tower"]) if row["tower"] != null else ""
		var intent := Hud.action_intent(String(row["action"]), true, true, true, tower_team)
		var tag := "[%s/%s] " % [row["action"], str(row["tower"])]
		check.call(bool(intent["handled"]) == bool(row["handled"]), tag + "handled matches")
		check.call(
			bool(intent["request_pause"]) == bool(row["request_pause"]),
			tag + "pause request matches"
		)
		check.call(
			int(bool(intent["toggle_debug"])) == int(row["debug_toggles"]),
			tag + "debug toggle matches"
		)
		check.call(
			bool(intent["replay_requested"]) == bool(row["replay"])
			and bool(intent["next_level_requested"]) == bool(row["next_level"])
			and bool(intent["return_to_menu_requested"]) == bool(row["menu"]),
			tag + "result-screen intents match"
		)
		check.call(
			(bool(intent["menu_escape"]) and int(row["menu_key"]) == 27)
			or (not bool(intent["menu_escape"]) and row["menu_key"] == null),
			tag + "menu escape matches"
		)
		var calls: Array = row["tactical"]
		if calls.is_empty():
			check.call(
				String(intent["tactical_action"]) == "",
				tag + "no tactical hold without a game tactical switch"
			)
		else:
			var call_row: Dictionary = calls[0]
			check.call(
				String(intent["tactical_action"]) == String(call_row["action"]),
				tag + "tactical hold starts the same command"
			)
			var want_tower := String(call_row["tower"]) if call_row["tower"] != null else ""
			check.call(
				String(intent["tactical_tower"]) == want_tower,
				tag + "only a blue selected tower is passed to protect_tower"
			)
	check.call(
		not bool(Hud.action_intent("gather", false, true, true)["handled"]),
		"a tactical press without a game is not handled"
	)
	check.call(
		bool(Hud.action_intent("pause", false, false, false)["request_pause"]),
		"PAUSE works even without a game or menu"
	)
	check.call(
		Platform.LOGICAL_WIDTH == Hud.LOGICAL_WIDTH,
		"the HUD shares the 1280 px logical width with the platform layer"
	)
