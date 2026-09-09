# SaveManager.gd — port _system.SaveManager + cloud payload protocol.
#
# Pygame adalah acuan perilaku. Godot menyimpan tiga working-copy slot di
# user://slot_1.json .. slot_3.json, lalu memuat slot aktif ke `data`.
# SAVE_PATH sengaja menunjuk slot 1 sebagai kompatibilitas dengan harness lama;
# kode produksi memakai slot_path(current_slot).
extends Node

## Dipancarkan SETELAH file slot ditutup. Harness mengamati write asli pada
## user:// terisolasi, bukan mengganti save() dengan mock yang selalu PASS.
signal saved

const NUM_SLOTS := 3
const LEGACY_SAVE_PATH := "user://progress.json"
const GODOT_LEGACY_SAVE_PATH := "user://mystic_save.json"
## Kompatibilitas harness lama; slot default Pygame adalah slot 1.
const SAVE_PATH := "user://slot_1.json"
const PAYLOAD_MAGIC := "MYSTIC_ARENA_BACKUP"
const PAYLOAD_VERSION := 1

var current_slot: int = 1

## Default = paritas _system.py get_empty_save() + settings Godot.
## "unlocked_heroes" adalah padanan purchased_heroes pygame (kaizen granted
## sebagai starter, _core.py:1603-1608). Daftar inilah yang dibaca
## GameManager.purchased_heroes -> Hero._catchup_unlocks.
var data: Dictionary = {
	"unlocked_heroes": ["kaizen"],
	"completed_levels": [],
	"gold": 0,
	"settings": {"sfx": 0.6, "bgm": 0.35, "quality": "medium"},
	"meta_gold": 0,
	"replay_reward_counts": {},
	"unlocked_bosses": [],
	"last_played_level": 1,
	"level_stats": {},
}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	load_save()


# ══════════════════════════════════════════════════════════
#  SLOT MANAGEMENT — _system.py:746-930
# ══════════════════════════════════════════════════════════

func slot_path(slot_num: int) -> String:
	return "user://slot_%d.json" % slot_num


func get_current_slot() -> int:
	return current_slot


## Pilih slot dan muat working copy-nya. Slot kosong menghasilkan default,
## tetapi belum membuat file sampai ada progres yang benar-benar disimpan.
func set_current_slot(slot_num: int, load_it: bool = true) -> bool:
	if slot_num < 1 or slot_num > NUM_SLOTS:
		return false
	current_slot = slot_num
	print("[SaveManager] Active slot: %d" % current_slot)
	if load_it:
		load_save()
	return true


func slot_exists(slot_num: int) -> bool:
	return slot_num >= 1 and slot_num <= NUM_SLOTS \
		and FileAccess.file_exists(slot_path(slot_num))


func get_all_slot_info() -> Array:
	var result: Array = []
	for slot_num in range(1, NUM_SLOTS + 1):
		result.append(get_slot_info(slot_num))
	return result


## Metadata yang dipakai layar SLOT_SELECT. Timestamp tetap disimpan di save,
## bukan dihitung dari wall-clock saat fixture/replay membaca data.
func get_slot_info(slot_num: int):
	if not slot_exists(slot_num):
		return null
	var parsed = _read_json(slot_path(slot_num))
	if not (parsed is Dictionary):
		return null
	var completed = parsed.get("completed_levels", [])
	if not (completed is Array):
		completed = []
	var highest := 0
	for lv in completed:
		highest = maxi(highest, int(lv))
	var purchased = parsed.get("unlocked_heroes", parsed.get("purchased_heroes", []))
	if not (purchased is Array):
		purchased = []
	var bosses = parsed.get("unlocked_bosses", [])
	if not (bosses is Array):
		bosses = []
	return {
		"slot_num": slot_num,
		"meta_gold": int(parsed.get("meta_gold", 0)),
		"completed_levels": completed.duplicate(),
		"highest_level": highest,
		"last_played_level": int(parsed.get("last_played_level", 1)),
		"purchased_heroes": purchased.duplicate(),
		"unlocked_bosses": bosses.duplicate(),
		"slot_created": float(parsed.get("slot_created", 0)),
		"slot_last_played": float(parsed.get("slot_last_played", 0)),
		"playtime_seconds": int(parsed.get("slot_playtime_seconds", 0)),
	}


func delete_slot(slot_num: int) -> bool:
	if not slot_exists(slot_num):
		return false
	var err := DirAccess.remove_absolute(slot_path(slot_num))
	if err == OK:
		if current_slot == slot_num:
			data = _empty_save()
		print("[SaveManager] Slot %d deleted" % slot_num)
		return true
	return false


## Port _system.SaveManager.migrate_legacy_save(): hanya progress.json ->
## slot_1 bila slot 1 belum ada. File lama dipertahankan sebagai backup.
func migrate_legacy_save() -> bool:
	if slot_exists(1):
		return false
	# Pygame's old desktop/mobile file is the oracle input. The previous Godot
	# port also used mystic_save.json; migrate it too so existing Godot players
	# do not lose progress when the slot system is introduced.
	var source := ""
	var backup := ""
	if FileAccess.file_exists(LEGACY_SAVE_PATH):
		source = LEGACY_SAVE_PATH
		backup = "user://progress_backup.json.old"
	elif FileAccess.file_exists(GODOT_LEGACY_SAVE_PATH):
		source = GODOT_LEGACY_SAVE_PATH
		backup = "user://mystic_save.json.old"
	else:
		return false
	var parsed = _read_json(source)
	if not (parsed is Dictionary):
		return false
	var now := float(Time.get_unix_time_from_system())
	parsed["slot_created"] = now
	parsed["slot_last_played"] = now
	parsed["slot_playtime_seconds"] = 0
	# Pygame legacy names the same permanent roster purchased_heroes; Godot's
	# previous schema calls it unlocked_heroes. Preserve both, but make the
	# Godot key the migrated source of truth.
	if not parsed.has("unlocked_heroes") and parsed.has("purchased_heroes") \
			and parsed["purchased_heroes"] is Array:
		parsed["unlocked_heroes"] = (parsed["purchased_heroes"] as Array).duplicate()
	if not _write_json(slot_path(1), parsed):
		return false
	# Pygame attempts the rename but migration remains successful if backup
	# rename fails. Do not overwrite an existing backup.
	if not FileAccess.file_exists(backup):
		DirAccess.rename_absolute(source, backup)
	print("[SaveManager] Legacy save migrated to Slot 1")
	return true


func load_save(slot_num: int = -1) -> Dictionary:
	if slot_num >= 1 and slot_num <= NUM_SLOTS:
		current_slot = slot_num
	migrate_legacy_save()
	var path := slot_path(current_slot)
	var parsed = _read_json(path)
	if parsed is Dictionary:
		data = parsed.duplicate(true)
		_backfill()
		print("[SaveManager] Loaded slot %d" % current_slot)
		return data
	data = _empty_save()
	print("[SaveManager] Slot %d empty, using defaults" % current_slot)
	return data


func save() -> bool:
	_backfill()
	var path := slot_path(current_slot)
	var now := float(Time.get_unix_time_from_system())
	if not data.has("slot_created") or float(data.get("slot_created", 0)) <= 0.0:
		data["slot_created"] = now
	data["slot_last_played"] = now
	if _write_json(path, data):
		saved.emit()
		print("[SaveManager] Slot %d saved" % current_slot)
		return true
	return false


func _read_json(path: String):
	if not FileAccess.file_exists(path):
		return null
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return null
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	return parsed


func _write_json(path: String, value: Dictionary) -> bool:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("[SaveManager] Cannot open file: " + path)
		return false
	f.store_string(JSON.stringify(value, "\t"))
	f.close()
	return true


func _empty_save() -> Dictionary:
	return {
		"unlocked_bosses": [],
		"unlocked_heroes": ["kaizen"],
		"meta_gold": 0,
		"completed_levels": [],
		"last_played_level": 1,
		"slot_created": 0.0,
		"slot_last_played": 0.0,
		"slot_playtime_seconds": 0,
		"level_stats": {},
		"run_difficulty": null,
		"replay_reward_counts": {},
		"settings": {"sfx": 0.6, "bgm": 0.35, "quality": "medium"},
		"gold": 0,
	}


## setdefault semua kunci meta. Unlock lama tidak pernah dicabut.
func _backfill() -> void:
	# Legacy Pygame slots used purchased_heroes; do not discard that roster.
	if not data.has("unlocked_heroes") and data.has("purchased_heroes") \
			and data["purchased_heroes"] is Array:
		data["unlocked_heroes"] = (data["purchased_heroes"] as Array).duplicate()
	var defaults: Dictionary = {
		"meta_gold": 0,
		"replay_reward_counts": {},
		"unlocked_bosses": [],
		"last_played_level": 1,
		"completed_levels": [],
		"unlocked_heroes": ["kaizen"],
		"settings": {"sfx": 0.6, "bgm": 0.35, "quality": "medium"},
		"level_stats": {},
	}
	for key in defaults:
		if not data.has(key) or data[key] == null:
			data[key] = defaults[key]
	# Starter hanya Kaizen. Unlock lama tidak pernah dicabut, tetapi save
	# kosong/malformed harus tetap mendapat starter seperti port sebelumnya.
	if not (data["unlocked_heroes"] is Array) or data["unlocked_heroes"].is_empty():
		data["unlocked_heroes"] = ["kaizen"]


# ══════════════════════════════════════════════════════════
#  HERO / BOSS / LEVEL HELPERS
# ══════════════════════════════════════════════════════════

func unlock_hero(hero_type: String) -> void:
	if hero_type not in data["unlocked_heroes"]:
		data["unlocked_heroes"].append(hero_type)
		save()


func is_unlocked(hero_type: String) -> bool:
	return hero_type in data.get("unlocked_heroes", [])


func unlock_boss(boss_type: String) -> void:
	if not (data["unlocked_bosses"] is Array):
		data["unlocked_bosses"] = []
	if boss_type not in data["unlocked_bosses"]:
		data["unlocked_bosses"].append(boss_type)
		save()


func is_boss_unlocked(boss_type: String) -> bool:
	var arr = data.get("unlocked_bosses", [])
	return arr is Array and boss_type in arr


func meta_gold() -> int:
	return int(data.get("meta_gold", 0))


func add_meta_gold(amount: int) -> void:
	data["meta_gold"] = meta_gold() + amount
	save()


## Atomic state update untuk transaksi Hero Shop: satu append, satu potong,
## satu write. Validasi katalog/boss/saldo tetap dilakukan MainMenu seperti
## `_unlock_hero_in_meta_shop` Pygame.
func commit_hero_purchase(hero_type: String, cost: int) -> bool:
	var heroes = data.get("unlocked_heroes", [])
	if hero_type.is_empty() or cost < 0 or not (heroes is Array) \
			or hero_type in heroes or meta_gold() < cost:
		return false
	# Keep the in-memory working copy atomic if the actual file write fails.
	var before := data.duplicate(true)
	data["meta_gold"] = meta_gold() - cost
	heroes.append(hero_type)
	data["unlocked_heroes"] = heroes
	if save():
		return true
	data = before
	return false


func complete_level(lv: int) -> void:
	var completed = data.get("completed_levels", [])
	if not (completed is Array):
		completed = []
	if lv not in completed:
		completed.append(lv)
	data["completed_levels"] = completed
	data["last_played_level"] = lv
	save()


func is_level_completed(lv: int) -> bool:
	var completed = data.get("completed_levels", [])
	return completed is Array and lv in completed


# ══════════════════════════════════════════════════════════
#  LEVEL STATS + FORMATTER — _system.py:1022-1119
# ══════════════════════════════════════════════════════════

func default_level_stats() -> Dictionary:
	return {
		"best_score": 0,
		"best_time_seconds": 0,
		"total_attempts": 0,
		"wins": 0,
		"total_kills": 0,
		"max_combo": 0,
		"total_playtime_seconds": 0,
	}


func get_level_stats(level_data: Dictionary, level_num: int) -> Dictionary:
	var stats_dict = level_data.get("level_stats", {})
	if not (stats_dict is Dictionary) or not stats_dict.has(str(level_num)):
		return default_level_stats()
	return stats_dict[str(level_num)]


func format_time(seconds: int) -> String:
	if seconds == 0:
		return "--:--"
	return "%d:%02d" % [int(seconds / 60), int(seconds % 60)]


func update_level_stats(level_data: Dictionary, level_num: int,
		match_stats: Dictionary) -> Dictionary:
	if not (level_data.get("level_stats") is Dictionary):
		level_data["level_stats"] = {}
	var current: Dictionary = get_level_stats(level_data, level_num)
	var is_new_best_score := false
	var is_new_best_time := false
	current["total_attempts"] = int(current.get("total_attempts", 0)) + 1
	current["total_playtime_seconds"] = int(current.get("total_playtime_seconds", 0)) \
		+ int(match_stats.get("playtime_seconds", 0))
	current["total_kills"] = int(current.get("total_kills", 0)) \
		+ int(match_stats.get("kills", 0))
	if int(match_stats.get("combo", 0)) > int(current.get("max_combo", 0)):
		current["max_combo"] = int(match_stats.get("combo", 0))
	if bool(match_stats.get("won", false)):
		current["wins"] = int(current.get("wins", 0)) + 1
		if int(match_stats.get("score", 0)) > int(current.get("best_score", 0)):
			current["best_score"] = int(match_stats.get("score", 0))
			is_new_best_score = true
		var match_time := int(match_stats.get("time_seconds", 0))
		if match_time > 0:
			var best_time := int(current.get("best_time_seconds", 0))
			if best_time == 0 or match_time < best_time:
				current["best_time_seconds"] = match_time
				is_new_best_time = true
	level_data["level_stats"][str(level_num)] = current
	return {
		"is_new_best_score": is_new_best_score,
		"is_new_best_time": is_new_best_time,
		"new_stats": current,
	}


# ══════════════════════════════════════════════════════════
#  CLOUD PAYLOAD — port mobile/cloud_save.py serialization layer
# ══════════════════════════════════════════════════════════

func _canonical_payload_without_checksum(payload: Dictionary) -> String:
	var body := payload.duplicate(true)
	body.erase("checksum")
	return JSON.stringify(body, "", true)


func compute_payload_checksum(payload: Dictionary) -> String:
	var ctx := HashingContext.new()
	ctx.start(HashingContext.HASH_SHA256)
	ctx.update(_canonical_payload_without_checksum(payload).to_utf8_buffer())
	return ctx.finish().hex_encode()


func build_payload() -> Dictionary:
	var slots := {}
	for slot_num in range(1, NUM_SLOTS + 1):
		var parsed = _read_json(slot_path(slot_num))
		if parsed is Dictionary:
			slots[str(slot_num)] = parsed
	var payload: Dictionary = {
		"magic": PAYLOAD_MAGIC,
		"version": PAYLOAD_VERSION,
		"exported_at": float(Time.get_unix_time_from_system()),
		"slots": slots,
		"settings": data.get("settings", {}).duplicate(true),
	}
	payload["checksum"] = compute_payload_checksum(payload)
	return payload


func parse_payload(text: String) -> Dictionary:
	var parsed = JSON.parse_string(text)
	if not (parsed is Dictionary):
		return {"ok": false, "error": "File corrupt (unexpected structure)"}
	if parsed.get("magic") != PAYLOAD_MAGIC:
		return {"ok": false, "error": "Not a Mystic Arena save file"}
	var version := int(parsed.get("version", 0))
	if version < 1 or version > PAYLOAD_VERSION:
		return {"ok": false, "error": "Save version %d not supported" % version}
	if not (parsed.get("slots") is Dictionary) or (parsed["slots"] as Dictionary).is_empty():
		return {"ok": false, "error": "Save contains no data"}
	if str(parsed.get("checksum", "")) != compute_payload_checksum(parsed):
		return {"ok": false, "error": "File corrupt (checksum mismatch)"}
	return {"ok": true, "payload": parsed}


func apply_payload(payload: Dictionary) -> bool:
	if payload.get("magic") != PAYLOAD_MAGIC or not (payload.get("slots") is Dictionary):
		return false
	var slots: Dictionary = payload["slots"]
	for slot_num in range(1, NUM_SLOTS + 1):
		var path := slot_path(slot_num)
		var key := str(slot_num)
		if not slots.has(key):
			if FileAccess.file_exists(path):
				DirAccess.remove_absolute(path)
			continue
		var slot_data = slots[key]
		if slot_data is Dictionary:
			if not _write_json(path, slot_data):
				return false
	if payload.get("settings") is Dictionary:
		data["settings"] = payload["settings"].duplicate(true)
	load_save(current_slot)
	return true


# ══════════════════════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════════════════════

func get_setting(key: String, default: float = 1.0) -> float:
	var s = data.get("settings", {})
	if s is Dictionary and s.has(key):
		return float(s[key])
	return default


func set_setting(key: String, value: float, persist: bool = true) -> void:
	if not (data["settings"] is Dictionary):
		data["settings"] = {}
	data["settings"][key] = value
	if persist:
		save()
