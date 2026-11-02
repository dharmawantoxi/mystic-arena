extends RefCounted

## Exact string parity against localization.py (pure data + str.format subset).


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/localization_parity.json", FileAccess.READ)
	runner.check(file != null, "localization Python oracle fixture exists")
	if file == null:
		return
	var oracle: Dictionary = JSON.parse_string(file.get_as_text())
	var localization := Localization.new()
	runner.check(localization.valid(), "native localization contract loads")
	runner.check(localization.languages == ["id", "en"], "localization languages match source")
	runner.check(localization.default_language == "id", "localization defaults to Indonesian")
	runner.check(
		localization.key_count == 224 and localization.key_order.size() == 224,
		"localization key count"
	)
	runner.check(
		localization.get_language_label("id") == "Bahasa Indonesia", "Indonesian language label"
	)
	runner.check(localization.get_language_label("en") == "English", "English language label")
	for row: Dictionary in oracle.language_cases:
		var returned := localization.set_language(str(row.input))
		var ok := returned == str(row.returned)
		ok = ok and localization.get_language() == str(row.active)
		ok = ok and localization.get_language_label() == str(row.label)
		runner.check(ok, "localization language switch: " + str(row.input))
	localization.set_language("en")
	for row: Dictionary in oracle.label_cases:
		runner.check(
			localization.get_language_label(str(row.input)) == str(row.expected),
			"localization label fallback: " + str(row.input)
		)
	for row: Dictionary in oracle.tr_cases:
		localization.set_language(str(row.language))
		var actual := localization.tr_text(str(row.key), _args(row.args))
		runner.check(actual == str(row.expected), "localization tr %s/%s" % [row.language, row.key])
	for row: Dictionary in oracle.missing_args_cases:
		localization.set_language(str(row.language))
		runner.check(
			localization.tr_text(str(row.key)) == str(row.expected),
			"localization missing args returns template: " + str(row.key)
		)
	for row: Dictionary in oracle.edge_cases:
		localization.set_language(str(row.language))
		runner.check(
			localization.tr_text(str(row.key), _args(row.args)) == str(row.expected),
			"localization edge: " + str(row.key)
		)
	_format_edges(runner)
	_core_data(runner, localization)
	var missing := Localization.new("user://missing_localization_%d.json" % Time.get_ticks_usec())
	runner.check(
		not missing.valid() and not missing.load_error.is_empty(),
		"missing localization contract fails closed"
	)


static func _args(raw: Dictionary) -> Dictionary:
	var result := raw.duplicate()
	for key: String in result:
		var value: Variant = result[key]
		if value is float and is_equal_approx(float(value), roundf(float(value))):
			result[key] = int(value)
	return result


static func _format_edges(runner) -> void:
	runner.check(
		Localization.format_template("{a} {b}", {"a": 1, "b": "x"}) == "1 x",
		"named format replacement"
	)
	runner.check(
		Localization.format_template("{a} {b}", {"a": 1}) == "{a} {b}",
		"missing placeholder keeps template"
	)
	runner.check(
		Localization.format_template("{{literal}}", {}) == "{literal}", "escaped braces format"
	)
	runner.check(
		Localization.format_template("{bad", {}) == "{bad", "malformed brace keeps template"
	)
	runner.check(
		Localization.format_template("{0}", {"0": "x"}) == "{0}",
		"positional placeholder is outside subset"
	)


static func _core_data(runner, localization: Localization) -> void:
	var core := CoreData.new()
	runner.check(core.valid() and core.localization.valid(), "CoreData loads native localization")
	var args := {"item": "Moon Shard", "hero": "Aldric"}
	runner.check(
		core.text("forge_queued", "en", args) == localization.tr_for("forge_queued", "en", args),
		"CoreData.text delegates to localization"
	)
	runner.check(
		core.text("forge_queued", "fr", args) == localization.tr_for("forge_queued", "id", args),
		"CoreData.text invalid language falls back to Indonesian"
	)
	core.localization.set_language("en")
	runner.check(
		core.localization.get_language() == "en", "CoreData localization keeps active language"
	)
