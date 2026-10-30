extends RefCounted
## Layer 9bv20: replays `mobile_platform_source_oracle.py`'s fixture through
## `scripts/platform/mobile_platform.gd`. The oracle runs the REAL
## `mobile/platform_utils.py` functions under a pygame shim, so every scale,
## offset, logical point, safe area and popup position below comes from the
## Pygame source rather than from the port's own assumptions.

const Platform = preload("res://scripts/platform/mobile_platform.gd")
const FIXTURE := "res://tests/fixtures/mobile_platform_source.json"

const EPSILON := 0.0000015


static func _close(a: float, b: float) -> bool:
	return absf(a - b) <= EPSILON


static func _vector(values: Array) -> Vector2:
	return Vector2(float(values[0]), float(values[1]))


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Mobile platform fixture parses")
	if not (data is Dictionary):
		return
	_constant_checks(data, check)
	_scale_checks(data, check)
	_conversion_checks(data, check)
	_pointer_checks(data, check)
	_safe_area_checks(data, check)
	_popup_checks(data, check)
	_mode_checks(data, check)


func _constant_checks(data: Dictionary, check: Callable) -> void:
	var logical: Array = data["logical_size"]
	check.call(
		Platform.LOGICAL_WIDTH == int(logical[0]) and Platform.LOGICAL_HEIGHT == int(logical[1]),
		"logical surface stays 1280x720"
	)
	var modes_match: bool = Platform.DISPLAY_MODES.size() == data["display_modes"].size()
	for index in range(mini(Platform.DISPLAY_MODES.size(), data["display_modes"].size())):
		if Platform.DISPLAY_MODES[index] != String(data["display_modes"][index]):
			modes_match = false
	check.call(modes_match, "display mode names keep the source order")
	check.call(Platform.DEFAULT_MODE == String(data["default_mode"]), "default display mode matches")
	check.call(
		Platform.SAFE_MARGIN == int(data["safe_margin"]), "safe-area margin matches the source"
	)
	check.call(
		Platform.ZONA_POPUP_Y == int(data["zona_popup_y"])
		and Platform.ZONA_BAWAH_H == int(data["zona_bawah_h"]),
		"right-panel popup lanes match panel_pos_bawah"
	)
	check.call(
		Platform.MODE_FILE == "display_mode.txt" and Platform.MODE_ENV == "MYSTIC_DISPLAY_MODE",
		"the persisted display mode keeps the source file name and env override"
	)


func _scale_checks(data: Dictionary, check: Callable) -> void:
	for row in data["refresh"]:
		var window: Array = row["window"]
		var metrics := Platform.window_scale_offset(Vector2i(int(window[0]), int(window[1])))
		check.call(
			_close(float(metrics["scale"]), float(row["scale"])),
			"scale for a %dx%d window matches" % [int(window[0]), int(window[1])]
		)
		check.call(
			_close(metrics["offset"].x, float(row["offset"][0]))
			and _close(metrics["offset"].y, float(row["offset"][1])),
			"letterbox offset for a %dx%d window matches" % [int(window[0]), int(window[1])]
		)


func _conversion_checks(data: Dictionary, check: Callable) -> void:
	for row in data["conversions"]:
		var window: Array = row["window"]
		var window_size := Vector2i(int(window[0]), int(window[1]))
		var metrics := Platform.window_scale_offset(window_size)
		for point in row["window_points"]:
			var got := Platform.window_to_logical(
				_vector(point["window"]), float(metrics["scale"]), metrics["offset"]
			)
			var want := _vector(point["logical"])
			check.call(
				_close(got.x, want.x) and _close(got.y, want.y),
				"window point %s maps to %s on %dx%d"
				% [point["window"], point["logical"], int(window[0]), int(window[1])]
			)
		for finger in row["finger_points"]:
			var got_finger := Platform.finger_to_logical(
				_vector(finger["finger"]), window_size, float(metrics["scale"]), metrics["offset"]
			)
			var want_finger := _vector(finger["logical"])
			check.call(
				_close(got_finger.x, want_finger.x) and _close(got_finger.y, want_finger.y),
				"finger %s maps to %s on %dx%d"
				% [finger["finger"], finger["logical"], int(window[0]), int(window[1])]
			)


func _pointer_checks(data: Dictionary, check: Callable) -> void:
	for row in data["pointer"]:
		var mode := String(row["mode"])
		for point in row["points"]:
			var got := Platform.pointer_to_logical(
				mode, _vector(point["input"]), 1.5, Vector2(258.0, 0.0)
			)
			var want := _vector(point["logical"])
			check.call(
				_close(got.x, want.x) and _close(got.y, want.y),
				"pointer in %s mode maps %s to %s" % [mode, point["input"], point["logical"]]
			)


func _safe_area_checks(data: Dictionary, check: Callable) -> void:
	for row in data["safe_area"]:
		var want: Array = row["rect"]
		var got := Platform.safe_area(bool(row["touch_mode"]))
		check.call(
			got == Rect2i(int(want[0]), int(want[1]), int(want[2]), int(want[3])),
			"safe area for touch_mode=%s matches" % str(row["touch_mode"])
		)


func _popup_checks(data: Dictionary, check: Callable) -> void:
	var panel_values: Array = data["panel"]
	var panel := Rect2i(
		int(panel_values[0]), int(panel_values[1]), int(panel_values[2]), int(panel_values[3])
	)
	for row in data["popups"]:
		var width := int(row["width"])
		var height := int(row["height"])
		var top := int(row["top"])
		var popup: Variant = Platform.panel_popup_pos(panel, width, height, top)
		var bottom: Variant = Platform.panel_pos_bawah(panel, width, height)
		if row["popup_pos"] == null:
			check.call(popup == null, "a %d px popup does not fit the panel" % width)
		else:
			var want_popup := _vector(row["popup_pos"])
			check.call(
				popup is Vector2i
				and float(popup.x) == want_popup.x
				and float(popup.y) == want_popup.y,
				"panel popup %dx%d lands at %s" % [width, height, row["popup_pos"]]
			)
		if row["bottom_pos"] == null:
			check.call(bottom == null, "a %d px bottom popup does not fit the panel" % width)
		else:
			var want_bottom := _vector(row["bottom_pos"])
			check.call(
				bottom is Vector2i
				and float(bottom.x) == want_bottom.x
				and float(bottom.y) == want_bottom.y,
				"bottom lane popup %dx%d lands at %s" % [width, height, row["bottom_pos"]]
			)
	check.call(
		Platform.panel_popup_pos(Rect2i(), 260, 165) == null
		and Platform.panel_pos_bawah(Rect2i(), 260, 165) == null,
		"without a right panel both popup routes fall back"
	)


func _mode_checks(data: Dictionary, check: Callable) -> void:
	for row in data["display_mode"]:
		var env_mode := String(row["env"]) if row["env"] != null else ""
		var file_text := String(row["file"]) if row["file"] != null else ""
		check.call(
			Platform.resolve_display_mode(env_mode, file_text) == String(row["resolved"]),
			"display mode env=%s file=%s resolves to %s"
			% [str(row["env"]), str(row["file"]), row["resolved"]]
		)
	for row in data["save_mode"]:
		# `save_display_mode` writes the same file the source writes; an
		# invalid name still saves, and the loader then falls back.
		check.call(
			Platform.resolve_display_mode("", String(row["save"])) == String(row["reloaded"]),
			"a stored '%s' reloads as %s" % [row["save"], row["reloaded"]]
		)
	check.call(
		Platform.mode_path().ends_with("display_mode.txt"),
		"the display mode file lives in the writable dir"
	)
	var path := Platform.mode_path()
	var had_file := FileAccess.file_exists(path)
	var previous := FileAccess.get_file_as_string(path) if had_file else ""
	check.call(Platform.save_display_mode("native"), "saving the display mode writes the file")
	if not Platform.DISPLAY_MODES.has(OS.get_environment(Platform.MODE_ENV).strip_edges()):
		check.call(
			Platform.load_display_mode() == "native", "the saved display mode loads back"
		)
	if had_file:
		Platform.save_display_mode(previous)
	elif FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)
