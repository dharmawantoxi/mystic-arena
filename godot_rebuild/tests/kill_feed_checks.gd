extends RefCounted
## Replays the `_render.py::KillFeed` source oracle fixture through the native
## port. `kill_feed_source_oracle.py` executes the real class with six kills
## scripted across 200 ticks, so the 180 tick lifetime and the 5 entry cap
## both fire inside the replay.

const KillFeed = preload("res://scripts/ui/kill_feed.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/kill_feed_source.json"

const TEXT := 0
const LIFETIME := 1
const Y_OFFSET := 2
const TARGET_Y := 3


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Kill feed fixture parses")
	if not (data is Dictionary):
		return

	var feed := KillFeed.new()
	for index in 8:
		feed.add_kill("Hero%d" % index, "Victim%d" % index, "blue")
	check.call(feed.entries.size() == 5, "Kill feed caps itself at 5 entries")

	var steps: Array = data["steps"]
	var scripted: Array = data["script"]
	check.call(scripted.size() == 6, "Source fixture keeps the 6 scripted kills")
	check.call(steps.size() == 200, "Source fixture keeps the 200 replayed ticks")

	var kills := {}
	for entry in scripted:
		kills[int(entry[0])] = entry

	feed = KillFeed.new()
	for index in range(steps.size()):
		if kills.has(index):
			var kill: Array = kills[index]
			feed.add_kill(String(kill[1]), String(kill[2]), String(kill[3]))
		feed.update()
		var expected: Array = steps[index]
		if not _matches(feed, expected):
			check.call(false, "Kill feed step %d drifted from source" % index)
			return

	check.call(true, "Kill feed replays %d source ticks exactly" % steps.size())
	_check_view_wiring(check)


func _check_view_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	check.call(
		int(view.overlay_draw_summary().get("kill_feed_count", -1)) == 0,
		"PrototypeView.overlay_draw_summary starts with zero kill feed entries"
	)
	world.effects.kill_feed.add_kill("Kaizen", "Grimjaw", "blue")
	check.call(
		int(view.overlay_draw_summary().get("kill_feed_count", 0)) == 1,
		"PrototypeView.overlay_draw_summary reflects added KillFeed entry"
	)
	for _tick in range(KillFeed.LIFETIME):
		world._step_combo_clock()
	check.call(
		int(view.overlay_draw_summary().get("kill_feed_count", -1)) == 0,
		"KillFeed entry retires from PrototypeView.overlay_draw_summary after lifetime"
	)
	view.free()
	session.free()


func _matches(feed, expected: Array) -> bool:
	if feed.entries.size() != expected.size():
		return false
	for slot in range(expected.size()):
		var want: Array = expected[slot]
		var got: Dictionary = feed.entries[slot]
		if (
			String(got.get("text", "")) != String(want[TEXT])
			or int(got.get("lifetime", 0)) != int(want[LIFETIME])
			or not is_equal_approx(float(got.get("y_offset", -1.0)), float(want[Y_OFFSET]))
			or not is_equal_approx(float(got.get("target_y", -1.0)), float(want[TARGET_Y]))
		):
			return false
	return true
