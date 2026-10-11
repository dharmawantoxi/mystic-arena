extends RefCounted
## Replays the `_render.py::AchievementPopup` source oracle fixture through the
## native port. `achievement_popup_source_oracle.py` runs the real `draw()`
## under a pygame shim and reads `x_offset` / `alpha` / `glow_alpha` off the
## frame with `settrace`, so the slide curve and the queue timing are the
## source's, not a re-implementation.

const AchievementPopup = preload("res://scripts/ui/achievement_popup.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/achievement_popup_source.json"

const SHOWING := 0
const TIMER := 1
const QUEUE := 2
const CURVE := 3
const TITLE := 4

const PROGRESS := 0
const OFFSET_X := 1
const ALPHA := 2
const GLOW := 3


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Achievement popup fixture parses")
	if not (data is Dictionary):
		return

	var popup := AchievementPopup.new()
	check.call(
		is_equal_approx(float(data["duration"]), float(popup.duration)),
		"Achievement slot matches source"
	)
	_check_layout(check, popup)
	_check_defaults(check, popup)
	_check_replay(check, popup, data)
	_check_view_wiring(check)


func _check_view_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	world.effects.unlock_achievement("GLOW TEST", "Early slot glow")
	world._step_combo_clock()
	check.call(
		(
			bool(view.overlay_draw_summary().get("achievement_showing", false))
			and bool(view.overlay_draw_summary().get("achievement_glow_active", false))
		),
		"PrototypeView.overlay_draw_summary reports active achievement glow during early slot"
	)
	for _step in range(60):
		world._step_combo_clock()
	check.call(
		(
			bool(view.overlay_draw_summary().get("achievement_showing", false))
			and not bool(view.overlay_draw_summary().get("achievement_glow_active", true))
		),
		"PrototypeView.overlay_draw_summary clears achievement glow after 30% slot threshold"
	)
	view.free()
	session.free()


func _check_layout(check: Callable, popup) -> void:
	# The source parks the panel top-right, 20px in, plus the slide offset.
	popup.current = {"title": "Layout", "description": "", "icon_type": "star"}
	popup.timer = popup.duration / 2
	check.call(popup.get_offset_x() == 0, "Held panel sits at zero offset")
	check.call(popup.panel_x(1280) == 1280 - 280 - 20, "Held panel parks 20px from the right edge")
	check.call(popup.panel_y() == 180, "Panel keeps the source's top offset")
	popup.current = {}
	popup.timer = 0


func _check_defaults(check: Callable, popup) -> void:
	popup.unlock("Solo", "No icon type given")
	var entry: Dictionary = popup.queue[0]
	check.call(String(entry["icon_type"]) == "star", "unlock() defaults the icon to star")
	check.call(String(entry["title"]) == "Solo", "unlock() stores the title")
	popup.queue.clear()


func _check_replay(check: Callable, popup, data: Dictionary) -> void:
	var steps: Array = data["steps"]
	check.call(steps.size() == 760, "Source fixture keeps the 760 replayed ticks")

	var unlocks: Array = data["unlocks"]
	check.call(unlocks.size() == 4, "Source fixture keeps the 4 scripted unlocks")
	var by_tick := {}
	for entry in unlocks:
		by_tick[int(entry[0])] = entry

	popup = AchievementPopup.new()
	for index in range(steps.size()):
		if by_tick.has(index):
			var unlock: Array = by_tick[index]
			popup.unlock(String(unlock[1]), String(unlock[2]), String(unlock[3]))
		popup.update()
		if not _matches(popup, steps[index]):
			check.call(false, "Achievement popup step %d drifted from source" % index)
			return

	check.call(true, "Achievement popup replays %d source ticks exactly" % steps.size())
	check.call(not popup.is_showing(), "Achievement popup retires once the queue drains")
	check.call(popup.queue.is_empty(), "Achievement queue is empty at the end")


func _matches(popup, expected: Array) -> bool:
	if popup.is_showing() != (int(expected[SHOWING]) == 1):
		return false
	if popup.timer != int(expected[TIMER]) or popup.queue.size() != int(expected[QUEUE]):
		return false
	if not popup.is_showing():
		return expected[CURVE] == null

	if String(popup.current.get("title", "")) != String(expected[TITLE]):
		return false
	var curve: Array = expected[CURVE]
	if not is_equal_approx(popup.progress(), float(curve[PROGRESS])):
		return false
	var glow: int = AchievementPopup.NO_GLOW if curve[GLOW] == null else int(curve[GLOW])
	return (
		popup.get_offset_x() == int(curve[OFFSET_X])
		and popup.get_alpha() == int(curve[ALPHA])
		and popup.get_glow_alpha() == glow
	)
