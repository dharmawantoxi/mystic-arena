extends RefCounted
## Native tests for the atomic source visual-preference store.

const Store = preload("res://scripts/settings/presentation_settings_store.gd")
const TEST_PATH := "user://arena_presentation_settings_test.json"
const BAD_PATH := "user://arena_presentation_settings_bad.json"
const GUARDED_PATH := "user://arena_presentation_settings_guarded.json"


func run(check: Callable) -> void:
	_cleanup(TEST_PATH)
	_cleanup(BAD_PATH)
	_cleanup(GUARDED_PATH)
	check.call(
		Store.load_settings(TEST_PATH) == {"screen_shake": false, "damage_numbers": true},
		"Missing visual preferences use source defaults"
	)
	check.call(
		(
			Store.decode_settings('{"version":1,"screen_shake":true,"damage_numbers":false}')
			== {"screen_shake": true, "damage_numbers": false}
		),
		"The versioned preference decoder accepts both boolean toggles"
	)
	check.call(
		Store.decode_settings('{"version":2}') == {}, "Unknown preference versions are rejected"
	)
	check.call(
		Store.decode_settings('{"version":1,"screen_shake":1,"damage_numbers":false}') == {},
		"Preference values must be actual booleans"
	)
	var selected := {"screen_shake": true, "damage_numbers": false}
	check.call(Store.save_settings(selected, TEST_PATH), "Valid preferences save atomically")
	check.call(Store.load_settings(TEST_PATH) == selected, "Saved visual preferences round-trip")
	check.call(
		(
			not FileAccess.file_exists(TEST_PATH + ".tmp")
			and not FileAccess.file_exists(TEST_PATH + ".bak")
		),
		"The completed preference transaction leaves no backup or stale temporary"
	)
	_write(BAD_PATH, "{corrupt")
	check.call(
		Store.load_settings(BAD_PATH) == {"screen_shake": false, "damage_numbers": true},
		"Corrupt preferences fall back to defaults"
	)
	check.call(
		not Store.save_settings(selected, BAD_PATH), "Corrupt preferences are never overwritten"
	)
	check.call(
		FileAccess.get_file_as_string(BAD_PATH) == "{corrupt",
		"Corrupt bytes are preserved for recovery"
	)
	_write(GUARDED_PATH + ".bak", "backup")
	check.call(
		not Store.save_settings(selected, GUARDED_PATH),
		"An outstanding recovery backup blocks writes"
	)
	_cleanup(TEST_PATH)
	_cleanup(BAD_PATH)
	_cleanup(GUARDED_PATH)


func _write(path: String, value: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(value)
		file.close()


func _cleanup(path: String) -> void:
	for suffix in ["", ".tmp", ".bak"]:
		var target: String = path + String(suffix)
		if FileAccess.file_exists(target):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(target))
