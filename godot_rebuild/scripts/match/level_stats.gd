extends RefCounted
## Native policy port of _system.py::SaveManager per-level statistics.
## Persistence and match reward ownership stay outside this pure transaction.

const MAX_LEVEL := 54
const INTEGER_FIELDS: Array[String] = [
	"best_score",
	"best_time_seconds",
	"total_attempts",
	"wins",
	"total_kills",
	"max_combo",
	"total_playtime_seconds",
]
const MATCH_INTEGER_FIELDS: Array[String] = [
	"score", "time_seconds", "kills", "combo", "playtime_seconds"
]


static func empty_stats() -> Dictionary:
	return {
		"best_score": 0,
		"best_time_seconds": 0,
		"total_attempts": 0,
		"wins": 0,
		"total_kills": 0,
		"max_combo": 0,
		"total_playtime_seconds": 0,
	}


static func get_level_stats(data: Dictionary, level_number: int) -> Dictionary:
	var all_stats: Variant = data.get("level_stats", {})
	if not (all_stats is Dictionary):
		return empty_stats()
	var value: Variant = all_stats.get(str(level_number))
	if value is Dictionary and valid_entry(value):
		return value.duplicate(true)
	return empty_stats()


static func update_level_stats(
	data: Dictionary, level_number: int, match_stats: Dictionary
) -> Dictionary:
	if level_number < 1 or level_number > MAX_LEVEL or not valid_match(match_stats):
		return {}
	var updated := data.duplicate(true)
	var all_stats: Variant = updated.get("level_stats", {})
	if not valid_map(all_stats):
		return {}
	var current := get_level_stats(updated, level_number)
	var new_best_score := false
	var new_best_time := false
	current["total_attempts"] += 1
	current["total_playtime_seconds"] += int(match_stats.get("playtime_seconds", 0))
	current["total_kills"] += int(match_stats.get("kills", 0))
	current["max_combo"] = maxi(int(current.max_combo), int(match_stats.get("combo", 0)))
	if bool(match_stats.get("won", false)):
		current["wins"] += 1
		var score := int(match_stats.get("score", 0))
		if score > int(current.best_score):
			current["best_score"] = score
			new_best_score = true
		var match_time := int(match_stats.get("time_seconds", 0))
		if (
			match_time > 0
			and (int(current.best_time_seconds) == 0 or match_time < int(current.best_time_seconds))
		):
			current["best_time_seconds"] = match_time
			new_best_time = true
	var stats_map := all_stats as Dictionary
	stats_map[str(level_number)] = current
	updated["level_stats"] = stats_map
	return {
		"state": updated,
		"is_new_best_score": new_best_score,
		"is_new_best_time": new_best_time,
		"new_stats": current.duplicate(true),
	}


static func valid_match(match_stats: Dictionary) -> bool:
	if not (match_stats.get("won") is bool):
		return false
	for field in MATCH_INTEGER_FIELDS:
		var value: Variant = match_stats.get(field)
		if not (value is int) or value < 0:
			return false
	return true


static func valid_map(value: Variant) -> bool:
	if not (value is Dictionary):
		return false
	for raw_key in value:
		if not (raw_key is String) or not String(raw_key).is_valid_int():
			return false
		var level_number := int(raw_key)
		if level_number < 1 or level_number > MAX_LEVEL or str(level_number) != raw_key:
			return false
		if not valid_entry(value[raw_key]):
			return false
	return true


static func valid_entry(value: Variant) -> bool:
	if not (value is Dictionary) or value.size() != INTEGER_FIELDS.size():
		return false
	for field in INTEGER_FIELDS:
		var field_value: Variant = value.get(field)
		if not (field_value is int) or field_value < 0:
			return false
	if int(value.wins) > int(value.total_attempts):
		return false
	return true


static func format_time(seconds: int) -> String:
	if seconds == 0:
		return "--:--"
	return "%d:%02d" % [int(seconds / 60), seconds % 60]
