extends RefCounted
## Layer 9bb: replays the `KillFeed.draw()` oracle fixture through
## `kill_feed_layout.gd`. `kill_feed_draw_source_oracle.py` runs the REAL class
## from `_render.py` under a recording pygame shim (0.55*size px per glyph), so
## every op (kind, geometry, colour, surface alpha, order) below comes from the
## source. Each frame is replayed twice: from the recorded entry state, and from
## the production `KillFeed` state machine fed the same scripted kills.

const Layout = preload("res://scripts/ui/kill_feed_layout.gd")
const KillFeed = preload("res://scripts/ui/kill_feed.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/kill_feed_draw_source.json"
const COMPARED_KEYS := [
	"kind", "rect", "color", "mult", "width", "radius", "text", "size", "style", "pos", "w", "h"
]
## [lifetime, alpha, slide_x] read off recorded source frames (max lifetime 180).
const PHASES := [
	[180, 0, 100],
	[178, 34, 86],
	[172, 136, 46],
	[166, 238, 6],
	[165, 255, 0],
	[46, 255, 0],
	[45, 255, 0],
	[44, 249, 0],
	[29, 164, 0],
	[9, 51, 0],
	[1, 5, 0],
]


static func _measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(float(font_size) * 0.55) * text.length(), font_size)


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
	for key_name in COMPARED_KEYS:
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


static func _has_tick(ticks: Array, tick: int) -> bool:
	for value in ticks:
		if int(value) == tick:
			return true
	return false


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Kill feed draw fixture parses")
	if not (data is Dictionary):
		return
	var screen := Vector2i(int(data["screen"][0]), int(data["screen"][1]))
	check.call(is_equal_approx(float(data["glyph_factor"]), 0.55), "Kill feed oracle glyph is 0.55")
	check.call(data["frames"].size() == 31, "Kill feed draw oracle pins 31 source frames")
	_check_phases(check)
	_check_recorded_frames(check, data, screen)
	_check_production_replay(check, data, screen)
	_check_view_wiring(check)


func _check_phases(check: Callable) -> void:
	for row_value in PHASES:
		var row: Array = row_value
		var life: int = row[0]
		check.call(
			Layout.fade_alpha(life, 180) == int(row[1]),
			"Kill feed alpha at lifetime %d is %d" % [life, int(row[1])]
		)
		check.call(
			Layout.slide_x(life, 180) == int(row[2]),
			"Kill feed slide at lifetime %d is %d" % [life, int(row[2])]
		)


func _expect_ops(check: Callable, label: String, actual: Array, expected: Array) -> void:
	var bad := _first_mismatch(actual, expected)
	check.call(
		bad < 0,
		(
			"Kill feed %s: %d ops match source (first mismatch #%d: got %s, want %s)"
			% [
				label,
				expected.size(),
				bad,
				str(actual[bad]) if 0 <= bad and bad < actual.size() else "",
				str(expected[bad]) if 0 <= bad and bad < expected.size() else ""
			]
		)
	)


func _check_recorded_frames(check: Callable, data: Dictionary, screen: Vector2i) -> void:
	var drawn := 0
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		var label := "%s t=%d %s" % [frame["label"], int(frame["tick"]), frame["phase"]]
		var entries: Array = frame["entries"]
		_expect_ops(check, label, Layout.ops(entries, screen.x, _measure), frame["ops"])
		drawn += frame["ops"].size()
	check.call(drawn == 192, "Kill feed oracle pins 192 recorded draw ops")


func _check_production_replay(check: Callable, data: Dictionary, screen: Vector2i) -> void:
	var frames := {}
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		frames["%s:%d:%s" % [frame["label"], int(frame["tick"]), frame["phase"]]] = frame
	var replayed := 0
	for scenario_value in data["scenarios"]:
		var scenario: Dictionary = scenario_value
		var feed := KillFeed.new()
		var sampled: Array = []
		sampled.append_array(scenario["after"])
		sampled.append_array(scenario["before"])
		var last_tick := 0
		for tick_value in sampled:
			last_tick = maxi(last_tick, int(tick_value))
		for tick in range(last_tick + 1):
			for kill_value in scenario["kills"]:
				var kill: Array = kill_value
				if int(kill[0]) == tick:
					feed.add_kill(String(kill[1]), String(kill[2]), String(kill[3]))
			if _has_tick(scenario["before"], tick):
				replayed += _replay_frame(check, frames, scenario, tick, "pre", feed, screen)
			feed.update()
			if _has_tick(scenario["after"], tick):
				replayed += _replay_frame(check, frames, scenario, tick, "post", feed, screen)
	check.call(
		replayed == data["frames"].size(),
		"Kill feed production state replays every recorded frame (%d)" % replayed
	)


func _replay_frame(
	check: Callable,
	frames: Dictionary,
	scenario: Dictionary,
	tick: int,
	phase: String,
	feed: KillFeed,
	screen: Vector2i
) -> int:
	var key := "%s:%d:%s" % [scenario["label"], tick, phase]
	check.call(frames.has(key), "Kill feed fixture has frame %s" % key)
	if not frames.has(key):
		return 0
	var expected: Array = frames[key]["ops"]
	_expect_ops(check, "production " + key, Layout.ops(feed.entries, screen.x, _measure), expected)
	return 1


func _check_view_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	check.call(view.kill_feed_draw_ops(world).is_empty(), "Empty kill feed paints no ops")
	world.effects.kill_feed.add_kill("Kaizen", "Grimjaw", "blue")
	check.call(view.kill_feed_draw_ops(world).is_empty(), "Fresh kill stays transparent until tick")
	world._step_combo_clock()
	var sliding: Array = view.kill_feed_draw_ops(world)
	check.call(sliding.size() == 3, "First tick paints backing box, border and text")
	if sliding.size() == 3:
		var text_op: Dictionary = sliding[2]
		var right: int = int(text_op["pos"][0]) + int(text_op["w"])
		check.call(
			right == 1280 - Layout.BASE_INSET_X + Layout.slide_x(179, 180),
			"Real-font text keeps the right anchor plus the slide-in offset"
		)
		check.call(
			String(text_op["text"]) == "Kaizen >> Grimjaw" and int(text_op["w"]) > 0,
			"Real font measures the production kill text"
		)
	for _tick in range(20):
		world._step_combo_clock()
	var settled: Array = view.kill_feed_draw_ops(world)
	check.call(
		settled.size() == 3 and int(settled[2]["mult"]) == 255,
		"Held kill paints fully opaque text after the slide-in"
	)
	for _tick in range(KillFeed.LIFETIME):
		world._step_combo_clock()
	check.call(view.kill_feed_draw_ops(world).is_empty(), "Expired kill paints no ops")
	view.free()
	session.free()
