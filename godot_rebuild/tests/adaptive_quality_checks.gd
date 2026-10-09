extends RefCounted
## Native parity tests for the adaptive-quality sample and cooldown state machine.

const Controller = preload("res://scripts/settings/adaptive_quality_controller.gd")
const RuntimeScript = preload("res://scripts/settings/adaptive_quality_runtime.gd")
const FIXTURE := "res://tests/fixtures/adaptive_quality_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "adaptive-quality source fixture parses")
	if not fixture is Dictionary:
		return
	check.call(
		(
			Controller.LOW == fixture.levels.low
			and Controller.MEDIUM == fixture.levels.medium
			and Controller.HIGH == fixture.levels.high
		),
		"native quality-level IDs match Python"
	)
	var controller = Controller.new()
	check.call(
		(
			controller.enabled
			and controller.low_fps == fixture.adaptive.low_fps
			and controller.high_fps == fixture.adaptive.high_fps
			and controller.sample_window == fixture.adaptive.sample_window
		),
		"native governor defaults match Python thresholds and sampling window"
	)
	check.call(
		(
			Controller.COOLDOWN_AFTER_LOWER == int(fixture.adaptive.cooldown_steps[0])
			and Controller.COOLDOWN_AFTER_RAISE == int(fixture.adaptive.cooldown_steps[1])
		),
		"native cooldown lengths match Python"
	)
	check.call(
		(
			RuntimeScript.LOW_TARGET_FPS == int(fixture.target_fps.low)
			and RuntimeScript.NORMAL_TARGET_FPS == int(fixture.target_fps.medium_and_high)
		),
		"native quality target FPS mapping matches the source preset"
	)

	controller.configure(Controller.HIGH)
	for index in 89:
		controller.update(0.0)
	check.call(
		controller.level == Controller.HIGH and controller.samples.size() == 89,
		"governor waits for the complete 90-frame source window"
	)
	controller.update(0.0)
	check.call(
		(
			controller.level == Controller.MEDIUM
			and controller.cooldown == 180
			and controller.samples.is_empty()
		),
		"low average steps High to Medium once and starts the 180-frame cooldown"
	)
	for index in 179:
		controller.update(0.0)
	check.call(
		controller.cooldown == 1 and controller.samples.is_empty(),
		"cooldown frames do not enter the next sample window"
	)
	controller.update(0.0)
	check.call(controller.cooldown == 0, "cooldown expires after exactly 180 calls")
	for index in 89:
		controller.update(0.0)
	check.call(controller.level == Controller.MEDIUM, "second drop waits for another full window")
	controller.update(0.0)
	check.call(
		controller.level == Controller.LOW and controller.cooldown == 180,
		"continued low FPS steps Medium to Low only after its cooldown"
	)

	var low_boundary = Controller.new()
	for index in 90:
		low_boundary.update(26.0)
	check.call(
		low_boundary.level == Controller.HIGH and low_boundary.cooldown == 0,
		"FPS exactly at the low threshold does not trigger a downgrade"
	)
	var high_boundary = Controller.new()
	high_boundary.configure(Controller.LOW)
	for index in 90:
		high_boundary.update(52.0)
	check.call(
		high_boundary.level == Controller.LOW and high_boundary.cooldown == 0,
		"FPS exactly at the high threshold does not trigger an upgrade"
	)

	var recovery = Controller.new()
	recovery.configure(Controller.LOW)
	for index in 90:
		recovery.update(53.0)
	check.call(
		recovery.level == Controller.MEDIUM and recovery.cooldown == 300,
		"high average steps Low to Medium and starts the 300-frame cooldown"
	)
	for index in 300:
		recovery.update(53.0)
	check.call(recovery.cooldown == 0, "raise cooldown expires after exactly 300 calls")
	for index in 89:
		recovery.update(53.0)
	check.call(recovery.level == Controller.MEDIUM, "upgrade waits for another full window")
	recovery.update(53.0)
	check.call(
		recovery.level == Controller.HIGH and recovery.cooldown == 300,
		"continued high FPS steps Medium to High once per sample window"
	)

	var disabled = Controller.new(false)
	for index in 180:
		disabled.update(0.0)
	check.call(
		(
			disabled.level == Controller.HIGH
			and disabled.samples.is_empty()
			and disabled.cooldown == 0
		),
		"disabled adaptive governor leaves quality and sampling state unchanged"
	)

	var tree := Engine.get_main_loop() as SceneTree
	var runtime: Variant = tree.root.get_node_or_null("AdaptiveQuality")
	check.call(runtime != null, "adaptive-quality runtime autoload is available")
	if runtime != null:
		var expected_level: String = Controller.LOW if runtime.touch_mode else Controller.HIGH
		check.call(
			runtime.quality_level == expected_level,
			"runtime chooses Python low-touch or high-desktop startup quality"
		)
