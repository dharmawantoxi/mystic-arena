# SaveManager.gd — Port dari mobile/cloud_save.py + storage_paths.py
# Di Godot: pakai user:// + Google Play Games via plugin (godot Google Play Games)
#
# Update sesi ini (progresi level + menu utama): kunci save kini paritas
# _system.py SaveManager.get_empty_save() (baris 912-928) —
#   meta_gold             : mata uang Hero Shop (pygame: save_data['meta_gold'])
#   replay_reward_counts  : berapa kali replay-win sudah dibayar 1500
#                           (_core.py:2383-2389, key = str(level_number))
#   unlocked_bosses       : boss yang sudah dikalahkan (syarat beli hero boss)
#   last_played_level     : level terakhir dimainkan (tombol CONTINUE)
#   level_stats           : best score/waktu + kills/combo kumulatif per
#                           level (pygame: save_data['level_stats'] —
#                           ditulis update_level_stats tiap akhir match,
#                           dibaca badge NEW BEST! panel menang/kalah)
# Kunci lama ("gold", "unlocked_heroes") tetap dipertahankan supaya save
# Godot yang sudah ada tidak rusak; end_match() sekarang menulis ke "meta_gold".
extends Node

## Dipancarkan SETELAH file ditutup. Harness mengamati write asli pada
## user:// terisolasi, bukan mengganti save() dengan mock yang selalu PASS.
signal saved

const SAVE_PATH := "user://mystic_save.json"

## Default = paritas _system.py get_empty_save() + settings Godot.
## "unlocked_heroes" adalah padanan purchased_heroes pygame (kaizen granted
## sebagai starter, _core.py:1603-1608). Daftar inilah yang dibaca
## GameManager.purchased_heroes -> Hero._catchup_unlocks (catch-up starter),
## jadi isinya tidak boleh dipangkas/dimigrasi diam-diam.
var data: Dictionary = {
	"unlocked_heroes": ["kaizen"],
	"completed_levels": [],
	"gold": 0,
	"settings": {"sfx": 0.6, "bgm": 0.35, "quality": "medium"},
	# ── paritas _system.py (meta progresi) ──
	"meta_gold": 0,
	"replay_reward_counts": {},
	"unlocked_bosses": [],
	"last_played_level": 1,
	"level_stats": {},
}

func _ready():
	load_save()

func load_save():
	if FileAccess.file_exists(SAVE_PATH):
		var f = FileAccess.open(SAVE_PATH, FileAccess.READ)
		var parsed = JSON.parse_string(f.get_as_text())
		if parsed is Dictionary:
			data.merge(parsed, true)
			# Backfill kunci baru untuk save lama (paritas SaveManager.load
			# _system.py:894-901 yang setdefault() semua field meta).
			_backfill()
			print("[SaveManager] Loaded save: ", data)
	else:
		print("[SaveManager] No save, using defaults")

## setdefault semua kunci meta — save hasil versi Godot lama tidak punya
## meta_gold/replay_reward_counts, dan Dictionary.merge tidak menambah kunci
## yang nilainya null/absen di file.
func _backfill() -> void:
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
	# Starter hanya Kaizen. Unlock lama tidak pernah dicabut saat upgrade port.
	if not (data["unlocked_heroes"] is Array) or data["unlocked_heroes"].is_empty():
		data["unlocked_heroes"] = ["kaizen"]


func save():
	_backfill()
	var f = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f == null:
		push_error("[SaveManager] Cannot open file: " + SAVE_PATH)
		return
	f.store_string(JSON.stringify(data, "\t"))
	f.close()
	saved.emit()
	print("[SaveManager] Saved")
	# TODO: integrate godot Google Play Games plugin for cloud save
	# if OS.has_feature("android"):
	#     GooglePlayGames.save_snapshot("mystic_save", data)

# ══════════════════════════════════════════════════════════
#  HERO (padanan purchased_heroes pygame)
# ══════════════════════════════════════════════════════════

func unlock_hero(hero_type: String):
	if hero_type not in data["unlocked_heroes"]:
		data["unlocked_heroes"].append(hero_type)
		save()

func is_unlocked(hero_type: String) -> bool:
	return hero_type in data["unlocked_heroes"]

# ══════════════════════════════════════════════════════════
#  BOSS (padanan unlocked_bosses pygame)
# ══════════════════════════════════════════════════════════

## Boss dicatat dikalahkan begitu mati di match apa pun; jadi SYARAT beli
## hero boss di Hero Shop (pygame _unlock_hero_in_meta_shop _core.py:5311-5314).
## Hero-nya sendiri baru diberikan gratis kalau match DIMENANGKAN
## (GameManager._auto_unlock_defeated_boss_heroes).
func unlock_boss(boss_type: String) -> void:
	if not (data["unlocked_bosses"] is Array):
		data["unlocked_bosses"] = []
	if boss_type not in data["unlocked_bosses"]:
		data["unlocked_bosses"].append(boss_type)
		save()

func is_boss_unlocked(boss_type: String) -> bool:
	var arr = data.get("unlocked_bosses", [])
	return arr is Array and boss_type in arr

# ══════════════════════════════════════════════════════════
#  META GOLD + LEVEL
# ══════════════════════════════════════════════════════════

func meta_gold() -> int:
	return int(data.get("meta_gold", 0))

## Dipakai Hero Shop (beli hero) dan _grant_meta_reward (menambah reward).
func add_meta_gold(amount: int) -> void:
	data["meta_gold"] = meta_gold() + amount
	save()

func complete_level(lv: int):
	var completed = data["completed_levels"]
	if lv not in completed:
		completed.append(lv)
	data["last_played_level"] = lv
	save()

func is_level_completed(lv: int) -> bool:
	var completed = data.get("completed_levels", [])
	return completed is Array and lv in completed

# ══════════════════════════════════════════════════════════
#  LEVEL STATS (best per level — paritas _system.py:1022-1116)
# ══════════════════════════════════════════════════════════

## Default stat level (paritas SaveManager.get_level_stats: level tanpa
## catatan mengembalikan dict nol; 0 di best_time_seconds = belum pernah).
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


## Paritas SaveManager.get_level_stats: baca stat level (dict HIDUP bila
## sudah ada — mutasi update_level_stats langsung menulis ke save).
func get_level_stats(level_data: Dictionary, level_num: int) -> Dictionary:
	var stats_dict = level_data.get("level_stats", {})
	if not (stats_dict is Dictionary) or not stats_dict.has(str(level_num)):
		return default_level_stats()
	return stats_dict[str(level_num)]


## Paritas SaveManager.update_level_stats (_system.py:1050): update stat
## level dengan hasil match. attempts/playtime/kills/combo kumulatif SELALU
## naik (menang ATAU kalah); best_score/best_time/wins HANYA saat menang;
## flag is_new_best_* dipakai badge NEW BEST! di panel menang/kalah.
## Return {"is_new_best_score", "is_new_best_time", "new_stats"}.
func update_level_stats(level_data: Dictionary, level_num: int,
		match_stats: Dictionary) -> Dictionary:
	if not (level_data.get("level_stats") is Dictionary):
		level_data["level_stats"] = {}
	var current: Dictionary = get_level_stats(level_data, level_num)

	var is_new_best_score := false
	var is_new_best_time := false

	# Update total attempts
	current["total_attempts"] = int(current.get("total_attempts", 0)) + 1

	# Update total playtime (kumulatif)
	current["total_playtime_seconds"] = int(
		current.get("total_playtime_seconds", 0)) \
		+ int(match_stats.get("playtime_seconds", 0))

	# Update total kills (kumulatif)
	current["total_kills"] = int(current.get("total_kills", 0)) \
		+ int(match_stats.get("kills", 0))

	# Update max combo (all-time — JUGA saat kalah)
	if int(match_stats.get("combo", 0)) > int(current.get("max_combo", 0)):
		current["max_combo"] = int(match_stats.get("combo", 0))

	# HANYA update best score/time kalau WIN
	if bool(match_stats.get("won", false)):
		current["wins"] = int(current.get("wins", 0)) + 1

		# Best score (lebih tinggi lebih baik)
		if int(match_stats.get("score", 0)) > int(current.get("best_score", 0)):
			current["best_score"] = int(match_stats.get("score", 0))
			is_new_best_score = true

		# Best time (lebih rendah lebih baik; 0 = belum pernah)
		var match_time := int(match_stats.get("time_seconds", 0))
		if match_time > 0:
			var best_time := int(current.get("best_time_seconds", 0))
			if best_time == 0 or match_time < best_time:
				current["best_time_seconds"] = match_time
				is_new_best_time = true

	# Save back
	level_data["level_stats"][str(level_num)] = current

	return {
		"is_new_best_score": is_new_best_score,
		"is_new_best_time": is_new_best_time,
		"new_stats": current,
	}

# ══════════════════════════════════════════════════════════
#  SETTINGS (volume sfx/bgm — dipakai AudioManager + menu SETTINGS)
# ══════════════════════════════════════════════════════════

func get_setting(key: String, default: float = 1.0) -> float:
	var s = data.get("settings", {})
	if s is Dictionary and s.has(key):
		return float(s[key])
	return default

## Simpan SATU setting + langsung tulis file (menulis file 50x/detik saat
## slider digeser itu boros — menu memanggil ini di drag_ended, sedangkan
## pergeseran nilai diterapkan lewat AudioManager tanpa save).
func set_setting(key: String, value: float, persist: bool = true) -> void:
	if not (data["settings"] is Dictionary):
		data["settings"] = {}
	data["settings"][key] = value
	if persist:
		save()
