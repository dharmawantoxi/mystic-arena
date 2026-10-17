extends RefCounted
## Layer 9as: replays the `mobile/sidepanel.py` source oracle fixture
## through the native layout. `side_panel_source_oracle.py` runs the REAL
## `SidePanel` under a recording pygame shim (7 px glyphs), so every box,
## string, colour, button box and hit decision below comes from the source.

const Layout = preload("res://scripts/ui/side_panel_layout.gd")
const SidePanel = preload("res://scripts/ui/side_panel.gd")
const FIXTURE := "res://tests/fixtures/side_panel_source.json"


static func _measure(text: String, _size: int) -> int:
	return 7 * text.length()


static func _rect(values: Array) -> Rect2i:
	return Rect2i(int(values[0]), int(values[1]), int(values[2]), int(values[3]))


static func _color(values: Array) -> Color:
	return Color8(int(values[0]), int(values[1]), int(values[2]))


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Side panel fixture parses")
	if not (data is Dictionary):
		return
	_constant_checks(data, check)
	var panel := Rect2i(1280, 0, int(data["panel_width"]), 720)
	var snapshots: Dictionary = data["snapshots"]
	for name in snapshots:
		_snapshot_checks(String(name), snapshots[name], panel, check)
	_hit_checks(data, panel, check)
	_control_checks(panel, check)


func _constant_checks(data: Dictionary, check: Callable) -> void:
	check.call(Layout.REFRESH_MS == int(data["refresh_ms"]), "refresh cadence is JEDA_SEGAR_MS")
	check.call(Layout.MIN_TAP == int(data["min_tap"]), "MIN_TAP matches the source")
	check.call(
		Layout.MIN_PANEL_WIDTH == int(data["min_panel_width"]),
		"panel needs the source minimum leftover width"
	)
	var colors: Dictionary = data["colors"]
	check.call(Layout.FG == _color(colors["FG"]), "FG colour matches")
	check.call(Layout.DIM == _color(colors["DIM"]), "DIM colour matches")
	check.call(Layout.EMAS == _color(colors["EMAS"]), "EMAS colour matches")
	check.call(Layout.OK == _color(colors["OK"]), "OK colour matches")
	check.call(Layout.BAHAYA == _color(colors["BAHAYA"]), "BAHAYA colour matches")
	check.call(Layout.BIRU == _color(colors["BIRU"]), "BIRU colour matches")
	check.call(Layout.UNGU == _color(colors["UNGU"]), "UNGU colour matches")
	var widths: Dictionary = data["display_width"]
	for key in widths:
		check.call(
			Layout.display_width(float(String(key))) == int(widths[key]),
			"display width for ratio %s matches create_display" % key
		)
	check.call(
		Layout.panel_rect(1280) == Rect2i() and bool(data["inactive_without_panel"]),
		"16:9 leaves no panel"
	)
	check.call(Layout.panel_rect(1280 + 119) == Rect2i(), "119 px leftover is too narrow")
	check.call(
		Layout.panel_rect(1280 + 344) == Rect2i(1280, 0, 344, 720),
		"344 px leftover becomes the right panel"
	)
	check.call(
		Layout.TACTICAL_KEYS == Array(data["tactical_keys"]), "tactical keys keep the source order"
	)
	var menu := Layout.build({"state": "menu"}, Rect2i(1280, 0, 344, 720), _measure)
	var all_hidden := true
	for key in menu["buttons"]:
		if bool(menu["buttons"][key]["visible"]):
			all_hidden = false
	check.call(
		all_hidden and bool(data["menu_hides_buttons"]), "outside gameplay every button hides"
	)


func _snapshot_checks(name: String, expected: Dictionary, panel: Rect2i, check: Callable) -> void:
	var built := Layout.build(expected["input"], panel, _measure)
	var tag := "[%s] " % name
	check.call(
		int(built["y_after_status"]) == int(expected["y_after_status"]),
		tag + "status box height matches"
	)
	check.call(
		int(built["y_after_heroes"]) == int(expected["y_after_heroes"]),
		tag + "hero box height matches"
	)
	check.call(
		int(built["y_after_tactical"]) == int(expected["y_after_tactical"]),
		tag + "tactical box height matches"
	)
	var texts: Array = expected["texts"]
	check.call(
		built["texts"].size() == texts.size(),
		tag + "text count matches (%d vs %d)" % [built["texts"].size(), texts.size()]
	)
	for index in range(mini(texts.size(), built["texts"].size())):
		var want: Dictionary = texts[index]
		var got: Dictionary = built["texts"][index]
		var same := (
			String(got["text"]) == String(want["text"])
			and got["color"] == _color(want["color"])
			and got["pos"] == Vector2i(int(want["pos"][0]), int(want["pos"][1]))
		)
		check.call(same, tag + "text %d '%s' matches" % [index, want["text"]])
	var rects: Array = expected["rects"]
	check.call(built["rects"].size() == rects.size(), tag + "rect count matches")
	for index in range(mini(rects.size(), built["rects"].size())):
		var want: Dictionary = rects[index]
		var got: Dictionary = built["rects"][index]
		var same := (
			got["rect"] == _rect(want["rect"])
			and got["color"] == _color(want["color"])
			and int(got["width"]) == int(want["width"])
			and int(got["radius"]) == int(want["radius"])
		)
		check.call(same, tag + "rect %d matches" % index)
	var circles: Array = expected["circles"]
	check.call(built["circles"].size() == circles.size(), tag + "skill dot count matches")
	for index in range(mini(circles.size(), built["circles"].size())):
		var want: Dictionary = circles[index]
		var got: Dictionary = built["circles"][index]
		var same := (
			got["center"] == Vector2i(int(want["center"][0]), int(want["center"][1]))
			and got["color"] == _color(want["color"])
			and int(got["radius"]) == int(want["radius"])
		)
		check.call(same, tag + "skill dot %d matches" % index)
	var buttons: Dictionary = expected["buttons"]
	for key in buttons:
		var want: Dictionary = buttons[key]
		var got: Dictionary = built["buttons"].get(key, {})
		check.call(not got.is_empty(), tag + "button %s exists" % key)
		if got.is_empty():
			continue
		check.call(
			bool(got["visible"]) == bool(want["visible"]),
			tag + "button %s visibility matches" % key
		)
		check.call(
			got["hit_rect"] == _rect(want["hit_rect"]), tag + "button %s hit box matches" % key
		)
		if bool(want["visible"]):
			check.call(got["rect"] == _rect(want["rect"]), tag + "button %s rect matches" % key)


func _hit_checks(data: Dictionary, panel: Rect2i, check: Callable) -> void:
	var five: Dictionary = data["snapshots"]["five"]
	var built := Layout.build(five["input"], panel, _measure)
	for case in data["hits"]:
		var pos := Vector2i(int(case["pos"][0]), int(case["pos"][1]))
		var popup := String(case["case"]).ends_with("_popup")
		var expected := "" if case["action"] == null else String(case["action"])
		check.call(
			Layout.hit_test(built["buttons"], pos, popup) == expected,
			"hit test %s -> '%s'" % [case["case"], expected]
		)
		check.call(
			Layout.blocks(panel, pos) == bool(case["blocks"]),
			"blocks() for %s matches" % case["case"]
		)


func _control_checks(panel: Rect2i, check: Callable) -> void:
	var control := SidePanel.new()
	control.configure(1280)
	check.call(not control.is_active() and not control.visible, "16:9 control stays hidden")
	control.configure(1280 + panel.size.x)
	check.call(
		control.is_active() and control.panel == panel and control.size == Vector2(panel.size),
		"wide control takes the leftover width"
	)
	check.call(
		control.blocks(Vector2(1300, 10)) and not control.blocks(Vector2(640, 360)),
		"control blocks panel points only"
	)
	var snapshot := {"state": "playing", "gold": 5, "heroes": []}
	control.update_snapshot(snapshot, 1000)
	check.call(not control.layout.is_empty(), "first snapshot builds the layout")
	var first_at: int = control._built_at
	control.update_snapshot(snapshot, 1100)
	check.call(control._built_at == first_at, "a snapshot 100 ms later keeps the cached layout")
	control.update_snapshot(snapshot, 1250)
	check.call(control._built_at == 1250, "250 ms later the layout refreshes")
	var changed := {"state": "defeat", "gold": 5, "heroes": []}
	control.update_snapshot(changed, 1260)
	check.call(control._built_at == 1260, "a state change refreshes immediately")
	check.call(control._press_at(Vector2i(1323, 43)) == "pause", "panel press hits PAUSE")
	control.update_snapshot({"state": "menu"}, 1300)
	check.call(control.layout.is_empty(), "leaving gameplay clears the panel")
	control.free()
