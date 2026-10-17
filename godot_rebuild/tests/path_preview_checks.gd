extends RefCounted
## Replays the `_render.py::PathPreview` source oracle fixture through the
## native port. `path_preview_source_oracle.py` runs the real `draw()` under a
## pygame shim and reads `alpha` / `offset` / per-arrow pulse off the frame
## with `settrace`, so the fade curve and dash phase are the source's.

const PathPreview = preload("res://scripts/ui/path_preview.gd")
const FIXTURE := "res://tests/fixtures/path_preview_source.json"

const ACTIVE := 0
const TIMER := 1
const ALPHA := 2


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Path preview fixture parses")
	if not (data is Dictionary):
		return

	var preview := PathPreview.new()
	check.call(
		is_equal_approx(float(data["duration"]), float(preview.duration)),
		"Path preview duration matches source"
	)
	_check_lifetime(check, preview, data)
	_check_samples(check, preview, data)


func _check_lifetime(check: Callable, preview, data: Dictionary) -> void:
	var steps: Array = data["steps"]
	check.call(steps.size() == 130, "Source fixture keeps the 130 replayed ticks")

	var lanes: Array = [[0, 0], [10, 100], [20, 100], [30, 100]]
	preview.show(lanes)
	check.call(preview.paths == lanes, "show() stores the lane paths")

	for index in range(steps.size()):
		preview.update()
		var expected: Array = steps[index]
		if int(expected[ACTIVE]) == 0:
			if preview.active or preview.timer != int(expected[TIMER]):
				check.call(false, "Path preview step %d should be idle" % index)
				return
			continue
		if not preview.active or preview.timer != int(expected[TIMER]):
			check.call(false, "Path preview step %d drifted on the timer" % index)
			return
		if preview.get_alpha() != int(expected[ALPHA]):
			check.call(false, "Path preview step %d drifted from source" % index)
			return

	check.call(true, "Path preview replays %d source ticks exactly" % steps.size())
	check.call(preview.paths.is_empty(), "Path preview clears its lanes on expiry")


func _check_samples(check: Callable, preview, data: Dictionary) -> void:
	var point_indices: Array = data["point_indices"]
	var arrow_segments: Array = data["arrow_segments"]
	check.call(point_indices.size() == 5, "Source fixture keeps the 5 sampled arrows")

	var samples: Array = data["samples"]
	check.call(not samples.is_empty(), "Source fixture keeps dash samples")

	for sample in samples:
		var animation_time: float = float(sample["animation_time"])
		preview.active = true
		preview.timer = int(sample["timer"])
		if sample["alpha"] == null:
			check.call(
				preview.get_alpha() <= 0,
				"Path preview hides at timer %d (source returns early)" % int(sample["timer"])
			)
			continue

		if preview.get_alpha() != int(sample["alpha"]):
			check.call(false, "Path preview alpha drifted at timer %d" % int(sample["timer"]))
			return
		if PathPreview.dash_offset(animation_time) != int(sample["dash_offset"]):
			check.call(false, "Dash offset drifted at animation time %s" % animation_time)
			return

		var arrows: Array = sample["arrows"]
		if arrows.size() != point_indices.size():
			check.call(false, "Arrow count drifted at timer %d" % int(sample["timer"]))
			return
		for slot in range(arrows.size()):
			var want: Array = arrows[slot]
			var point_index := int(point_indices[slot])
			var pulse: int = PathPreview.pulse_index(point_index, animation_time)
			var segment: Array = arrow_segments[slot]
			var source_point := Vector2(float(segment[0][0]), float(segment[0][1]))
			var target_point := Vector2(float(segment[1][0]), float(segment[1][1]))
			var points := PathPreview.arrow_points(source_point, target_point, int(want[1]))
			if (
				pulse != int(want[0])
				or PathPreview.arrow_size(pulse) != int(want[1])
				or PathPreview.arrow_alpha(int(sample["alpha"]), pulse) != int(want[2])
				or not _points_match(points, want[3])
			):
				check.call(
					false,
					(
						"Arrow %d drifted at timer %d / time %s"
						% [slot, int(sample["timer"]), animation_time]
					)
				)
				return

	check.call(
		true,
		"Path preview replays %d dash samples and source arrow geometry exactly" % samples.size()
	)


func _points_match(actual: PackedVector2Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		var pair: Array = expected[index]
		if int(actual[index].x) != int(pair[0]) or int(actual[index].y) != int(pair[1]):
			return false
	return true
