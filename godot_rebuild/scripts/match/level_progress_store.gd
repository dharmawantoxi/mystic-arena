extends RefCounted
## Separate development-only progression file. Never reads/writes Python's
## save slots or cloud data. Caller owns the match-result claim boundary.

const PATH := "user://level_progress_v1.json"
const VERSION := 1


static func load_state(path: String = PATH) -> Dictionary:
	var primary := _read_state(path)
	if not primary.is_empty():
		return primary
	# A process killed between the two renames still has the previous save.
	return _read_state(path + ".bak")


static func _read_state(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not (parsed is Dictionary) or int(parsed.get("version", -1)) != VERSION:
		return {}
	var state: Variant = parsed.get("state")
	if not (state is Dictionary) or not _valid(state):
		return {}
	return state.duplicate(true)


static func recover_backup(path: String = PATH) -> bool:
	var backup := path + ".bak"
	if FileAccess.file_exists(path) or _read_state(backup).is_empty():
		return false
	return DirAccess.rename_absolute(backup, path) == OK


static func save_state(state: Dictionary, path: String = PATH) -> bool:
	if not _valid(state) or FileAccess.file_exists(path + ".bak"):
		return false
	if FileAccess.file_exists(path) and _read_state(path).is_empty():
		return false
	# Write to a sibling file first: invalid/partial JSON must never replace
	# the last good save. Keep a backup until the replacement succeeds.
	var temp := path + ".tmp"
	var backup := path + ".bak"
	var file := FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({"version": VERSION, "state": state}) + "\n")
	file.flush()
	var failed := file.get_error() != OK
	file.close()
	if failed:
		DirAccess.remove_absolute(temp)
		return false
	var had_previous := FileAccess.file_exists(path)
	if had_previous:
		# Never overwrite an existing backup: it may be a recovery copy from
		# a previous interrupted transaction.
		if FileAccess.file_exists(backup) or DirAccess.rename_absolute(path, backup) != OK:
			DirAccess.remove_absolute(temp)
			return false
	if DirAccess.rename_absolute(temp, path) != OK:
		if had_previous:
			DirAccess.rename_absolute(backup, path)
		DirAccess.remove_absolute(temp)
		return false
	if had_previous:
		DirAccess.remove_absolute(backup)
	return true


static func _valid(state: Dictionary) -> bool:
	if not state.has("meta_gold"):
		return false
	var gold: Variant = state["meta_gold"]
	if not (gold is int) or gold < 0:
		return false
	var completed: Variant = state.get("completed_levels", [])
	var counts: Variant = state.get("replay_reward_counts", {})
	if not (completed is Array) or not (counts is Dictionary):
		return false
	var seen := {}
	for number in completed:
		if not (number is int) or number < 1 or number > 54 or seen.has(number):
			return false
		seen[number] = true
	for key in counts:
		if not (key is String) or not key.is_valid_int():
			return false
		var number := int(key)
		if number < 1 or number > 54 or not (counts[key] is int) or counts[key] < 0:
			return false
	return true
