extends RefCounted
## Layer 9as: replays the `mobile/sidepanel.py` source oracle fixture
## through the native layout. `side_panel_source_oracle.py` runs the REAL
## `SidePanel` under a recording pygame shim (7 px glyphs), so every box,
## string, colour, button box and hit decision below comes from the source.

const Layout = preload("res://scripts/ui/side_panel_layout.gd")
const SidePanel = preload("res://scripts/ui/side_panel.gd")
const SourceFonts = preload("res://scripts/ui/source_fonts.gd")
const FIXTURE := "res://tests/fixtures/side_panel_source.json"


static func _measure(text: String, _size: int) -> int:
	return 7 * text.length()


static func _measure_wide(text: String, _size: int) -> int:
	# A second width for the `body_bold` probe; real metrics arrive through
	# `SidePanel._measure_bold`.
	return 12 * text.length()


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
	_style_checks(data, panel, check)
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
		# `style` is what the source passed to `get_font(size, style)`; the
		# rebuild must pick the same face (body -> Barlow-Regular,
		# body_bold -> Barlow-Bold) for the same string.
		var same: bool = (
			String(got["text"]) == String(want["text"])
			and got["color"] == _color(want["color"])
			and got["pos"] == Vector2i(int(want["pos"][0]), int(want["pos"][1]))
			and int(got["size"]) == int(want["size"])
			and String(got["style"]) == String(want["style"])
			and bool(got["bold"]) == (String(want["style"]) == Layout.STYLE_BOLD)
		)
		check.call(
			same,
			tag
			+ "text %d '%s' (%s %d) matches"
			% [index, want["text"], want["style"], int(want["size"])]
		)
	var rects: Array = expected["rects"]
	check.call(built["rects"].size() == rects.size(), tag + "rect count matches")
	for index in range(mini(rects.size(), built["rects"].size())):
		var want: Dictionary = rects[index]
		var got: Dictionary = built["rects"][index]
		var same: bool = (
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
		var same: bool = (
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
		# Hidden tactical buttons keep whatever stale rect the previous frame
		# left in the source dict; only drawn buttons have a meaningful box.
		if bool(want["visible"]):
			check.call(
				got["hit_rect"] == _rect(want["hit_rect"]), tag + "button %s hit box matches" % key
			)
			check.call(got["rect"] == _rect(want["rect"]), tag + "button %s rect matches" % key)


## The source renders `body_bold` strings with Barlow-Bold and measures them
## with the same font, so a right-aligned or centred bold string sits on a
## different pixel than the regular face would put it. These checks pin the
## style->face lookup and the fact that the layout measures bold strings with
## the bold width (the earlier port measured everything with one face).
func _style_checks(data: Dictionary, panel: Rect2i, check: Callable) -> void:
	check.call(
		SourceFonts.for_style(Layout.STYLE_BOLD) == SourceFonts.BOLD
		and SourceFonts.for_style(Layout.STYLE_BODY) == SourceFonts.REGULAR,
		"panel styles resolve to the source body/body_bold faces"
	)
	check.call(
		SourceFonts.file_for_style(Layout.STYLE_BOLD) == "Barlow-Bold.ttf",
		"body_bold is Barlow-Bold, not SemiBold"
	)
	var styles_seen: Dictionary = {}
	for name in data["snapshots"]:
		for entry in data["snapshots"][name]["texts"]:
			styles_seen[String(entry["style"])] = true
	var known := true
	for style in styles_seen:
		if not SourceFonts.has_style(String(style)):
			known = false
	check.call(
		known and styles_seen.has(Layout.STYLE_BOLD) and styles_seen.has(Layout.STYLE_BODY),
		"the oracle records only source styles, and the panel uses both weights"
	)
	var snapshot := {
		"state": "playing",
		"gold": 12345,
		"difficulty": "normal",
		"wave": 4,
		"level": 7,
		"shield_active": false,
		"heroes":
		[
			{
				"name": "Kaizen",
				"alive": true,
				"level": 3,
				"hp": 50.0,
				"max_hp": 100.0,
				"ready": [],
			}
		],
		"has_boss": true,
		"has_enemy_hero": true,
		"held": "gather",
		"press": {},
	}
	var regular := Layout.build(snapshot, panel, _measure)
	var bold := Layout.build(snapshot, panel, _measure, _measure_wide)
	var gather: Rect2i = bold["buttons"]["gather"]["rect"]
	var cx := gather.position.x - panel.position.x + gather.size.x / 2
	var expect_gather := cx - _measure_wide("GATHER [G]", 13) / 2
	var regular_gather := cx - _measure("GATHER [G]", 13) / 2
	var gather_pos := Vector2i(-1, -1)
	var level_pos := Vector2i(-1, -1)
	for entry in bold["texts"]:
		var entry_pos: Vector2i = entry["pos"]
		if String(entry["text"]) == "GATHER [G]":
			gather_pos = entry_pos
		elif String(entry["text"]) == "LV 7":
			level_pos = entry_pos
	check.call(
		gather_pos.x == expect_gather and gather_pos.x != regular_gather,
		"a centred tactical label is centred with the bold width"
	)
	var right := panel.size.x - 14 - 10
	check.call(
		level_pos.x == right - _measure_wide("LV 7", 16),
		"the right-aligned bold level uses the bold width"
	)
	# The gold font-size fallback compares the rendered width against 55 % of
	# the box; the source measures with the bold face it renders with.
	# 316 px box -> 173 px budget; the 15 glyph string measures 105 px in the
	# regular probe and 180 px in the bold one.
	var long_gold := snapshot.duplicate()
	long_gold["gold"] = 123456789012000
	var threshold := Layout.build(long_gold, panel, _measure, _measure_wide)
	var plain_threshold := Layout.build(long_gold, panel, _measure)
	var bold_size := 0
	var regular_size := 0
	for entry in threshold["texts"]:
		if String(entry["text"]) == Layout.format_gold(123456789012000):
			bold_size = int(entry["size"])
	for entry in plain_threshold["texts"]:
		if String(entry["text"]) == Layout.format_gold(123456789012000):
			regular_size = int(entry["size"])
	check.call(
		bold_size == 18 and regular_size == 22,
		"the gold size fallback triggers on the bold width (18 vs 22)"
	)
	check.call(
		regular["texts"].size() == bold["texts"].size()
		and int(regular["y_after_tactical"]) == int(bold["y_after_tactical"]),
		"the bold width only moves strings, never the box geometry"
	)


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
	check.call(
		control._measure("TACTICAL", 13) == _font_width(SourceFonts.REGULAR, "TACTICAL", 13),
		"the regular measure uses Barlow-Regular"
	)
	check.call(
		control._measure_bold("TACTICAL", 13) == _font_width(SourceFonts.BOLD, "TACTICAL", 13),
		"the bold measure uses Barlow-Bold"
	)
	check.call(
		control._measure_bold("TACTICAL COMMANDS (HOLD)", 13)
		> control._measure("TACTICAL COMMANDS (HOLD)", 13),
		"the bold face is wider than the regular face at the same size"
	)
	check.call(control._press_at(Vector2i(1323, 43)) == "pause", "panel press hits PAUSE")
	control.update_snapshot({"state": "menu"}, 1300)
	check.call(control.layout.is_empty(), "leaving gameplay clears the panel")
	control.free()


static func _font_width(font: Font, text: String, size: int) -> int:
	return int(ceilf(font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x))
