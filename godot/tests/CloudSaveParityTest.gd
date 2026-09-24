extends Node

## Headless integration test for Godot's checksum/parser/transaction/provider
## adapter. The fixture is generated from mobile/cloud_save.py by
## tools/test_godot_cloud_save_parity.py.
const FIXTURE := "res://tests/fixtures/cloud_save_parity.json"

class FakeCloudBridge:
	extends RefCounted

	var status_json := ""
	var upload_path := ""
	var upload_raw := ""
	var download_path := ""
	var download_envelope_json := ""

	func initializeBridge() -> bool:
		return true

	func isAvailable() -> bool:
		return true

	func isSignedIn() -> bool:
		return true

	func checkAuthAsync(op_id: String) -> void:
		_complete(op_id, "check")

	func signInAsync(op_id: String) -> void:
		_complete(op_id, "signin")

	func uploadAsync(path: String, op_id: String) -> void:
		upload_path = path
		upload_raw = FileAccess.get_file_as_string(path)
		_complete(op_id, "upload")

	func downloadAsync(path: String, op_id: String) -> void:
		download_path = path
		var file := FileAccess.open(path, FileAccess.WRITE)
		if file != null:
			file.store_string(download_envelope_json)
			file.close()
		_complete(op_id, "download")

	func readStatusJson() -> String:
		return status_json

	func _complete(op_id: String, kind: String) -> void:
		status_json = JSON.stringify({
			"op_id": op_id,
			"kind": kind,
			"ok": true,
			"code": 0,
			"message": "ok",
			"file_path": download_path if kind == "download" else "",
			"signed_in": true,
			"ts": 1700000000000,
		})


var _checks := 0
var _failures := 0
var _saved_data: Dictionary = {}
var _saved_slot := 1
var _slot_before: Dictionary = {}
var _download_result: Dictionary = {}
var _fake: FakeCloudBridge


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		printerr("[CloudSaveParityTest] FAIL: ", message)


func _run() -> void:
	_saved_data = SaveManager.data.duplicate(true)
	_saved_slot = SaveManager.get_current_slot()
	for slot_num in range(1, SaveManager.NUM_SLOTS + 1):
		var path := SaveManager.slot_path(slot_num)
		if FileAccess.file_exists(path):
			_slot_before[path] = FileAccess.get_file_as_string(path)
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))

	var fixture_value: Variant = JSON.parse_string(
		FileAccess.get_file_as_string(FIXTURE))
	_expect(fixture_value is Dictionary, "fixture JSON valid")
	if not (fixture_value is Dictionary):
		_finish()
		return
	var cases: Array = fixture_value.get("cases", [])
	_expect(cases.size() >= 2, "fixture includes numeric + minimal payload cases")
	if cases.size() < 2:
		_finish()
		return

	var first: Dictionary = cases[0]
	var payload_json := str(first.get("payload_json", ""))
	var parsed_result := CloudSaveManager.parse_payload(payload_json)
	_expect(parsed_result.get("payload") is Dictionary,
		"Pygame payload/checksum accepted by Godot: " +
		str(parsed_result.get("error", "unknown error")))
	if not (parsed_result.get("payload") is Dictionary):
		var typed_result: Dictionary = CloudSaveManager._parse_json_typed(payload_json)
		var typed_payload: Variant = typed_result.get("value")
		if typed_payload is Dictionary:
			var debug_body: Dictionary = typed_payload.duplicate(true)
			debug_body.erase("checksum")
			print("[CloudSaveParityTest] expected checksum: ",
				str(first.get("expected_checksum", "")))
			print("[CloudSaveParityTest] actual checksum: ",
				CloudSaveManager.compute_checksum(typed_payload))
			print("[CloudSaveParityTest] expected canonical: ",
				str(first.get("expected_canonical", "")))
			print("[CloudSaveParityTest] actual canonical: ",
				CloudSaveManager.canonical_json(debug_body))
		_finish()
		return
	var payload: Dictionary = parsed_result["payload"]
	_expect(CloudSaveManager.compute_checksum(payload) ==
		str(first["expected_checksum"]), "SHA-256 checksum matches Python oracle")
	var body := payload.duplicate(true)
	body.erase("checksum")
	_expect(CloudSaveManager.canonical_json(body) ==
		str(first["expected_canonical"]), "canonical JSON matches Python oracle")
	var numeric_slot: Dictionary = payload["slots"]["1"]
	_expect(numeric_slot["integer_value"] is int,
		"JSON integer token remains integer (not float)")
	_expect(numeric_slot["float_value"] is float,
		"JSON float token remains float (not integer)")
	_expect(numeric_slot["completed_levels"][2] is float,
		"mixed integer/float arrays retain Python number types")
	_expect(numeric_slot["profile"] == "Naga \"Áruna\"\\東\nline",
		"Unicode, quotes, slash and escaped newline survive parsing")
	_expect(numeric_slot["control_text"] == "tab\t vertical\u000b",
		"Python-compatible JSON escapes nonstandard control characters")

	var second: Dictionary = cases[1]
	var second_result := CloudSaveManager.parse_payload(
		str(second.get("payload_json", "")))
	_expect(second_result.get("payload") is Dictionary,
		"minimal payload accepted by Godot")
	_expect(CloudSaveManager.parse_payload("{").get("payload") == null,
		"invalid JSON rejected")

	_fake = FakeCloudBridge.new()
	_fake.download_envelope_json = _make_envelope(
		str(first.get("payload_json", "")))
	CloudSaveManager.use_bridge_for_testing(_fake, true, true)

	# Upload must leave local payload intact and clean its transient file after
	# the fake Java bridge reports completion.
	CloudSaveManager.upload_payload(payload)
	_expect(CloudSaveManager.busy(), "upload starts asynchronously")
	_expect(not _fake.upload_raw.is_empty(), "bridge received upload envelope")
	var uploaded: Variant = JSON.parse_string(_fake.upload_raw)
	_expect(uploaded is Dictionary and
			str(uploaded.get("payload", {}).get("checksum", "")) ==
			str(first["expected_checksum"]),
		"uploaded envelope carries checksum-verified payload")
	var upload_path := _fake.upload_path
	CloudSaveManager.poll()
	_expect(not CloudSaveManager.busy(), "upload poll completes operation")
	_expect(not upload_path.is_empty() and not FileAccess.file_exists(upload_path),
		"upload temporary file removed after completion")

	# Download exercises the same native JSON file protocol and must not apply
	# anything before the user confirms the restore.
	CloudSaveManager.download_payload(
		_on_download_complete, false)
	_expect(CloudSaveManager.busy(), "download starts asynchronously")
	var download_path := _fake.download_path
	CloudSaveManager.poll()
	_expect(bool(_download_result.get("ok", false)),
		"download callback receives validated payload")
	_expect(_download_result.get("payload") is Dictionary,
		"download result includes parsed payload")
	_expect(CloudSaveManager.all_slots_empty(),
		"download without apply does not overwrite local slots")
	_expect(not download_path.is_empty() and
			not FileAccess.file_exists(download_path),
		"download temporary file removed after completion")

	# Restore replaces the current working copy only after an explicit call,
	# adapts Pygame's purchased_heroes/settings schema and keeps other engine
	# globals in sync.
	var local_slot := SaveManager.slot_path(2)
	_write_json(local_slot, {"completed_levels": [99], "meta_gold": 999})
	var applied := CloudSaveManager.apply_payload(
		_download_result["payload"])
	_expect(bool(applied.get("ok", false)), "transactional restore succeeds")
	_expect(FileAccess.file_exists(SaveManager.slot_path(1)) and
			FileAccess.file_exists(SaveManager.slot_path(3)),
		"restored cloud slots installed")
	_expect(not FileAccess.file_exists(local_slot),
		"slot missing from cloud snapshot is cleared")
	_expect(SaveManager.data.get("unlocked_heroes", []).has("kaizen"),
		"Pygame purchased_heroes adapted to Godot unlocked_heroes")
	_expect(is_equal_approx(
			SaveManager.get_setting("master", 0.0), 0.7),
		"global Pygame master-volume setting mapped into slot data")
	_expect(GameManager.difficulty == "hard",
		"difficulty restored into GameManager")

	# Invalid data is rejected before staging and leaves installed save bytes
	# untouched.
	var slot_one_path := SaveManager.slot_path(1)
	var slot_one_before := FileAccess.get_file_as_string(slot_one_path)
	var invalid_payload: Dictionary = _download_result["payload"].duplicate(true)
	invalid_payload["checksum"] = "invalid"
	var invalid_result := CloudSaveManager.apply_payload(invalid_payload)
	_expect(not bool(invalid_result.get("ok", false)),
		"checksum mismatch blocks restore")
	_expect(FileAccess.get_file_as_string(slot_one_path) == slot_one_before,
		"rejected restore leaves local data untouched")

	_finish()


func _make_envelope(payload_json: String) -> String:
	return ("{\"magic\":\"MYSTIC_ARENA_CLOUD\",\"version\":1," +
		"\"exported_at\":1700000000,\"payload\":" + payload_json + "}")


func _on_download_complete(result: Dictionary) -> void:
	_download_result = result.duplicate(true)


func _write_json(path: String, value: Variant) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		_expect(false, "test could not write " + path)
		return
	file.store_string(JSON.stringify(value, "\t", false, true))
	file.close()


func _finish() -> void:
	CloudSaveManager.dismiss_restore_prompt()
	for slot_num in range(1, SaveManager.NUM_SLOTS + 1):
		var path := SaveManager.slot_path(slot_num)
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
		if _slot_before.has(path):
			_write_json_raw(path, str(_slot_before[path]))
	SaveManager.data = _saved_data
	SaveManager.set_current_slot(_saved_slot)
	print("[CloudSaveParityTest] %s: %d checks, %d failures" % [
		"PASS" if _failures == 0 else "FAIL", _checks, _failures])
	get_tree().quit(0 if _failures == 0 else 1)


func _write_json_raw(path: String, value: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(value)
		file.close()
