extends RefCounted
## Separate development-only progression file. Never reads/writes Python's
## save slots or cloud data. Caller owns the match-result claim boundary.

const PATH := "user://level_progress_v1.json"
const VERSION := 1
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS


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
	var decoder := JSON.new()
	if decoder.parse(file.get_as_text()) != OK:
		return {}
	var parsed: Variant = decoder.data
	if not (parsed is Dictionary) or _disk_integer(parsed.get("version")) != VERSION:
		return {}
	var state: Variant = parsed.get("state")
	if not (state is Dictionary):
		return {}
	var normalized := _normalize_disk_state(state)
	return normalized if _valid(normalized) else {}


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


## Godot JSON decodes numeric values as floats. Convert only exact, bounded
## integers; never truncate fractional/corrupt currency or completion IDs.
static func _disk_integer(value: Variant) -> Variant:
	if value is int:
		return value
	if value is float and not is_nan(value) and not is_inf(value):
		if absf(value) <= 9007199254740991.0 and floor(value) == value:
			return int(value)
	return null


static func _normalize_disk_state(state: Dictionary) -> Dictionary:
	var copy := state.duplicate(true)
	copy["meta_gold"] = _disk_integer(copy.get("meta_gold"))
	var completed: Variant = copy.get("completed_levels", [])
	if completed is Array:
		var converted: Array = []
		for value in completed:
			converted.append(_disk_integer(value))
		copy["completed_levels"] = converted
	var counts: Variant = copy.get("replay_reward_counts", {})
	if counts is Dictionary:
		for key in counts:
			counts[key] = _disk_integer(counts[key])
	if copy.has("last_played_level"):
		copy["last_played_level"] = _disk_integer(copy["last_played_level"])
	return copy


static func _valid(state: Dictionary) -> bool:
	if not state.has("meta_gold"):
		return false
	var gold: Variant = state["meta_gold"]
	if not (gold is int) or gold < 0:
		return false
	if state.has("last_played_level"):
		var last: Variant = state["last_played_level"]
		if not (last is int) or last < 1 or last > 54:
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
	for field in ["purchased_heroes", "unlocked_bosses"]:
		if not state.has(field):
			continue  # Backward-compatible with saves created before Hero Shop.
		var values: Variant = state[field]
		if not (values is Array):
			return false
		var hero_seen := {}
		for value in values:
			if not (value is String) or not HERO_ROSTER.has(value) or hero_seen.has(value):
				return false
			if field == "unlocked_bosses" and not HERO_ROSTER[value].is_boss_hero:
				return false
			hero_seen[value] = true
	return true
