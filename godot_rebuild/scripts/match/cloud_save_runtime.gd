extends Node
## Google Play Games Saved Games adapter; all paths are Godot user:// storage.

signal status_changed(ok: bool, message: String, available: bool, signed_in: bool, busy: bool)
signal operation_finished(kind: String, ok: bool, message: String)
signal restore_available(payload: Dictionary, summary: Dictionary)
signal restored

const Codec = preload("res://scripts/match/cloud_save_codec.gd")
const Slots = preload("res://scripts/match/save_slot_store.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const GameSpeedStore = preload("res://scripts/simulation/game_speed_store.gd")
const PLUGIN_SINGLETON := "MysticCloudSave"
const POLL_INTERVAL := 0.2
const WORK_DIR_NAME := "mystic_cloud"

var slot_path_template := Slots.PATH_TEMPLATE
var speed_path := GameSpeedStore.PATH
var enabled := true
var available := false
var signed_in := false
var busy := false
var last_ok := true
var last_message := "Cloud save aktif di Android melalui Google Play Games."
var bridge: Object
var work_dir := ""
var status_path := ""
var _operation_id := ""
var _operation_kind := ""
var _operation_file := ""
var _download_apply := false
var _poll_elapsed := 0.0
var _operation_counter := 0
var _restoring := false
var _startup_restore_checked := false
var _pending_restore_payload: Dictionary = {}
var _pending_restore_summary: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	work_dir = OS.get_user_data_dir().path_join(WORK_DIR_NAME)
	status_path = work_dir.path_join("cloud_status.json")
	DirAccess.make_dir_recursive_absolute(work_dir)
	enabled = bool(ProjectSettings.get_setting("application/config/cloud_save_enabled", true))
	if not enabled:
		_set_status(true, "Cloud save dinonaktifkan di pengaturan project.")
		return
	if not Engine.has_singleton(PLUGIN_SINGLETON):
		_set_status(true, "Cloud save hanya tersedia di Android dengan Google Play Games.")
		return
	bridge = Engine.get_singleton(PLUGIN_SINGLETON)
	if (
		bridge == null
		or not bridge.has_method("initialize")
		or not bridge.has_method("isAvailable")
		or not bridge.has_method("isSignedIn")
	):
		_set_status(false, "Godot cloud plugin belum siap.")
		return
	var initialized: Variant = bridge.call("initialize", work_dir)
	available = bool(initialized) and bool(bridge.call("isAvailable"))
	if not available:
		_set_status(false, "Cloud save belum tersedia — periksa Google Play Games dan Project ID.")
		return
	signed_in = bool(bridge.call("isSignedIn"))
	_set_status(true, "Cloud save siap; memeriksa akun Google Play Games.")
	check_auth()


func _process(delta: float) -> void:
	if not busy:
		return
	_poll_elapsed += delta
	if _poll_elapsed < POLL_INTERVAL:
		return
	_poll_elapsed = 0.0
	poll()


func configure_native_paths(
	path_template: String, native_speed_path: String = GameSpeedStore.PATH
) -> bool:
	if not path_template.contains("%d"):
		return false
	slot_path_template = path_template
	speed_path = native_speed_path
	return true


func is_available() -> bool:
	return available


func is_signed_in() -> bool:
	return signed_in


func is_busy() -> bool:
	return busy


func get_status() -> Dictionary:
	return {
		"available": available,
		"signed_in": signed_in,
		"busy": busy,
		"ok": last_ok,
		"message": last_message,
	}


func get_pending_restore() -> Dictionary:
	if _pending_restore_payload.is_empty():
		return {}
	return {
		"payload": _pending_restore_payload.duplicate(true),
		"summary": _pending_restore_summary.duplicate(true),
	}


func dismiss_restore_prompt() -> void:
	_pending_restore_payload.clear()
	_pending_restore_summary.clear()


func check_auth() -> bool:
	if not _ready_for_operation("check"):
		return false
	return _start_operation("check") and _call_bridge("checkAuthAsync", [_operation_id])


func sign_in() -> bool:
	if not _ready_for_operation("signin"):
		return false
	return _start_operation("signin") and _call_bridge("signInAsync", [_operation_id])


func upload_payload() -> bool:
	if not _ready_for_operation("upload"):
		return false
	if not signed_in:
		_set_status(false, "Masuk ke Google Play Games dulu.")
		return false
	var payload := _build_payload()
	if payload.is_empty():
		_set_status(false, "Tidak ada save yang bisa diunggah.")
		return false
	if not _start_operation("upload"):
		return false
	var envelope := {
		"magic": Codec.CLOUD_MAGIC,
		"version": Codec.CLOUD_VERSION,
		"exported_at": Time.get_unix_time_from_system(),
		"payload": payload,
	}
	_operation_file = work_dir.path_join("upload_%s.json" % _operation_id)
	if not _write_json_atomic(_operation_file, envelope):
		_fail_operation("File upload cloud tidak dapat disiapkan.")
		return false
	return _call_bridge("uploadAsync", [_operation_file, _operation_id])


func download_payload(apply_immediately: bool = true) -> bool:
	if not _ready_for_operation("download"):
		return false
	if not signed_in:
		_set_status(false, "Masuk ke Google Play Games dulu.")
		return false
	if not _start_operation("download"):
		return false
	_download_apply = apply_immediately
	_operation_file = work_dir.path_join("download_%s.json" % _operation_id)
	return _call_bridge("downloadAsync", [_operation_file, _operation_id])


func auto_upload() -> bool:
	if _restoring or not available or not signed_in or busy:
		return false
	return upload_payload()


func poll() -> void:
	if not busy or status_path.is_empty() or not FileAccess.file_exists(status_path):
		return
	var file := FileAccess.open(status_path, FileAccess.READ)
	if file == null:
		return
	var parser := JSON.new()
	var parse_error := parser.parse(file.get_as_text())
	file.close()
	if parse_error != OK or not parser.data is Dictionary:
		return
	var status: Dictionary = parser.data
	if String(status.get("op_id", "")) != _operation_id:
		return
	if status.has("signed_in"):
		signed_in = bool(status.signed_in)
	_complete_operation(status)


func apply_payload(payload: Dictionary) -> Dictionary:
	var result := _validate_restore_target(payload)
	if not bool(result.ok):
		return result
	var slots: Dictionary = payload.get("slots", {})
	var previous: Dictionary = {}
	for slot in range(1, Slots.SLOT_COUNT + 1):
		var path := Slots.slot_path(slot, slot_path_template)
		var existed := Slots.slot_exists(slot, slot_path_template)
		previous[slot] = {
			"exists": existed,
			"state": ProgressStore.load_state(path) if existed else {},
		}
	_restoring = true
	var changed: Array[int] = []
	for slot in range(1, Slots.SLOT_COUNT + 1):
		var path := Slots.slot_path(slot, slot_path_template)
		var key := str(slot)
		var saved := true
		if slots.has(key):
			var normalized: Dictionary = ProgressStore._normalize_disk_state(slots[key])
			saved = ProgressStore.save_state(normalized, path)
		elif Slots.slot_exists(slot, slot_path_template):
			saved = Slots.delete_slot(slot, slot_path_template)
		if not saved:
			_rollback_slots(previous, changed)
			_restoring = false
			return {"ok": false, "error": "Save game %d gagal ditulis; restore dibatalkan." % slot}
		changed.append(slot)
	var settings: Variant = payload.get("settings", {})
	if settings is Dictionary and settings.has("game_speed"):
		var value: Variant = settings.game_speed
		if not (value is int or value is float) or not GameSpeedStore.is_valid_speed(float(value)):
			_rollback_slots(previous, changed)
			_restoring = false
			return {"ok": false, "error": "Pengaturan kecepatan cloud tidak valid."}
		if not GameSpeedStore.save_speed(float(value), speed_path, false):
			_rollback_slots(previous, changed)
			_restoring = false
			return {"ok": false, "error": "Pengaturan lokal tidak dapat dipulihkan."}
		_sync_runtime_speed(float(value))
	_restoring = false
	dismiss_restore_prompt()
	restored.emit()
	return {"ok": true, "error": ""}


func _build_payload() -> Dictionary:
	var native_slots: Dictionary = {}
	for slot in range(1, Slots.SLOT_COUNT + 1):
		if not Slots.slot_exists(slot, slot_path_template):
			continue
		var state := ProgressStore.load_state(Slots.slot_path(slot, slot_path_template))
		if not state.is_empty():
			native_slots[str(slot)] = state
	if native_slots.is_empty():
		return {}
	var settings: Dictionary = {}
	if (
		FileAccess.file_exists(speed_path)
		and not FileAccess.file_exists(speed_path + ".bak")
		and not FileAccess.file_exists(speed_path + ".tmp")
	):
		var saved_speed := GameSpeedStore._read_speed(speed_path)
		if GameSpeedStore.is_valid_speed(saved_speed):
			settings["game_speed"] = saved_speed
	return Codec.build_payload(native_slots, settings, Time.get_unix_time_from_system())


func _validate_restore_target(payload: Dictionary) -> Dictionary:
	var raw_slots: Variant = payload.get("slots")
	if not raw_slots is Dictionary or (raw_slots as Dictionary).is_empty():
		return {"ok": false, "error": "Save contains no data."}
	for key in (raw_slots as Dictionary).keys():
		var slot_key := String(key)
		if (
			not slot_key.is_valid_int()
			or not Slots.valid_slot(int(slot_key))
			or str(int(slot_key)) != slot_key
		):
			return {"ok": false, "error": "Nomor slot cloud di luar rentang."}
		if not _valid_cloud_slot(raw_slots[key]):
			return {"ok": false, "error": "Isi save game %s tidak lolos validasi." % slot_key}
	for slot in range(1, Slots.SLOT_COUNT + 1):
		var path := Slots.slot_path(slot, slot_path_template)
		var recovery_pending := (
			FileAccess.file_exists(path + ".bak") or FileAccess.file_exists(path + ".tmp")
		)
		var corrupt_local := (
			FileAccess.file_exists(path) and ProgressStore.load_state(path).is_empty()
		)
		if recovery_pending or corrupt_local:
			var message := "lokal rusak; restore tidak akan menimpanya."
			if recovery_pending:
				message = "memiliki transaksi/pemulihan tertunda."
			return {"ok": false, "error": "Save game %d %s" % [slot, message]}
	if not _valid_cloud_settings(payload.get("settings", {})):
		return {"ok": false, "error": "Pengaturan cloud tidak valid."}
	return {"ok": true, "error": ""}


func _valid_cloud_slot(raw_state: Variant) -> bool:
	if not raw_state is Dictionary:
		return false
	var normalized: Dictionary = ProgressStore._normalize_disk_state(raw_state)
	return ProgressStore._valid(normalized)


func _valid_cloud_settings(settings: Variant) -> bool:
	if not settings is Dictionary:
		return false
	if not (settings as Dictionary).has("game_speed"):
		return true
	var value: Variant = (settings as Dictionary).get("game_speed")
	return (value is int or value is float) and GameSpeedStore.is_valid_speed(float(value))


func _rollback_slots(previous: Dictionary, changed: Array[int]) -> void:
	for slot in changed:
		var snapshot: Dictionary = previous[slot]
		var path := Slots.slot_path(slot, slot_path_template)
		if bool(snapshot.exists):
			ProgressStore.save_state(snapshot.state, path)
		elif Slots.slot_exists(slot, slot_path_template):
			Slots.delete_slot(slot, slot_path_template)


func _sync_runtime_speed(value: float) -> void:
	var runtime := get_tree().root.get_node_or_null("GameSpeed")
	if runtime == null or String(runtime.get("settings_path")) != speed_path:
		return
	runtime.set("speed", value)
	runtime.set("last_save_ok", true)
	runtime.emit_signal("speed_changed", value)


func _all_local_slots_empty() -> bool:
	for slot in range(1, Slots.SLOT_COUNT + 1):
		var path := Slots.slot_path(slot, slot_path_template)
		if Slots.slot_exists(slot, slot_path_template) or FileAccess.file_exists(path + ".tmp"):
			return false
	return true


func _maybe_offer_startup_restore() -> void:
	if _startup_restore_checked or not available or not signed_in:
		return
	_startup_restore_checked = true
	if _all_local_slots_empty():
		download_payload(false)


func _complete_operation(status: Dictionary) -> void:
	var kind := _operation_kind
	var ok := bool(status.get("ok", false))
	var message := String(status.get("message", "Cloud operation failed."))
	var completed_file := _operation_file
	busy = false
	_operation_id = ""
	_operation_kind = ""
	_operation_file = ""
	if kind == "download" and ok:
		var validation := _read_download(completed_file)
		if not bool(validation.ok):
			ok = false
			message = String(validation.error)
		elif _download_apply:
			var apply_result := apply_payload(validation.payload)
			ok = bool(apply_result.ok)
			message = "Cloud save berhasil dipulihkan." if ok else String(apply_result.error)
		else:
			message = "Cloud save ditemukan."
			if _all_local_slots_empty():
				_pending_restore_payload = validation.payload.duplicate(true)
				_pending_restore_summary = Codec.get_payload_summary(validation.payload)
				_set_status(true, message)
				restore_available.emit(_pending_restore_payload, _pending_restore_summary)
			else:
				message = "Cloud save ditemukan; slot lokal berubah saat pemeriksaan."
	if completed_file != "":
		_remove_file(completed_file)
	_download_apply = false
	if ok:
		_set_status(true, message)
	else:
		_set_status(false, message)
	operation_finished.emit(kind, ok, message)
	if kind == "check":
		_startup_restore_checked = false
		_maybe_offer_startup_restore()


func _read_download(path: String) -> Dictionary:
	if path.is_empty() or not FileAccess.file_exists(path):
		return {"ok": false, "error": "File cloud tidak ditemukan."}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"ok": false, "error": "File cloud tidak dapat dibaca."}
	var source_text := file.get_as_text()
	file.close()
	var validation := Codec.validate_envelope_text(source_text)
	if validation.payload == null:
		return {"ok": false, "error": String(validation.error)}
	return {"ok": true, "payload": validation.payload}


func _ready_for_operation(kind: String) -> bool:
	if not available or bridge == null:
		_set_status(false, "Cloud save belum tersedia di perangkat ini.")
		operation_finished.emit(kind, false, last_message)
		return false
	return true


func _start_operation(kind: String) -> bool:
	if busy:
		_set_status(false, "Operasi cloud lain sedang berjalan.")
		operation_finished.emit(kind, false, last_message)
		return false
	_operation_counter += 1
	_operation_id = "godot-%s-%d-%d" % [kind, Time.get_ticks_msec(), _operation_counter]
	_operation_kind = kind
	_operation_file = ""
	busy = true
	_poll_elapsed = POLL_INTERVAL
	_set_status(true, "Memproses %s cloud…" % kind)
	return true


func _call_bridge(method: String, arguments: Array) -> bool:
	if bridge == null or not bridge.has_method(method):
		_fail_operation("Bridge Android tidak mendukung %s." % method)
		return false
	bridge.callv(method, arguments)
	return true


func _fail_operation(message: String) -> void:
	var kind := _operation_kind
	var path := _operation_file
	busy = false
	_operation_id = ""
	_operation_kind = ""
	_operation_file = ""
	_remove_file(path)
	_set_status(false, message)
	operation_finished.emit(kind, false, message)


func _set_status(ok: bool, message: String) -> void:
	last_ok = ok
	last_message = message
	status_changed.emit(last_ok, last_message, available, signed_in, busy)


func _write_json_atomic(path: String, data: Dictionary) -> bool:
	var temporary := path + ".tmp"
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(data, "", true, true) + "\n")
	file.flush()
	var failed := file.get_error() != OK
	file.close()
	if failed:
		_remove_file(temporary)
		return false
	if DirAccess.rename_absolute(temporary, path) != OK:
		_remove_file(temporary)
		return false
	return true


func _remove_file(path: String) -> void:
	if not path.is_empty() and FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)


## Test seam used only by native Godot tests; production discovers the v2 plugin singleton.
func _install_adapter_for_tests(adapter: Object, test_work_dir: String) -> void:
	bridge = adapter
	work_dir = test_work_dir
	status_path = work_dir.path_join("cloud_status.json") if not work_dir.is_empty() else ""
	available = false
	if adapter != null:
		DirAccess.make_dir_recursive_absolute(work_dir)
		available = (
			bool(adapter.call("initialize", work_dir)) if adapter.has_method("initialize") else true
		)
	signed_in = false if adapter == null else bool(adapter.call("isSignedIn"))
	busy = false
	_operation_id = ""
	_operation_kind = ""
	_operation_file = ""
	_startup_restore_checked = true
	_set_status(available, "Test cloud adapter installed" if available else "Cloud unavailable")


## Called by the v2 plugin after a restored speed has passed native validation.
func _notify_local_setting_saved() -> void:
	if not _restoring:
		auto_upload()
