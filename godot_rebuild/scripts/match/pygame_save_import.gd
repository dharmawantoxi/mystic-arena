extends RefCounted
## Pygame slot-file import into the native save slot layer.
##
## `_system.py::SaveManager` stays the oracle for what a Python slot file means:
## `load()` backfills the documented default fields and `get_slot_info()` reads the
## same keys. This module reproduces that meaning inside Godot, then sanitises the
## values the Godot save envelope cannot store and reports every value it drops
## instead of silently rewriting the player's history.
##
## The Python save directory is never touched: the caller supplies the source
## path of a copy (for example `user://pygame_slot_1.json`). Nothing is written
## when the source is unreadable or the target slot is occupied.

const LevelStats = preload("res://scripts/match/level_stats.gd")
const SaveSlotStore = preload("res://scripts/match/save_slot_store.gd")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS

const MAX_LEVEL := 54
const DIFFICULTIES: Array[String] = ["normal", "hard"]
const MARKER := "pygame"
## Where the player (or QA) drops a copied Pygame slot file. Slot N of Pygame is
## imported into save game N; the Python directory itself is never read.
const STAGED_TEMPLATE := "user://pygame_slot_%d.json"


## `_system.py::SaveManager.load` backfill list. Values are duplicated per call so
## no import can mutate the constants.
static func _backfilled(source: Dictionary, now: float) -> Dictionary:
	var data := source.duplicate(true)
	if not data.has("unlocked_bosses"):
		data["unlocked_bosses"] = []
	if not data.has("purchased_heroes"):
		data["purchased_heroes"] = []
	if not data.has("meta_gold"):
		data["meta_gold"] = 0
	if not data.has("completed_levels"):
		data["completed_levels"] = []
	if not data.has("last_played_level"):
		data["last_played_level"] = 1
	if not data.has("slot_created"):
		data["slot_created"] = now
	if not data.has("slot_last_played"):
		data["slot_last_played"] = now
	if not data.has("slot_playtime_seconds"):
		data["slot_playtime_seconds"] = 0
	if not data.has("level_stats"):
		data["level_stats"] = {}
	if not data.has("run_difficulty"):
		data["run_difficulty"] = null
	return data


## Godot JSON decodes numbers as floats. Accept only exact, bounded integers so a
## corrupt currency is never truncated into a different amount.
static func _integer(value: Variant) -> Variant:
	if value is int:
		return value
	if value is float and not is_nan(value) and not is_inf(value):
		if absf(value) <= 9007199254740991.0 and floor(value) == value:
			return int(value)
	return null


static func _rejected(reason: String) -> Dictionary:
	return {"ok": false, "reason": reason, "state": {}, "report": _empty_report()}


static func _empty_report() -> Dictionary:
	return {
		"dropped_heroes": [],
		"dropped_bosses": [],
		"dropped_levels": [],
		"dropped_level_stats": [],
		"dropped_duplicates": [],
		"rejected_difficulty": "",
		"clamped_last_level": 0,
	}


## Pygame slot dictionary -> `{ok, reason, state, report}`. `state` is a Godot slot
## state (the shape `SaveSlotStore`/`LevelProgressStore` validate), never a copy of
## the Python file.
static func normalize(source: Variant, now: float = -1.0) -> Dictionary:
	if now < 0.0:
		now = Time.get_unix_time_from_system()
	if not (source is Dictionary):
		return _rejected("not_a_save")
	var data := _backfilled(source as Dictionary, now)
	var gold: Variant = _integer(data.get("meta_gold"))
	if gold == null or int(gold) < 0:
		return _rejected("corrupt_meta_gold")
	var report := _empty_report()
	var state := {
		"meta_gold": int(gold),
		"completed_levels": _levels(data.get("completed_levels"), report),
		"purchased_heroes": _heroes(data.get("purchased_heroes"), false, report),
		"unlocked_bosses": _heroes(data.get("unlocked_bosses"), true, report),
		"level_stats": _level_stats(data.get("level_stats"), report),
		"last_played_level": _last_level(data.get("last_played_level"), report),
		"slot_created": _timestamp(data.get("slot_created"), now),
		"slot_last_played": _timestamp(data.get("slot_last_played"), now),
		"slot_playtime_seconds": _playtime(data.get("slot_playtime_seconds")),
		"run_difficulty": _difficulty(data.get("run_difficulty"), report),
		# The replay reward ledger is Godot-only: the Pygame save has no equivalent,
		# so an imported level counts as completed (replay reward tier) with no
		# second replay paid yet.
		"replay_reward_counts": {},
		"import_source": MARKER,
	}
	return {"ok": true, "reason": "", "state": state, "report": report}


## Slot card summary for a "what will be imported" prompt.
static func preview(source: Variant, now: float = -1.0) -> Dictionary:
	var result := normalize(source, now)
	if not bool(result.get("ok", false)):
		return {"ok": false, "reason": String(result.get("reason", ""))}
	var state: Dictionary = result.get("state", {})
	var highest := 0
	for value in state.get("completed_levels", []):
		highest = maxi(highest, int(value))
	return {
		"ok": true,
		"reason": "",
		"meta_gold": int(state.get("meta_gold", 0)),
		"highest_level": highest,
		"last_played_level": int(state.get("last_played_level", 1)),
		"completed": (state.get("completed_levels", []) as Array).size(),
		"heroes": (state.get("purchased_heroes", []) as Array).size(),
		"bosses": (state.get("unlocked_bosses", []) as Array).size(),
		"playtime_seconds": int(state.get("slot_playtime_seconds", 0)),
	}


## Read a copied Pygame slot file and store it as a Godot slot. The write goes
## through `SaveSlotStore`, so the file keeps the versioned envelope, the atomic
## rename and the cloud notification. Godot stamps `slot_last_played`, exactly as
## the source `save()` does.
static func import_file(
	source_path: String,
	slot: int,
	path_template: String = SaveSlotStore.PATH_TEMPLATE,
	now: float = -1.0,
	overwrite: bool = false
) -> Dictionary:
	if not SaveSlotStore.valid_slot(slot):
		return _import_failure("invalid_slot")
	if not FileAccess.file_exists(source_path):
		return _import_failure("missing_source")
	var decoder := JSON.new()
	if decoder.parse(FileAccess.get_file_as_string(source_path)) != OK:
		return _import_failure("invalid_json")
	var result := normalize(decoder.data, now)
	if not bool(result.get("ok", false)):
		return _import_failure(String(result.get("reason", "")))
	if not overwrite and SaveSlotStore.slot_exists(slot, path_template):
		return _import_failure("slot_occupied")
	var state: Dictionary = result.get("state", {})
	if not SaveSlotStore.save_state(state, slot, now, path_template):
		return _import_failure("write_failed")
	# Report what was actually stored: the slot layer stamps `slot_last_played`
	# with the import time, exactly as `SaveManager.save` stamps a Python slot.
	var stored := SaveSlotStore.load_state(slot, path_template)
	return {
		"ok": true,
		"reason": "",
		"slot": slot,
		"state": stored if not stored.is_empty() else state,
		"report": result.get("report", {}),
	}


static func staged_path(slot: int, staged_template: String = STAGED_TEMPLATE) -> String:
	if not SaveSlotStore.valid_slot(slot) or not staged_template.contains("%d"):
		return ""
	return staged_template % slot


static func staged_slots(staged_template: String = STAGED_TEMPLATE) -> Array[int]:
	var result: Array[int] = []
	for slot in range(1, SaveSlotStore.SLOT_COUNT + 1):
		var path := staged_path(slot, staged_template)
		if not path.is_empty() and FileAccess.file_exists(path):
			result.append(slot)
	return result


## Import every staged file into the save game with the same number. The menu only
## has to render the returned `lines`; the Pygame files stay untouched.
static func import_staged_slots(
	staged_template: String = STAGED_TEMPLATE,
	path_template: String = SaveSlotStore.PATH_TEMPLATE,
	now: float = -1.0,
	overwrite: bool = true
) -> Dictionary:
	if now < 0.0:
		now = Time.get_unix_time_from_system()
	var imported: Array[int] = []
	var refused: Array = []
	var lines: Array[String] = []
	for slot in range(1, SaveSlotStore.SLOT_COUNT + 1):
		var source := staged_path(slot, staged_template)
		if source.is_empty() or not FileAccess.file_exists(source):
			continue
		var result := import_file(source, slot, path_template, now, overwrite)
		if bool(result.get("ok", false)):
			var state: Dictionary = result.get("state", {})
			imported.append(slot)
			var level := int(state.get("last_played_level", 1))
			var gold := int(state.get("meta_gold", 0))
			lines.append("Slot %d imported: Level %d · Hero Gold %d" % [slot, level, gold])
		else:
			var reason := String(result.get("reason", ""))
			refused.append({"slot": slot, "reason": reason})
			lines.append("Slot %d refused: %s" % [slot, reason])
	if lines.is_empty():
		lines.append(
			"No staged Pygame save found. Copy slot_N.json as user://pygame_slot_N.json first."
		)
	return {
		"ok": not imported.is_empty(),
		"imported": imported,
		"refused": refused,
		"lines": lines,
	}


static func _import_failure(reason: String) -> Dictionary:
	return {"ok": false, "reason": reason, "slot": -1, "state": {}, "report": _empty_report()}


static func _levels(value: Variant, report: Dictionary) -> Array:
	var result: Array = []
	if not (value is Array):
		return result
	var seen := {}
	for raw in value:
		var number: Variant = _integer(raw)
		if number == null or int(number) < 1 or int(number) > MAX_LEVEL:
			report["dropped_levels"].append(raw)
			continue
		if seen.has(int(number)):
			report["dropped_duplicates"].append("level:%d" % int(number))
			continue
		seen[int(number)] = true
		result.append(int(number))
	return result


static func _heroes(value: Variant, boss_only: bool, report: Dictionary) -> Array:
	var result: Array = []
	if not (value is Array):
		return result
	var bucket: Array = report["dropped_bosses"] if boss_only else report["dropped_heroes"]
	var seen := {}
	for raw in value:
		if not (raw is String):
			bucket.append(raw)
			continue
		var hero_type := String(raw)
		var definition: Variant = HERO_ROSTER.get(hero_type)
		if definition == null or (boss_only and not definition.is_boss_hero):
			bucket.append(hero_type)
			continue
		if seen.has(hero_type):
			report["dropped_duplicates"].append("hero:%s" % hero_type)
			continue
		seen[hero_type] = true
		result.append(hero_type)
	return result


static func _level_stats(value: Variant, report: Dictionary) -> Dictionary:
	var result := {}
	if not (value is Dictionary):
		return result
	var source: Dictionary = value
	for raw_key in source:
		if not (raw_key is String) or not String(raw_key).is_valid_int():
			report["dropped_level_stats"].append(str(raw_key))
			continue
		var level_number := int(raw_key)
		if level_number < 1 or level_number > MAX_LEVEL or str(level_number) != String(raw_key):
			report["dropped_level_stats"].append(str(raw_key))
			continue
		var entry: Variant = source[raw_key]
		if not (entry is Dictionary):
			report["dropped_level_stats"].append(str(raw_key))
			continue
		var converted := _stat_entry(entry as Dictionary)
		if converted.is_empty():
			report["dropped_level_stats"].append(str(raw_key))
			continue
		result[str(level_number)] = converted
	return result


static func _stat_entry(entry: Dictionary) -> Dictionary:
	var converted := {}
	for field in LevelStats.INTEGER_FIELDS:
		var number: Variant = _integer(entry.get(field, 0))
		if number == null or int(number) < 0:
			return {}
		converted[field] = int(number)
	if int(converted["wins"]) > int(converted["total_attempts"]):
		return {}
	return converted


static func _last_level(value: Variant, report: Dictionary) -> int:
	var number: Variant = _integer(value)
	if number == null:
		report["clamped_last_level"] = 1
		return 1
	if int(number) < 1:
		report["clamped_last_level"] = int(number)
		return 1
	if int(number) > MAX_LEVEL:
		report["clamped_last_level"] = int(number)
		return MAX_LEVEL
	return int(number)


static func _timestamp(value: Variant, now: float) -> float:
	if value is int or value is float:
		var number := float(value)
		if not is_nan(number) and not is_inf(number) and number >= 0.0:
			return number
	return now


static func _playtime(value: Variant) -> int:
	var number: Variant = _integer(value)
	return 0 if number == null or int(number) < 0 else int(number)


static func _difficulty(value: Variant, report: Dictionary) -> Variant:
	if value == null:
		return null
	if value is String and DIFFICULTIES.has(String(value)):
		return String(value)
	report["rejected_difficulty"] = str(value)
	return null
