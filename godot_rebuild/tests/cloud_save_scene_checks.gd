# gdlint:disable=function-name
extends RefCounted
## Real main-menu cloud controls plus the native save/restore path.

const CloudRuntime = preload("res://scripts/match/cloud_save_runtime.gd")
const Codec = preload("res://scripts/match/cloud_save_codec.gd")
const Slots = preload("res://scripts/match/save_slot_store.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const GameSpeedStore = preload("res://scripts/simulation/game_speed_store.gd")
const SLOT_TEMPLATE := "user://cloud_save_scene_slot_%d.json"
const STARTUP_TEMPLATE := "user://cloud_save_startup_slot_%d.json"
const SPEED_PATH := "user://cloud_save_scene_speed.json"
const TEST_WORK_DIR := "user://cloud_save_scene_bridge"


class FakeCloudBridge:
	extends RefCounted
	var work_dir := ""
	var signed_in := false
	var cloud_snapshot := PackedByteArray()
	var upload_count := 0
	var download_count := 0

	func initialize(path: String) -> bool:
		work_dir = path
		DirAccess.make_dir_recursive_absolute(work_dir)
		return true

	func isSignedIn() -> bool:
		return signed_in

	func checkAuthAsync(operation_id: String) -> void:
		_write_status(operation_id, "check", true, "Auth checked")

	func signInAsync(operation_id: String) -> void:
		signed_in = true
		_write_status(operation_id, "signin", true, "Signed in")

	func uploadAsync(file_path: String, operation_id: String) -> void:
		var file := FileAccess.open(file_path, FileAccess.READ)
		if file == null:
			_write_status(operation_id, "upload", false, "Missing upload")
			return
		cloud_snapshot = file.get_buffer(file.get_length())
		file.close()
		upload_count += 1
		_write_status(operation_id, "upload", true, "Snapshot uploaded")

	func downloadAsync(file_path: String, operation_id: String) -> void:
		download_count += 1
		if cloud_snapshot.is_empty():
			_write_status(operation_id, "download", false, "No cloud snapshot")
			return
		var file := FileAccess.open(file_path, FileAccess.WRITE)
		if file == null:
			_write_status(operation_id, "download", false, "Cannot write download")
			return
		file.store_buffer(cloud_snapshot)
		file.close()
		_write_status(operation_id, "download", true, "Snapshot downloaded")

	func _write_status(operation_id: String, kind: String, ok: bool, message: String) -> void:
		var status := {
			"op_id": operation_id,
			"kind": kind,
			"ok": ok,
			"code": 0 if ok else 1,
			"message": message,
			"signed_in": signed_in,
		}
		var file := FileAccess.open(work_dir.path_join("cloud_status.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify(status))
		file.close()


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var runtime = tree.root.get_node("CloudSave")
	var menu = app.current_screen
	var panel = menu.get_node("SaveSlotPanel")
	_cleanup_path(SLOT_TEMPLATE)
	_cleanup_path(STARTUP_TEMPLATE)
	_cleanup_speed()
	_cleanup_work_dir()
	check.call(
		menu.configure_slot_paths(SLOT_TEMPLATE, 1), "Cloud menu selects isolated native paths"
	)
	runtime.call("configure_native_paths", SLOT_TEMPLATE, SPEED_PATH)
	var initial_state := _state(240, [1, 2], 2)
	check.call(
		Slots.save_state(initial_state, 1, 1_700_000_100.0, SLOT_TEMPLATE),
		"Playable cloud fixture uses the production three-slot store"
	)
	check.call(
		GameSpeedStore.save_speed(1.5, SPEED_PATH, false),
		"Playable cloud fixture writes native settings"
	)

	var bridge := FakeCloudBridge.new()
	runtime.call(
		"_install_adapter_for_tests", bridge, ProjectSettings.globalize_path(TEST_WORK_DIR)
	)
	runtime.call("check_auth")
	runtime.call("poll")
	check.call(not bool(runtime.call("is_signed_in")), "Startup auth follows the bridge status")

	menu.get_node("%SaveGamesButton").pressed.emit()
	await _settle(tree)
	check.call(panel.visible, "Main menu opens the cloud-save controls with slots")
	check.call(
		(
			panel._cloud_sign_in != null
			and panel._cloud_upload != null
			and panel._cloud_download != null
		),
		"Save-slot panel exposes sign-in, upload and download actions"
	)
	panel._cloud_sign_in.pressed.emit()
	runtime.call("poll")
	check.call(bool(runtime.call("is_signed_in")), "Sign-in action updates native cloud auth")

	panel._cloud_upload.pressed.emit()
	check.call(
		panel._cloud_pending_action == "upload" and panel._cloud_confirm.visible,
		"Manual cloud upload always requires explicit confirmation"
	)
	check.call(bridge.upload_count == 0, "Upload waits for confirmation")
	panel._cloud_confirm_yes.pressed.emit()
	check.call(bridge.upload_count == 1, "Confirmed upload reaches the Android bridge contract")
	runtime.call("poll")
	check.call(
		not bool(runtime.call("is_busy")), "Upload completion releases the single-operation lock"
	)
	var uploaded_validation := Codec.validate_envelope_text(
		bridge.cloud_snapshot.get_string_from_utf8()
	)
	check.call(
		uploaded_validation.payload is Dictionary,
		"Uploaded snapshot keeps the validated source envelope"
	)
	check.call(
		(
			uploaded_validation.payload.slots.has("1")
			and uploaded_validation.payload.settings.get("game_speed") == 1.5
		),
		"Uploaded cloud payload contains Godot slots and settings"
	)

	var changed_state := ProgressStore.load_state(Slots.slot_path(1, SLOT_TEMPLATE))
	changed_state["meta_gold"] = 9
	check.call(
		ProgressStore.save_state(changed_state, Slots.slot_path(1, SLOT_TEMPLATE)),
		"Scene test creates a local/cloud conflict without triggering another upload"
	)
	panel.refresh_slots(Slots.all_slot_info(SLOT_TEMPLATE), 1)
	panel._cloud_download.pressed.emit()
	check.call(
		panel._cloud_pending_action == "download" and panel._cloud_confirm.visible,
		"Download asks before replacing an occupied local slot"
	)
	check.call(bridge.download_count == 0, "Download waits for overwrite confirmation")
	panel._cloud_confirm_yes.pressed.emit()
	check.call(bridge.download_count == 1, "Confirmed download reaches the Android bridge contract")
	runtime.call("poll")
	check.call(
		int(Slots.load_state(1, SLOT_TEMPLATE).meta_gold) == 240,
		"Cloud restore atomically replaces native slot content"
	)
	check.call(
		GameSpeedStore.load_speed(SPEED_PATH) == 1.5,
		"Cloud restore applies the existing Godot game-speed setting"
	)

	var auto_state := Slots.load_state(1, SLOT_TEMPLATE)
	auto_state["meta_gold"] = 241
	check.call(
		Slots.save_state(auto_state, 1, 1_700_000_200.0, SLOT_TEMPLATE),
		"Local slot save succeeds independently of cloud work"
	)
	await tree.process_frame
	check.call(
		bridge.upload_count == 2, "Successful local save triggers a non-blocking cloud upload"
	)
	runtime.call("poll")

	_cleanup_path(STARTUP_TEMPLATE)
	check.call(
		menu.configure_slot_paths(STARTUP_TEMPLATE, 1),
		"Startup restore test uses an isolated empty slot set"
	)
	runtime.call("configure_native_paths", STARTUP_TEMPLATE, SPEED_PATH)
	runtime.set("_startup_restore_checked", false)
	runtime.call("check_auth")
	runtime.call("poll")
	check.call(
		bool(runtime.call("is_busy")),
		"Signed-in startup check fetches cloud only when every local slot is empty"
	)
	runtime.call("poll")
	check.call(
		panel._cloud_pending_action == "restore" and panel._cloud_confirm.visible,
		"Startup cloud snapshot is offered in the real menu confirmation"
	)
	check.call(
		not Slots.slot_exists(1, STARTUP_TEMPLATE),
		"Startup cloud probe does not overwrite before player confirmation"
	)
	panel._cloud_confirm_yes.pressed.emit()
	check.call(
		int(Slots.load_state(1, STARTUP_TEMPLATE).meta_gold) == 241,
		"Player-confirmed startup restore writes the cloud slot"
	)

	panel.set_open(false)
	_cleanup_path(SLOT_TEMPLATE)
	_cleanup_path(STARTUP_TEMPLATE)
	_cleanup_speed()
	_cleanup_work_dir()
	runtime.call("_install_adapter_for_tests", null, "")
	runtime.call("configure_native_paths", Slots.PATH_TEMPLATE, GameSpeedStore.PATH)
	check.call(
		menu.configure_slot_paths(Slots.PATH_TEMPLATE, 1),
		"Cloud scene test restores production slot paths"
	)
	await _settle(tree)


func _state(gold: int, completed: Array, last_level: int) -> Dictionary:
	var state := Slots.empty_state(1_700_000_000.0)
	state["meta_gold"] = gold
	state["completed_levels"] = completed
	state["last_played_level"] = last_level
	return state


func _cleanup_path(template: String) -> void:
	for slot in range(1, Slots.SLOT_COUNT + 1):
		Slots.delete_slot(slot, template)


func _cleanup_speed() -> void:
	for path in [SPEED_PATH, SPEED_PATH + ".tmp", SPEED_PATH + ".bak"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _cleanup_work_dir() -> void:
	var directory := DirAccess.open(TEST_WORK_DIR)
	if directory == null:
		return
	for path in [
		TEST_WORK_DIR.path_join("cloud_status.json"),
		TEST_WORK_DIR.path_join("cloud_status.json.tmp")
	]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_WORK_DIR))


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
