extends RefCounted
## Replays the `_render.py::ComboCounter` source oracle fixture through the
## native port. `combo_counter_source_oracle.py` executes the real class, so
## the timer window, spring scale and flash decay are the source's, not a
## re-implementation.

const ComboCounter = preload("res://scripts/ui/combo_counter.gd")
const FIXTURE := "res://tests/fixtures/combo_counter_source.json"

const COUNT := 0
const TIMER := 1
const DISPLAY_SCALE := 2
const TARGET_SCALE := 3
const COLOR_FLASH := 4
const LAST_COMBO := 5


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Combo counter fixture parses")
	if not (data is Dictionary):
		return

	var counter := ComboCounter.new()
	check.call(
		is_equal_approx(float(data["max_timer"]), float(counter.max_timer)),
		"Combo window matches source"
	)

	var steps: Array = data["steps"]
	var kill_ticks: Array = data["kill_ticks"]
	check.call(kill_ticks.size() == 5, "Source fixture keeps the 5 scripted kills")
	check.call(steps.size() == 220, "Source fixture keeps the 220 replayed ticks")

	var kills := {}
	for tick in kill_ticks:
		kills[int(tick)] = true

	for index in range(steps.size()):
		if kills.has(index):
			counter.add_kill()
		counter.update()
		var expected: Array = steps[index]
		if not _matches(counter, expected):
			check.call(false, "Combo counter step %d drifted from source" % index)
			return

	check.call(true, "Combo counter replays %d source ticks exactly" % steps.size())
	_check_tiers(check)


func _matches(counter, expected: Array) -> bool:
	return (
		counter.count == int(expected[COUNT])
		and counter.timer == int(expected[TIMER])
		and is_equal_approx(counter.display_scale, float(expected[DISPLAY_SCALE]))
		and is_equal_approx(counter.target_scale, float(expected[TARGET_SCALE]))
		and counter.color_flash == int(expected[COLOR_FLASH])
		and counter.last_combo == int(expected[LAST_COMBO])
	)


func _check_tiers(check: Callable) -> void:
	var cases := [
		[3, "COMBO x3"],
		[5, "KILLING SPREE!"],
		[10, "RAMPAGE!"],
		[15, "UNSTOPPABLE!"],
		[20, "GODLIKE!"]
	]
	for case in cases:
		var tier: Dictionary = ComboCounter.tier_for(int(case[0]))
		check.call(
			String(tier.get("label", "")) == String(case[1]),
			"Combo tier %d matches source" % case[0]
		)
		check.call(tier.has("color"), "Combo tier %d carries a colour" % case[0])

	# The source uses `==`, not `>=`, so these counts announce nothing.
	for silent in [1, 2, 4, 7, 11, 21]:
		check.call(
			ComboCounter.tier_for(silent).is_empty(), "Combo tier %d announces nothing" % silent
		)
