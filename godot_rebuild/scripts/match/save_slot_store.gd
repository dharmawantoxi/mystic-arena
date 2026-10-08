extends RefCounted
## Native three-slot adapter for _system.py::SaveManager.
##
## Slot files stay inside this Godot project's custom user directory and retain
## LevelProgressStore's atomic/validated envelope. Python/Pygame saves are never
## opened. Callers may inject a test-only path template.

const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const SLOT_COUNT := 3
const PATH_TEMPLATE := "user://slot_%d.json"
const LEGACY_PATH := ProgressStore.PATH

static var _current_slot := 1


static func valid_slot(slot: int) -> bool:
	return slot >= 1 and slot <= SLOT_COUNT


static func slot_path(slot: int, path_template: String = PATH_TEMPLATE) -> String:
	return path_template % slot if valid_slot(slot) and path_template.contains("%d") else ""


static func slot_for_path(path: String, path_template: String = PATH_TEMPLATE) -> int:
	for slot in range(1, SLOT_COUNT + 1):
		if path == slot_path(slot, path_template):
			return slot
	return -1


static func get_current_slot() -> int:
	return _current_slot


static func set_current_slot(slot: int) -> bool:
	if not valid_slot(slot):
		return false
	_current_slot = slot
	return true


static func current_path(path_template: String = PATH_TEMPLATE) -> String:
	return slot_path(_current_slot, path_template)


static func empty_state(now: float = -1.0) -> Dictionary:
	if now < 0.0:
		now = Time.get_unix_time_from_system()
	return {
		"unlocked_bosses": [],
		"purchased_heroes": [],
		"meta_gold": 0,
		"completed_levels": [],
		"last_played_level": 1,
		"slot_created": now,
		"slot_last_played": now,
		"slot_playtime_seconds": 0,
		"level_stats": {},
		"run_difficulty": null,
	}


static func slot_exists(slot: int, path_template: String = PATH_TEMPLATE) -> bool:
	var path := slot_path(slot, path_template)
	return (
		not path.is_empty()
		and (FileAccess.file_exists(path) or FileAccess.file_exists(path + ".bak"))
	)


static func load_state(slot: int = -1, path_template: String = PATH_TEMPLATE) -> Dictionary:
	var selected := _current_slot if slot < 0 else slot
	var path := slot_path(selected, path_template)
	return {} if path.is_empty() else ProgressStore.load_state(path)


static func save_state(
	state: Dictionary, slot: int = -1, now: float = -1.0, path_template: String = PATH_TEMPLATE
) -> bool:
	var selected := _current_slot if slot < 0 else slot
	var path := slot_path(selected, path_template)
	if path.is_empty():
		return false
	return save_path(state, path, now, path_template)


static func save_path(
	state: Dictionary, path: String, now: float = -1.0, path_template: String = PATH_TEMPLATE
) -> bool:
	var slot := slot_for_path(path, path_template)
	if slot < 0:
		return ProgressStore.save_state(state, path)
	if now < 0.0:
		now = Time.get_unix_time_from_system()
	var stamped := state.duplicate(true)
	if not stamped.has("slot_created"):
		var existing := ProgressStore.load_state(path)
		stamped["slot_created"] = existing.get("slot_created", now)
	stamped["slot_last_played"] = now
	if not stamped.has("slot_playtime_seconds"):
		stamped["slot_playtime_seconds"] = 0
	if not stamped.has("level_stats"):
		stamped["level_stats"] = {}
	if not stamped.has("last_played_level"):
		stamped["last_played_level"] = 1
	if not stamped.has("run_difficulty"):
		stamped["run_difficulty"] = null
	return ProgressStore.save_state(stamped, path)


static func slot_info(slot: int, path_template: String = PATH_TEMPLATE) -> Dictionary:
	var path := slot_path(slot, path_template)
	if path.is_empty() or not slot_exists(slot, path_template):
		return {}
	var state := ProgressStore.load_state(path)
	if state.is_empty():
		return {"slot_num": slot, "corrupt": true}
	var completed: Array = state.get("completed_levels", [])
	var highest := 0
	for value in completed:
		highest = maxi(highest, int(value))
	return {
		"slot_num": slot,
		"meta_gold": int(state.get("meta_gold", 0)),
		"completed_levels": completed.duplicate(),
		"highest_level": highest,
		"last_played_level": int(state.get("last_played_level", 1)),
		"purchased_heroes": (state.get("purchased_heroes", []) as Array).duplicate(),
		"unlocked_bosses": (state.get("unlocked_bosses", []) as Array).duplicate(),
		"slot_created": float(state.get("slot_created", 0.0)),
		"slot_last_played": float(state.get("slot_last_played", 0.0)),
		"playtime_seconds": int(state.get("slot_playtime_seconds", 0)),
		"corrupt": false,
	}


static func all_slot_info(path_template: String = PATH_TEMPLATE) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for slot in range(1, SLOT_COUNT + 1):
		result.append(slot_info(slot, path_template))
	return result


static func delete_slot(slot: int, path_template: String = PATH_TEMPLATE) -> bool:
	var path := slot_path(slot, path_template)
	if path.is_empty():
		return false
	var removed := false
	for suffix in ["", ".tmp", ".bak"]:
		if FileAccess.file_exists(path + suffix):
			removed = DirAccess.remove_absolute(path + suffix) == OK or removed
	return removed


static func migrate_legacy(
	legacy_path: String = LEGACY_PATH, path_template: String = PATH_TEMPLATE, now: float = -1.0
) -> bool:
	if not FileAccess.file_exists(legacy_path) or slot_exists(1, path_template):
		return false
	var state := ProgressStore.load_state(legacy_path)
	if state.is_empty() or not save_state(state, 1, now, path_template):
		return false
	var archive := legacy_path + ".migrated"
	if not FileAccess.file_exists(archive):
		DirAccess.rename_absolute(legacy_path, archive)
	return true


static func format_playtime(seconds: int) -> String:
	var hours := int(seconds / 3600)
	var minutes := int((seconds % 3600) / 60)
	return "%dh %dm" % [hours, minutes] if hours > 0 else "%dm" % minutes


static func format_time(seconds: int) -> String:
	if seconds == 0:
		return "--:--"
	return "%d:%02d" % [int(seconds / 60), seconds % 60]


static func format_last_played(timestamp: float, now: float = -1.0) -> String:
	if timestamp == 0.0:
		return "Never"
	if now < 0.0:
		now = Time.get_unix_time_from_system()
	var elapsed := maxf(0.0, now - timestamp)
	if elapsed < 60.0:
		return "Just now"
	if elapsed < 3600.0:
		return "%dm ago" % int(elapsed / 60.0)
	if elapsed < 86400.0:
		return "%dh ago" % int(elapsed / 3600.0)
	if elapsed < 604800.0:
		return "%dd ago" % int(elapsed / 86400.0)
	var date := Time.get_datetime_dict_from_unix_time(int(timestamp))
	var months := [
		"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
	]
	return "%02d %s %04d" % [int(date.day), months[int(date.month) - 1], int(date.year)]
