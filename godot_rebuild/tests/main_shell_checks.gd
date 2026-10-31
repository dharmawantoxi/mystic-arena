extends RefCounted
## Native checks for the `main.py` shell port (layer 9cn).

const FrameErrorLog = preload("res://scripts/app/frame_error_log.gd")
const StartupReport = preload("res://scripts/app/startup_report.gd")
const FIXTURE := "res://tests/fixtures/main_source.json"
const APP_SCRIPT := "res://app/app.gd"
const TEST_DIR := "user://main_shell_checks"
const TEST_LOG := "user://main_shell_checks/crash_log.txt"


func run(check: Callable) -> void:
	var fixture: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "main.py source fixture parses")
	if not fixture is Dictionary:
		return
	_error_log(check, fixture)
	_startup_banner(check, fixture)
	_project_contract(check, fixture)
	_shell_wiring(check, fixture)


func _error_log(check: Callable, fixture: Dictionary) -> void:
	var constants: Dictionary = fixture.constants
	var log := FrameErrorLog.new(TEST_LOG)
	_check_cleanup()
	check.call(
		(
			FrameErrorLog.text("update", "boom") == "[FRAME ERROR:update]\nboom"
			and FrameErrorLog.section("2026-01-02 03:04:05", "draw", "x")
			== "\n===== 2026-01-02 03:04:05 =====\n[FRAME ERROR:draw]\nx"
			and FrameErrorLog.timestamp(0) == "1970-01-01 00:00:00"
		),
		"frame error header and timestamp match main.py::_log_frame_error"
	)
	check.call(
		FrameErrorLog.COOLDOWN_SECONDS == float(constants.frame_error_cooldown),
		"frame error cooldown mirrors _FRAME_ERR_COOLDOWN"
	)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(TEST_DIR))
	# Source reads `_FRAME_ERR_LAST.get(kind, 0.0)`, so an error at t=0.0 is
	# swallowed by the very first comparison (0.0 - 0.0 < 2.0). Keep that quirk.
	var early := log.record("update", "first", 0.0, "2026-01-02 03:04:05", TEST_DIR)
	var second := log.record("update", "second", 2.5, "2026-01-02 03:04:06", TEST_DIR)
	var repeat := log.record("update", "third", 3.0, "2026-01-02 03:04:07", TEST_DIR)
	var other_kind := log.record("draw", "other", 3.0, "2026-01-02 03:04:08", TEST_DIR)
	var contents := log.read_log()
	check.call(
		not early and second and not repeat and other_kind,
		"frame error log throttles one write per kind per cooldown window"
	)
	check.call(
		(
			contents.count("===== 2026-01-02") == 2
			and contents.contains("===== 2026-01-02 03:04:06 =====\n[FRAME ERROR:update]\nsecond")
			and contents.contains("===== 2026-01-02 03:04:08 =====\n[FRAME ERROR:draw]\nother")
			and not contents.contains("third")
		),
		"frame error log appends timestamped sections and drops throttled ones"
	)
	log.reset()
	var after_reset := log.record("update", "fourth", 2.6, "2026-01-02 03:04:09", TEST_DIR)
	check.call(after_reset, "frame error log reset clears the cooldown table")
	_check_cleanup()


func _startup_banner(check: Callable, fixture: Dictionary) -> void:
	var banner: Array = fixture.constants.banner
	check.call(
		banner.size() == 8
		and String(banner[0]).length() == 60
		and String(banner[0]) == StartupReport.RULE
		and String(banner[1]) == StartupReport.TITLE_LINE,
		"startup banner keeps the 60-character rule and build title"
	)
	var values := ["SM-A125F", "13", "33", "/data/user/0/app/files", "TOUCH", "LOW"]
	var expected := PackedStringArray()
	var cursor := 0
	for line in banner:
		var template := String(line)
		var placeholders := template.count("%s")
		if placeholders == 0:
			expected.append(template)
			continue
		expected.append(template % values.slice(cursor, cursor + placeholders))
		cursor += placeholders
	var actual := StartupReport.lines(
		"SM-A125F", "13", "33", "/data/user/0/app/files", true, "LOW"
	)
	check.call(
		actual == expected,
		"startup report reproduces every source banner line: %s" % str(actual)
	)
	check.call(
		(
			StartupReport.input_mode(true) == "TOUCH"
			and StartupReport.input_mode(false) == "MOUSE/KEYBOARD"
			and StartupReport.lines("d", "r", "a", "s", false, "HIGH")[5]
			== "  input  : MOUSE/KEYBOARD"
		),
		"startup report picks the input mode like platform_utils.TOUCH_MODE"
	)
	var live := StartupReport.collect(Engine.get_main_loop() as SceneTree)
	check.call(
		live.size() == 8 and live[0] == StartupReport.RULE and live[7] == StartupReport.RULE,
		"live startup report is the same eight-line block"
	)


func _project_contract(check: Callable, fixture: Dictionary) -> void:
	var constants: Dictionary = fixture.constants
	var catchup := int(constants.max_catchup)
	check.call(
		(
			int(ProjectSettings.get_setting("physics/common/max_physics_steps_per_frame", 8))
			== catchup
			and int(Engine.max_physics_steps_per_frame) == catchup
			and int(ProjectSettings.get_setting("physics/common/physics_ticks_per_second", 0)) == 60
			and is_equal_approx(1000.0 / 60.0, float(constants.fixed_dt_ms))
		),
		"fixed timestep and MAX_CATCHUP mirror main.py in project.godot"
	)
	check.call(
		int(ProjectSettings.get_setting("audio/driver/mix_rate", 0))
		== int(constants.mixer_pre_init.frequency),
		"mixer rate mirrors pygame.mixer.pre_init(frequency=44100)"
	)
	var states: Array = constants.states
	check.call(
		states == ["splash", "menu", "game", "pause"],
		"state machine keeps the source splash/menu/game/pause order"
	)


func _shell_wiring(check: Callable, fixture: Dictionary) -> void:
	var app := FileAccess.get_file_as_string(APP_SCRIPT)
	check.call(
		(
			app.contains("StartupReport.collect(get_tree())")
			and app.contains("FrameErrorLog.new()")
			and app.contains("_frame_errors.record(")
			and app.contains("_install_screen(SPLASH)")
			and app.contains("NOTIFICATION_APPLICATION_PAUSED")
		),
		"App shell prints the banner, logs boot failures and owns the splash/pause states"
	)
	var keys: Dictionary = fixture.constants.keys
	var missing: Array = []
	for key in keys:
		if String(keys[key]).is_empty():
			missing.append(key)
	check.call(
		keys.size() == 6 and missing.is_empty(),
		"keyboard map keeps all six source bindings: %s" % str(missing)
	)
	check.call(
		(
			String(keys.get("K_F7", "")) == "sylara_review_mod.toggle"
			and String(keys.get("K_F8", "")) == "debug.toggle"
			and String(keys.get("K_ESCAPE", "")) == "state-transition"
		),
		"review/debug toggles stay dev-only and ESC still requests pause"
	)
	var deviations: Array = fixture.deviations
	check.call(
		(
			deviations.has("mobile.debug")
			and deviations.has("mobile.bootcheck")
			and deviations.has("mobile.kaizen_review")
			and deviations.size() == 7
		),
		"dev-only screens and review sheets stay documented deviations"
	)


func _check_cleanup() -> void:
	for path in [TEST_LOG, TEST_LOG + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
