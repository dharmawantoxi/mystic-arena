# gdlint:disable=max-returns
extends RefCounted
## Deterministic native replay of _system.py::SaveManager slot lifecycle.

const Slots = preload("res://scripts/match/save_slot_store.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const FIXTURE := "res://tests/fixtures/save_slot_source.json"
const TEMPLATE := "user://save_slot_test_%d.json"
const LEGACY := "user://save_slot_legacy_test.json"


func run(check: Callable) -> void:
	_cleanup()
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Save-slot source fixture parses")
	if not (parsed is Dictionary):
		return
	var fixture: Dictionary = parsed
	check.call(Slots.SLOT_COUNT == int(fixture.policy.slot_count), "Save-slot count matches source")
	check.call(
		Slots.get_current_slot() == int(fixture.policy.initial_slot),
		"Initial save slot matches source"
	)
	check.call(Slots.set_current_slot(2), "Valid source slot can be selected")
	check.call(not Slots.set_current_slot(0), "Slot zero is rejected")
	check.call(not Slots.set_current_slot(4), "Slot above source count is rejected")
	check.call(
		Slots.get_current_slot() == int(fixture.policy.selected_after_invalid),
		"Invalid selection preserves the active source slot"
	)
	check.call(
		_value_matches(Slots.empty_state(1_700_000_000.0), fixture.empty),
		"Native empty save fields match source SaveManager"
	)

	var state := {
		"meta_gold": 7250,
		"completed_levels": [1, 2, 4],
		"last_played_level": 4,
		"purchased_heroes": ["kaizen", "thorne"],
		"unlocked_bosses": ["gornak"],
		"slot_playtime_seconds": 3665,
	}
	check.call(
		Slots.save_state(state, 2, 1_700_000_000.0, TEMPLATE),
		"Selected native slot saves through the atomic progress store"
	)
	var first := Slots.slot_info(2, TEMPLATE)
	_check_info(first, fixture.save.first_info, check, "first")
	var infos := Slots.all_slot_info(TEMPLATE)
	check.call(infos.size() == Slots.SLOT_COUNT, "All source slot cards are returned")
	check.call(infos[0].is_empty() and infos[2].is_empty(), "Missing slots remain empty cards")
	_check_info(infos[1], fixture.save.all_info[1], check, "all")

	state.meta_gold = 8000
	check.call(
		Slots.save_state(state, 2, 1_700_000_125.0, TEMPLATE),
		"Second slot save replaces the same atomic file"
	)
	var second := Slots.slot_info(2, TEMPLATE)
	_check_info(second, fixture.save.second_info, check, "second")
	check.call(
		(
			is_equal_approx(float(second.slot_created), 1_700_000_000.0)
			and is_equal_approx(float(second.slot_last_played), 1_700_000_125.0)
		),
		"Replacement preserves creation time and advances last-played"
	)
	var invalid_metadata := Slots.load_state(2, TEMPLATE)
	invalid_metadata["slot_created"] = -1.0
	check.call(
		not Slots.save_state(invalid_metadata, 2, 1_700_000_125.0, TEMPLATE),
		"Negative slot timestamp is rejected"
	)
	invalid_metadata = Slots.load_state(2, TEMPLATE)
	invalid_metadata["level_stats"] = []
	check.call(
		not Slots.save_state(invalid_metadata, 2, 1_700_000_125.0, TEMPLATE),
		"Malformed per-level metadata is rejected"
	)
	_check_info(Slots.slot_info(2, TEMPLATE), fixture.save.second_info, check, "protected")
	check.call(Slots.delete_slot(2, TEMPLATE) == fixture.delete.first, "First slot delete succeeds")
	check.call(
		Slots.delete_slot(2, TEMPLATE) == fixture.delete.second, "Empty slot delete is inert"
	)
	check.call(Slots.slot_info(2, TEMPLATE).is_empty(), "Deleted source slot has no metadata")

	var legacy := {
		"meta_gold": 99,
		"completed_levels": [1],
		"last_played_level": 1,
		"purchased_heroes": ["kaizen"],
		"unlocked_bosses": [],
	}
	check.call(ProgressStore.save_state(legacy, LEGACY), "Seed isolated native legacy save")
	check.call(
		Slots.migrate_legacy(LEGACY, TEMPLATE, 1_700_000_125.0) == fixture.migration.first,
		"Valid legacy progress migrates into slot one"
	)
	var migrated := Slots.load_state(1, TEMPLATE)
	for field in fixture.migration.state:
		check.call(
			_value_matches(migrated.get(field), fixture.migration.state[field]),
			"Migrated source field survives: " + String(field)
		)
	check.call(
		not FileAccess.file_exists(LEGACY) and FileAccess.file_exists(LEGACY + ".migrated"),
		"Successful migration archives the native legacy file"
	)
	check.call(
		Slots.migrate_legacy(LEGACY, TEMPLATE, 1_700_000_125.0) == fixture.migration.second,
		"Legacy migration cannot repeat"
	)

	var corrupt_path := Slots.slot_path(3, TEMPLATE)
	var corrupt := FileAccess.open(corrupt_path, FileAccess.WRITE)
	check.call(corrupt != null, "Open isolated corrupt slot")
	if corrupt != null:
		corrupt.store_string("{truncated")
		corrupt.close()
	var corrupt_info := Slots.slot_info(3, TEMPLATE)
	check.call(bool(corrupt_info.get("corrupt", false)), "Corrupt slot is not presented as empty")
	check.call(
		not Slots.save_state(state, 3, 1_700_000_125.0, TEMPLATE),
		"Corrupt slot cannot be overwritten silently"
	)
	check.call(Slots.delete_slot(3, TEMPLATE), "Explicit delete clears a corrupt slot")

	check.call(
		(
			Slots.format_playtime(59) == fixture.format.playtime_59
			and Slots.format_playtime(3665) == fixture.format.playtime_3665
		),
		"Save-slot playtime formatting matches source"
	)
	check.call(
		(
			Slots.format_time(0) == fixture.format.time_0
			and Slots.format_time(125) == fixture.format.time_125
		),
		"Save-slot match-time formatting matches source"
	)
	check.call(
		(
			Slots.format_last_played(0.0, 1_700_000_125.0) == fixture.format.last_zero
			and (
				Slots.format_last_played(1_700_000_000.0, 1_700_000_125.0)
				== fixture.format.last_125
			)
		),
		"Save-slot relative time formatting matches source"
	)
	Slots.set_current_slot(1)
	_cleanup()


func _check_info(actual: Dictionary, expected: Dictionary, check: Callable, label: String) -> void:
	for field in expected:
		check.call(
			_value_matches(actual.get(field), expected[field]),
			"Save-slot %s metadata field %s" % [label, field]
		)
	check.call(not bool(actual.get("corrupt", true)), "Save-slot %s is healthy" % label)


func _value_matches(actual: Variant, expected: Variant) -> bool:
	if (actual is int or actual is float) and (expected is int or expected is float):
		return is_equal_approx(float(actual), float(expected))
	if actual is Array and expected is Array:
		if actual.size() != expected.size():
			return false
		for index in range(actual.size()):
			if not _value_matches(actual[index], expected[index]):
				return false
		return true
	if actual is Dictionary and expected is Dictionary:
		if actual.size() != expected.size():
			return false
		for key in expected:
			if not actual.has(key) or not _value_matches(actual[key], expected[key]):
				return false
		return true
	return actual == expected


func _cleanup() -> void:
	for slot in range(1, Slots.SLOT_COUNT + 1):
		Slots.delete_slot(slot, TEMPLATE)
	for suffix in ["", ".tmp", ".bak", ".migrated"]:
		if FileAccess.file_exists(LEGACY + suffix):
			DirAccess.remove_absolute(LEGACY + suffix)
