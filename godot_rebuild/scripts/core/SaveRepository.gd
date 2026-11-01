class_name SaveRepository
extends RefCounted

## Native 3-slot save/progress repository. Writes only under user://godot_core/.
## Python saves/ remains untouched; import/export is explicit via CloudSaveCodec.
const NUM_SLOTS := 3
const REPEAT_REWARD := 200
var directory := "user://godot_core"
var current_slot := 1
var last_error := ""


func _init(dir_path := "user://godot_core") -> void:
	directory = dir_path


func slot_path(slot: int) -> String:
	return "%s/slot_%d.json" % [directory, slot]


func empty_save(now := 0.0) -> Dictionary:
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
		"replay_reward_counts": {},
		"redeemed_codes": [],
		"topup_history": [],
	}


func backfill(data: Dictionary, now := 0.0) -> Dictionary:
	var defaults := empty_save(now)
	for key: String in defaults:
		if not data.has(key):
			data[key] = defaults[key]
	return data


func set_current_slot(slot: int) -> bool:
	if slot < 1 or slot > NUM_SLOTS:
		return false
	current_slot = slot
	return true


func exists(slot: int) -> bool:
	return FileAccess.file_exists(slot_path(slot))


func load_slot(slot := -1, now := 0.0) -> Dictionary:
	if slot < 0:
		slot = current_slot
	last_error = ""
	if not exists(slot):
		return empty_save(now)
	var file := FileAccess.open(slot_path(slot), FileAccess.READ)
	if file == null:
		last_error = "Cannot read slot %d" % slot
		return empty_save(now)
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		last_error = "Slot %d corrupt" % slot
		return empty_save(now)
	return backfill(parsed, now)


func save_slot(data: Dictionary, slot := -1, now := 0.0) -> bool:
	if slot < 0:
		slot = current_slot
	if slot < 1 or slot > NUM_SLOTS:
		last_error = "Invalid slot"
		return false
	last_error = ""
	var err := DirAccess.make_dir_recursive_absolute(directory)
	if err != OK:
		last_error = "Cannot create save directory"
		return false
	data["slot_last_played"] = now
	if not data.has("slot_created"):
		data["slot_created"] = now
	var path := slot_path(slot)
	var tmp := path + ".tmp"
	var file := FileAccess.open(tmp, FileAccess.WRITE)
	if file == null:
		last_error = "Cannot write slot %d" % slot
		return false
	file.store_string(JSON.stringify(data, "\t"))
	file.close()
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)
	err = DirAccess.rename_absolute(tmp, path)
	if err != OK:
		last_error = "Cannot replace slot %d" % slot
		return false
	return true


func delete_slot(slot: int) -> bool:
	if not exists(slot):
		return false
	return DirAccess.remove_absolute(slot_path(slot)) == OK


func slot_info(slot: int) -> Dictionary:
	if not exists(slot):
		return {}
	var data := load_slot(slot)
	var completed: Array = data.get("completed_levels", [])
	var highest := 0
	for level: Variant in completed:
		highest = maxi(highest, int(level))
	return {
		"slot_num": slot,
		"meta_gold": int(data.get("meta_gold", 0)),
		"completed_levels": completed,
		"highest_level": highest,
		"last_played_level": int(data.get("last_played_level", 1)),
		"purchased_heroes": data.get("purchased_heroes", []),
		"slot_playtime_seconds": int(data.get("slot_playtime_seconds", 0)),
	}


static func empty_level_stats() -> Dictionary:
	return {
		"total_attempts": 0,
		"wins": 0,
		"best_score": 0,
		"best_time_seconds": 0,
		"total_playtime_seconds": 0,
		"total_kills": 0,
		"max_combo": 0,
	}


static func update_level_stats(
	data: Dictionary, level_number: int, match_stats: Dictionary
) -> Dictionary:
	if not data.has("level_stats"):
		data["level_stats"] = {}
	var key := str(level_number)
	var current: Dictionary = data.level_stats.get(key, empty_level_stats())
	for field: String in empty_level_stats():
		if not current.has(field):
			current[field] = 0
	var new_best_score := false
	var new_best_time := false
	current["total_attempts"] = int(current.total_attempts) + 1
	current["total_playtime_seconds"] = (
		int(current.total_playtime_seconds) + int(match_stats.get("playtime_seconds", 0))
	)
	current["total_kills"] = int(current.total_kills) + int(match_stats.get("kills", 0))
	current["max_combo"] = maxi(int(current.max_combo), int(match_stats.get("combo", 0)))
	if bool(match_stats.get("won", false)):
		current["wins"] = int(current.wins) + 1
		if int(match_stats.get("score", 0)) > int(current.best_score):
			current["best_score"] = int(match_stats.get("score", 0))
			new_best_score = true
		var match_time := int(match_stats.get("time_seconds", 0))
		if (
			match_time > 0
			and (int(current.best_time_seconds) == 0 or match_time < int(current.best_time_seconds))
		):
			current["best_time_seconds"] = match_time
			new_best_time = true
	data.level_stats[key] = current
	return {
		"is_new_best_score": new_best_score, "is_new_best_time": new_best_time, "new_stats": current
	}


static func is_level_unlocked(level_config: Dictionary, completed: Array) -> bool:
	var required: Variant = level_config.get("unlock_after_level", null)
	if required == null:
		return true
	return int(required) in completed


static func grant_match_result(
	data: Dictionary,
	level_number: int,
	level_config: Dictionary,
	victory: bool,
	is_replay: bool,
	difficulty: String,
	match_stats: Dictionary,
	bosses_defeated: Array,
	total_levels: int,
	now := 0.0
) -> Dictionary:
	var reward := 0
	var newly_unlocked: Array[String] = []
	if victory:
		var completed: Array = data.get("completed_levels", [])
		var counts: Dictionary = data.get("replay_reward_counts", {})
		var key := str(level_number)
		var count := int(counts.get(key, 0))
		if is_replay or level_number in completed:
			reward = (
				int(level_config.get("meta_gold_reward_replay", 1500))
				if count == 0
				else int(level_config.get("meta_gold_reward_replay_repeat", REPEAT_REWARD))
			)
			counts[key] = count + 1
		else:
			reward = int(level_config.get("meta_gold_reward_win", 3000))
		data["replay_reward_counts"] = counts
		var purchased: Array = data.get("purchased_heroes", [])
		var unlocked: Array = data.get("unlocked_bosses", [])
		for boss: Variant in bosses_defeated:
			var boss_type := str(boss)
			if boss_type not in unlocked:
				unlocked.append(boss_type)
			if boss_type not in purchased:
				purchased.append(boss_type)
				newly_unlocked.append(boss_type)
		data["purchased_heroes"] = purchased
		data["unlocked_bosses"] = unlocked
		if level_number not in completed:
			completed.append(level_number)
		data["completed_levels"] = completed
		data["last_played_level"] = level_number
		if completed.size() >= total_levels:
			data["run_difficulty"] = null
		elif data.get("run_difficulty", null) == null:
			data["run_difficulty"] = difficulty
	data["meta_gold"] = int(data.get("meta_gold", 0)) + reward
	data["slot_playtime_seconds"] = (
		int(data.get("slot_playtime_seconds", 0)) + int(match_stats.get("playtime_seconds", 0))
	)
	var stats_result := update_level_stats(data, level_number, match_stats)
	data["slot_last_played"] = now
	return {"reward": reward, "new_heroes": newly_unlocked, "stats": stats_result}


static func purchase_hero(data: Dictionary, hero_type: String, cost: int) -> bool:
	var purchased: Array = data.get("purchased_heroes", [])
	if hero_type in purchased or int(data.get("meta_gold", 0)) < cost:
		return false
	data["meta_gold"] = int(data.meta_gold) - cost
	purchased.append(hero_type)
	data["purchased_heroes"] = purchased
	return true


static func grant_voucher(data: Dictionary, code: String, gold: int, now_ms: int) -> Dictionary:
	var normalized := code.strip_edges().to_upper()
	var redeemed: Array = data.get("redeemed_codes", [])
	if normalized in redeemed:
		return {"ok": false, "reason": "already_redeemed", "gold": 0}
	if gold <= 0:
		return {"ok": false, "reason": "invalid_amount", "gold": 0}
	redeemed.append(normalized)
	if redeemed.size() > 50:
		redeemed = redeemed.slice(redeemed.size() - 50)
	data["redeemed_codes"] = redeemed
	data["meta_gold"] = int(data.get("meta_gold", 0)) + gold
	var history: Array = data.get("topup_history", [])
	history.append(
		{
			"id": "MA-%010d" % (now_ms % 10000000000),
			"kind": "voucher",
			"code": normalized,
			"gold": gold,
			"at": now_ms
		}
	)
	if history.size() > 50:
		history = history.slice(history.size() - 50)
	data["topup_history"] = history
	return {"ok": true, "reason": "ok", "gold": gold}


static func grant_topup(
	data: Dictionary, transaction_id: String, gold: int, now_ms: int
) -> Dictionary:
	var history: Array = data.get("topup_history", [])
	for entry: Dictionary in history:
		if str(entry.get("id", "")) == transaction_id:
			return {"ok": false, "reason": "already_granted", "gold": 0}
	if gold <= 0 or transaction_id.is_empty():
		return {"ok": false, "reason": "invalid_transaction", "gold": 0}
	data["meta_gold"] = int(data.get("meta_gold", 0)) + gold
	history.append({"id": transaction_id, "kind": "topup", "gold": gold, "at": now_ms})
	if history.size() > 50:
		history = history.slice(history.size() - 50)
	data["topup_history"] = history
	return {"ok": true, "reason": "ok", "gold": gold}
