# BakedPropDB.gd — pembaca manifest bake PROPS (minion, menara, nexus).
#
# Fase 7. Sebelumnya Godot menggambar menara/minion/nexus dengan primitif
# geometris (Tower.gd::_draw 20 panggilan draw, UnitSilhouette 56, Nexus 18)
# padahal pygame memakai renderer prosedural penuh:
#
#     towers/_bundle.py    7.274 baris (4 jenis menara x 6 level)
#     minions/_bundle.py   9.531 baris (5 jenis minion, animasi jalan/serang)
#     _entity.Castle       1.637 baris (5 level kastil + obor + aura)
#
# Sama seperti Fase 5 (hero/boss), seninya TIDAK ditulis ulang di GDScript:
# tools/convert_to_godot.py --props-png memanggil renderer pygame ASLI dan
# membekukan hasilnya jadi strip PNG + manifest res://data/baked_props.json.
# File ini adalah SATU pintu baca manifest itu, pola yang sama dengan
# BakedUnitDB.gd.
#
# Kenapa lazy: 20 strip tidak besar, tapi nexus/menara hanya beberapa yang
# benar-benar tampil sekaligus. Tekstur dimuat saat pertama diminta, cache
# FIFO sebagai pengaman.
extends RefCounted
class_name BakedPropDB

const MANIFEST_PATH := "res://data/baked_props.json"

static var _loaded := false
static var _data: Dictionary = {}
## res:// path -> Texture2D (lazy + cache sederhana).
static var _textures: Dictionary = {}


static func _ensure_loaded() -> void:
	if _loaded:
		return
	_loaded = true
	if not FileAccess.file_exists(MANIFEST_PATH):
		# Bake belum dijalankan. BUKAN error fatal: pemanggil jatuh ke
		# gambar geometris lama (perilaku pra-Fase 7 tetap utuh).
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST_PATH))
	if parsed is Dictionary:
		_data = parsed


static func _section(name: String) -> Dictionary:
	_ensure_loaded()
	var s = _data.get(name)
	return s if s is Dictionary else {}


## Entri minion (kunci "<jenis>_<tim>"). Kosong = belum dibake.
static func minion_entry(minion_type: String, team: String) -> Dictionary:
	return _section("minions").get("%s_%s" % [minion_type, team], {})


## Entri menara (kunci "<jenis>_<tim>"). Kosong = belum dibake.
static func tower_entry(tower_type: String, team: String) -> Dictionary:
	return _section("towers").get("%s_%s" % [tower_type, team], {})


## Entri nexus (kunci = tim). Kosong = belum dibake.
static func nexus_entry(team: String) -> Dictionary:
	return _section("nexus").get(team, {})


## Tekstur strip (lazy). Null kalau berkas tidak ada.
static func texture(res_path: String) -> Texture2D:
	if res_path.is_empty():
		return null
	if _textures.has(res_path):
		return _textures[res_path] as Texture2D
	if not ResourceLoader.exists(res_path):
		return null
	var tex: Texture2D = load(res_path) as Texture2D
	if tex != null:
		_textures[res_path] = tex
	return tex


## Region atlas untuk frame ke-`index` (grid frames_per_row kolom).
static func frame_region(e: Dictionary, index: int) -> Rect2:
	var fw := float(e.get("frame_w", 0))
	var fh := float(e.get("frame_h", 0))
	var fpr := int(e.get("frames_per_row", 8))
	if fw <= 0.0 or fh <= 0.0 or fpr <= 0 or index < 0:
		return Rect2()
	return Rect2(float(index % fpr) * fw, float(index / fpr) * fh, fw, fh)


## Titik jangkar dalam sel — harus jatuh tepat di origin node
## (telapak kaki minion, pusat alas menara, posisi nexus).
static func anchor(e: Dictionary) -> Vector2:
	var a = e.get("anchor", [0, 0])
	if a is Array and a.size() >= 2:
		return Vector2(float(a[0]), float(a[1]))
	return Vector2.ZERO


## Daftar frame idle menara untuk satu level (4 fase nyala obor).
static func tower_idle_frames(e: Dictionary, level: int) -> Array:
	var levels = e.get("levels", {})
	var lv = levels.get(str(level), levels.get(level, {}))
	if lv is Dictionary:
		return lv.get("idle", [])
	return []


## Daftar frame tembak menara untuk satu level.
static func tower_shoot_frames(e: Dictionary, level: int) -> Array:
	var levels = e.get("levels", {})
	var lv = levels.get(str(level), levels.get(level, {}))
	if lv is Dictionary:
		return lv.get("shoot", [])
	return []


## Index frame nexus untuk satu level (fallback ke frame terakhir).
static func nexus_frame(e: Dictionary, level: int) -> int:
	var levels = e.get("levels", {})
	if levels.has(str(level)):
		return int(levels[str(level)])
	if levels.has(level):
		return int(levels[level])
	# Level di luar NEXUS_LEVELS (game memakai level 5 untuk 6+).
	var keys = levels.keys()
	if keys.is_empty():
		return 0
	return int(levels[keys[keys.size() - 1]])
