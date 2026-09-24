# CloudSaveManager.gd — Google Play Games Saved Games (Snapshots).
#
# Arsitektur Godot:
#   SaveManager (working copy user://) <-> CloudSaveManager <-> MysticCloudSave
#   Android plugin -> CloudSaveBridge.java -> Play Games Services v2.
#
# Tanpa Android / plugin / Project ID Play Games, semua jalur cloud menjadi
# no-op yang aman. Save lokal tidak pernah dihapus saat cloud tidak tersedia.
extends Node

signal state_changed(available: bool, signed_in: bool, busy: bool)
signal status_changed(ok: bool, message: String)
signal operation_completed(result: Dictionary)
signal restore_found(payload: Dictionary, summary: Dictionary)

const PLUGIN_NAME := "MysticCloudSave"
const CLOUD_SAVE_CODEC := preload("res://scripts/utils/CloudSaveCodec.gd")
const CLOUD_MAGIC := "MYSTIC_ARENA_CLOUD"
const CLOUD_VERSION := 1
const PAYLOAD_MAGIC := "MYSTIC_ARENA_BACKUP"
const PAYLOAD_VERSION := 1
const NUM_SLOTS := 3
const SNAPSHOT_NAME := "mystic_arena_main"
const POLL_INTERVAL_MS := 150
const CLOUD_DIR := "user://mystic_cloud"
const RESTORE_DIR := "user://.cloud_restore"

var pending_restore: Dictionary = {}
var _bridge: Variant = null
var _inited := false
var _available := false
var _signed_in := false
var _busy := false
var _op_id := ""
var _op_kind := ""
var _op_callback: Callable = Callable()
var _op_aux: Dictionary = {}
var _seen_ops: Dictionary = {}
var _op_counter := 0
var _last_poll_ms := 0
var _last_message := "Cloud save: hanya tersedia di Android + Google Play Games"
var _last_ok := false
var _auto_restore_checked := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_process(true)
	# Autoload SaveManager harus selesai membaca slot lebih dulu.
	call_deferred("start")


func _process(_delta: float) -> void:
	if not _inited or _bridge == null:
		return
	var now := Time.get_ticks_msec()
	if now - _last_poll_ms < POLL_INTERVAL_MS:
		return
	_last_poll_ms = now
	poll()


# ══════════════════════════════════════════════════════════
#  PUBLIC STATE / STARTUP
# ══════════════════════════════════════════════════════════

func available() -> bool:
	return _available


func signed_in() -> bool:
	return _signed_in


func busy() -> bool:
	return _busy


func last_message() -> String:
	return _last_message


func last_ok() -> bool:
	return _last_ok


func start() -> bool:
	if _inited:
		return _available
	_inited = true
	if OS.get_environment("MYSTIC_CLOUD_SAVE") == "0":
		_set_status(true, "Cloud save dimatikan (MYSTIC_CLOUD_SAVE=0)")
		return false
	if not Engine.has_singleton(PLUGIN_NAME):
		_set_status(false, "Cloud hanya aktif di Android + Google Play Games")
		return false

	_bridge = Engine.get_singleton(PLUGIN_NAME)
	if _bridge == null:
		_set_status(false, "Plugin cloud save tidak dapat dimuat")
		return false
	var initialized := bool(_bridge.initializeBridge())
	var classpath_available := bool(_bridge.isAvailable())
	_signed_in = bool(_bridge.isSignedIn())
	_available = initialized and classpath_available
	_emit_state()
	if _available:
		_set_status(true, "Cloud save siap (Google Play Games)")
		check_auth()
	else:
		var native_status := _read_native_status()
		var message := str(native_status.get("message", ""))
		_set_status(false, message if not message.is_empty() else
			"Cloud belum tersedia — cek Play Games / Project ID")
	return _available


## Status auto-upload dipanggil setelah SaveManager menyelesaikan write lokal.
## Cloud gagal / sibuk tidak pernah membatalkan save lokal.
func auto_upload() -> bool:
	if not _inited:
		start()
	if not _available or not _signed_in or _busy:
		return false
	var payload: Variant = build_payload()
	if not (payload is Dictionary) or payload.is_empty():
		return false
	upload_payload(payload)
	return _busy


func check_auth(callback: Callable = Callable()) -> void:
	if not _ready_for_operation("check", callback):
		return
	var id := _start_op("check", callback)
	if id.is_empty():
		return
	_bridge.checkAuthAsync(id)


func sign_in(callback: Callable = Callable()) -> void:
	if not _ready_for_operation("signin", callback):
		return
	var id := _start_op("signin", callback)
	if id.is_empty():
		return
	_bridge.signInAsync(id)


func upload_payload(payload: Dictionary, callback: Callable = Callable()) -> void:
	if not _ready_for_operation("upload", callback):
		return
	if not _signed_in:
		_deliver_immediate(callback, _err_result("upload", 4,
			"Masuk ke Google Play Games dulu"))
		return
	var payload_slots: Variant = payload.get("slots", {})
	var payload_settings: Variant = payload.get("settings", {})
	var has_slots := payload_slots is Dictionary and not payload_slots.is_empty()
	var has_settings := payload_settings is Dictionary and not payload_settings.is_empty()
	if payload.is_empty() or (not has_slots and not has_settings):
		_deliver_immediate(callback, _err_result("upload", 5,
			"Tidak ada save untuk diunggah"))
		return
	var validation := _validate_payload(payload)
	if not bool(validation.get("ok", false)):
		_deliver_immediate(callback, _err_result("upload", 5,
			str(validation.get("error", "Payload save tidak sah"))))
		return

	var id := _start_op("upload", callback)
	if id.is_empty():
		return
	var path := _operation_path("upload", id)
	_op_aux = {"file": path, "delete": true}
	var envelope := {
		"magic": CLOUD_MAGIC,
		"version": CLOUD_VERSION,
		"exported_at": Time.get_unix_time_from_system(),
		"payload": payload,
	}
	if not _write_json(path, envelope):
		_fail_op("upload", id, 6, "File upload cloud tidak dapat ditulis")
		return
	_bridge.uploadAsync(ProjectSettings.globalize_path(path), id)


func download_payload(callback: Callable = Callable(), apply: bool = false) -> void:
	if not _ready_for_operation("download", callback):
		return
	if not _signed_in:
		_deliver_immediate(callback, _err_result("download", 7,
			"Masuk ke Google Play Games dulu"))
		return
	var id := _start_op("download", callback)
	if id.is_empty():
		return
	var path := _operation_path("download", id)
	_op_aux = {"file": path, "apply": apply, "delete": true}
	_bridge.downloadAsync(ProjectSettings.globalize_path(path), id)


func all_slots_empty() -> bool:
	for slot_num in range(1, NUM_SLOTS + 1):
		if FileAccess.file_exists(SaveManager.slot_path(slot_num)):
			return false
	return true


func dismiss_restore_prompt() -> void:
	pending_restore.clear()


# ══════════════════════════════════════════════════════════
#  PAYLOAD (format kompatibel dengan mobile/cloud_save.py)
# ══════════════════════════════════════════════════════════

func build_payload() -> Variant:
	var slots: Dictionary = {}
	for slot_num in range(1, NUM_SLOTS + 1):
		var path := SaveManager.slot_path(slot_num)
		if not FileAccess.file_exists(path):
			continue
		var parsed := _read_json_typed(path)
		if bool(parsed.get("ok", false)) and parsed.get("value") is Dictionary:
			slots[str(slot_num)] = parsed["value"]
		else:
			push_warning("[CloudSaveManager] Slot %d unreadable; skipped" % slot_num)
	if slots.is_empty():
		return null

	var payload := {
		"magic": PAYLOAD_MAGIC,
		"version": PAYLOAD_VERSION,
		"exported_at": Time.get_unix_time_from_system(),
		"slots": slots,
		"settings": _export_settings(),
	}
	payload["checksum"] = compute_checksum(payload)
	return payload


func compute_checksum(payload: Dictionary) -> String:
	var body := payload.duplicate(true)
	body.erase("checksum")
	var context := HashingContext.new()
	if context.start(HashingContext.HASH_SHA256) != OK:
		return ""
	context.update(canonical_json(body).to_utf8_buffer())
	return context.finish().hex_encode()


## JSON kanonis seperti json.dumps(sort_keys=True, separators=(",", ":"),
## ensure_ascii=False) di Python. Parser cloud di bawah mempertahankan
## token integer vs float; tanpa itu checksum akan berubah setelah parse Godot.
func canonical_json(value: Variant) -> String:
	return CLOUD_SAVE_CODEC.canonical_json(value)


func parse_payload(text: String) -> Dictionary:
	var decoded := _parse_json_typed(text)
	if not bool(decoded.get("ok", false)):
		return {"payload": null, "error": "File corrupt (not valid JSON)"}
	var payload: Variant = decoded.get("value")
	if not (payload is Dictionary):
		return {"payload": null, "error": "File corrupt (unexpected structure)"}
	if payload.get("magic") != PAYLOAD_MAGIC:
		return {"payload": null, "error": "Not a Mystic Arena save file"}
	var raw_version: Variant = payload.get("version", 0)
	if not (raw_version is int or raw_version is float):
		return {"payload": null, "error": "File corrupt (bad version)"}
	var version := int(raw_version)
	if version < 1 or version > PAYLOAD_VERSION:
		return {"payload": null,
			"error": "Save version %s not supported" % str(raw_version)}
	if not (payload.get("slots") is Dictionary) or payload["slots"].is_empty():
		return {"payload": null, "error": "Save contains no data"}
	if str(payload.get("checksum", "")) != compute_checksum(payload):
		return {"payload": null, "error": "File corrupt (checksum mismatch)"}
	return {"payload": payload, "error": null}


func get_payload_summary(payload: Dictionary) -> Dictionary:
	var highest_level := 0
	var best_gold := 0
	var newest_played := 0.0
	var slots: Dictionary = payload.get("slots", {})
	for slot_data in slots.values():
		if not (slot_data is Dictionary):
			continue
		var completed: Variant = slot_data.get("completed_levels", [])
		if completed is Array:
			for level in completed:
				highest_level = maxi(highest_level, int(level))
		best_gold = maxi(best_gold, int(slot_data.get("meta_gold", 0)))
		newest_played = maxf(newest_played,
			float(slot_data.get("slot_last_played", 0.0)))
	return {
		"highest_level": highest_level,
		"meta_gold": best_gold,
		"slot_count": slots.size(),
		"exported_at": float(payload.get("exported_at", 0.0)),
		"newest_played": newest_played,
	}


## Stage all files before replacing any slot. Existing files are moved to a
## same-filesystem backup and restored if a later rename fails.
func apply_payload(payload: Dictionary) -> Dictionary:
	var validation := _validate_payload(payload)
	if not bool(validation.get("ok", false)):
		return {"ok": false, "error": str(validation.get("error", "Payload tidak sah"))}
	var cloud_slots: Dictionary = payload.get("slots", {})
	var raw_settings: Variant = payload.get("settings", {})
	var cloud_settings: Dictionary = raw_settings if raw_settings is Dictionary else {}
	if not _prepare_restore_dir():
		return {"ok": false, "error": "Folder restore tidak dapat dibuat"}

	var staged: Dictionary = {}
	for slot_num in range(1, NUM_SLOTS + 1):
		var key := str(slot_num)
		if not cloud_slots.has(key):
			continue
		var raw_slot: Variant = cloud_slots[key]
		if not (raw_slot is Dictionary):
			_clear_restore_dir()
			return {"ok": false, "error": "Slot %d cloud rusak" % slot_num}
		var slot_data: Dictionary = raw_slot.duplicate(true)
		_adapt_slot_data(slot_data, cloud_settings)
		var stage_path := "%s/slot_%d.new" % [RESTORE_DIR, slot_num]
		if not _write_json(stage_path, slot_data):
			_clear_restore_dir()
			return {"ok": false, "error": "Slot %d tidak dapat ditulis" % slot_num}
		staged[slot_num] = stage_path

	var backups: Dictionary = {}
	var installed: Dictionary = {}
	for slot_num in range(1, NUM_SLOTS + 1):
		var target := SaveManager.slot_path(slot_num)
		if FileAccess.file_exists(target):
			var backup := "%s/slot_%d.bak" % [RESTORE_DIR, slot_num]
			if not _rename_user_file(target, backup):
				_rollback_restore(installed, backups)
				return {"ok": false, "error": "Slot %d lama tidak dapat diamankan" % slot_num}
			backups[slot_num] = backup
		if staged.has(slot_num):
			if not _rename_user_file(str(staged[slot_num]), target):
				_rollback_restore(installed, backups)
				return {"ok": false, "error": "Slot %d cloud tidak dapat dipasang" % slot_num}
			installed[slot_num] = true

	for backup_path in backups.values():
		_remove_user_file(str(backup_path))
	_clear_restore_dir()

	SaveManager.load_save()
	# Python stores settings globally, while this Godot port keeps them per
	# slot. If the active slot is absent from the snapshot, preserve the cloud
	# preferences in memory for the current session; the next regular save
	# persists them without inventing a progress slot during restore.
	if not cloud_settings.is_empty() and not SaveManager.slot_exists(
			SaveManager.get_current_slot()):
		var active_settings: Variant = SaveManager.data.get("settings", {})
		var merged_settings: Dictionary = active_settings.duplicate(true) \
			if active_settings is Dictionary else {}
		merged_settings.merge(_import_settings(cloud_settings), true)
		SaveManager.data["settings"] = merged_settings
	_apply_runtime_settings(cloud_settings)
	print("[CloudSaveManager] Restore selesai (%d slot)" % cloud_slots.size())
	return {"ok": true, "error": ""}


# ══════════════════════════════════════════════════════════
#  STATUS FILE POLLING (bridge async)
# ══════════════════════════════════════════════════════════

func poll() -> void:
	var status := _read_native_status()
	if status.is_empty():
		return
	var id := str(status.get("op_id", ""))
	if id.is_empty():
		return
	if status.has("signed_in"):
		var now_signed := bool(status.get("signed_in", false))
		if now_signed != _signed_in:
			_signed_in = now_signed
			_emit_state()
	if _seen_ops.has(id):
		return
	_seen_ops[id] = true
	if _seen_ops.size() > 32:
		_seen_ops.clear()
		_seen_ops[id] = true
	if not _busy or id != _op_id:
		return

	var kind := _op_kind
	var callback := _op_callback
	var aux := _op_aux
	_busy = false
	_op_id = ""
	_op_kind = ""
	_op_callback = Callable()
	_op_aux = {}
	_emit_state()
	_dispatch_result(kind, status, callback, aux)


# ══════════════════════════════════════════════════════════
#  TEST SEAM — same provider contract, fake used in headless tests.
# ══════════════════════════════════════════════════════════

func use_bridge_for_testing(bridge: Variant, is_available: bool = true,
		is_signed_in: bool = true) -> void:
	_bridge = bridge
	_inited = true
	_available = is_available
	_signed_in = is_signed_in
	_busy = false
	_op_id = ""
	_op_kind = ""
	_op_callback = Callable()
	_op_aux = {}
	_seen_ops.clear()
	_auto_restore_checked = true
	_last_poll_ms = 0
	_emit_state()


# ══════════════════════════════════════════════════════════
#  INTERNALS
# ══════════════════════════════════════════════════════════

func _ready_for_operation(kind: String, callback: Callable) -> bool:
	if not _inited:
		start()
	if not _available or _bridge == null:
		_deliver_immediate(callback, _err_result(kind, 1, _last_message))
		return false
	return true


func _start_op(kind: String, callback: Callable) -> String:
	if _busy:
		_deliver_immediate(callback, _err_result(kind, 9,
			"Operasi cloud lain sedang berjalan"))
		return ""
	_op_counter += 1
	var id := "op-%s-%d-%d" % [kind, Time.get_ticks_msec(), _op_counter]
	_busy = true
	_op_id = id
	_op_kind = kind
	_op_callback = callback
	_op_aux = {}
	_emit_state()
	return id


func _fail_op(kind: String, id: String, code: int, message: String) -> void:
	if id != _op_id:
		return
	var callback := _op_callback
	var aux := _op_aux
	_busy = false
	_op_id = ""
	_op_kind = ""
	_op_callback = Callable()
	_op_aux = {}
	_emit_state()
	_set_status(false, message)
	var result := _err_result(kind, code, message)
	operation_completed.emit(result)
	if callback.is_valid():
		callback.call(result)
	_cleanup_aux(aux)


func _dispatch_result(kind: String, status: Dictionary,
		callback: Callable, aux: Dictionary) -> void:
	var ok := bool(status.get("ok", false))
	var code := int(status.get("code", 0))
	var message := str(status.get("message", ""))
	if status.has("signed_in"):
		_signed_in = bool(status.get("signed_in", false))
		_emit_state()
	if not ok:
		_set_status(false, message)
		var failed := _err_result(kind, code, message)
		operation_completed.emit(failed)
		if callback.is_valid():
			callback.call(failed)
		_cleanup_aux(aux)
		return

	if kind == "download":
		_handle_download_ok(aux, callback)
		return
	_set_status(true, message)
	var result := _ok_result(kind, message,
		str(status.get("file_path", "")))
	operation_completed.emit(result)
	if callback.is_valid():
		callback.call(result)
	_cleanup_aux(aux)
	if kind == "check" and not _auto_restore_checked:
		_auto_restore_checked = true
		if _signed_in and all_slots_empty():
			call_deferred("_peek_cloud_restore")


func _handle_download_ok(aux: Dictionary, callback: Callable) -> void:
	var path := str(aux.get("file", ""))
	var result_error := ""
	var payload: Dictionary = {}
	var summary: Dictionary = {}
	if path.is_empty() or not FileAccess.file_exists(path):
		result_error = "File cloud tidak ditemukan"
	else:
		var envelope_result := _read_json_typed(path)
		if not bool(envelope_result.get("ok", false)):
			result_error = "Baca cloud gagal: JSON tidak valid"
		else:
			var envelope: Variant = envelope_result.get("value")
			if not (envelope is Dictionary):
				result_error = "Bukan file cloud Mystic Arena"
			elif envelope.get("magic") != CLOUD_MAGIC:
				result_error = "Bukan file cloud Mystic Arena"
			elif int(envelope.get("version", 0)) > CLOUD_VERSION:
				result_error = "Versi cloud lebih baru dari game"
			elif not (envelope.get("payload") is Dictionary):
				result_error = "Payload cloud rusak"
			else:
				# Envelope JSON has already been parsed with typed number tokens.
				# Re-stringifying here would expand floats to Godot's 17-digit
				# representation and change the Python checksum input.
				var raw_payload: Dictionary = envelope["payload"]
				var validation := _validate_payload(raw_payload)
				if bool(validation.get("ok", false)):
					payload = raw_payload
					summary = get_payload_summary(payload)
				else:
					result_error = str(validation.get("error", "Validasi cloud gagal"))

	if not result_error.is_empty():
		_set_status(false, result_error)
		var failed := _err_result("download", 10, result_error)
		operation_completed.emit(failed)
		if callback.is_valid():
			callback.call(failed)
		_cleanup_aux(aux)
		return

	var apply_now := bool(aux.get("apply", false))
	if apply_now:
		var applied := apply_payload(payload)
		if not bool(applied.get("ok", false)):
			var apply_error := "Terapkan cloud gagal: %s" % str(applied.get("error", "unknown"))
			_set_status(false, apply_error)
			var failed := _err_result("download", 11, apply_error)
			operation_completed.emit(failed)
			if callback.is_valid():
				callback.call(failed)
			_cleanup_aux(aux)
			return
	var success_message := "Cloud restored!" if apply_now else "Cloud save ditemukan"
	_set_status(true, success_message)
	var result := _ok_result("download", success_message, path)
	result["payload"] = payload
	result["summary"] = summary
	operation_completed.emit(result)
	if callback.is_valid():
		callback.call(result)
	_cleanup_aux(aux)


func _peek_cloud_restore() -> void:
	if _busy or not _available or not _signed_in or not all_slots_empty():
		return
	download_payload(_on_restore_peek, false)


func _on_restore_peek(result: Dictionary) -> void:
	if not bool(result.get("ok", false)) or not (result.get("payload") is Dictionary):
		return
	pending_restore = {
		"payload": result["payload"],
		"summary": result.get("summary", {}),
	}
	restore_found.emit(pending_restore["payload"], pending_restore["summary"])


func _read_native_status() -> Dictionary:
	if _bridge == null:
		return {}
	var text := str(_bridge.readStatusJson())
	if text.is_empty():
		return {}
	var parsed: Variant = JSON.parse_string(text)
	return parsed if parsed is Dictionary else {}


func _set_status(ok: bool, message: String) -> void:
	_last_ok = ok
	_last_message = message
	status_changed.emit(ok, message)


func _emit_state() -> void:
	state_changed.emit(_available, _signed_in, _busy)


func _deliver_immediate(callback: Callable, result: Dictionary) -> void:
	_set_status(false, str(result.get("message", "")))
	operation_completed.emit(result)
	if callback.is_valid():
		callback.call(result)


func _ok_result(kind: String, message: String = "", path: String = "") -> Dictionary:
	return {
		"ok": true,
		"kind": kind,
		"code": 0,
		"message": message,
		"payload": null,
		"summary": null,
		"path": path if not path.is_empty() else null,
	}


func _err_result(kind: String, code: int, message: String) -> Dictionary:
	return {
		"ok": false,
		"kind": kind,
		"code": code,
		"message": message,
		"payload": null,
		"summary": null,
		"path": null,
	}


func _operation_path(kind: String, id: String) -> String:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(CLOUD_DIR))
	return "%s/%s_%s.json" % [CLOUD_DIR, kind, id]


func _write_json(path: String, value: Variant) -> bool:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(canonical_json(value))
	var ok := f.get_error() == OK
	f.close()
	return ok


func _read_json_typed(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"ok": false, "value": null}
	return _parse_json_typed(FileAccess.get_file_as_string(path))


## JSON.parse_string Godot 4.3 mengubah semua angka JSON menjadi FLOAT.
## Bungkus token numerik di luar string sebelum parse, lalu pulihkan int/float
## berdasarkan tata bahasa JSON supaya checksum Python/Godot tetap identik.
func _parse_json_typed(text: String) -> Dictionary:
	var marker := "__MYSTIC_JSON_NUMBER_%d_" % absi(hash(text))
	while text.contains(marker):
		marker += "_"
	var output := ""
	var in_string := false
	var escaped := false
	var index := 0
	while index < text.length():
		var ch := text.substr(index, 1)
		if in_string:
			output += ch
			if escaped:
				escaped = false
			elif ch == "\\":
				escaped = true
			elif ch == "\"":
				in_string = false
			index += 1
			continue
		if ch == "\"":
			in_string = true
			output += ch
			index += 1
			continue
		if ch == "-" or _is_digit(ch):
			var end := _json_number_end(text, index)
			if end > index:
				var token := text.substr(index, end - index)
				output += JSON.stringify(marker + token)
				index = end
				continue
		output += ch
		index += 1

	var parsed: Variant = JSON.parse_string(output)
	if parsed == null and text.strip_edges() != "null":
		return {"ok": false, "value": null}
	return {"ok": true, "value": _restore_number_markers(parsed, marker)}


func _json_number_end(text: String, start: int) -> int:
	var i := start
	if text.substr(i, 1) == "-":
		i += 1
	if i >= text.length() or not _is_digit(text.substr(i, 1)):
		return start
	if text.substr(i, 1) == "0":
		i += 1
		if i < text.length() and _is_digit(text.substr(i, 1)):
			return start
	else:
		while i < text.length() and _is_digit(text.substr(i, 1)):
			i += 1
	if i < text.length() and text.substr(i, 1) == ".":
		i += 1
		var decimal_start := i
		while i < text.length() and _is_digit(text.substr(i, 1)):
			i += 1
		if decimal_start == i:
			return start
	if i < text.length() and text.substr(i, 1).to_lower() == "e":
		i += 1
		if i < text.length() and ["+", "-"].has(text.substr(i, 1)):
			i += 1
		var exponent_start := i
		while i < text.length() and _is_digit(text.substr(i, 1)):
			i += 1
		if exponent_start == i:
			return start
	return i


func _restore_number_markers(value: Variant, marker: String) -> Variant:
	if value is String and value.begins_with(marker):
		var token := value.substr(marker.length())
		if token.find(".") < 0 and token.find("e") < 0 and token.find("E") < 0:
			return int(token)
		return float(token)
	if value is Array:
		for i in value.size():
			value[i] = _restore_number_markers(value[i], marker)
	elif value is Dictionary:
		for key in value.keys():
			value[key] = _restore_number_markers(value[key], marker)
	return value


func _is_digit(ch: String) -> bool:
	if ch.is_empty():
		return false
	var code := ch.unicode_at(0)
	return code >= 48 and code <= 57


func _validate_payload(payload: Variant) -> Dictionary:
	if not (payload is Dictionary):
		return {"ok": false, "error": "File corrupt (unexpected structure)"}
	if payload.get("magic") != PAYLOAD_MAGIC:
		return {"ok": false, "error": "Not a Mystic Arena save file"}
	var version: Variant = payload.get("version", 0)
	if not (version is int or version is float):
		return {"ok": false, "error": "File corrupt (bad version)"}
	if int(version) < 1 or int(version) > PAYLOAD_VERSION:
		return {"ok": false,
			"error": "Save version %s not supported" % str(version)}
	if not (payload.get("slots") is Dictionary) or payload["slots"].is_empty():
		return {"ok": false, "error": "Save contains no data"}
	if str(payload.get("checksum", "")) != compute_checksum(payload):
		return {"ok": false, "error": "File corrupt (checksum mismatch)"}
	return {"ok": true, "error": ""}


func _export_settings() -> Dictionary:
	var saved_settings: Variant = SaveManager.data.get("settings", {})
	if not (saved_settings is Dictionary):
		saved_settings = {}
	return {
		"master_volume": float(saved_settings.get("master", 0.7)),
		"sfx_volume": float(saved_settings.get("sfx", 0.6)),
		"bgm_volume": float(saved_settings.get("bgm", 0.35)),
		"voice_volume": float(saved_settings.get("voice", 0.5)),
		"difficulty": str(GameManager.difficulty),
		"screen_shake_enabled": float(saved_settings.get("screen_shake", 1.0)) > 0.5,
		"damage_numbers_enabled": float(saved_settings.get("damage_numbers_enabled", 1.0)) > 0.5,
		"game_speed": float(saved_settings.get("game_speed", 1.0)),
		"fps_limit": float(saved_settings.get("fps_limit", 0.0)),
		"language": str(saved_settings.get("language", GameManager.language)),
	}


func _adapt_slot_data(slot_data: Dictionary, cloud_settings: Dictionary) -> void:
	if not slot_data.has("unlocked_heroes"):
		var heroes: Array = ["kaizen"]
		var purchased: Variant = slot_data.get("purchased_heroes", [])
		if purchased is Array:
			for hero in purchased:
				if hero is String and not heroes.has(hero):
					heroes.append(hero)
		slot_data["unlocked_heroes"] = heroes
	var slot_settings: Variant = slot_data.get("settings", {})
	if (not (slot_settings is Dictionary) or slot_settings.is_empty()) \
			and not cloud_settings.is_empty():
		slot_data["settings"] = _import_settings(cloud_settings)


func _import_settings(settings: Dictionary) -> Dictionary:
	return {
		"master": float(settings.get("master_volume", 0.7)),
		"sfx": float(settings.get("sfx_volume", 0.6)),
		"bgm": float(settings.get("bgm_volume", 0.35)),
		"voice": float(settings.get("voice_volume", 0.5)),
		"screen_shake": 1.0 if bool(settings.get("screen_shake_enabled", false)) else 0.0,
		"damage_numbers_enabled": 1.0 if bool(settings.get("damage_numbers_enabled", true)) else 0.0,
		"game_speed": float(settings.get("game_speed", 1.0)),
		"fps_limit": float(settings.get("fps_limit", 0.0)),
		"language": str(settings.get("language", "id")),
	}


func _apply_runtime_settings(cloud_settings: Dictionary) -> void:
	var language := SaveManager.get_setting_str("language", "id")
	GameManager.apply_language(language)
	AudioManager.apply_settings()
	GameManager.apply_game_speed(SaveManager.get_setting("game_speed", 1.0))
	GameManager.apply_fps_limit(SaveManager.get_setting("fps_limit", 0.0))
	GameManager.set_screen_shake(SaveManager.get_setting("screen_shake", 1.0) > 0.5)
	GameManager.set_damage_numbers(
		SaveManager.get_setting("damage_numbers_enabled", 1.0) > 0.5)
	var difficulty := str(cloud_settings.get("difficulty", ""))
	if ["easy", "normal", "hard"].has(difficulty):
		GameManager.set_difficulty(difficulty)


func _prepare_restore_dir() -> bool:
	var absolute := ProjectSettings.globalize_path(RESTORE_DIR)
	if DirAccess.make_dir_recursive_absolute(absolute) != OK:
		return false
	_clear_restore_dir()
	return true


func _clear_restore_dir() -> void:
	var dir := DirAccess.open(RESTORE_DIR)
	if dir == null:
		return
	for file_name in dir.get_files():
		_remove_user_file("%s/%s" % [RESTORE_DIR, file_name])


func _rename_user_file(from_path: String, to_path: String) -> bool:
	var err := DirAccess.rename_absolute(
		ProjectSettings.globalize_path(from_path),
		ProjectSettings.globalize_path(to_path))
	return err == OK


func _remove_user_file(path: String) -> bool:
	if not FileAccess.file_exists(path):
		return true
	return DirAccess.remove_absolute(ProjectSettings.globalize_path(path)) == OK


func _rollback_restore(installed: Dictionary, backups: Dictionary) -> void:
	for slot_num in range(1, NUM_SLOTS + 1):
		if installed.has(slot_num):
			_remove_user_file(SaveManager.slot_path(slot_num))
	for slot_num in range(1, NUM_SLOTS + 1):
		if backups.has(slot_num):
			var backup := str(backups[slot_num])
			if FileAccess.file_exists(backup) and not _rename_user_file(
					backup, SaveManager.slot_path(slot_num)):
				push_error("[CloudSaveManager] Restore rollback failed for slot %d" % slot_num)
	_clear_restore_dir()


func _cleanup_aux(aux: Dictionary) -> void:
	if bool(aux.get("delete", false)) and aux.has("file"):
		_remove_user_file(str(aux["file"]))


