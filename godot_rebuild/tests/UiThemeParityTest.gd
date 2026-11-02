class_name UiThemeParity
extends RefCounted

## Replays the pygame ui_theme oracle: helpers, icons, and every component in
## both alpha quality modes. Numeric comparisons use a small float tolerance.
const FIXTURE := "res://tests/fixtures/ui_theme_parity.json"
const CONTRACT := "res://data/ui_theme.json"


static func run(runner) -> void:
	UiTheme.load_contract(CONTRACT)
	runner.check(UiTheme.valid(), "ui_theme contract loads")
	var file := FileAccess.open(FIXTURE, FileAccess.READ)
	if file == null:
		runner.check(false, "ui_theme fixture opens")
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		runner.check(false, "ui_theme fixture parses")
		return
	var oracle: Dictionary = parsed
	_text(runner, oracle.text)
	_surfaces(runner, oracle.surfaces)
	for row: Dictionary in oracle.icons:
		var ops := UiThemeIcons.draw_data(
			str(row.name), _v2(row.center), row.color, float(row.scale)
		)
		runner.check(_equal(ops, row.ops), "ui_theme icon parity: %s @%.1f" % [row.name, row.scale])
	for row: Dictionary in oracle.ticks:
		var ops := UiThemeComponents.corner_ticks(_rect(row.rect), row.color)
		runner.check(_equal(ops, row.ops), "ui_theme corner ticks parity")
	for row: Dictionary in oracle.tab_widths:
		var width := UiThemeComponentsExtra.tab_width(str(row.label), _measure(24), int(row.min_w))
		runner.check(width == int(row.result), "ui_theme tab_width parity: %s" % row.label)
	for row: Dictionary in oracle.components:
		_component(runner, row)
	UiTheme.set_quality_override(null)
	UiThemeSurfaces.clear_caches()
	UiTheme.load_contract("")
	runner.check(not UiTheme.valid(), "ui_theme missing contract fails closed")
	UiTheme.load_contract(CONTRACT)
	runner.check(UiTheme.valid(), "ui_theme contract restores")


static func _text(runner, data: Dictionary) -> void:
	for row: Dictionary in data.letter:
		runner.check(
			UiThemeText.letter(str(row.text), str(row.gap)) == str(row.result),
			"ui_theme letter parity"
		)
	var blits := UiThemeText.layout(Vector2(10, 10), [50, 50], null, true, [2, 2])
	runner.check(blits.size() == 2, "ui_theme text layout accepts JSON points")
	for row: Dictionary in data.ellipsis:
		var glyph := bool(row.glyph)
		var result := UiThemeText.fit_ellipsis(
			str(row.text), float(row.max_w), _measure(24), func(_ch: String) -> bool: return glyph
		)
		runner.check(result == str(row.result), "ui_theme ellipsis parity")


static func _surfaces(runner, data: Dictionary) -> void:
	for row: Dictionary in data.gradient:
		var got := UiThemeSurfaces.gradient_data(
			int(row.w), int(row.h), row.top, row.bottom, int(row.radius)
		)
		runner.check(
			_equal(got.size, row.size) and _equal(got.rows, row.rows), "ui_theme gradient parity"
		)
	for row: Dictionary in data.radial:
		var got := UiThemeSurfaces.radial_data(int(row.w), int(row.h), row.color, int(row.alpha))
		runner.check(
			_equal(got.size, row.size) and _equal(got.blocks, row.blocks), "ui_theme radial parity"
		)
	for row: Dictionary in data.shadow:
		var got := UiThemeSurfaces.shadow_data(
			int(row.w), int(row.h), int(row.radius), int(row.alpha), int(row.spread)
		)
		runner.check(
			_equal(got.size, row.size) and _equal(got.small_ops, row.small_ops),
			"ui_theme shadow parity"
		)


static func _component(runner, row: Dictionary) -> void:
	UiTheme.set_quality_override(bool(row.cheap_alpha))
	var args: Array = row.args
	var kwargs: Dictionary = row.kwargs
	var got: Dictionary = {}
	match str(row.name):
		"panel":
			var d: Dictionary = UiTheme.defaults.panel
			got = UiThemeComponents.panel(
				_rect(args[0]),
				kwargs.get("border", d.border),
				kwargs.get("fill_top", d.fill_top),
				kwargs.get("fill_bottom", d.fill_bottom),
				bool(kwargs.get("ticks", d.ticks)),
				bool(kwargs.get("shadow", d.shadow)),
				int(kwargs.get("border_w", d.border_w))
			)
		"panel_solid":
			got = UiThemeComponents.panel_solid(
				_rect(args[0]), kwargs.get("border", UiTheme.defaults.panel_solid.border)
			)
		"button":
			var opts := _button_opts(kwargs)
			var size := int(opts.get("font_size_override", 0))
			if size <= 0:
				size = _font_size(args[5])
			got = UiThemeComponents.button(
				str(args[0]),
				str(args[1]),
				float(args[2]),
				float(args[3]),
				args[4],
				_font_size(args[5]),
				_measure(size),
				opts
			)
		"pill":
			var opts := _defaults("pill", kwargs)
			got = UiThemeComponents.pill(
				str(args[0]),
				str(args[1]),
				_rect(args[2]),
				str(args[3]),
				_font_size(args[4]),
				_measure(_font_size(args[4])),
				opts
			)
		"chip":
			var opts := _defaults("chip", kwargs)
			got = UiThemeComponents.chip(
				_v2(args[0]),
				str(args[1]),
				args[2],
				_font_size(args[3]),
				_measure(_font_size(args[3])),
				opts
			)
		"section_header":
			got = UiThemeComponents.section_header(
				float(args[0]),
				float(args[1]),
				str(args[2]),
				str(args[3]),
				args[4],
				_font_size(args[5]),
				_measure(_font_size(args[5])),
				int(kwargs.get("rule_w", UiTheme.defaults.section_header.rule_w))
			)
		"toggle":
			got = UiThemeComponents.toggle(
				str(args[0]),
				_rect(args[1]),
				bool(args[2]),
				_font_size(args[3]),
				bool(kwargs.get("hover", false))
			)
		"slider":
			got = UiThemeComponents.slider(
				float(args[0]),
				float(args[1]),
				float(args[2]),
				float(args[3]),
				bool(kwargs.get("knob_hover", false))
			)
		"option_cycler":
			got = UiThemeComponentsExtra.option_cycler(
				str(args[0]),
				str(args[1]),
				str(args[2]),
				float(args[3]),
				float(args[4]),
				float(args[5]),
				_font_size(args[6]),
				_font_size(args[7]),
				_measure(_font_size(args[7])),
				kwargs.get("hover")
			)
		"tab":
			got = UiThemeComponentsExtra.tab(
				str(args[0]),
				_rect(args[1]),
				str(args[2]),
				args[3],
				_font_size(args[4]),
				bool(args[5]),
				bool(kwargs.get("hover", false))
			)
		"screen_title":
			var sub_color: Variant = kwargs.get(
				"sub_color", UiTheme.defaults.screen_title.sub_color
			)
			got = UiThemeComponentsExtra.screen_title(
				str(args[0]),
				float(args[1]),
				float(args[2]),
				bool(kwargs.get("glow", UiTheme.defaults.screen_title.glow)),
				kwargs.get("sub"),
				sub_color,
				bool(kwargs.get("ornament", UiTheme.defaults.screen_title.ornament)),
				_measure(UiTheme.integer("title.sub_font_size"))
			)
		"back_button":
			var fs := _font_size(kwargs.get("font")) if kwargs.get("font") != null else 0
			got = UiThemeComponentsExtra.back_button(
				str(args[0]),
				float(args[1]),
				float(args[2]),
				bool(kwargs.get("hover", false)),
				fs,
				_measure(24)
			)
		"scroll_indicator":
			got = UiThemeComponentsExtra.scroll_indicator(
				float(args[0]),
				float(args[1]),
				float(args[2]),
				float(args[3]),
				float(args[4]),
				int(kwargs.get("width", UiTheme.defaults.scroll_indicator.width))
			)
		"hp_bar":
			got = UiThemeComponentsExtra.hp_bar(
				float(args[0]),
				float(args[1]),
				float(args[2]),
				float(args[3]),
				float(args[4]),
				kwargs.get("color", UiTheme.defaults.hp_bar.color)
			)
		"progress_bar":
			got = UiThemeComponentsExtra.progress_bar(
				float(args[0]),
				float(args[1]),
				float(args[2]),
				float(args[3]),
				kwargs.get("color", UiTheme.defaults.progress_bar.color),
				int(kwargs.get("h", UiTheme.defaults.progress_bar.h))
			)
		_:
			runner.check(false, "ui_theme unknown component: %s" % row.name)
			return
	var ok := (
		_equal(got.ops, row.ops) and _equal(got.btns, row.btns) and _equal(got.result, row.result)
	)
	runner.check(ok, "ui_theme component parity: %s cheap=%s" % [row.name, row.cheap_alpha])


static func _button_opts(kwargs: Dictionary) -> Dictionary:
	var d: Dictionary = UiTheme.defaults.button
	var opts := {
		"w": int(kwargs.get("w", d.w)),
		"h": int(kwargs.get("h", d.h)),
		"hover": bool(kwargs.get("hover", d.hover)),
		"icon": kwargs.get("icon", d.icon),
		"letter_gap": bool(kwargs.get("letter_gap", d.letter_gap)),
		"font_size_override":
		int(kwargs.get("font_size", 0)) if kwargs.get("font_size") != null else 0,
	}
	return opts


static func _defaults(name: String, kwargs: Dictionary) -> Dictionary:
	var result: Dictionary = UiTheme.defaults[name].duplicate(true)
	for key: Variant in kwargs:
		result[key] = kwargs[key]
	return result


static func _font_size(value: Variant) -> int:
	if value is Dictionary:
		return int(value.get("font_size", 24))
	return 24


static func _measure(font_size: int) -> Callable:
	return func(text: String) -> float: return float(floori(str(text).length() * font_size / 2.0))


static func _rect(row: Array) -> Rect2i:
	return Rect2i(int(row[0]), int(row[1]), int(row[2]), int(row[3]))


static func _v2(row: Array) -> Vector2:
	return Vector2(float(row[0]), float(row[1]))


static func _equal(a: Variant, b: Variant) -> bool:
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size():
			return false
		for key: Variant in a:
			if not b.has(key) or not _equal(a[key], b[key]):
				return false
		return true
	if a is Array and b is Array:
		if a.size() != b.size():
			return false
		for index in range(a.size()):
			if not _equal(a[index], b[index]):
				return false
		return true
	if (a is float or a is int) and (b is float or b is int):
		return absf(float(a) - float(b)) < 0.0001
	return a == b
