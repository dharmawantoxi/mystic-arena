extends RefCounted
## Replays the `_render.py::PopupAnimation` source oracle fixture through the
## native port. `popup_animation_source_oracle.py` executes the real source
## block (including the module-level `_ease_out_back` it calls), so the easing
## curve is the source's, not a re-implementation.

const PopupAnimation = preload("res://scripts/ui/popup_animation.gd")
const FIXTURE := "res://tests/fixtures/popup_animation_source.json"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Popup animation fixture parses")
	if not (data is Dictionary):
		return
	check.call(
		is_equal_approx(float(data["speed"]), PopupAnimation.SPEED), "Popup speed matches source"
	)
	var cases: Array = data["cases"]
	check.call(cases.size() == 2, "Source fixture covers show and hide")
	for entry in cases:
		_replay(entry as Dictionary, check)


func _replay(entry: Dictionary, check: Callable) -> void:
	var label: String = entry["name"]
	var item := PopupAnimation.new()
	item.show()
	for _warmup in range(int(entry["warmup"])):
		item.update()
	if String(entry["action"]) == "hide":
		item.hide()
	var steps: Array = entry["steps"]
	for index in range(steps.size()):
		item.update()
		var expected: Array = steps[index]
		check.call(
			is_equal_approx(item.progress, float(expected[0])),
			"Progress matches source step %d: %s" % [index, label]
		)
		check.call(
			is_equal_approx(item.get_scale(), float(expected[1])),
			"Eased scale matches source step %d: %s" % [index, label]
		)
		check.call(
			item.get_offset_y() == int(expected[2]),
			"Slide offset matches source step %d: %s" % [index, label]
		)
