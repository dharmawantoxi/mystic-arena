extends RefCounted
## Layer 9bi2: replays the tactical command visuals of `tactical_commands.py` through
## `tactical_layout.gd`. `tactical_draw_source_oracle.py` runs the REAL `draw_world` /
## `draw_ui` under the recording pygame shim, so every op (kind, geometry, colour, alpha,
## order) below comes from the source. The view must build the marker and the banner from
## the live tactical state and stack the banner right after the achievement popup; a
## feedback must also float its text as a critical damage number like `_set_feedback`.

const Layout = preload("res://scripts/ui/tactical_layout.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/tactical_draw_source.json"
const COMPARED_KEYS := [
	"kind", "rect", "center", "radius", "a", "b", "color", "mult", "width", "blend", "text"
]
const TEXT_KEYS := ["size", "style", "pos"]


static func _value_equal(actual: Variant, expected: Variant) -> bool:
	if expected is Array:
		if not (actual is Array) or actual.size() != expected.size():
			return false
		for index in range(expected.size()):
			if not _value_equal(actual[index], expected[index]):
				return false
		return true
	if expected is float or expected is int:
		return (actual is float or actual is int) and absf(float(actual) - float(expected)) < 1e-6
	return str(actual) == str(expected)


static func _op_equal(actual: Dictionary, expected: Dictionary) -> bool:
	for key_name in COMPARED_KEYS + TEXT_KEYS:
		if expected.has(key_name) != actual.has(key_name):
			return false
		if expected.has(key_name) and not _value_equal(actual[key_name], expected[key_name]):
			return false
	return true


## Index of the first differing op, or -1 when both lists match exactly.
static func _first_mismatch(actual: Array, expected: Array) -> int:
	if actual.size() != expected.size():
		return mini(actual.size(), expected.size())
	for index in range(expected.size()):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1


## The oracle's text metrics: `int(size * 0.55)` px per glyph, `size` px tall.
static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


static func _frame(frames: Array, label: String) -> Dictionary:
	for frame in frames:
		if String(frame["label"]) == label:
			return frame
	return {}


static func _world_ops(frame: Dictionary) -> Array:
	var heroes: Array = []
	for hero in frame["heroes"]:
		heroes.append(Vector2(float(hero[0]), float(hero[1])))
	var point: Variant = frame["point"]
	var at := Vector2(float(point[0]), float(point[1])) if point is Array else Vector2.ZERO
	return Layout.world_ops(
		String(frame["command"]),
		at,
		point is Array,
		int(frame["timer"]),
		int(frame["ticks"]),
		heroes
	)


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Tactical draw fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["world_frames"] + data["feedback_frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 18 and ops_total == 105,
		"Tactical draw oracle pins 18 source frames and 105 draw ops"
	)
	_check_colors(check, data)
	_check_world_frames(check, data["world_frames"])
	_check_feedback_frames(check, data["feedback_frames"])
	_check_view_wiring(check, data)
	_check_feedback_side_effects(check)


func _check_colors(check: Callable, data: Dictionary) -> void:
	var colors: Dictionary = data["colors"]
	var tactical = Prototype.new().tactical
	var all_match := colors.size() == 6
	for command in colors:
		var rgb: Array = colors[command]
		tactical.active_command = String(command)
		var live: Color = tactical.command_color()
		all_match = (
			all_match
			and _value_equal(Layout.command_rgb(String(command)), rgb)
			and _value_equal([live.r8, live.g8, live.b8], rgb)
		)
	check.call(all_match, "Tactical marker colours match `_get_command_color` for every command")


func _check_world_frames(check: Callable, frames: Array) -> void:
	for frame in frames:
		var mismatch := _first_mismatch(_world_ops(frame), frame["ops"])
		check.call(
			mismatch == -1,
			(
				"Tactical marker %s matches the source ops (first mismatch %d)"
				% [frame["label"], mismatch]
			)
		)


func _check_feedback_frames(check: Callable, frames: Array) -> void:
	for frame in frames:
		var actual := Layout.feedback_ops(
			String(frame["text"]), frame["color"], int(frame["timer"]), _fake_measure
		)
		var mismatch := _first_mismatch(actual, frame["ops"])
		check.call(
			mismatch == -1,
			(
				"Tactical banner %s matches the source ops (first mismatch %d)"
				% [frame["label"], mismatch]
			)
		)


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var world := Prototype.new()
	var view := PrototypeView.new()
	var order: Array = view.overlay_paint_order()
	check.call(
		(
			order.find("tactical_feedback") == order.find("achievement") + 1
			and order.find("tactical_feedback") < order.find("level_intro")
		),
		"The tactical banner paints right after effects.draw_ui and before the level intro"
	)
	check.call(view.tactical_feedback_draw_ops(world).is_empty(), "No feedback paints no banner")
	check.call(
		view.tactical_world_draw_ops(world, 0).is_empty(), "No gather point paints no marker"
	)
	var held: Dictionary = _frame(data["feedback_frames"], "held")
	var rgb: Array = held.get("color", [255, 255, 255])
	world.tactical.feedback_text = String(held.get("text", ""))
	world.tactical.feedback_color = Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))
	world.tactical.feedback_timer = int(held.get("timer", 0))
	check.call(
		_first_mismatch(view.tactical_feedback_draw_ops(world, _fake_measure), held["ops"]) == -1,
		"The view builds the banner from the live feedback text, colour and timer"
	)
	var marker: Dictionary = _frame(data["world_frames"], "dealer_no_dashes")
	var point: Array = marker.get("point", [0, 0])
	world.tactical.active_command = String(marker.get("command", ""))
	world.tactical.gather_point = Vector2(float(point[0]), float(point[1]))
	world.tactical.gather_point_active = true
	world.tactical.gather_point_timer = int(marker.get("timer", 0))
	check.call(
		(
			_first_mismatch(
				view.tactical_world_draw_ops(world, int(marker.get("ticks", 0))), marker["ops"]
			)
			== -1
		),
		"The view builds the marker from the live gather point, command and timer"
	)
	view.free()


func _check_feedback_side_effects(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	if world.player_roster().is_empty():
		var hero = world.spawn_hero(KAIZEN, world.BLUE, Vector2(300, 300))
		world.player_hero_ids.append(hero.id)
	var before: int = world.effects.floating_texts.size()
	world.tactical.issue(world, "attack_boss")
	var tactical = world.tactical
	check.call(
		(
			tactical.feedback_text == "No boss active!"
			and tactical.feedback_color == Color8(255, 150, 100)
		),
		"A boss order without a boss warns in the source orange: %s" % tactical.feedback_text
	)
	var floats: Array = world.effects.floating_texts
	var spawned = floats.back() if floats.size() == before + 1 else null
	check.call(
		(
			spawned != null
			and spawned.text == tactical.feedback_text + "!"
			and spawned.critical
			and spawned.color == Color8(255, 220, 50)
			and absf(spawned.x - 640.0) <= 8.0
			and absf(spawned.y - 100.0) <= 3.0
		),
		"The feedback floats as a critical damage number at (640, 100), like `_set_feedback`"
	)
	tactical.cooldown = 0
	world.tactical.issue(world, "attack_boss", Vector2.ZERO, false, -1, -1, true)
	check.call(
		world.effects.floating_texts.size() == before + 1,
		"A silent order shows no banner and floats no text"
	)
