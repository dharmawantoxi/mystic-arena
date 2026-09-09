# ProgressionParityTest — FASE 20A/B/C.
#
# Replay production nodes/systems against the three insert-only oracle
# sections generated from the original Pygame SaveManager/Menu:
#   level_select_stats : BEST SCORE/BEST TIME view model + format_time
#   hero_shop_meta     : validasi + transaksi pembelian Hero Shop
#   save_slots         : tiga slot, metadata, legacy migration
#   save_slot_delete   : create/delete + delete kosong tidak mengubah state
#
# No pixel/audio parity is claimed. Wall-clock metadata is reduced to the
# presence flags used by the Pygame oracle. All writes use the isolated user://
# directory supplied by CI.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainMenuScript = preload("res://scenes/ui/MainMenu.gd")

var _failures: int = 0
var _checks: int = 0
var _save_before: Dictionary = {}
var _file_before: Dictionary = {}
var _slot_before: int = 1
var _error_messages: Array[String] = []
var _done: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	_slot_before = SaveManager.get_current_slot()
	_file_before = _snapshot_files()
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("level_select_stats") \
			or not fixture.has("hero_shop_meta") or not fixture.has("save_slots") \
			or not fixture.has("save_slot_delete"):
		_fail("fixture FASE 20 belum ada — jalankan tools/test_godot_match_parity.py --write-fixture")
		_restore_all()
		_finish()
		return

	var determinism: Dictionary = fixture.get("phase20_determinism", {})
	_expect(bool(determinism.get("identical", false)), "dua seed oracle FASE 20 identik")
	_expect(determinism.get("seeds", []) == [20260920, 42420],
		"seed oracle FASE 20 tercatat")
	_expect((determinism.get("rng_sites", []) as Array).is_empty(),
		"jalur FASE 20 tidak memakai RNG gameplay")

	_test_level_select(fixture["level_select_stats"])
	_test_hero_shop(fixture["hero_shop_meta"])
	_test_save_slots(fixture["save_slots"])
	_test_save_slot_delete(fixture["save_slot_delete"])
	_test_cloud_payload()
	_restore_all()
	_finish()


func _test_level_select(section: Dictionary) -> void:
	_expect(SaveManager.format_time(0) == str(section["rules"]["time_zero"]),
		"format_time 0")
	_expect(SaveManager.format_time(65) == str(section["rules"]["time_65"]),
		"format_time 65")
	_expect(SaveManager.format_time(3723) == str(section["rules"]["time_3723"]),
		"format_time 3723")

	var menu = MainMenuScript.new()
	for row in section["cases"]:
		var case: Dictionary = row
		SaveManager.data = {"level_stats": {str(case["level"]): case["stats"]}}
		var got: Dictionary = menu.level_stat_display(int(case["level"]))
		var tag := "level stats %s" % str(case["name"])
		_expect(bool(got["has_stats"]) == bool(case["has_stats"]), tag + " has_stats")
		_expect(str(got["score_text"]) == str(case["score_text"]), tag + " score")
		_expect(str(got["time_text"]) == str(case["time_text"]), tag + " time")
		_expect(int(got["attempts"]) == int(case["attempts"]), tag + " attempts")
		_expect(int(got["wins"]) == int(case["wins"]), tag + " wins")
		_expect(int(got["win_rate"]) == int(case["win_rate"]), tag + " win rate")
	menu.free()


func _test_hero_shop(section: Dictionary) -> void:
	var catalog: Dictionary = section["catalog"]
	_expect(int(catalog["boss_cost"]) == 4500, "Hero Shop boss cost oracle")
	_expect(not str(catalog["boss_requirement"]).is_empty(), "Hero Shop boss gate oracle")
	var menu = MainMenuScript.new()
	for row in section["cases"]:
		var case: Dictionary = row
		var before: Dictionary = case["before"]
		SaveManager.data = {
			"unlocked_heroes": (before["purchased"] as Array).duplicate(),
			"unlocked_bosses": (before["bosses"] as Array).duplicate(),
			"meta_gold": int(before["meta_gold"]),
			"level_stats": {}, "completed_levels": [],
			"settings": {"sfx": 0.6, "bgm": 0.35},
		}
		var result: Dictionary = menu.hero_shop_transaction(str(case["hero"]))
		var after: Dictionary = {
			"purchased": (SaveManager.data.get("unlocked_heroes", []) as Array).duplicate(),
			"bosses": (SaveManager.data.get("unlocked_bosses", []) as Array).duplicate(),
			"meta_gold": SaveManager.meta_gold(),
		}
		var tag := "hero shop %s" % str(case["name"])
		var want_after: Dictionary = case["after"]
		_expect(after == want_after, tag + " state")
		var want_ok := str(case["result"]) == "purchased"
		_expect(bool(result.get("ok", false)) == want_ok, tag + " accepted")
		if want_ok:
			_expect(str(result.get("reason")) == "purchased", tag + " reason")
			_expect(int(result.get("cost", -1)) == int(case["cost"]), tag + " cost")
		else:
			_expect(after == before, tag + " rejected atomically")
	menu.free()


func _test_save_slots(section: Dictionary) -> void:
	_expect(int(section["rules"]["num_slots"]) == SaveManager.NUM_SLOTS,
		"jumlah slot")
	var cases: Array = section["cases"]
	_clean_phase20_files()
	SaveManager.set_current_slot(1, false)
	SaveManager.data = {"unlocked_heroes": ["kaizen"], "level_stats": {}}
	var slots: Array = []
	for i in range(1, SaveManager.NUM_SLOTS + 1):
		slots.append(_slot_view(SaveManager.get_slot_info(i)))
	_expect(slots == cases[0]["slots"], "slot kosong")
	_expect(SaveManager.get_current_slot() == int(cases[0]["current"]), "slot aktif default")

	_save_slot(1, {"meta_gold": 120, "completed_levels": [1, 3],
		"last_played_level": 3, "unlocked_heroes": ["kaizen", "abaddon"],
		"unlocked_bosses": ["abaddon"], "slot_playtime_seconds": 3600})
	_save_slot(2, {"meta_gold": 900, "completed_levels": [1],
		"last_played_level": 1, "unlocked_heroes": ["kaizen"],
		"unlocked_bosses": [], "slot_playtime_seconds": 90})
	slots = []
	for i in range(1, SaveManager.NUM_SLOTS + 1):
		slots.append(_slot_view(SaveManager.get_slot_info(i)))
	_expect(slots == cases[1]["slots"], "metadata dua slot")
	_expect(SaveManager.get_current_slot() == int(cases[1]["current"]), "slot aktif setelah save")

	SaveManager.set_current_slot(2, true)
	var selected: Dictionary = {
		"current": SaveManager.get_current_slot(),
		"loaded": _slot_view(SaveManager.get_slot_info(2)),
		"loaded_gold": SaveManager.meta_gold(),
	}
	_expect(selected == cases[2], "memilih dan memuat slot 2")

	_clean_phase20_files()
	var legacy := {"meta_gold": 777, "completed_levels": [4],
		"purchased_heroes": ["kaizen", "gornak"]}
	_write_json("user://progress.json", legacy)
	SaveManager.set_current_slot(1, false)
	var migrated := SaveManager.migrate_legacy_save()
	var legacy_info: Dictionary = _slot_view(SaveManager.get_slot_info(1))
	var migrated_view := {
		"migrated": migrated,
		"slot1": {"meta_gold": int(legacy_info["meta_gold"]),
			"completed_levels": legacy_info["completed_levels"],
			"purchased_heroes": legacy_info["purchased_heroes"],
			"has_created": bool(legacy_info["has_created"]),
			"has_last_played": bool(legacy_info["has_last_played"]),
			"playtime_seconds": int(legacy_info["playtime_seconds"])},
		"legacy_exists": FileAccess.file_exists("user://progress.json"),
		"backup_exists": FileAccess.file_exists("user://progress_backup.json.old"),
	}
	_expect(migrated_view == cases[3], "migrasi legacy ke slot 1")

	_clean_phase20_files()
	_write_json("user://slot_1.json", {"meta_gold": 11})
	_write_json("user://progress.json", {"meta_gold": 99})
	var collision := SaveManager.migrate_legacy_save()
	var collision_view := {"migrated": collision,
		"slot1_gold": int((JSON.parse_string(FileAccess.get_file_as_string("user://slot_1.json")) as Dictionary).get("meta_gold", 0)),
		"legacy_exists": FileAccess.file_exists("user://progress.json")}
	_expect(collision_view == cases[4], "legacy tidak overwrite slot 1")


func _test_save_slot_delete(expected: Dictionary) -> void:
	_clean_phase20_files()
	SaveManager.set_current_slot(1, false)
	SaveManager.data = {"unlocked_heroes": ["kaizen"], "level_stats": {}}
	_save_slot(1, {"meta_gold": 321, "completed_levels": [1],
		"unlocked_heroes": ["kaizen"]})
	var created_info = SaveManager.get_slot_info(1)
	var view := {
		"created": {"exists": SaveManager.slot_exists(1),
			"meta_gold": int(created_info["meta_gold"]) if created_info != null else -1},
		"deleted": SaveManager.delete_slot(1),
		"empty_after_delete": SaveManager.get_slot_info(1) == null,
		"empty_delete_returns_false": not SaveManager.delete_slot(1),
	}
	_expect(view == expected, "slot create + delete + empty delete")


func _test_cloud_payload() -> void:
	_clean_phase20_files()
	SaveManager.set_current_slot(1, false)
	SaveManager.data = {"unlocked_heroes": ["kaizen"], "meta_gold": 42,
		"completed_levels": [1], "settings": {"sfx": 0.5, "bgm": 0.25}}
	SaveManager.save()
	var payload: Dictionary = SaveManager.build_payload()
	_expect(str(payload.get("magic")) == SaveManager.PAYLOAD_MAGIC, "cloud payload magic")
	_expect(int(payload.get("version", 0)) == SaveManager.PAYLOAD_VERSION, "cloud payload version")
	var parsed: Dictionary = SaveManager.parse_payload(JSON.stringify(payload))
	_expect(bool(parsed.get("ok", false)), "cloud payload checksum valid")
	var tampered: Dictionary = payload.duplicate(true)
	tampered["checksum"] = "0".repeat(64)
	var bad: Dictionary = SaveManager.parse_payload(JSON.stringify(tampered))
	_expect(not bool(bad.get("ok", false)), "cloud payload checksum menolak korupsi")


func _save_slot(slot_num: int, value: Dictionary) -> void:
	SaveManager.set_current_slot(slot_num, false)
	SaveManager.data = value.duplicate(true)
	SaveManager.save()


func _slot_view(info) -> Variant:
	if info == null:
		return null
	return {
		"slot_num": int(info["slot_num"]),
		"meta_gold": int(info["meta_gold"]),
		"completed_levels": (info["completed_levels"] as Array).duplicate(),
		"highest_level": int(info["highest_level"]),
		"last_played_level": int(info["last_played_level"]),
		"purchased_heroes": (info["purchased_heroes"] as Array).duplicate(),
		"unlocked_bosses": (info["unlocked_bosses"] as Array).duplicate(),
		"playtime_seconds": int(info["playtime_seconds"]),
		"has_created": float(info["slot_created"]) > 0.0,
		"has_last_played": float(info["slot_last_played"]) > 0.0,
	}


func _clean_phase20_files() -> void:
	for slot_num in range(1, SaveManager.NUM_SLOTS + 1):
		var path := SaveManager.slot_path(slot_num)
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)
	for path in [SaveManager.LEGACY_SAVE_PATH, "user://progress_backup.json.old"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)


func _write_json(path: String, value: Dictionary) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(value))
	f.close()


func _snapshot_files() -> Dictionary:
	var result := {}
	for slot_num in range(1, SaveManager.NUM_SLOTS + 1):
		var path := SaveManager.slot_path(slot_num)
		result[path] = FileAccess.get_file_as_string(path) if FileAccess.file_exists(path) else null
	for path in [SaveManager.LEGACY_SAVE_PATH, "user://progress_backup.json.old"]:
		result[path] = FileAccess.get_file_as_string(path) if FileAccess.file_exists(path) else null
	return result


func _restore_all() -> void:
	_clean_phase20_files()
	for path in _file_before:
		var content = _file_before[path]
		if content == null:
			continue
		var f := FileAccess.open(path, FileAccess.WRITE)
		f.store_string(str(content))
		f.close()
	SaveManager.current_slot = _slot_before
	SaveManager.data = _save_before


func _expect(ok: bool, message: String) -> void:
	_checks += 1
	if not ok:
		_fail(message)


func _fail(message: String) -> void:
	_failures += 1
	_error_messages.append(message)
	push_error("[ProgressionParityTest] " + message)


func _finish() -> void:
	if _failures == 0:
		print("[ProgressionParityTest] PASS (%d checks)" % _checks)
	else:
		push_error("[ProgressionParityTest] FAIL: %d/%d checks" % [_failures, _checks])
	_done = true
	get_tree().quit()
