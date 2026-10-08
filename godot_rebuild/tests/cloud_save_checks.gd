extends RefCounted

const Codec = preload("res://scripts/match/cloud_save_codec.gd")
const Runtime = preload("res://scripts/match/cloud_save_runtime.gd")
const Slots = preload("res://scripts/match/save_slot_store.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const GameSpeedStore = preload("res://scripts/simulation/game_speed_store.gd")
const FIXTURE_PATH := "res://tests/fixtures/cloud_save_source.json"
const TEST_DIR := "user://cloud_save_checks"
const SLOT_TEMPLATE := TEST_DIR + "/slot_%d.json"
const SPEED_PATH := TEST_DIR + "/game_speed.json"


func run(check: Callable) -> void:
	var fixture_variant: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	check(fixture_variant is Dictionary, "cloud source oracle fixture parses")
	if not fixture_variant is Dictionary:
		return
	var fixture: Dictionary = fixture_variant
	check(fixture.payload_magic == Codec.PAYLOAD_MAGIC, "cloud payload magic matches Python source")
	check(
		int(fixture.payload_version) == Codec.PAYLOAD_VERSION,
		"cloud payload version matches Python source"
	)
	check(fixture.cloud_magic == Codec.CLOUD_MAGIC, "cloud envelope magic matches Python source")
	check(
		int(fixture.cloud_version) == Codec.CLOUD_VERSION,
		"cloud envelope version matches Python source"
	)
	check(int(fixture.slot_count) == Slots.SLOT_COUNT, "cloud slot count matches native slots")
	for case in fixture.cases:
		var parsed := Codec.parse_payload(String(case.payload_json))
		var expected_error := "" if case.expected_error == null else String(case.expected_error)
		check(String(parsed.error) == expected_error, "cloud source fixture parse result")
		if parsed.payload is Dictionary:
			var payload: Dictionary = parsed.payload
			check(
				Codec.compute_checksum(payload) == String(case.expected_checksum),
				"cloud SHA-256 matches source fixture"
			)
			var summary := Codec.get_payload_summary(payload)
			for key in ["highest_level", "meta_gold", "slot_count", "exported_at", "newest_played"]:
				check(
					summary.get(key) == case.summary.get(key),
					"cloud summary field %s matches source" % key
				)
	for invalid_case in fixture.invalid:
		var invalid_result := Codec.parse_payload(String(invalid_case.payload_json))
		check(
			String(invalid_result.error) == String(invalid_case.expected_error),
			"cloud parser rejects source invalid case %s" % invalid_case.label
		)

	var valid_result := Codec.parse_payload(String(fixture.cases[0].payload_json))
	var valid_payload: Dictionary = valid_result.payload
	var wrong_magic := valid_payload.duplicate(true)
	wrong_magic["magic"] = "NOT_MYSTIC_ARENA"
	check(
		(
			Codec.parse_payload(JSON.stringify(wrong_magic)).error
			== fixture.expected_errors.wrong_magic
		),
		"cloud parser rejects foreign magic before checksum"
	)
	var wrong_version := valid_payload.duplicate(true)
	wrong_version["version"] = Codec.PAYLOAD_VERSION + 1
	check(
		(
			Codec.parse_payload(JSON.stringify(wrong_version)).error
			== fixture.expected_errors.wrong_version
		),
		"cloud parser rejects unsupported version"
	)
	var no_slots := {
		"magic": Codec.PAYLOAD_MAGIC,
		"version": Codec.PAYLOAD_VERSION,
		"exported_at": 0,
		"slots": {},
		"settings": {},
	}
	no_slots["checksum"] = Codec.compute_checksum(no_slots)
	check(
		Codec.parse_payload(JSON.stringify(no_slots)).error == fixture.expected_errors.empty_slots,
		"cloud parser rejects empty slot maps"
	)
	var bad_checksum := valid_payload.duplicate(true)
	bad_checksum["checksum"] = "0".repeat(64)
	check(
		(
			Codec.parse_payload(JSON.stringify(bad_checksum)).error
			== fixture.expected_errors.bad_checksum
		),
		"cloud parser rejects checksum tampering"
	)
	var envelope := {
		"magic": Codec.CLOUD_MAGIC,
		"version": Codec.CLOUD_VERSION,
		"payload": valid_payload,
	}
	check(
		Codec.validate_envelope(envelope).payload is Dictionary,
		"cloud envelope accepts a validated Python-compatible payload"
	)
	envelope["magic"] = "OTHER_CLOUD"
	check(Codec.validate_envelope(envelope).payload == null, "cloud envelope rejects foreign data")

	_clear_native_test_files()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(TEST_DIR))
	var native_state := Slots.empty_state(1700000000.0)
	native_state["meta_gold"] = 240
	native_state["completed_levels"] = [1, 2]
	check(
		ProgressStore.save_state(native_state, Slots.slot_path(1, SLOT_TEMPLATE)),
		"cloud native payload test writes isolated Godot slot"
	)
	check(
		GameSpeedStore.save_speed(1.5, SPEED_PATH, false),
		"cloud native settings fixture saves atomically"
	)
	var runtime := Runtime.new()
	check(
		runtime.configure_native_paths(SLOT_TEMPLATE, SPEED_PATH),
		"cloud manager accepts native test paths"
	)
	var native_payload: Dictionary = runtime._build_payload()
	check(native_payload.slots.has("1"), "cloud payload extracts state from native slot envelope")
	check(
		native_payload.settings.get("game_speed") == 1.5,
		"cloud payload maps persisted Godot game speed"
	)
	check(
		Codec.parse_payload(JSON.stringify(native_payload)).payload is Dictionary,
		"cloud payload produced from native saves passes checksum validation"
	)
	check(
		runtime._validate_restore_target(native_payload).ok,
		"cloud restore prevalidates a native save"
	)

	var corrupt := FileAccess.open(Slots.slot_path(2, SLOT_TEMPLATE), FileAccess.WRITE)
	corrupt.store_string("not valid slot json")
	corrupt.close()
	check(
		not runtime._validate_restore_target(native_payload).ok,
		"cloud restore refuses to overwrite a corrupt local slot"
	)
	_clear_native_test_files()
	runtime.free()


func _clear_native_test_files() -> void:
	for slot in range(1, Slots.SLOT_COUNT + 1):
		Slots.delete_slot(slot, SLOT_TEMPLATE)
	for path in [SPEED_PATH, SPEED_PATH + ".tmp", SPEED_PATH + ".bak"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	if DirAccess.open(TEST_DIR) != null:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_DIR))
