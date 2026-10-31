extends RefCounted
## Layer 9cp: replay `tests/fixtures/ui_theme_source.json` (31 cases recorded from the real
## `ui_theme.py` under `draw_recorder.py`) against `scripts/ui/ui_theme.gd`, then verify the
## 68-symbol inventory, the palette hand-off and the policy constants.
##
## Text is measured exactly like the recorder (`int(size * 0.55)` px per glyph, height = size),
## which is the same fake metric the other draw checks use; the source passes a `font.size()`
## callable, the port takes a `measure` callable.

const UiTheme = preload("res://scripts/ui/ui_theme.gd")
const UiSkin = preload("res://scripts/ui/ui_skin.gd")
const FIXTURE := "res://tests/fixtures/ui_theme_source.json"
const INVENTORY := "res://tests/fixtures/ui_theme_inventory.json"
const SOURCE_GD := "res://scripts/ui/ui_theme.gd"
const PROJECT_ROOT := "res://"
const GLYPH_FACTOR := 0.55


func run(check: Callable) -> void:
	var data := _json(FIXTURE)
	check.call(not data.is_empty(), "the ui_theme source fixture parses")
	if data.is_empty():
		return
	_check_strings(check, data)
	_check_cases(check, data)
	_check_palette(check, data)
	_check_inventory(check)


## `ui_theme.py` measures with a real font; the recorder models `int(size * 0.55)` per glyph.
func _measure(text: String, size: int) -> Vector2i:
	return Vector2i(int(float(size) * GLYPH_FACTOR) * text.length(), size)


func _json(path: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


func _check_strings(check: Callable, data: Dictionary) -> void:
	var results := {}
	for row in data.get("strings", []):
		results[String(row["label"])] = row["result"]
	check.call(
		UiTheme.letter("PLAY") == "P L A Y"
		and UiTheme.letter("HEROES", "·") == "H·E·R·O·E·S"
		and UiTheme.letter("") == ""
		and results.get("letter_default", "") == UiTheme.letter("PLAY")
		and results.get("letter_dot", "") == UiTheme.letter("HEROES", "·"),
		"letter() spaces characters exactly like the source"
	)
	check.call(
		UiTheme.tab_width(_measure, "HEROES", 26) == int(results.get("tab_width_min", -1))
		and UiTheme.tab_width(_measure, "VERY LONG LABEL", 26)
		== int(results.get("tab_width_long", -1)),
		"tab_width() follows the letter-spaced label with the 150 px floor"
	)
	check.call(
		UiTheme.fit_ellipsis(_measure, "SHORT", 400, 26) == String(results.get("fit_ellipsis_fits", "?"))
		and UiTheme.fit_ellipsis(_measure, "A VERY LONG SETTING LABEL", 150, 26)
		== String(results.get("fit_ellipsis_cut", "?"))
		and UiTheme.fit_ellipsis(_measure, "ABCDEFG", 6, 26)
		== String(results.get("fit_ellipsis_tiny", "?")),
		"fit_ellipsis() truncates without a dangling dot"
	)
	check.call(
		is_equal_approx(UiTheme.math_hyp(3.0, 4.0), 5.0)
		and UiTheme.dim([255, 205, 85], 0.55) == [140, 112, 46]
		and UiTheme.dim([255, 205, 85]) == [140, 112, 46],
		"math_hyp and dim mirror the source arithmetic"
	)


func _check_cases(check: Callable, data: Dictionary) -> void:
	var broken: Array = []
	for stage in data.get("cases", []):
		var label := String(stage["label"])
		var native := _native(label)
		if native.is_empty():
			broken.append(label + ":unmapped")
			continue
		if _canon(native["ops"]) != _canon(stage.get("ops", [])):
			broken.append(label + ":ops")
			continue
		if _canon(native["buttons"]) != _canon(stage.get("buttons", {})):
			broken.append(label + ":buttons")
			continue
		var expected: Variant = stage.get("result")
		if expected is float or expected is int:
			if int(native["result"]) != int(expected):
				broken.append(label + ":result")
		elif expected is Array and (expected as Array).size() == 4 \
				and (expected as Array)[0] is float:
			if _canon(native["rect"]) != _canon(expected):
				broken.append(label + ":rect")
	check.call(broken.is_empty(), "every recorded op sequence matches: %s" % str(broken))
	check.call(
		(data.get("cases", []) as Array).size() == 31,
		"31 ui_theme cases stay recorded: %d" % (data.get("cases", []) as Array).size()
	)


func _native(label: String) -> Dictionary:
	var out: Dictionary = {}
	match label:
		"panel_rich":
			out = _ops_only(UiTheme.panel_ops({
				"rect": [40, 30, 260, 140], "cheap_alpha": true,
			}))
		"panel_cheap":
			out = _ops_only(UiTheme.panel_ops({
				"rect": [40, 30, 260, 140], "cheap_alpha": false,
			}))
		"panel_solid":
			out = _ops_only(UiTheme.panel_solid_ops({"rect": [60, 40, 200, 90]}))
		"pill_gold_hover":
			out = UiTheme.pill_ops({
				"rect": [20, 20, 160, 44], "id": "play", "label": "PLAY", "kind": "gold",
				"size": 26, "style": "body_semibold", "hover": true, "icon": "play",
			}, _measure)
		"pill_locked_disabled":
			out = UiTheme.pill_ops({
				"rect": [20, 90, 160, 44], "id": "locked", "label": "LOCKED", "kind": "locked",
				"size": 26, "style": "body_semibold", "enabled": false,
			}, _measure)
		"button_hover_icon":
			out = UiTheme.button_ops({
				"cx": 640, "cy": 300, "w": 360, "h": 54, "accent": [140, 225, 255],
				"id": "continue", "label": "CONTINUE", "icon": "continue", "hover": true,
				"size": 26, "style": "body_semibold",
			}, _measure)
		"button_plain":
			out = UiTheme.button_ops({
				"cx": 640, "cy": 420, "accent": [200, 130, 210], "id": "credits",
				"label": "CREDITS", "size": 26, "style": "body_semibold",
				"cheap_alpha": false,
			}, _measure)
		"toggle_on_hover":
			out = UiTheme.toggle_ops({
				"rect": [100, 200, 60, 26], "id": "audio", "on": true, "hover": true,
				"size": 26, "style": "body_semibold",
			}, _measure)
		"toggle_off":
			out = UiTheme.toggle_ops({
				"rect": [100, 240, 60, 26], "id": "audio", "on": false,
				"size": 26, "style": "body_semibold",
			}, _measure)
		"tab_active":
			out = UiTheme.tab_ops({
				"rect": [0, 0, 200, 40], "id": "tab_starter", "label": "STARTER",
				"accent": [100, 200, 255], "active": true, "size": 26,
				"style": "body_semibold",
			}, _measure)
		"tab_hover":
			out = UiTheme.tab_ops({
				"rect": [0, 60, 200, 40], "id": "tab_mini", "label": "MINI",
				"accent": [255, 150, 100], "hover": true, "size": 26,
				"style": "body_semibold",
			}, _measure)
		"slider_half_hover":
			out = UiTheme.slider_ops({
				"x": 100, "y": 300, "w": 240, "value": 0.5, "knob_hover": true,
			})
		"chip_icon_value":
			out = UiTheme.chip_ops({
				"pos": [30, 20], "text": "GOLD", "accent": [255, 205, 85], "icon": "coin",
				"value": "+3/s", "size": 26, "style": "body_semibold",
			}, _measure)
		"chip_right_no_value":
			out = UiTheme.chip_ops({
				"pos": [1250, 40], "text": "WAVE", "accent": [110, 195, 255],
				"align": "right", "size": 26, "style": "body_semibold",
			}, _measure)
		"section_header":
			out = UiTheme.section_header_ops({
				"x": 60, "y": 100, "title": "HERO SHOP", "icon": "swords",
				"color": [255, 205, 85], "size": 26, "style": "body_semibold",
				"rule_w": 240,
			}, _measure)
		"option_cycler":
			out = UiTheme.option_cycler_ops({
				"x": 60, "y": 200, "width": 400, "id": "lang", "label": "Language",
				"value": "English", "label_size": 26, "label_style": "body_semibold",
				"value_size": 22, "value_style": "body_medium",
			}, _measure)
		"option_cycler_hover_long":
			out = UiTheme.option_cycler_ops({
				"x": 60, "y": 250, "width": 400, "id": "lang", "label": "Language",
				"value": "Bahasa Indonesia", "hover": "lang_prev", "label_size": 26,
				"label_style": "body_semibold", "value_size": 22, "value_style": "body_medium",
			}, _measure)
		"screen_title_full":
			out = _dict_only(UiTheme.screen_title_ops({
				"cx": 640, "y": 120, "text": "MYSTIC ARENA",
			}, _measure))
		"screen_title_sub_solid":
			out = _dict_only(UiTheme.screen_title_ops({
				"cx": 640, "y": 140, "text": "DEFEAT", "glow": false, "sub": "TRY AGAIN",
				"sub_color": [255, 168, 96], "cheap_alpha": false,
			}, _measure))
		"back_button_hover":
			out = UiTheme.back_button_ops({
				"cx": 640, "y": 660, "id": "back", "hover": true,
			}, _measure)
		"back_button_plain":
			out = UiTheme.back_button_ops({"cx": 640, "y": 660, "id": "back"}, _measure)
		"scroll_indicator_mid":
			out = UiTheme.scroll_indicator_ops({
				"x": 1240, "y": 100, "height": 300, "scroll_pos": 120, "max_scroll": 240,
			})
		"scroll_indicator_none":
			out = UiTheme.scroll_indicator_ops({
				"x": 1240, "y": 440, "height": 200, "cheap_alpha": false,
			})
		"hp_bar_70":
			out = _ops_only(UiTheme.hp_bar_ops({"x": 60, "y": 600, "w": 220, "h": 16,
				"ratio": 0.7}))
		"hp_bar_cheap_20":
			out = _ops_only(UiTheme.hp_bar_ops({"x": 60, "y": 630, "w": 220, "h": 16,
				"ratio": 0.2, "color": [255, 108, 108], "cheap_alpha": false}))
		"progress_bar_half":
			out = _ops_only(UiTheme.progress_bar_ops({"x": 60, "y": 660, "w": 220,
				"frac": 0.45}))
		"progress_bar_zero":
			out = _ops_only(UiTheme.progress_bar_ops({"x": 60, "y": 680, "w": 220,
				"frac": 0.0, "cheap_alpha": false}))
		"draw_text_center":
			out = _ops_only(UiTheme.draw_text_ops({
				"text": "VICTORY", "size": 26, "style": "body_semibold",
				"color": [240, 244, 255], "center": [640, 200],
			}, _measure))
		"draw_text_topleft":
			out = _ops_only(UiTheme.draw_text_ops({
				"text": "GOLD +125", "size": 26, "style": "body_semibold",
				"color": [255, 220, 110], "topleft": [40, 60], "shadow": false,
			}, _measure))
		"outline_text_default":
			out = UiTheme.outline_text_ops({
				"text": "VICTORY", "center": [640, 220],
			}, _measure)
		"outline_text_custom":
			out = UiTheme.outline_text_ops({
				"text": "DEFEAT", "center": [640, 260], "width": 3,
				"body_top": [255, 108, 108], "body_bottom": [132, 44, 44],
				"cheap_alpha": false,
			}, _measure)
		_:
			pass
	return out


## Op-only builders return an Array; wrap them in the component shape of the fixture.
func _ops_only(ops: Array) -> Dictionary:
	return {"ops": ops, "rect": [], "buttons": {}, "result": null}


## Component builders already return `ops`/`rect`/`buttons`; add the `result` slot the
## fixture replay reads, so both shapes reach `_check_cases` identically.
func _dict_only(payload: Dictionary) -> Dictionary:
	return {
		"ops": payload.get("ops", []),
		"rect": payload.get("rect", []),
		"buttons": payload.get("buttons", {}),
		"result": payload.get("result", null),
	}


func _check_palette(check: Callable, data: Dictionary) -> void:
	var palette: Dictionary = data.get("palette", {})
	var wrong: Array = []
	for name in palette:
		if _canon(UiTheme.rgb(String(name))) != _canon(palette[name]):
			wrong.append(name)
	check.call(
		palette.size() == 32 and wrong.is_empty(),
		"all 32 palette constants reach ui_theme.gd unchanged: %s" % str(wrong)
	)
	check.call(
		UiTheme.rgb("GOLD") == [255, 205, 85] and UiTheme.rgb("PANEL_TOP") == [30, 37, 66],
		"the identity gold and the panel top keep their source values"
	)


func _check_inventory(check: Callable) -> void:
	var fixture := _json(INVENTORY)
	check.call(not fixture.is_empty(), "the ui_theme inventory parses")
	if fixture.is_empty():
		return
	var file: Dictionary = fixture.get("file", {})
	check.call(
		int(file.get("lines", 0)) == 1011
		and int(file.get("functions", 0)) == 31
		and int(file.get("assigns", 0)) == 36
		and int(file.get("imports", 0)) == 1
		and int(file.get("classes", -1)) == 0,
		"ui_theme.py stays 1011 lines of 31 functions and 36 assigns: %s" % str(file)
	)
	var symbols: Dictionary = fixture.get("symbols", {})
	check.call(
		int(symbols.get("count", 0)) == 68,
		"68 module symbols are classified: %d" % int(symbols.get("count", 0))
	)
	var kinds: Dictionary = fixture.get("kinds", {})
	check.call(
		int(kinds.get("data", -1)) == 32
		and int(kinds.get("ported", -1)) == 25
		and int(kinds.get("baked", -1)) == 4
		and int(kinds.get("folded", -1)) == 7
		and int(kinds.get("deviation", 0)) == 0
		and int(kinds.get("dead", 0)) == 0,
		"every symbol kind is counted: %s" % str(kinds)
	)
	check.call(
		_canon(fixture.get("baked", [])) == _canon(["_radial", "_shadow", "_vgrad", "draw_icon"]),
		"only the four pixel primitives stay baked"
	)
	check.call(
		(fixture.get("ported", []) as Array).size() == 25
		and (fixture.get("native_only", []) as Array).size() >= 12,
		"25 ported helpers plus the native op primitives: %d"
		% (fixture.get("native_only", []) as Array).size()
	)
	var broken: Array = []
	var row: Dictionary = fixture.get("classification", {})
	for name in row:
		var entry: Dictionary = row[name]
		var text := FileAccess.get_file_as_string(PROJECT_ROOT + String(entry.target))
		if text.is_empty() or text.find(String(entry.token)) < 0:
			broken.append(name)
	check.call(broken.is_empty(), "every classified token lives in its target: %s" % str(broken))
	var policy: Dictionary = fixture.get("policy", {})
	check.call(
		int(policy.get("palette_colors", 0)) == 32
		and int(policy.get("tick_length", 0)) == UiTheme.TICK_LENGTH
		and int(policy.get("tick_inset", 0)) == UiTheme.TICK_INSET
		and int(policy.get("panel_radius", 0)) == UiTheme.PANEL_RADIUS
		and int(policy.get("pill_radius", 0)) == UiTheme.PILL_RADIUS
		and int(policy.get("tab_radius", 0)) == UiTheme.TAB_RADIUS
		and int(policy.get("slider_track", 0)) == UiTheme.SLIDER_TRACK
		and int(policy.get("toggle_knob", 0)) == UiTheme.TOGGLE_KNOB
		and int(policy.get("chip_height", 0)) == UiTheme.CHIP_HEIGHT
		and int(policy.get("chip_pad", 0)) == UiTheme.CHIP_PAD
		and int(policy.get("tab_min_width", 0)) == UiTheme.TAB_MIN_WIDTH
		and int(policy.get("tab_pad", 0)) == UiTheme.TAB_PAD
		and int(policy.get("option_min_box", 0)) == UiTheme.OPTION_MIN_BOX
		and int(policy.get("option_box_pad", 0)) == UiTheme.OPTION_BOX_PAD
		and int(policy.get("scroll_min_thumb", 0)) == UiTheme.SCROLL_MIN_THUMB
		and int(policy.get("grad_text_cache_limit", 0)) == UiTheme.GRAD_TEXT_CACHE_LIMIT,
		"the policy constants match the module"
	)
	check.call(
		(policy.get("back_button", []) as Array)[0] == UiTheme.BACK_BUTTON_WIDTH
		and (policy.get("back_button", []) as Array)[1] == UiTheme.BACK_BUTTON_HEIGHT
		and (policy.get("title_glow", []) as Array)[0] == UiTheme.TITLE_GLOW[0]
		and (policy.get("title_glow", []) as Array)[1] == UiTheme.TITLE_GLOW[1]
		and int((policy.get("title_glow", []) as Array)[2]) == UiTheme.TITLE_GLOW_ALPHA
		and int(policy.get("ornament_span", 0)) == UiTheme.ORNAMENT_SPAN,
		"back button, title glow and ornament spans agree"
	)
	UiTheme.clear_caches()
	check.call(
		not UiSkin.manifest().is_empty() and UiSkin.panels_texture() != null,
		"clear_caches() forgets the sheet cache and the manifest reloads"
	)
	check.call(
		FileAccess.get_file_as_string(SOURCE_GD).find("static func screen_title_ops(") > 0,
		"ui_theme.gd owns the ported helpers"
	)


## Key-order independent string form, so JSON dictionaries compare with native ones.
func _canon(value: Variant) -> String:
	if value is Dictionary:
		var keys: Array = (value as Dictionary).keys()
		keys.sort()
		var parts := PackedStringArray()
		for key in keys:
			parts.append("%s=%s" % [str(key), _canon((value as Dictionary)[key])])
		return "{" + ",".join(parts) + "}"
	if value is Array:
		var items := PackedStringArray()
		for item in value:
			items.append(_canon(item))
		return "[" + ",".join(items) + "]"
	if value is float or value is int:
		return "%.4f" % float(value)
	return JSON.stringify(value)
