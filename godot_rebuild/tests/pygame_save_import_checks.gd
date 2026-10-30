# gdlint:disable=max-returns
extends RefCounted
## Pygame slot file -> Godot slot, checked against the read-only source oracle.
## The fixture records what `_system.py::SaveManager` makes of eleven slot files
## plus what the stricter native envelope must produce from them.

const Import = preload("res://scripts/match/pygame_save_import.gd")
const Slots = preload("res://scripts/match/save_slot_store.gd")
const LevelStats = preload("res://scripts/match/level_stats.gd")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS
const FIXTURE := "res://tests/fixtures/pygame_save_import_source.json"
const TEMPLATE := "user://pygame_import_test_%d.json"
const SOURCE := "user://pygame_import_source_test.json"


func run(check: Callable) -> void:
	_cleanup()
	var parsed: Variant = _parse(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Pygame save-import fixture parses")
	if not (parsed is Dictionary):
		return
	var fixture: Dictionary = parsed
	var policy: Dictionary = fixture.policy
	var clock := float(policy.clock)
	_check_policy(policy, check)

	var cases: Array = fixture.cases
	check.call(cases.size() >= 11, "Every source slot-file case is covered")
	var faithful := {}
	for case in cases:
		var record: Dictionary = case
		# Parse the recorded file text: the drop report follows the key order of
		# the file, and JSON.stringify'd fixture copies would sort it away.
		var source: Variant = _parse(String(record.raw_text))
		var result := Import.normalize(source, clock)
		var expected: Dictionary = record.expected
		if bool(expected.ok):
			check.call(
				_matches(result, expected),
				"Slot file '%s' imports as the source profile" % String(record.name)
			)
			faithful[String(record.name)] = result
		else:
			check.call(
				(
					not bool(result.ok)
					and String(result.reason) == String(expected.reason)
					and (result.state as Dictionary).is_empty()
				),
				"Slot file '%s' is refused with %s" % [String(record.name), String(expected.reason)]
			)
		check.call(
			Import.normalize(source, clock) == result,
			"Slot file '%s' imports deterministically" % String(record.name)
		)

	_check_faithful(fixture, faithful, clock, check)
	_check_import_files(cases, clock, check)
	_check_refusals(cases, clock, check)
	_cleanup()
	check.call(not Slots.slot_exists(1, TEMPLATE), "Import test slots are cleaned up")


func _check_policy(policy: Dictionary, check: Callable) -> void:
	check.call(Import.MAX_LEVEL == int(policy.max_level), "Import level ceiling matches source")
	check.call(LevelStats.MAX_LEVEL == Import.MAX_LEVEL, "Import reuses the level-stat ceiling")
	check.call(
		HERO_ROSTER.size() == int(policy.roster_size),
		"Import roster size matches the source hero list"
	)
	var difficulties: Array = policy.difficulties
	check.call(
		difficulties.size() == Import.DIFFICULTIES.size(), "Import difficulty list matches source"
	)
	for index in range(difficulties.size()):
		check.call(
			String(difficulties[index]) == Import.DIFFICULTIES[index],
			"Import difficulty '%s' matches source" % Import.DIFFICULTIES[index]
		)
	var fields: Array = policy.stats_fields
	check.call(
		fields.size() == LevelStats.INTEGER_FIELDS.size(),
		"Import level-stat fields match the native schema"
	)
	for index in range(fields.size()):
		check.call(
			String(fields[index]) == LevelStats.INTEGER_FIELDS[index],
			"Import level-stat field '%s' matches source" % LevelStats.INTEGER_FIELDS[index]
		)
	check.call(
		not bool(policy.replay_reward_counts_in_source), "Source save has no replay reward ledger"
	)


## Everything the source profile says and the native envelope can hold must survive.
func _check_faithful(
	fixture: Dictionary, faithful: Dictionary, clock: float, check: Callable
) -> void:
	for case in fixture.cases:
		var record: Dictionary = case
		if not faithful.has(String(record.name)):
			continue
		var state: Dictionary = faithful[String(record.name)].state
		var loaded: Dictionary = record.source_loaded
		check.call(
			int(state.meta_gold) == int(loaded.meta_gold),
			"Imported currency of '%s' equals the source profile" % String(record.name)
		)
		check.call(
			int(state.slot_playtime_seconds) == int(loaded.slot_playtime_seconds),
			"Imported playtime of '%s' equals the source profile" % String(record.name)
		)
		check.call(
			String(state.get("import_source", "")) == Import.MARKER,
			"Imported slot of '%s' is marked as a Pygame import" % String(record.name)
		)
		check.call(
			(state.replay_reward_counts as Dictionary).is_empty(),
			"Imported slot of '%s' starts with an empty replay ledger" % String(record.name)
		)
	check.call(_full_profile(faithful), "A complete Pygame profile imports unchanged")
	var legacy: Dictionary = faithful["legacy_minimal"].state
	check.call(
		legacy.slot_created == clock and legacy.slot_last_played == clock,
		"Legacy slot without metadata is stamped at import time like source load()"
	)
	var preview := Import.preview(_parse(String(_case(fixture.cases, "full").raw_text)), clock)
	check.call(preview.ok and preview.highest_level == 4, "Preview reports the highest level")
	check.call(preview.completed == 3, "Preview counts completed levels")
	check.call(preview.heroes == 2 and preview.bosses == 1, "Preview counts the collections")
	check.call(preview.playtime_seconds == 3665, "Preview reports the source playtime")
	var migration: Dictionary = fixture.migration.state
	var upgraded := Import.normalize(migration, clock)
	check.call(
		bool(fixture.migration.migrated) and bool(upgraded.ok),
		"A migrated legacy progress file can be imported"
	)
	check.call(
		int(upgraded.state.meta_gold) == int(migration.meta_gold),
		"Migrated legacy currency survives the import"
	)


func _full_profile(faithful: Dictionary) -> bool:
	var full: Dictionary = faithful["full"].state
	return (
		full.purchased_heroes == ["kaizen", "thorne"]
		and full.unlocked_bosses == ["gornak"]
		and full.completed_levels == [1, 2, 4]
		and full.last_played_level == 4
		and String(full.run_difficulty) == "hard"
		and int(full.level_stats["3"].best_score) == 1820
		and int(full.level_stats["3"].total_playtime_seconds) == 905
	)


func _check_import_files(cases: Array, clock: float, check: Callable) -> void:
	var full: Dictionary = _case(cases, "full")
	var raw := String(full.raw_text)
	check.call(_write(SOURCE, raw), "Source slot file is staged in the user directory")
	var imported := Import.import_file(SOURCE, 1, TEMPLATE, clock)
	check.call(bool(imported.ok), "A Pygame slot file imports into an empty native slot")
	check.call(Slots.slot_exists(1, TEMPLATE), "The import writes the atomic slot file")
	var stored := Slots.load_state(1, TEMPLATE)
	check.call(_matches(imported.state, stored), "The import reports the stored profile")
	var expected: Dictionary = Import.normalize(_parse(raw), clock).state.duplicate(true)
	expected["slot_last_played"] = clock
	check.call(_matches(stored, expected), "Stored slot keeps the imported profile")
	var info := Slots.slot_info(1, TEMPLATE)
	check.call(int(info.meta_gold) == 7250, "Native slot card reports the imported currency")
	check.call(int(info.highest_level) == 4, "Native slot card reports the imported progress")
	check.call(int(info.playtime_seconds) == 3665, "Native slot card reports the imported playtime")
	check.call(
		is_equal_approx(float(info.slot_last_played), clock),
		"Import stamps last-played exactly as the source save() does"
	)
	check.call(
		FileAccess.get_file_as_string(SOURCE) == raw,
		"The Pygame source file is never modified by the import"
	)
	var blocked := Import.import_file(SOURCE, 1, TEMPLATE, clock)
	check.call(
		not bool(blocked.ok) and String(blocked.reason) == "slot_occupied",
		"Import never overwrites an occupied slot without consent"
	)
	check.call(
		bool(Import.import_file(SOURCE, 1, TEMPLATE, clock, true).ok),
		"Explicit overwrite replaces the native slot"
	)
	check.call(
		bool(Import.import_file(SOURCE, 3, TEMPLATE, clock).ok),
		"The same source file imports into any of the three slots"
	)
	check.call(
		int(Slots.slot_info(3, TEMPLATE).meta_gold) == 7250,
		"Each imported slot keeps its own copy of the profile"
	)
	var legacy: Dictionary = _case(cases, "legacy_minimal")
	check.call(_write(SOURCE, String(legacy.raw_text)), "Legacy slot file is staged")
	check.call(
		bool(Import.import_file(SOURCE, 2, TEMPLATE, clock).ok),
		"A legacy slot file without metadata imports"
	)
	var minimal := Slots.load_state(2, TEMPLATE)
	check.call(
		int(minimal.meta_gold) == 410 and (minimal.level_stats as Dictionary).is_empty(),
		"Backfilled defaults of the legacy slot are stored"
	)
	check.call(int(minimal.slot_created) != 0, "A legacy slot still gets a native creation stamp")
	for slot in range(1, Slots.SLOT_COUNT + 1):
		check.call(Slots.delete_slot(slot, TEMPLATE), "Slot %d is removable" % slot)
	_cleanup()


func _check_refusals(cases: Array, clock: float, check: Callable) -> void:
	_cleanup()
	for name in ["corrupt_json", "list_json", "negative_gold", "string_gold"]:
		var record: Dictionary = _case(cases, name)
		check.call(_write(SOURCE, String(record.raw_text)), "Refusal case '%s' is staged" % name)
		check.call(
			not bool(Import.import_file(SOURCE, 1, TEMPLATE, clock).ok),
			"Refusal case '%s' does not import" % name
		)
		check.call(
			not Slots.slot_exists(1, TEMPLATE), "Refusal case '%s' leaves the slot untouched" % name
		)
	check.call(
		String(Import.import_file(SOURCE, 0, TEMPLATE, clock).reason) == "invalid_slot",
		"Slot zero is refused before reading"
	)
	check.call(
		String(Import.import_file(SOURCE, 4, TEMPLATE, clock).reason) == "invalid_slot",
		"Slot four is refused before reading"
	)
	check.call(
		(
			String(Import.import_file(SOURCE + ".absent", 1, TEMPLATE, clock).reason)
			== "missing_source"
		),
		"A missing source file is refused"
	)


func _parse(text: String) -> Variant:
	# Instance parsing keeps a syntax error out of the log: the runner fails on
	# any `ERROR:` line, and a refused Pygame file is an expected outcome here.
	var decoder := JSON.new()
	if decoder.parse(text) != OK:
		return null
	return decoder.data


func _case(cases: Array, name: String) -> Dictionary:
	for case in cases:
		if String(case.name) == name:
			return case
	return {}


func _write(path: String, text: String) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(text)
	file.close()
	return FileAccess.get_file_as_string(path) == text


func _cleanup() -> void:
	for slot in range(1, Slots.SLOT_COUNT + 1):
		_remove(Slots.slot_path(slot, TEMPLATE))
	_remove(SOURCE)


func _remove(path: String) -> void:
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(path + suffix):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path + suffix))


func _matches(actual: Variant, expected: Variant) -> bool:
	if (actual is int or actual is float) and (expected is int or expected is float):
		return is_equal_approx(float(actual), float(expected))
	if actual is Array and expected is Array:
		if actual.size() != expected.size():
			return false
		for index in range(actual.size()):
			if not _matches(actual[index], expected[index]):
				return false
		return true
	if actual is Dictionary and expected is Dictionary:
		if actual.size() != expected.size():
			return false
		for key in expected:
			if not actual.has(key) or not _matches(actual[key], expected[key]):
				return false
		return true
	if actual == null and expected == null:
		return true
	return actual == expected
