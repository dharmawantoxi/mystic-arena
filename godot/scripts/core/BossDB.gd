# BossDB.gd — Port dari bosses/boss_data.py + levels/level_data.py
#
# FASE 34: katalog level tidak lagi di-parse dari levels.json di sini, tapi
# diminta dari LevelDBLoader — saklar backend levels/level_data.py yang
# memakai GDScript (LevelDB.gd + levels.json, default) atau GDExtension C++
# MysticLevels (godot/gdext/mystic_levels, opt-in lewat
# mystic/levels/use_gdext_levels). Bentuk hasilnya identik (Array of
# Dictionary, tipe Python dipulihkan), jadi 20+ pemakai BossDB.levels /
# BossDB.get_level tidak berubah.
extends Node

const LevelDBLoader = preload("res://scripts/core/LevelDBLoader.gd")

var bosses: Dictionary = {}
var levels: Array = []

func _ready():
	# levels dimuat dulu: jalur pemulihan load_bosses() butuh jadwal level
	# (smooth_boss_progression membaca mini_bosses/true_boss per level).
	load_levels()
	load_bosses()

func load_bosses():
	var path = "res://data/bosses.json"
	if not FileAccess.file_exists(path):
		push_warning("[BossDB] bosses.json belum ada. Jalankan tools/convert_to_godot.py"
			+ " — sementara katalog dihitung ulang dari tabel mentah")
		# FASE 32: dulunya tiga baris hardcode (gornak/morgath/drakar) dengan
		# angka PRE-pipeline yang salah. Sekarang seluruh 216 boss dihitung
		# ulang lewat pipeline boss_data.py yang di-port (BossData.gd) dari
		# godot/data/boss_pristine.json — angka yang sama persis dengan yang
		# di-bake converter. Dikunci tools/test_boss_data_parity.py +
		# godot/tests/BossDataParityTest.gd.
		bosses = rebuild_from_pristine()
		if bosses.is_empty():
			push_warning("[BossDB] boss_pristine.json juga tidak ada — katalog kosong")
		return
	var f = FileAccess.open(path, FileAccess.READ)
	var parsed = JSON.parse_string(f.get_as_text())
	bosses = parsed if parsed is Dictionary else {}
	print("[BossDB] Loaded %d bosses" % bosses.size())

func load_levels():
	# LevelDBLoader = satu-satunya pintu katalog level (GDScript LevelDB.gd
	# atau C++ MysticLevels). Peringatan "levels.json belum ada" dicetak
	# LevelDB.gd sendiri; MainMenu tetap menampilkan kartu penjelasan kalau
	# hasilnya kosong.
	levels = LevelDBLoader.all_levels()
	if levels.is_empty():
		return
	print("[BossDB] Loaded %d levels (backend %s)"
		% [levels.size(), LevelDBLoader.backend_name()])

## Jalur pemulihan katalog: pipeline 5 langkah BossData atas tabel mentah.
## Field yang tidak ikut pipeline (nama/warna/radius/kecepatan/label) tidak
## bisa dipulihkan dari pristine — barisnya tetap cukup untuk spawn karena
## Boss.gd punya default untuk semuanya, dan ANGKAnya (hp/damage/ability/skill/
## hero_unlock) sama persis dengan hasil baker.
func rebuild_from_pristine(path: String = "res://data/boss_pristine.json") -> Dictionary:
	var pristine: Dictionary = BossData.load_pristine(path)
	if pristine.is_empty():
		return {}
	var built: Dictionary = BossData.build(pristine,
		BossData.schedule_from_levels(levels))
	var all_rows: Dictionary = built.get("all", {})
	var out := {}
	for btype in all_rows:
		var row: Dictionary = (all_rows[btype] as Dictionary).duplicate()
		row["name"] = title_from_key(str(btype))
		out[str(btype)] = row
	print("[BossDB] Rebuilt %d bosses dari pristine (pipeline BossData)" % out.size())
	return out


## "ghost_warrior" -> "Ghost Warrior" (nama tampilan darurat).
static func title_from_key(key: String) -> String:
	var words: Array = []
	for part in key.replace("-", "_").split("_"):
		if part.length() > 0:
			words.append(part.capitalize())
	return " ".join(words)


func get_boss(boss_type: String) -> Dictionary:
	return bosses.get(boss_type, {})

## Config satu level ({} kalau tidak ada) — padanan levels.get_level_config.
## Sengaja tetap scan `levels` (bukan LevelDBLoader.get_level_config) supaya
## BossDB selalu konsisten dengan katalog yang DIPEGANG-nya: harness paritas
## menyuntik backend berbeda, dan pemakai yang menyimpan BossDB.levels harus
## melihat baris yang sama. Isinya tetap berasal dari backend aktif karena
## load_levels() mengambilnya dari LevelDBLoader. Semantik null-vs-{} milik
## loader (Python mengembalikan None) dikunci LevelDataParityTest.
func get_level(level_num: int) -> Dictionary:
	for lv in levels:
		if lv.get("level_number") == level_num:
			return lv
	return {}
