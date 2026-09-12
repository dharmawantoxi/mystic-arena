# LevelDB.gd — port levels/level_data.py (backend GDScript, jalur default).
#
# Bagian dari migrasi levels/ -> godot++ (FASE 34). Tiga lapisan dari satu
# sumber, pola yang sama dengan hero_skills:
#   python side  levels/level_data.py                 (sumber kebenaran)
#   GDScript     scripts/core/LevelDB.gd              (berkas ini; data levels.json)
#   C++ side     gdext/mystic_levels/src/levels_*.    (tools/gen_levels_cpp.py)
# Saklar backend ada di scripts/core/LevelDBLoader.gd — pemakai (BossDB,
# GameManager) memanggil loader, bukan berkas ini langsung.
#
# API = persis ekspor levels/__init__.py: ALL_LEVELS (all_levels),
# get_level_config, get_level_count, is_level_unlocked, get_next_level.
#
# ══ KENAPA ADA NORMALISASI TIPE (FIELD_KINDS) ══
# JSON Godot 4.3 mengubah SEMUA angka jadi float: tokenizer-nya memanggil
# String::to_float lalu menyimpan double apa adanya (core/io/json.cpp:341),
# tanpa cabang "bilangan bulat -> int". Jadi levels.json yang memuat
# `"starting_gold": 1000` tiba di GDScript sebagai 1000.0, sedangkan Python
# (json/ast literal) menyimpan int 1000. Tanpa normalisasi, katalog Godot
# beda TIPE dengan katalog pygame untuk 11 dari 17 field, dan itu bukan
# kosmetik:
#   * `Array.has()` Godot memakai hash_compare yang MENOLAK pasangan beda tipe
#     (core/variant/variant.cpp:3309 `if (type != p_variant.type) return false`),
#     jadi `3 in [3.0]` false — padahal Python `3 in [3.0]` True. Save Godot
#     juga hasil JSON.parse_string, jadi completed_levels berisi float dan
#     level tampak TERKUNCI lagi setelah restart.
#   * `str(1000.0)` = "1000.0" vs pygame "1000" kalau ada label yang lupa
#     int().
# FIELD_KINDS di bawah memulihkan tipe Python saat load. Isinya DIKUNCI
# tools/test_godot_level_data_parity.py terhadap level_data.py ASLI
# (closed-world: field baru yang belum terdaftar = CI merah).
extends RefCounted

const DATA_PATH := "res://data/levels.json"

## Tipe Python tiap field level ("int" / "float" / "str" / "int?" = int atau
## None / "mini_bosses" = dict wave->nama boss). Jangan disunting tanpa
## mengubah level_data.py — oracle statis membandingkan keduanya.
const FIELD_KINDS := {
	"level_number": "int",
	"name": "str",
	"description": "str",
	"enemy_hp_mult": "float",
	"enemy_damage_mult": "float",
	"enemy_speed_mult": "float",
	"castle_start_level": "int",
	"starting_gold": "int",
	"starting_castle_level": "int",
	"map_theme": "str",
	"bgm_track": "str",
	"mini_bosses": "mini_bosses",
	"true_boss": "str",
	"meta_gold_reward_win": "int",
	"meta_gold_reward_replay": "int",
	"meta_gold_reward_lose": "int",
	"unlock_after_level": "int?",
}

## Katalog ternormalisasi (dimuat sekali; `reload()` membuang cache).
static var _levels: Array = []
static var _loaded: bool = false
## Field tak dikenal dicurigai sekali saja, bukan sekali per level (54x).
static var _warned_fields: Dictionary = {}


# ══════════════════════════════════════════════════════════
#  ALL_LEVELS
# ══════════════════════════════════════════════════════════

## Katalog 54 level (paritas ALL_LEVELS). Array yang SAMA dikembalikan tiap
## panggilan — pemakai boleh menyimpannya (BossDB.levels), sama seperti
## hasil JSON.parse_string sebelumnya.
static func all_levels() -> Array:
	_ensure_loaded()
	return _levels


## Buang cache (dipakai harness paritas + setelah convert_to_godot.py).
static func reload() -> void:
	_loaded = false
	_levels = []


static func _ensure_loaded() -> void:
	if not _loaded:
		_load()


static func _load() -> void:
	_loaded = true
	_levels = []
	if not FileAccess.file_exists(DATA_PATH):
		push_warning("[LevelDB] %s belum ada — jalankan tools/convert_to_godot.py"
			% DATA_PATH)
		return
	var f := FileAccess.open(DATA_PATH, FileAccess.READ)
	if f == null:
		push_warning("[LevelDB] %s tidak bisa dibuka" % DATA_PATH)
		return
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	if not (parsed is Array):
		push_warning("[LevelDB] %s bukan array level" % DATA_PATH)
		return
	for row in parsed:
		if row is Dictionary:
			_levels.append(_normalize_row(row))


## Pulihkan tipe Python per baris (lihat FIELD_KINDS). Urutan kunci JSON
## dipertahankan = urutan literal dict level_data.py = urutan Dictionary C++.
static func _normalize_row(row: Dictionary) -> Dictionary:
	var out := {}
	for key in row:
		var kind: String = str(FIELD_KINDS.get(key, ""))
		var value = row[key]
		match kind:
			"int":
				out[key] = _as_int(value)
			"int?":
				out[key] = null if value == null else _as_int(value)
			"float":
				out[key] = 0.0 if value == null else float(value)
			"str":
				out[key] = "" if value == null else str(value)
			"mini_bosses":
				out[key] = _normalize_mini_bosses(value)
			_:
				_warn_unknown_field(key)
				out[key] = value
	return out


## Kunci wave jadi STRING (kunci objek JSON selalu string — C++ GDExt juga
## memakainya) dan URUTAN insert dipertahankan: level 3 memang 25, 10, 17
## di level_data.py, dan Main._roll_mini_boss_schedule bergantung pada
## urutan `values()` itu.
static func _normalize_mini_bosses(value) -> Dictionary:
	var out := {}
	if value is Dictionary:
		for wave in value:
			out[str(wave)] = str((value as Dictionary)[wave])
	return out


static func _as_int(value) -> int:
	if value == null:
		return 0
	if typeof(value) == TYPE_BOOL:
		return 1 if value else 0
	if typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT:
		return int(value)
	if typeof(value) == TYPE_STRING:
		return int(str(value).to_float())
	return 0


static func _warn_unknown_field(key: String) -> void:
	if _warned_fields.has(key):
		return
	_warned_fields[key] = true
	push_warning("[LevelDB] field '%s' belum ada di FIELD_KINDS — tipe Python-nya "
		% key
		+ "tidak dipulihkan (tambahkan ke LevelDB.gd lalu jalankan "
		+ "tools/gen_levels_cpp.py + tools/test_godot_level_data_parity.py)")


# ══════════════════════════════════════════════════════════
#  HELPER (paritas level_data.py:2295-2347)
# ══════════════════════════════════════════════════════════

## Config level tertentu, atau null (Python: None) kalau tidak ada.
## Pembanding numerik lintas tipe: get_level_config(3.0) juga kena, persis
## `lvl["level_number"] == level_number` Python.
static func get_level_config(level_number):
	_ensure_loaded()
	var kind := typeof(level_number)
	if kind != TYPE_INT and kind != TYPE_FLOAT:
		return null
	var wanted := float(level_number)
	for row in _levels:
		if not (row as Dictionary).has("level_number"):
			continue
		if float((row as Dictionary)["level_number"]) == wanted:
			return row
	return null


## Total level (paritas get_level_count = len(ALL_LEVELS)).
static func get_level_count() -> int:
	_ensure_loaded()
	return _levels.size()


## Kunci level (paritas is_level_unlocked level_data.py:2318-2337):
##   config tidak ada      -> False
##   unlock_after_level None -> True (level 1 selalu terbuka)
##   selain itu            -> required in completed_levels
static func is_level_unlocked(level_number, completed_levels) -> bool:
	var config = get_level_config(level_number)
	if not (config is Dictionary) or (config as Dictionary).is_empty():
		return false
	var required = (config as Dictionary).get("unlock_after_level")
	if required == null:
		return true
	if not (completed_levels is Array):
		# Python `x in <bukan list>` -> TypeError; di sini dianggap terkunci
		# supaya UI tidak crash karena save rusak.
		return false
	return py_contains(completed_levels, required)


## Level berikutnya, atau null (Python: None) kalau sudah terakhir.
static func get_next_level(current_level):
	var nxt
	match typeof(current_level):
		TYPE_INT:
			nxt = int(current_level) + 1
		TYPE_FLOAT:
			nxt = float(current_level) + 1.0
		_:
			return null
	if nxt > get_level_count():
		return null
	if get_level_config(nxt) == null:
		return null
	return nxt


## `needle in haystack` semantik Python (== numerik int/float).
## SENGAJA bukan `in` / Array.has(): keduanya memakai Variant::hash_compare
## yang menolak pasangan beda tipe (variant.cpp:3309), jadi [3.0] tidak akan
## pernah "berisi" 3 — persis bug kunci-level-setelah-restart yang ditutup
## fase ini.
static func py_contains(haystack: Array, needle) -> bool:
	for entry in haystack:
		if py_equal(entry, needle):
			return true
	return false


## `a == b` ala Python untuk nilai yang bisa muncul di save: numerik
## dibandingkan lintas tipe, selain itu harus se-tipe. bool TIDAK disamakan
## dengan int (Python: True == 1) — deviasi dicatat docs/LEVELS_GODOTPP.md;
## save Godot hanya menyimpan int/float jadi tidak pernah terjadi.
static func py_equal(a, b) -> bool:
	var ta := typeof(a)
	var tb := typeof(b)
	var a_num := ta == TYPE_INT or ta == TYPE_FLOAT
	var b_num := tb == TYPE_INT or tb == TYPE_FLOAT
	if a_num and b_num:
		return float(a) == float(b)
	if ta != tb:
		return false
	if ta == TYPE_STRING or ta == TYPE_STRING_NAME or ta == TYPE_BOOL:
		return bool(a == b)
	return false
