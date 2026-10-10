extends RefCounted
## Replays the `_render.py::WaveAnnouncer` source oracle fixture through the
## native port. `wave_announcer_source_oracle.py` runs the real `draw()` under
## a pygame shim and reads `x_offset` / `alpha` off the frame with `settrace`,
## so the three phase slide curve is the source's, not a re-implementation.

const WaveAnnouncer = preload("res://scripts/ui/wave_announcer.gd")
const FIXTURE := "res://tests/fixtures/wave_announcer_source.json"

const ACTIVE := 0
const TIMER := 1
const CURVE := 2

const PROGRESS := 0
const OFFSET_X := 1
const ALPHA := 2


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Wave announcer fixture parses")
	if not (data is Dictionary):
		return

	var banner := WaveAnnouncer.new()
	check.call(
		is_equal_approx(float(data["duration"]), float(banner.duration)),
		"Wave banner duration matches source"
	)
	check.call(int(data["wave_num"]) == 7, "Source fixture announces wave 7")

	var screen_w: int = int(data["screen_w"])
	var steps: Array = data["steps"]
	check.call(steps.size() == 130, "Source fixture keeps the 130 replayed ticks")

	banner.announce(int(data["wave_num"]))
	check.call(banner.title() == "WAVE 7", "Banner title matches the source format")

	for index in range(steps.size()):
		banner.update()
		var expected: Array = steps[index]
		if int(expected[ACTIVE]) == 0:
			if banner.active or banner.timer != int(expected[TIMER]):
				check.call(false, "Wave banner step %d should be idle" % index)
				return
			continue
		if not banner.active or banner.timer != int(expected[TIMER]):
			check.call(false, "Wave banner step %d drifted on the timer" % index)
			return
		var curve: Array = expected[CURVE]
		if not _matches(banner, screen_w, curve):
			check.call(false, "Wave banner step %d drifted from source" % index)
			return

	check.call(true, "Wave announcer replays %d source ticks exactly" % steps.size())
	check.call(not banner.active, "Wave banner retires itself once the timer runs out")


func _matches(banner, screen_w: int, curve: Array) -> bool:
	return (
		is_equal_approx(banner.progress(), float(curve[PROGRESS]))
		and banner.get_offset_x(screen_w) == int(curve[OFFSET_X])
		and banner.get_alpha() == int(curve[ALPHA])
	)
