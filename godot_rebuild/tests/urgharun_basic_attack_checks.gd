extends RefCounted
## Layer 9bq8: replays the basic-attack fixture of `urgharun_basic_attack_source_oracle.py` through
## `urgharun_skill_fx_layout.gd::basic_attack_ops` and `urgharun_attack_clock.gd`. The oracle runs
## the REAL `_draw_basic_attack_fx` and `_update_urg_attack_anim` from `bosses/level40.py` under
## the recording pygame shim, so every op and every clock step comes from the source.
## `painter_scene_checks.gd` proves the live scene paints the layer once the swing arms.

const Layout = preload("res://scripts/ui/urgharun_skill_fx_layout.gd")
const Clock = preload("res://scripts/ui/urgharun_attack_clock.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/urgharun_basic_attack_source.json"
const COMPARED_KEYS := {
	"circle": ["center", "radius", "width", "color", "mult"],
	"rect": ["rect", "width", "radius", "color", "mult"],
	"line": ["a", "b", "width", "color", "mult"],
}
const ANCHOR := 640
const ANCHOR_Y := 360


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
	if str(actual.get("kind", "")) != str(expected.get("kind", "")):
		return false
	var keys: Array = COMPARED_KEYS.get(str(expected.get("kind", "")), [])
	for key_name in keys:
		if expected.has(key_name) != actual.has(key_name):
			return false
		if expected.has(key_name) and not _value_equal(actual[key_name], expected[key_name]):
			return false
	return true


static func _first_mismatch(actual: Array, expected: Array) -> int:
	for index in range(mini(actual.size(), expected.size())):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1 if actual.size() == expected.size() else mini(actual.size(), expected.size())


static func _report(label: String, actual: Array, expected: Array) -> String:
	var index := _first_mismatch(actual, expected)
	if index == -1:
		return "%s matches the source ops" % label
	var mine: Variant = actual[index] if index < actual.size() else {}
	var theirs: Variant = expected[index] if index < expected.size() else {}
	return (
		"%s differs at op %d/%d: %s vs source %s"
		% [label, index, expected.size(), str(mine), str(theirs)]
	)


static func _frame(frames: Array, label: String) -> Dictionary:
	for frame in frames:
		if String(frame["label"]) == label:
			return frame
	return {}


static func _run(runs: Array, label: String) -> Dictionary:
	for run in runs:
		if String(run["label"]) == label:
			return run
	return {}


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Urgharun basic attack fixture parses")
	if not (data is Dictionary):
		return
	var total := 0
	for frame in data["fx_frames"]:
		total += frame["ops"].size()
	var steps := 0
	for run_entry in data["clock_runs"]:
		steps += run_entry["steps"].size()
	check.call(
		(
			total == 1132
			and int(data["fx_frames"].size()) == 11
			and int(data["clock_runs"].size()) == 5
			and steps == 52
			and int(data["attack_duration"]) == 28
		),
		(
			"Urgharun basic attack oracle pins 11 frames / 1132 ops and 5 clock runs (got %d/%d)"
			% [total, steps]
		)
	)
	_check_palette(check, data)
	_check_frames(check, data)
	_check_phases(check, data)
	_check_clock(check, data)
	_check_view_wiring(check, data)


func _check_palette(check: Callable, data: Dictionary) -> void:
	var palette: Dictionary = data["palette"]
	var pairs := [
		["fury_darkest", Layout.FURY_DARKEST],
		["fury_dark", Layout.FURY_DARK],
		["fury_mid", Layout.FURY_MID],
		["fury_light", Layout.FURY_LIGHT],
		["fury_hot", Layout.FURY_HOT],
		["fury_shine", Layout.FURY_SHINE],
	]
	for pair in pairs:
		check.call(
			_value_equal(pair[1], palette[pair[0]]),
			"The %s palette still matches the source" % pair[0]
		)
	check.call(
		_value_equal(Layout.WHITE, palette["white"]),
		"The basic-attack tips use the source's raw white"
	)
	check.call(Layout.ATTACK_DURATION == int(data["attack_duration"]), "The swing lasts 28 frames")


func _check_frames(check: Callable, data: Dictionary) -> void:
	for frame in data["fx_frames"]:
		var target: Array = []
		if frame["target"] != null:
			target = [int(frame["target"][0]), int(frame["target"][1])]
		var actual := Layout.basic_attack_ops(
			ANCHOR,
			ANCHOR_Y,
			int(frame["direction"]),
			float(frame["progress"]),
			target,
			float(frame["pulse"])
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Basic attack %s" % frame["label"], actual, frame["ops"])
		)


func _check_phases(check: Callable, data: Dictionary) -> void:
	# The three source phases: claws glow, five nested arcs, then the impact burst.
	var counts: Array = []
	for frame in data["fx_frames"]:
		counts.append(frame["ops"].size())
	check.call(
		(
			counts[0] == 6
			and counts[2] == 10
			and counts[3] == 246
			and counts[6] == 31
			and counts[9] == 31
		),
		"The wind-up grows its claw rings, the slash carries 246 ops and the impact 31"
	)
	var windup: Dictionary = _frame(data["fx_frames"], "fx_windup_start")
	check.call(
		int(windup["ops"][0]["color"][3]) == 0,
		"The first wind-up frame is fully transparent, exactly like the source"
	)
	# The tip of each arc sits right after that arc's 40 line ops, so op 40 is the first tip ring.
	var slash: Dictionary = _frame(data["fx_frames"], "fx_slash_mid")
	var tip_ring: Dictionary = slash["ops"][40]
	check.call(
		(
			str(tip_ring["kind"]) == "circle"
			and int(tip_ring["radius"]) == 4
			and int(tip_ring["color"][3]) == 0
			and int(slash["ops"][41]["color"][3]) == 60
		),
		"The slash tip starts with its invisible outermost ring"
	)
	# The far target records the 80 px melee clamp; `fx_no_target` the facing fallback.
	var far: Dictionary = _frame(data["fx_frames"], "fx_far_target")
	check.call(
		(
			_value_equal(far["target"], [1100, 600])
			and far["ops"].size() == 246
			and _clamped_target(far) == [693, 387]
		),
		"A target past melee range is pulled back to 60 px on the same bearing"
	)
	var no_target: Dictionary = _frame(data["fx_frames"], "fx_no_target")
	check.call(
		no_target["target"] == null and int(no_target["ops"][0]["center"][0]) == 700,
		"Without a target the impact lands at `x + facing * 60`"
	)


## Rebuild the clamped target the source would use, straight from the recorded frame data.
static func _clamped_target(frame: Dictionary) -> Array:
	var target: Array = frame["target"]
	var dx := int(target[0]) - ANCHOR
	var dy := int(target[1]) - ANCHOR_Y
	var distance := sqrt(float(dx * dx + dy * dy))
	if distance > 80.0:
		return [
			ANCHOR + int(float(dx) / distance * 60.0), ANCHOR_Y + int(float(dy) / distance * 60.0)
		]
	return [int(target[0]), int(target[1])]


func _check_clock(check: Callable, data: Dictionary) -> void:
	for entry in data["clock_runs"]:
		var clock := Clock.new()
		var actual: Array = []
		for step in entry["steps"]:
			clock.advance(int(step["timer"]), int(entry["cooldown"]))
			(
				actual
				. append(
					{
						"timer": int(step["timer"]),
						"active": clock.active,
						"frame": clock.frame,
						"previous_timer": clock.previous_timer,
						"progress": clock.progress,
					}
				)
			)
		check.call(
			_steps_equal(actual, entry["steps"]),
			"The %s clock run matches the source frame by frame" % entry["label"]
		)
	var cycle: Dictionary = _run(data["clock_runs"], "clock_attack_cycle")
	check.call(
		(
			bool(cycle["steps"][0]["active"])
			and int(cycle["steps"][0]["frame"]) == 1
			and bool(cycle["steps"][-1]["active"])
		),
		"The swing arms on the tick right after the attack resets the timer"
	)
	var slowed: Dictionary = _run(data["clock_runs"], "clock_slowed_early_arm")
	check.call(
		bool(slowed["steps"][0]["active"]),
		"A slowed boss arms early because the clock reads the raw attack cooldown"
	)
	var full: Dictionary = _run(data["clock_runs"], "clock_full_window")
	# The 28th advance disarms in the same step (`frame` reaches 28 -> active = false), so the
	# first step that drops out of the swing is index 27, carrying frame 0. The run then re-arms
	# on the next top-of-window timer, which is the source's own re-trigger behaviour.
	var disarm := -1
	for index in range(1, full["steps"].size()):
		if bool(full["steps"][index - 1]["active"]) and not bool(full["steps"][index]["active"]):
			disarm = index
			break
	check.call(
		(
			disarm == 27
			and int(full["steps"][26]["frame"]) == 27
			and int(full["steps"][27]["frame"]) == 0
			and bool(full["steps"][-1]["active"])
		),
		"The swing disarms after exactly 28 frames"
	)
	check.call(
		absf(float(full["steps"][13]["progress"]) - 0.5) < 1e-6,
		"The fourteenth swing frame reports half progress"
	)


static func _steps_equal(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		var mine: Dictionary = actual[index]
		var theirs: Dictionary = expected[index]
		if int(mine["timer"]) != int(theirs["timer"]):
			return false
		if bool(mine["active"]) != bool(theirs["active"]):
			return false
		if int(mine["frame"]) != int(theirs["frame"]):
			return false
		if int(mine["previous_timer"]) != int(theirs["previous_timer"]):
			return false
		if absf(float(mine["progress"]) - float(theirs["progress"])) > 1e-6:
			return false
	return true


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var view := PrototypeView.new()
	var boss := BossState.new()
	boss.boss_type = "urgharun"
	boss.position = Vector2(ANCHOR, ANCHOR_Y)
	boss.attack_cooldown = 38
	boss.timer = 38
	check.call(view.urgharun_basic_attack_draw_ops(boss).is_empty(), "An idle swing paints nothing")
	view.urgharun_attack_clock_step(boss)
	var clock: Clock = view.urgharun_attack_clock(boss)
	check.call(
		clock.active and clock.frame == 1,
		"The view advances the source swing clock once per painted frame"
	)
	# Park the clock on the recorded impact frame so the wiring comparison is exact.
	var no_target: Dictionary = _frame(data["fx_frames"], "fx_no_target")
	clock.progress = float(no_target["progress"])
	boss.direction = int(no_target["direction"])
	boss.pulse = float(no_target["pulse"])
	check.call(
		_first_mismatch(view.urgharun_basic_attack_draw_ops(boss), no_target["ops"]) == -1,
		_report("Basic attack wiring", view.urgharun_basic_attack_draw_ops(boss), no_target["ops"])
	)
	boss.active_skill = "q"
	check.call(
		view.urgharun_basic_attack_draw_ops(boss).is_empty(),
		"A skill cast suppresses the source basic-attack FX"
	)
	boss.active_skill = ""
	check.call(
		not view.urgharun_basic_attack_draw_ops(boss).is_empty(),
		"The basic-attack FX returns once the cast ends"
	)
	boss.boss_type = "yhoranth"
	check.call(
		view.urgharun_basic_attack_draw_ops(boss).is_empty(),
		"Other bosses own no urgharun basic-attack FX"
	)
	boss.boss_type = "urgharun"
	clock.active = false
	check.call(
		view.urgharun_basic_attack_draw_ops(boss).is_empty(), "A disarmed swing paints nothing"
	)
	view.free()
