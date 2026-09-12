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
# ══════════════════════════════════════════════════════════
#  FASE 21 — MULTI-SLOT SAVE + MIGRASI LEGACY (TANPA CLOUD)
# ══════════════════════════════════════════════════════════
# Paritas _system.py:746-1020: tiga slot (`slot_1.json` .. `slot_3.json`),
# metadata per slot (`slot_created` / `slot_last_played` /
# `slot_playtime_seconds`), migrasi SEKALI dari berkas legacy ke slot 1,
# `delete_slot`, `get_slot_info`/`get_all_slot_info`, `format_playtime`,
# dan `format_last_played`.
#
# PETA NAMA LEGACY: berkas tunggal lama Godot adalah `user://mystic_save.
# json` (BUKAN `progress.json` seperti pygame - port Godot tidak pernah
# punya berkas itu), jadi `LEGACY_SAVE_FILE` menunjuk ke sana dan setelah
# migrasi dipindahkan ke `mystic_save_backup.json.old`, persis pola pygame
# `progress.json -> progress_backup.json.old`. Save pengguna TIDAK pernah
# dihapus: migrasi hanya jalan kalau slot 1 masih kosong, dan berkas lama
# tidak dibuang (cuma di-rename).
#
# CLOUD SAVE (`mobile/cloud_save.py`) TIDAK ikut diport - di luar scope
# FASE 21; ketiadaannya tidak mengubah state yang dikunci oracle.
extends Node

## Dipancarkan SETELAH file ditutup. Harness mengamati write asli pada
## user:// terisolasi, bukan mengganti save() dengan mock yang selalu PASS.
signal saved

## Jumlah slot — paritas `NUM_SLOTS` _system.py:746.
const NUM_SLOTS := 3
## Pola nama berkas slot — paritas `get_slot_file` _system.py:765-767.
const SLOT_PATH_TEMPLATE := "user://slot_%d.json"
## Berkas save TUNGGAL warisan port Godot (lihat catatan peta nama di file
## ini, bagian FASE 21).
const LEGACY_SAVE_FILE := "user://mystic_save.json"
## Hasil rename berkas legacy setelah migrasi — paritas `progress_backup.
## json.old` _system.py:834-836.
const LEGACY_BACKUP_FILE := "user://mystic_save_backup.json.old"

# FASE 34: pembanding anggota list semantik Python (`x in list` memakai ==,
# jadi 3 cocok dengan 3.0) — satu implementasi dipakai is_level_completed dan
# LevelDB.is_level_unlocked. Lihat komentar is_level_completed.
const LevelDBScript = preload("res://scripts/core/LevelDB.gd")
## Nama bulan singkat locale C — dipakai `format_last_played` pada cabang
## tanggal (paritas `time.strftime("%d %b %Y")`).
const MONTH_ABBR := ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
	"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

## Berkas slot AKTIF — mengikuti `current_slot`. Dulu `const` yang selalu
## "user://mystic_save.json"; sekarang VAR karena sepuluh harness lama
## membaca/menulis jalur ini untuk snapshot & restore, dan mereka harus
## ikut berpindah bersama slot aktif.
var SAVE_PATH: String = SLOT_PATH_TEMPLATE % 1
## Slot aktif untuk save/load tanpa argumen — paritas `SaveManager.
## _current_slot` _system.py:759 (default 1).
var current_slot: int = 1

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
	# Migrasi legacy dijalankan sebelum load pertama — paritas SaveManager.
	# load _system.py:884 yang memanggil migrate_legacy_save() lebih dulu.
	load_save()


# ══════════════════════════════════════════════════════════
#  SLOT (paritas _system.py:763-798)
# ══════════════════════════════════════════════════════════

## Jalur berkas slot — paritas `get_slot_file` _system.py:765-767.
func slot_path(slot_num: int) -> String:
	return SLOT_PATH_TEMPLATE % slot_num


## Slot aktif — paritas `get_current_slot` _system.py:770-772.
func get_current_slot() -> int:
	return current_slot


## Ganti slot aktif — paritas `set_current_slot` _system.py:775-780:
## nomor di luar 1..NUM_SLOTS DIABAIKAN (slot aktif tidak berubah).
func set_current_slot(slot_num: int) -> void:
	if slot_num < 1 or slot_num > NUM_SLOTS:
		return
	current_slot = slot_num
	SAVE_PATH = slot_path(slot_num)
	print("[SaveManager] Active slot: %d" % slot_num)


## `user://` selalu ada di Godot — padanan `ensure_save_dir` _system.py:782.
func ensure_save_dir() -> void:
	pass


## Ada berkas save di slot ini? — paritas `slot_exists` _system.py:788-795.
func slot_exists(slot_num: int) -> bool:
	return FileAccess.file_exists(slot_path(slot_num))


# ══════════════════════════════════════════════════════════
#  MIGRASI LEGACY -> SLOT 1 (paritas _system.py:797-845)
# ══════════════════════════════════════════════════════════

## Pindahkan save tunggal lama ke slot 1. Berjalan hanya kalau berkas
## legacy ADA dan slot 1 MASIH KOSONG; kalau gagal (JSON rusak / slot 1
## sudah ada) mengembalikan false dan tidak menyentuh apa pun — paritas
## persis `migrate_legacy_save`, termasuk rename berkas lama ke
## `*_backup.json.old` (bukan dihapus).
func migrate_legacy_save() -> bool:
	if not FileAccess.file_exists(LEGACY_SAVE_FILE):
		return false
	var slot_1 := slot_path(1)
	if FileAccess.file_exists(slot_1):
		# Slot 1 sudah ada — jangan menimpa save yang lebih baru.
		return false

	var f := FileAccess.open(LEGACY_SAVE_FILE, FileAccess.READ)
	if f == null:
		return false
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	if not (parsed is Dictionary):
		# Paritas jalur exception pygame: berkas rusak -> gagal tanpa efek.
		print("[SaveManager] Migration failed: legacy save is not an object")
		return false

	var migrated: Dictionary = parsed
	var now := Time.get_unix_time_from_system()
	migrated["slot_created"] = now
	migrated["slot_last_played"] = now
	migrated["slot_playtime_seconds"] = 0

	var w := FileAccess.open(slot_1, FileAccess.WRITE)
	if w == null:
		print("[SaveManager] Migration failed: cannot write %s" % slot_1)
		return false
	w.store_string(JSON.stringify(migrated, "\t"))
	w.close()
	print("[SaveManager] Legacy save migrated to Slot 1")

	# Rename berkas lama (backup) — kegagalan rename TIDAK membatalkan
	# migrasi, sama seperti `except: pass` di pygame.
	var err := DirAccess.rename_absolute(
		ProjectSettings.globalize_path(LEGACY_SAVE_FILE),
		ProjectSettings.globalize_path(LEGACY_BACKUP_FILE))
	if err != OK:
		print("[SaveManager] Legacy backup skipped (err %d)" % err)
	return true


# ══════════════════════════════════════════════════════════
#  SAVE / LOAD (paritas _system.py:847-911)
# ══════════════════════════════════════════════════════════

## Tulis `data` ke slot (default = slot aktif) — paritas `save`
## _system.py:847-876: `slot_last_played` SELALU diperbarui, `slot_created`
## hanya dibuat kalau belum ada. CLOUD auto-upload pygame sengaja tidak
## diport (lihat catatan FASE 21 di kepala berkas).
func save(slot_num: int = -1) -> void:
	_backfill(data)
	var target := current_slot if slot_num < 0 else slot_num
	var now := Time.get_unix_time_from_system()
	data["slot_last_played"] = now
	if not data.has("slot_created") or data["slot_created"] == null:
		data["slot_created"] = now
	var f = FileAccess.open(slot_path(target), FileAccess.WRITE)
	if f == null:
		push_error("[SaveManager] Cannot open file: " + slot_path(target))
		return
	f.store_string(JSON.stringify(data, "\t"))
	f.close()
	saved.emit()
	print("[SaveManager] Slot %d saved!" % target)


## Baca slot (default = slot aktif) — paritas `load` _system.py:878-911:
## migrasi legacy dipicu lebih dulu, berkas yang tidak ada/rusak
## mengembalikan `get_empty_save()`, dan kunci yang absen di-backfill
## (setdefault) tanpa menimpa nilai yang sudah tersimpan.
func load_slot(slot_num: int = -1) -> Dictionary:
	var target := current_slot if slot_num < 0 else slot_num
	migrate_legacy_save()
	var path := slot_path(target)
	if FileAccess.file_exists(path):
		var f = FileAccess.open(path, FileAccess.READ)
		if f != null:
			var parsed = JSON.parse_string(f.get_as_text())
			f.close()
			if parsed is Dictionary:
				var loaded: Dictionary = parsed
				_apply_defaults(loaded)
				print("[SaveManager] Slot %d loaded!" % target)
				return loaded
			print("[SaveManager] Slot %d is not an object — using empty save"
				% target)
	return get_empty_save()


## Muat slot aktif ke `data` — padanan `Menu.reload_progress` yang
## menugaskan ulang `self.save_data = SaveManager.load()`.
func load_save() -> void:
	data = load_slot(current_slot)
	print("[SaveManager] Loaded save: ", data)


## Save kosong — paritas `get_empty_save` _system.py:913-928 DITAMBAH
## kunci khusus Godot (`unlocked_heroes` = purchased_heroes pygame,
## `gold`, `settings`, `replay_reward_counts`) supaya hasilnya tetap save
## yang valid bagi seluruh sistem produksi.
func get_empty_save() -> Dictionary:
	var now := Time.get_unix_time_from_system()
	return {
		# ── paritas _system.py get_empty_save (urutan kunci sama) ──
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
		# ── kunci khusus port Godot ──
		"unlocked_heroes": ["kaizen"],
		"gold": 0,
		"settings": {"sfx": 0.6, "bgm": 0.35, "quality": "medium"},
		"replay_reward_counts": {},
	}


## Hapus berkas slot — paritas `delete_slot` _system.py:929-944 (true
## hanya kalau berkasnya benar-benar ada danberhasil dihapus).
func delete_slot(slot_num: int) -> bool:
	if not FileAccess.file_exists(slot_path(slot_num)):
		return false
	var err := DirAccess.remove_absolute(
		ProjectSettings.globalize_path(slot_path(slot_num)))
	if err != OK:
		print("[SaveManager] Delete failed (err %d)" % err)
		return false
	print("[SaveManager] Slot %d deleted!" % slot_num)
	return true


# ══════════════════════════════════════════════════════════
#  METADATA SLOT (paritas _system.py:946-1022)
# ══════════════════════════════════════════════════════════

## Ringkasan slot untuk UI — paritas `get_slot_info` _system.py:946-980:
## `null` kalau slot kosong ATAU berkasnya rusak (jalur exception pygame).
func get_slot_info(slot_num: int):
	if not slot_exists(slot_num):
		return null
	var f = FileAccess.open(slot_path(slot_num), FileAccess.READ)
	if f == null:
		return null
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	if not (parsed is Dictionary):
		print("[SaveManager] Get slot info failed: not an object")
		return null
	var d: Dictionary = parsed
	var completed = d.get("completed_levels", [])
	if not (completed is Array):
		completed = []
	var highest := 0
	for lv in completed:
		highest = maxi(highest, int(lv))
	return {
		"slot_num": slot_num,
		"meta_gold": d.get("meta_gold", 0),
		"completed_levels": completed,
		"highest_level": highest,
		"last_played_level": d.get("last_played_level", 1),
		"purchased_heroes": d.get("purchased_heroes", []),
		"unlocked_bosses": d.get("unlocked_bosses", []),
		"slot_created": d.get("slot_created", 0),
		"slot_last_played": d.get("slot_last_played", 0),
		"playtime_seconds": d.get("slot_playtime_seconds", 0),
	}


## Info semua slot (larik sepanjang NUM_SLOTS; unsur bisa null).
func get_all_slot_info() -> Array:
	var out: Array = []
	for i in range(1, NUM_SLOTS + 1):
		out.append(get_slot_info(i))
	return out


## Detik -> "Xh Ym" / "Ym" — paritas `format_playtime` _system.py:988-996.
func format_playtime(seconds) -> String:
	var total := int(seconds)
	@warning_ignore("integer_division")
	var hours := total / 3600
	@warning_ignore("integer_division")
	var minutes := (total % 3600) / 60
	if hours > 0:
		return "%dh %dm" % [hours, minutes]
	return "%dm" % minutes


## Timestamp -> "Never" / "Just now" / "Xm|Xh|Xd ago" / "DD Mon YYYY".
## Paritas `format_last_played` _system.py:997-1022 — ambang 60 / 3600 /
## 86400 / 604800 detik, dan cabang tanggal memakai UTC (oracle pygame
## menjalankan strftime dengan TZ=UTC; lihat seksi `save_slots`).
func format_last_played(timestamp) -> String:
	var ts := float(timestamp)
	if ts == 0.0:
		return "Never"
	var elapsed := Time.get_unix_time_from_system() - ts
	if elapsed < 60:
		return "Just now"
	if elapsed < 3600:
		return "%dm ago" % int(elapsed / 60.0)
	if elapsed < 86400:
		return "%dh ago" % int(elapsed / 3600.0)
	if elapsed < 604800:
		return "%dd ago" % int(elapsed / 86400.0)
	# UTC MURNI: `Time.get_datetime_dict_from_unix_time` di Godot 4.3 cuma
	# menerima SATU argumen ( zona mesin ) dan 4.3 tidak punya varian UTC,
	# jadi tanggal dihitung sendiri dari hari sejak epoch — identik dengan
	# `time.localtime()` oracle yang dipaksa TZ=UTC, bebas DST/zona mesin.
	var parts := _civil_from_days(int(floor(ts / 86400.0)))
	return "%02d %s %04d" % [parts.z,
		MONTH_ABBR[clampi(parts.y - 1, 0, 11)], parts.x]


## Konversi hari sejak epoch (1970-01-01) -> Vector3i(tahun, bulan, hari).
## Algoritma civil_from_days Howard Hinnant; semua pembagian dilakukan
## atas nilai NON-NEGATIF (koreksi `era` menjamin itu), jadi pembulatan
## integer GDScript (potong ke nol) sama dengan floor().
static func _civil_from_days(z: int) -> Vector3i:
	var zz := z + 719468
	var era: int = (zz if zz >= 0 else zz - 146096) / 146097
	var doe: int = zz - era * 146097
	var yoe: int = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365
	var year: int = yoe + era * 400
	var doy: int = doe - (365 * yoe + yoe / 4 - yoe / 100)
	var mp: int = (5 * doy + 2) / 153
	var day: int = doy - (153 * mp + 2) / 5 + 1
	var month: int = mp + 3 if mp < 10 else mp - 9
	if month <= 2:
		year += 1
	return Vector3i(year, month, day)


## setdefault semua kunci meta + metadata slot — paritas baris
## `data.setdefault(...)` di `SaveManager.load` _system.py:894-901.
func _apply_defaults(target: Dictionary) -> void:
	_backfill(target)
	var now := Time.get_unix_time_from_system()
	if not target.has("slot_created") or target["slot_created"] == null:
		target["slot_created"] = now
	if not target.has("slot_last_played") or target["slot_last_played"] == null:
		target["slot_last_played"] = now
	if (not target.has("slot_playtime_seconds")
			or target["slot_playtime_seconds"] == null):
		target["slot_playtime_seconds"] = 0
	if not target.has("run_difficulty"):
		target["run_difficulty"] = null


## setdefault kunci meta — save hasil versi Godot lama tidak punya
## meta_gold/replay_reward_counts, dan Dictionary.merge tidak menambah kunci
## yang nilainya null/absen di file.
## `target` kosong/absen = pakai `data` (dipakai harness lama yang
## memanggil `_backfill()` tanpa argumen).
func _backfill(target: Variant = null) -> void:
	var d := data
	if target is Dictionary:
		d = target
	var defaults: Dictionary = {
		"meta_gold": 0,
		"replay_reward_counts": {},
		"unlocked_bosses": [],
		"last_played_level": 1,
		"completed_levels": [],
		"unlocked_heroes": ["kaizen"],
		# `purchased_heroes` adalah kunci MIRROR sisi pygame (daftar yang
		# sama dengan `unlocked_heroes` di Godot). pygame menyetelnya lewat
		# `data.setdefault('purchased_heroes', [])` saat load, jadi bentuk
		# save hasil load wajib memilikinya walau port Godot tidak pernah
		# membacanya. Backfill polos (bukan salinan unlocked_heroes):
		# persis perilaku setdefault pygame untuk save yang tidak punya
		# kunci ini.
		"purchased_heroes": [],
		"settings": {"sfx": 0.6, "bgm": 0.35, "quality": "medium"},
		"level_stats": {},
	}
	for key in defaults:
		if not d.has(key) or d[key] == null:
			d[key] = defaults[key]
	# Starter hanya Kaizen. Unlock lama tidak pernah dicabut saat upgrade port.
	if (not (d["unlocked_heroes"] is Array)
			or d["unlocked_heroes"].is_empty()):
		d["unlocked_heroes"] = ["kaizen"]


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

## Level sudah pernah dimenang (Python: `lv in save["completed_levels"]`).
## FASE 34: pembanding numerik lintas tipe, bukan `in`/Array.has(). Array.has()
## memakai Variant::hash_compare yang MENOLAK pasangan beda tipe
## (core/variant/variant.cpp:3309), sementara save Godot hasil
## JSON.parse_string berisi FLOAT untuk semua angka (core/io/json.cpp:341) —
## jadi setelah restart `3 in [3.0]` false: badge "MAIN LAGI", deteksi replay
## (GameManager._grant_meta_reward) dan tombol NEXT di GameOverOverlay semua
## salah baca progres. Python `in` memakai ==, dan itulah yang ditiru di sini
## (satu implementasi: LevelDB.py_contains, dipakai juga is_level_unlocked).
func is_level_completed(lv: int) -> bool:
	var completed = data.get("completed_levels", [])
	if not (completed is Array):
		return false
	return LevelDBScript.py_contains(completed, lv)

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


## Paritas SaveManager.format_time (_system.py:1118-1125): detik → "M:SS"
## (menit tidak di-pad dua digit, detik di-pad). 0 = "--:--" (belum pernah
## menang di level ini). FASE 20.
func format_time(seconds: int) -> String:
	if seconds == 0:
		return "--:--"
	@warning_ignore("integer_division")
	var minutes := seconds / 60
	var secs := seconds % 60
	return "%d:%02d" % [minutes, secs]


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


## Pasangan get_setting/set_setting untuk nilai STRING. Pasangan di atas
## bertipe float (volume/toggle/kecepatan), sedangkan bahasa antarmuka
## adalah kode string "id"/"en" — paritas `GameSettings.language`
## (_core.py:9141 default, :9167-9169 validasi saat load, :9193 disimpan).
## Deviasi yang tercatat: pygame menyimpan setting di settings.json GLOBAL
## (storage_paths.SAVE_DIR, bukan per slot); port Godot menyimpan semua
## setting di `data["settings"]` per slot, jadi bahasa ikut per slot.
func get_setting_str(key: String, default: String = "") -> String:
	var s = data.get("settings", {})
	if s is Dictionary and s.has(key):
		return str(s[key])
	return default


func set_setting_str(key: String, value: String, persist: bool = true) -> void:
	if not (data.get("settings") is Dictionary):
		data["settings"] = {}
	data["settings"][key] = value
	if persist:
		save()
