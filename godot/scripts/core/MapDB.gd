# MapDB.gd — port map_components/_bundle.py (backend GDScript, jalur default).
#
# Bagian dari migrasi map_components/ -> godot++ (FASE 35). Tiga lapisan dari
# satu sumber, pola yang sama dengan levels (FASE 34) dan hero_skills (33):
#   python side  map_components/_bundle.py          (sumber kebenaran)
#   GDScript     scripts/core/MapDB.gd              (berkas ini; data themes_raw.json)
#   C++ side     gdext/mystic_maps/src/maps_*       (tools/gen_maps_cpp.py)
# Saklar backend ada di scripts/core/MapDBLoader.gd — pemakai (ArenaMap)
# memanggil loader, bukan berkas ini langsung.
#
# API = permukaan modul palettes/themes/generators: tile_size, palettes,
# theme_names, theme_count, get_theme, all_themes, make_curved_path,
# generate_lanes, generate_river, generate_decorations (+ helper build_theme,
# theme_index, catalog_signature, derive_palette).
#
# ══ NORMALISASI TIPE (KEY_KINDS) ══
# JSON Godot 4.3 mengubah SEMUA angka jadi float (core/io/json.cpp:341), jadi
# themes_raw.json memberi [28.0, 55.0, 32.0] untuk tuple Python (28, 55, 32).
# KEY_KINDS memulihkan tipe + bentuk Python saat load (Color untuk tuple
# warna, PackedColorArray untuk list 3 warna, null tetap null). Isinya DIKUNCI
# tools/test_godot_map_data_parity.py terhadap _bundle.py ASLI (closed-world:
# kunci baru yang belum terdaftar = CI merah).
#
# ══ REPLIKA random CPython (kelas PyMt) ══
# DecorationGenerator.generate_all deterministik via random.seed(42), dan
# RandomNumberGenerator Godot (PCG) TIDAK se-stream dengan Mersenne Twister
# Python — apalagi CPython me-seed int lewat init_by_array, bukan
# init_genrand (spike pra-migrasi: draw pertama 2746317213 vs 1608637542).
# Kelas di bawah adalah port baris-per-baris replika C++ (PyMt di
# maps_processor.cpp, sudah dibuktikan bit-eksak vs CPython 3.11 oleh
# tools/test_maps_cpp_selftest.py): 19.834 cek). Semua op 32-bit di-mask
# & 0xFFFFFFFF karena int GDScript 64-bit; perkalian terbesar
# (1812433253 * 2^32) muat di int64.
extends RefCounted

const DATA_PATH := "res://data/themes_raw.json"

## Kind Python tiap kunci tema ("str"/"bool"/"int"/"color3"/"color4"/
## "color4?" = color4 atau null/"colorlist3"). Jangan disunting tanpa mengubah
## map_components/_bundle.py — oracle statis membandingkan keduanya.
const KEY_KINDS := {
	"name": "str",
	"boss_identity": "str",
	"boss_title": "str",
	"radiant_grass_1": "color3",
	"radiant_grass_2": "color3",
	"radiant_grass_3": "color3",
	"radiant_grass_4": "color3",
	"radiant_grass_high": "color3",
	"radiant_moss": "color3",
	"dire_earth_1": "color3",
	"dire_earth_2": "color3",
	"dire_earth_3": "color3",
	"dire_earth_4": "color3",
	"dire_ash": "color3",
	"dire_burnt": "color3",
	"transition_1": "color3",
	"transition_2": "color3",
	"path_stone_1": "color3",
	"path_stone_2": "color3",
	"path_stone_3": "color3",
	"path_stone_4": "color3",
	"path_moss": "color3",
	"path_crack": "color3",
	"river_deep": "color3",
	"river_mid": "color3",
	"river_light": "color3",
	"river_glow": "color3",
	"river_foam": "color3",
	"has_dark_trees": "bool",
	"has_dead_trees": "bool",
	"has_gravestones": "bool",
	"has_crystals_blue": "bool",
	"has_crystals_red": "bool",
	"has_ancient_ruins": "bool",
	"has_bones": "bool",
	"has_mushrooms_dark": "bool",
	"has_rocks_mossy": "bool",
	"has_dark_bushes": "bool",
	"has_glow_flowers": "bool",
	"has_spike_traps": "bool",
	"has_torch_stones": "bool",
	"has_cactus": "bool",
	"has_palm_trees": "bool",
	"has_sand_dunes": "bool",
	"has_ice_crystals": "bool",
	"has_frozen_trees": "bool",
	"has_snow_drifts": "bool",
	"particle_type": "str",
	"particle_colors_radiant": "colorlist3",
	"particle_colors_dire": "colorlist3",
	"particle_count": "int",
	"fog_enabled": "bool",
	"fog_color": "color4",
	"fog_count": "int",
	"ambient_tint": "color4?",
	"level_identity": "str",
	"void_black": "color3",
	"rift_violet": "color3",
	"soul_teal": "color3",
	"bone_white": "color3",
	"bone_highlight": "color3",
	"causeway_dark": "color3",
	"causeway_mid": "color3",
	"arena_stone": "color3",
	"arena_highlight": "color3",
	"obelisk_stone": "color3",
	"obelisk_highlight": "color3",
	"gate_stone": "color3",
	"gate_highlight": "color3",
	"border_stone": "color3",
	"border_highlight": "color3",
	"ash_high": "color3",
	"has_ghost_lights": "bool",
	"has_ectoplasm_pools": "bool",
	"has_crypt_gates": "bool",
	"has_spirit_wisps": "bool",
	"has_cursed_candles": "bool",
}

## Kunci tema fallback (paritas THEMES.get(nama, FOREST_THEME)).
const FALLBACK_THEME := "forest"

## Cache dokumen MENTAH (hasil JSON.parse_string); normalisasi dikerjakan per
## panggilan supaya tiap get_theme() mengembalikan Dictionary SEGAR (Python
## mengembalikan objek live yang bisa dimutasi — deviasi didokumentasikan,
## tidak ada konsumen Godot yang memutasi).
static var _doc: Dictionary = {}
static var _loaded: bool = false
static var _warned_fields: Dictionary = {}


# ══════════════════════════════════════════════════════════
#  Muat + normalisasi
# ══════════════════════════════════════════════════════════

## Buang cache (dipakai harness paritas + setelah convert_to_godot.py).
static func reload() -> void:
	_loaded = false
	_doc = {}


static func _ensure_loaded() -> void:
	if not _loaded:
		_load()


static func _load() -> void:
	_loaded = true
	_doc = {}
	if not FileAccess.file_exists(DATA_PATH):
		push_warning("[MapDB] %s belum ada — jalankan tools/convert_to_godot.py --map-raw"
			% DATA_PATH)
		return
	var f := FileAccess.open(DATA_PATH, FileAccess.READ)
	if f == null:
		push_warning("[MapDB] %s tidak bisa dibuka" % DATA_PATH)
		return
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	if parsed is Dictionary:
		_doc = parsed


static func _raw_themes() -> Dictionary:
	_ensure_loaded()
	var t = _doc.get("themes")
	return t if t is Dictionary else {}


## Pulihkan tipe Python per baris. Urutan kunci = urutan dokumen JSON = urutan
## literal dict Python (json.dump + JSON.parse_string sama-sama ordered).
static func _normalize_row(row: Dictionary) -> Dictionary:
	var out := {}
	for key in row:
		var kind: String = str(KEY_KINDS.get(key, ""))
		var value = row[key]
		match kind:
			"str":
				out[key] = "" if value == null else str(value)
			"bool":
				out[key] = bool(value)
			"int":
				out[key] = _as_int(value)
			"color3":
				out[key] = _as_color3(value, key)
			"color4":
				out[key] = _as_color4(value, key)
			"color4?":
				out[key] = null if value == null else _as_color4(value, key)
			"colorlist3":
				out[key] = _as_colorlist(value, key)
			_:
				_warn_unknown_field(key)
				out[key] = value
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


static func _chan(value, idx: int, key: String) -> int:
	if value is Array and (value as Array).size() > idx:
		return _as_int((value as Array)[idx])
	_warn_unknown_field("%s[%d]" % [key, idx])
	return 255 if idx == 3 else 0


static func _as_color3(value, key: String) -> Color:
	if value is Array and (value as Array).size() == 3:
		return Color8(_as_int((value as Array)[0]), _as_int((value as Array)[1]),
			_as_int((value as Array)[2]))
	_warn_unknown_field(key)
	return Color.MAGENTA


static func _as_color4(value, key: String) -> Color:
	if value is Array and (value as Array).size() == 4:
		return Color8(_as_int((value as Array)[0]), _as_int((value as Array)[1]),
			_as_int((value as Array)[2]), _as_int((value as Array)[3]))
	_warn_unknown_field(key)
	return Color.MAGENTA


static func _as_colorlist(value, key: String) -> PackedColorArray:
	var out := PackedColorArray()
	if value is Array:
		for triple in (value as Array):
			out.append(_as_color3(triple, key))
	if out.size() != 3:
		_warn_unknown_field(key)
	return out


static func _warn_unknown_field(key: String) -> void:
	if _warned_fields.has(key):
		return
	_warned_fields[key] = true
	push_warning("[MapDB] kunci '%s' belum ada di KEY_KINDS — tipe Python-nya "
		% key
		+ "tidak dipulihkan (tambahkan ke MapDB.gd lalu jalankan "
		+ "tools/test_godot_map_data_parity.py)")


# ══════════════════════════════════════════════════════════
#  API palet + tema (paritas palettes/themes.py)
# ══════════════════════════════════════════════════════════

## TILE_SIZE palettes.py (16).
static func tile_size() -> int:
	_ensure_loaded()
	return _as_int(_doc.get("tile_size", 16))


## Seluruh konstanta warna palettes.py {NAMA: Color}, urutan sumber.
static func palettes() -> Dictionary:
	_ensure_loaded()
	var out := {}
	var raw = _doc.get("palettes")
	if raw is Dictionary:
		for name in raw:
			out[str(name)] = _as_color3((raw as Dictionary)[name], str(name))
	return out


## 54 nama tema, urutan THEMES.
static func theme_names() -> Array:
	_ensure_loaded()
	return _raw_themes().keys()


## Jumlah tema (len(THEMES)).
static func theme_count() -> int:
	return _raw_themes().size()


## Tema ke-`index`, Dictionary segar (urutan kunci = literal Python).
## Di luar jangkauan -> Dictionary kosong.
static func build_theme(index: int) -> Dictionary:
	var raw := _raw_themes()
	var names := raw.keys()
	if index < 0 or index >= names.size():
		return {}
	var row = raw[names[index]]
	return _normalize_row(row) if row is Dictionary else {}


## Indeks tema untuk nama, -1 kalau tidak ada.
static func theme_index(theme_name: String) -> int:
	return _raw_themes().keys().find(theme_name)


## Config tema, fallback forest (paritas THEMES.get(nama, FOREST_THEME)).
static func get_theme(theme_name: String) -> Dictionary:
	var raw := _raw_themes()
	if raw.has(theme_name) and raw[theme_name] is Dictionary:
		return _normalize_row(raw[theme_name])
	if raw.has(FALLBACK_THEME) and raw[FALLBACK_THEME] is Dictionary:
		return _normalize_row(raw[FALLBACK_THEME])
	return {}


## Seluruh katalog {nama: tema} (paritas THEMES), Dictionary segar.
static func all_themes() -> Dictionary:
	var raw := _raw_themes()
	var out := {}
	for name in raw:
		if raw[name] is Dictionary:
			out[str(name)] = _normalize_row(raw[name])
	return out


## Backend GDScript tidak punya tabel terkompilasi — kembalikan "" (pola
## LevelDB: tanda tangan hanya bermakna dari C++).
static func catalog_signature() -> String:
	return ""


# ══════════════════════════════════════════════════════════
#  PathGenerator (port make_curved_path/generate_lanes/generate_river)
# ══════════════════════════════════════════════════════════
#
# DUA deviasi port lama (ArenaMap._curved_path) yang ditutup di sini:
#   1. Python me-truncate tiap titik ke int (int(x), int(y)); port lama
#      menyimpan float — minion berjalan di jalur yang (sedikit) beda.
#   2. Lane mid memakai smoothness=8 di Python; port lama memakai 10 untuk
#      semua lane (jumlah titik mid 65, bukan 81).

## Interpolasi Catmull-Rom — port make_curved_path. Urutan operasi double
## sama persis (t3 = t*t*t), lalu int() = trunc ke nol.
static func make_curved_path(waypoints: PackedVector2Array, smoothness: int) -> PackedVector2Array:
	if waypoints.size() < 2:
		return waypoints.duplicate() # Python: objek SAMA; di sini salinan (deviasi)
	var padded: Array = [waypoints[0]]
	for p in waypoints:
		padded.append(p)
	padded.append(waypoints[waypoints.size() - 1])
	var out := PackedVector2Array()
	for i in range(padded.size() - 3):
		var p0: Vector2 = padded[i]
		var p1: Vector2 = padded[i + 1]
		var p2: Vector2 = padded[i + 2]
		var p3: Vector2 = padded[i + 3]
		for step in range(smoothness):
			var t := float(step) / float(smoothness)
			var t2 := t * t
			var t3 := t * t * t
			var x := 0.5 * ((2.0 * p1.x) + (-p0.x + p2.x) * t
				+ (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2
				+ (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3)
			var y := 0.5 * ((2.0 * p1.y) + (-p0.y + p2.y) * t
				+ (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2
				+ (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3)
			out.append(Vector2(int(x), int(y)))
	out.append(waypoints[waypoints.size() - 1])
	return out


## Tiga lane (top/mid/bot) — waypoint + smoothness dari AST generate_lanes.
static func generate_lanes(map_w: int, map_h: int) -> Dictionary:
	var top := PackedVector2Array([
		Vector2(90, map_h - 130), Vector2(85, map_h - 260),
		Vector2(95, map_h - 380), Vector2(120, map_h - 500),
		Vector2(170, 180), Vector2(240, 100), Vector2(380, 75),
		Vector2(550, 70), Vector2(720, 75), Vector2(880, 85),
		Vector2(1030, 110), Vector2(map_w - 100, 180),
	])
	var bot := PackedVector2Array([
		Vector2(130, map_h - 90), Vector2(260, map_h - 70),
		Vector2(420, map_h - 60), Vector2(600, map_h - 60),
		Vector2(780, map_h - 65), Vector2(940, map_h - 75),
		Vector2(1070, map_h - 100), Vector2(map_w - 110, map_h - 220),
		Vector2(map_w - 90, map_h - 380), Vector2(map_w - 85, 250),
		Vector2(map_w - 100, 180),
	])
	# map_w // 2 Python = map_w / 2 GDScript (int/int trunc; sama karena
	# map_w/map_h selalu positif).
	var mid := PackedVector2Array([
		Vector2(170, map_h - 170), Vector2(300, map_h - 300),
		Vector2(440, map_h - 400),
		Vector2(map_w / 2 - 60, map_h / 2 + 40),
		Vector2(map_w / 2, map_h / 2),
		Vector2(map_w / 2 + 60, map_h / 2 - 40),
		Vector2(map_w - 440, 400), Vector2(map_w - 300, 300),
		Vector2(map_w - 170, 170),
	])
	return {
		"top": make_curved_path(top, 10),
		"mid": make_curved_path(mid, 8),
		"bot": make_curved_path(bot, 10),
	}


## Jalur sungai — waypoint + smoothness dari AST generate_river.
static func generate_river(map_w: int, map_h: int) -> PackedVector2Array:
	var pts := PackedVector2Array([
		Vector2(0, 200), Vector2(150, 270), Vector2(350, 350),
		Vector2(map_w / 2, map_h / 2),
		Vector2(map_w - 350, map_h - 350),
		Vector2(map_w - 150, map_h - 270),
		Vector2(map_w, map_h - 200),
	])
	return make_curved_path(pts, 10)


# ══════════════════════════════════════════════════════════
#  Replika CPython random (MT19937 + init_by_array)
# ══════════════════════════════════════════════════════════

## Port kelas PyMt C++ (maps_processor.cpp) baris-per-baris. State per
## instance (Array 624 int); tiap generate_decorations() membuat instance
## baru + seed 42 — tidak ada state global yang bisa bocor antar panggilan.
class PyMt:
	const N := 624
	const M := 397
	const MATRIX_A := 0x9908b0df
	const UPPER_MASK := 0x80000000
	const LOWER_MASK := 0x7fffffff
	const MASK_32 := 0xFFFFFFFF
	var mt: Array = []
	var mti: int = 0

	func _init() -> void:
		mt.resize(N)
		for i in range(N):
			mt[i] = 0

	func init_genrand(s: int) -> void:
		mt[0] = s & MASK_32
		mti = 1
		while mti < N:
			mt[mti] = (1812433253 * (mt[mti - 1] ^ (mt[mti - 1] >> 30)) + mti) & MASK_32
			mti += 1

	func init_by_array(init_key: Array, key_length: int) -> void:
		init_genrand(19650218)
		var i := 1
		var j := 0
		var k: int = N if N > key_length else key_length
		while k > 0:
			# Tanda kurung di sekitar XOR hukumnya WAJIB: `^` LEBIH RENDAH
			# dari `+` (GDScript seperti C), jadi tanpa kurung luar artinya
			# menjadi mt[i] ^ (suku + key + j) — stream salah total. Bentuk
			# yang benar (rujukan mt19937ar.c + CPython _randommodule.c):
			# (mt[i] ^ suku) + key + j.
			mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1664525))
				+ init_key[j] + j) & MASK_32
			i += 1
			j += 1
			if i >= N:
				mt[0] = mt[N - 1]
				i = 1
			if j >= key_length:
				j = 0
			k -= 1
		k = N - 1
		while k > 0:
			# Kurung luar wajib (alasan sama di atas): (mt[i] ^ suku) - i.
			mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1566083941))
				- i) & MASK_32
			i += 1
			if i >= N:
				mt[0] = mt[N - 1]
				i = 1
			k -= 1
		mt[0] = 0x80000000

	func seed_int(n: int) -> void:
		init_by_array([n & MASK_32], 1)

	func genrand_int32() -> int:
		if mti >= N:
			var kk := 0
			while kk < N - M:
				var y0: int = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK)
				mt[kk] = mt[kk + M] ^ (y0 >> 1) ^ (0 if y0 % 2 == 0 else MATRIX_A)
				kk += 1
			while kk < N - 1:
				var y1: int = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK)
				mt[kk] = mt[kk + (M - N)] ^ (y1 >> 1) ^ (0 if y1 % 2 == 0 else MATRIX_A)
				kk += 1
			var yn: int = (mt[N - 1] & UPPER_MASK) | (mt[0] & LOWER_MASK)
			mt[N - 1] = mt[M - 1] ^ (yn >> 1) ^ (0 if yn % 2 == 0 else MATRIX_A)
			mti = 0
		var y: int = mt[mti]
		mti += 1
		y ^= y >> 11
		y ^= (y << 7) & 0x9d2c5680
		y ^= (y << 15) & 0xefc60000
		y ^= y >> 18
		return y & MASK_32

	## getrandbits(k), k <= 32 — persis _randommodule.c.
	func getrandbits(k: int) -> int:
		var words := int((k + 31) / 32)
		var r := 0
		for i in range(words):
			r = (r << 32) | genrand_int32()
		r >>= words * 32 - k
		return r

	## _randbelow(n) — Lib/random.py: k = bit_length, rejection loop.
	func randbelow(n: int) -> int:
		var k := 0
		var t := n
		while t > 0:
			k += 1
			t >>= 1
		var r := getrandbits(k)
		while r >= n:
			r = getrandbits(k)
		return r

	## randint(a, b) = _randbelow(b-a+1)+a.
	func randint(a: int, b: int) -> int:
		return a + randbelow(b - a + 1)

	## choice(seq) = seq[_randbelow(len)] — indeksnya saja.
	func choice_idx(n: int) -> int:
		return randbelow(n)


# ══════════════════════════════════════════════════════════
#  DecorationGenerator (port generate_all + validator)
# ══════════════════════════════════════════════════════════

static func _threshold_y(x: int, map_w: int, map_h: int) -> float:
	# threshold_y = 200 + (map_h - 400) * x / map_w — perkalian int eksak
	# lalu SATU divisi float, persis urutan Python (GDScript float = double).
	return 200.0 + float((map_h - 400) * x) / float(map_w)


static func _is_radiant(x: int, y: int, map_w: int, map_h: int) -> bool:
	return float(y) > _threshold_y(x, map_w, map_h) + 20.0


static func _is_dire(x: int, y: int, map_w: int, map_h: int) -> bool:
	return float(y) < _threshold_y(x, map_w, map_h) - 20.0


## Jarak hypot — Vector2.length() = sqrt(dx²+dy²) float32 vs math.hypot
## double Python. SELALU sepakat di sini: dx²+dy² < 2^24 (eksak di kedua
## presisi), sqrt correctly-rounded di keduanya, dan ambang semuanya int —
## jarak dua titik integer-koordinat tidak pernah mendarat di dalam setengah
## ulp dari bilangan bulat (|sqrt(S) - T| >= ~1/2T untuk S != T²).
static func _dist(ax: float, ay: float, bx: float, by: float) -> float:
	return Vector2(ax - bx, ay - by).length()


static func _too_close_to_lane(lane_points: PackedVector2Array, x: int, y: int, min_dist: float) -> bool:
	for p in lane_points:
		if _dist(float(x), float(y), p.x, p.y) < min_dist:
			return true
	return false


static func _too_close_to_river(river_points: PackedVector2Array, x: int, y: int, min_dist: float) -> bool:
	for p in river_points:
		if _dist(float(x), float(y), p.x, p.y) < min_dist:
			return true
	return false


static func _too_close_to_base(x: int, y: int, map_w: int, map_h: int) -> bool:
	# BUG ASLI DIREPLIKA (lihat komentar C++): lingkaran pertama berpusat di
	# (120, 120), bukan base Radiant. Jangan "diperbaiki".
	if _dist(float(x - 120), float(map_h - 120 - (map_h - y)), 0.0, 0.0) < 120.0:
		return true
	if _dist(float(x - (map_w - 120)), float(y - 120), 0.0, 0.0) < 120.0:
		return true
	return false


static func _too_close_to_shop(shop_positions: Array, x: int, y: int, min_dist: float) -> bool:
	for pos in shop_positions:
		var p: Vector2 = pos
		if _dist(float(x), float(y), p.x, p.y) < min_dist:
			return true
	return false


static func _is_valid_spot(lane_points: PackedVector2Array, river_points: PackedVector2Array,
		shop_positions: Array, map_w: int, map_h: int, x: int, y: int, min_lane: float) -> bool:
	if _too_close_to_lane(lane_points, x, y, min_lane):
		return false
	if _too_close_to_river(river_points, x, y, 25.0):
		return false
	if _too_close_to_base(x, y, map_w, map_h):
		return false
	if _too_close_to_shop(shop_positions, x, y, 70.0):
		return false
	return true


## Port generate_all: 14 kategori, urutan kunci = literal `data` Python.
## Tiap entri = Array [x, y, ...] (int/str/Color/bool) — uniform agar kedua
## backend + fixture JSON membandingkan bentuk yang sama.
static func generate_decorations(map_w: int, map_h: int, lane_points: PackedVector2Array,
		river_points: PackedVector2Array, shop_positions: Array) -> Dictionary:
	var rng := PyMt.new()
	rng.seed_int(42)
	var ts := tile_size()
	var nx := map_w / ts - 3
	var nx2 := map_w / ts - 2
	var ny := map_h / ts - 3
	var ny2 := map_h / ts - 2
	var dark_trees: Array = []
	var dead_trees: Array = []
	var gravestones: Array = []
	var crystals_blue: Array = []
	var crystals_red: Array = []
	var ancient_ruins: Array = []
	var bones: Array = []
	var mushrooms_dark: Array = []
	var rocks_mossy: Array = []
	var dark_bushes: Array = []
	var glow_flowers: Array = []
	var spike_traps: Array = []
	var torch_stones: Array = []
	var boss_landmarks: Array = []
	# ─── DARK TREES (radiant) — 45 attempt ───
	for _attempt in range(45):
		var x := rng.randint(2, nx) * ts
		var y := rng.randint(2, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_radiant(x, y, map_w, map_h):
			var sizes := [16, 20, 24]
			var variants := [0, 0, 1, 1, 2]
			dark_trees.append([x, y, sizes[rng.choice_idx(3)], variants[rng.choice_idx(5)]])
	# ─── DEAD TREES (dire) — 35 attempt ───
	for _attempt in range(35):
		var x := rng.randint(2, nx) * ts
		var y := rng.randint(2, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_dire(x, y, map_w, map_h):
			var sizes := [14, 18, 22]
			dead_trees.append([x, y, sizes[rng.choice_idx(3)]])
	# ─── GRAVESTONES (dire) — 12 attempt ───
	for _attempt in range(12):
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_dire(x, y, map_w, map_h):
			gravestones.append([x, y])
	# ─── BLUE CRYSTALS (radiant) — 15 attempt ───
	for _attempt in range(15):
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_radiant(x, y, map_w, map_h):
			crystals_blue.append([x, y, rng.randint(8, 14)])
	# ─── RED CRYSTALS (dire) — 12 attempt ───
	for _attempt in range(12):
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_dire(x, y, map_w, map_h):
			crystals_red.append([x, y, rng.randint(6, 12)])
	# ─── ANCIENT RUINS — 10 attempt, min_lane 60 ───
	for _attempt in range(10):
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 60.0):
			var variants := ["pillar", "arch", "wall"]
			ancient_ruins.append([x, y, variants[rng.choice_idx(3)]])
	# ─── BONES (dire) — 15 attempt ───
	for _attempt in range(15):
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_dire(x, y, map_w, map_h):
			var types := ["skull", "rib", "skeleton"]
			bones.append([x, y, types[rng.choice_idx(3)]])
	# ─── DARK MUSHROOMS — 25 attempt (warna ikut sisi) ───
	for _attempt in range(25):
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0):
			var pick := rng.choice_idx(3)
			var col: Color
			if _is_dire(x, y, map_w, map_h):
				var dire := [Color8(140, 30, 30), Color8(100, 20, 60), Color8(80, 40, 80)]
				col = dire[pick]
			else:
				var radiant := [Color8(60, 80, 150), Color8(100, 60, 130), Color8(140, 50, 100)]
				col = radiant[pick]
			mushrooms_dark.append([x, y, col])
	# ─── MOSSY ROCKS — 20 attempt (batas -2, bukan -3) ───
	for _attempt in range(20):
		var x := rng.randint(2, nx2) * ts
		var y := rng.randint(2, ny2) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0):
			var sizes := [12, 16, 20]
			rocks_mossy.append([x, y, sizes[rng.choice_idx(3)], _is_radiant(x, y, map_w, map_h)])
	# ─── DARK BUSHES (radiant) — 20 attempt ───
	for _attempt in range(20):
		var x := rng.randint(2, nx2) * ts
		var y := rng.randint(2, ny2) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_radiant(x, y, map_w, map_h):
			var sizes := [12, 16]
			dark_bushes.append([x, y, sizes[rng.choice_idx(2)]])
	# ─── GLOWING FLOWERS (radiant) — 20 attempt ───
	for _attempt in range(20):
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_radiant(x, y, map_w, map_h):
			# [0] = CRYSTAL_BLUE_L palettes.py (100, 170, 240).
			var cols := [Color8(100, 170, 240), Color8(150, 100, 200),
				Color8(100, 200, 150), Color8(255, 200, 100)]
			glow_flowers.append([x, y, cols[rng.choice_idx(4)]])
	# ─── SPIKE TRAPS (dire) — 8 attempt ───
	for _attempt in range(8):
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0) \
				and _is_dire(x, y, map_w, map_h):
			spike_traps.append([x, y])
	# ─── BOSS LANDMARKS — while <30, maks 240 attempt, min_lane 74 ───
	var landmark_attempts := 0
	while boss_landmarks.size() < 30 and landmark_attempts < 240:
		landmark_attempts += 1
		var x := rng.randint(3, nx) * ts
		var y := rng.randint(3, ny) * ts
		if _is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 74.0):
			var variants := [0, 1, 2, 3]
			boss_landmarks.append([x, y, variants[rng.choice_idx(4)]])
	# ─── TORCH STONES (border, tanpa RNG) ───
	for x in range(120, map_w - 80, 200):
		torch_stones.append([x, 32])
		torch_stones.append([x, map_h - 32])
	for y in range(120, map_h - 80, 200):
		torch_stones.append([32, y])
		torch_stones.append([map_w - 32, y])
	return {
		"dark_trees": dark_trees,
		"dead_trees": dead_trees,
		"gravestones": gravestones,
		"crystals_blue": crystals_blue,
		"crystals_red": crystals_red,
		"ancient_ruins": ancient_ruins,
		"bones": bones,
		"mushrooms_dark": mushrooms_dark,
		"rocks_mossy": rocks_mossy,
		"dark_bushes": dark_bushes,
		"glow_flowers": glow_flowers,
		"spike_traps": spike_traps,
		"torch_stones": torch_stones,
		"boss_landmarks": boss_landmarks,
	}


# ══════════════════════════════════════════════════════════
#  Derivasi palet ArenaMap (port export_themes converter)
# ══════════════════════════════════════════════════════════
#
# ArenaMap menggambar fallback prosedural + cuaca dari skema TURUNAN 45 kunci
# (grass_dark..., tree/light/energy/modulate, fog terpecah). Dulu skema itu
# datang dari data/themes.json; sekarang dihitung dari dict tema mentah
# (backend mana pun) oleh fungsi murni ini — themes.json tinggal menjadi
# pembanding independen (engine test membandingkan keduanya per tema).
#
# JEBAKAN: converter memakai round() Python = banker's (half-even), sedangkan
# round() GDScript = half-away-from-zero. 69 dari ribuan pembulatan derivasi
# mendarat TEPAT di .5 (mis. 55*0.9=49.5, 25*0.9=22.5) — tanpa round_half_even
# di bawah, palet Godot meleset 1 LSB di tema-tema itu.

## pygame key -> kunci ArenaMap (23 warna; salinan THEME_KEY_MAP converter —
## dicek oracle).
const THEME_KEY_MAP := {
	"radiant_grass_1": "grass_dark",
	"radiant_grass_2": "grass_mid",
	"radiant_grass_3": "grass",
	"radiant_grass_4": "grass_light",
	"radiant_grass_high": "grass_high",
	"radiant_moss": "moss",
	"dire_earth_1": "earth_dark",
	"dire_earth_2": "earth",
	"dire_earth_3": "earth_light",
	"dire_earth_4": "earth_high",
	"dire_ash": "ash",
	"dire_burnt": "burnt",
	"path_stone_1": "path_border",
	"path_stone_2": "path",
	"path_stone_3": "path_light",
	"path_stone_4": "path_bright",
	"path_moss": "path_moss",
	"path_crack": "path_crack",
	"river_deep": "river_dark",
	"river_mid": "river",
	"river_light": "river_light",
	"river_glow": "river_glow",
	"river_foam": "river_foam",
}

## Flag dekor yang dipakai ArenaMap (salinan THEME_DECOR_FLAGS — dicek oracle).
const THEME_DECOR_FLAGS := [
	"has_dark_trees", "has_dead_trees", "has_gravestones", "has_bones",
	"has_crystals_blue", "has_crystals_red", "has_ice_crystals",
	"has_rocks_mossy", "has_torch_stones",
]


## round() Python: half-even pada nilai biner eksak. Input kami selalu
## non-negatif (kanal warna, energi, alpha).
static func round_half_even(x: float) -> float:
	var f := floor(x)
	var d := x - f
	if d < 0.5:
		return f
	if d > 0.5:
		return f + 1.0
	return f if int(f) % 2 == 0 else f + 1.0


## round(x, nd) Python — bit-eksak (lihat docs/MAPS_GODOTPP.md § bankir).
##
## Cara naif round_half_even(x * 10^nd) / 10^nd SALAH: x*10^nd dibulatkan dulu
## ke double, dan royal.energy (x = 1.1685000000000001, tepat DI ATAS batas
## 1.1685) menjadi 1168.5 tepat -> 1.168, padahal round(x, 3) = 1.169. Bahkan
## pembulatan repr terpendek pun salah (repr(x) = "1.1685" tepat di batas ->
## 1.168) — satu-satunya jalan yang benar adalah membulatkan nilai BINER
## eksak x, bit per bit.
##
## Algoritme: x = m * 2^e eksak (m = mantissa 53 bit dari representasi IEEE
## 754 via encode_double), P = m * 10^nd dalam dua limb 64-bit (P muat 67
## bit; hi*S < 2^36 dan lo*S < 2^46 muat int64), P * 2^e dibulatkan half-even
## ke integer q dengan perbandingan sisa yang eksak, lalu q/10^nd — SATU
## divisi yang correctly-rounded = double terdekat ke desimal yang benar,
## sama dengan yang dikembalikan CPython. Domain kami x di [0.05, 1.3)
## sehingga s = -e selalu dalam [52, 60] (cabang s >= 32); di luar itu
## fallback naif (tak terjangkau — fungsinya tetap total).
static func _round_nd(x: float, nd: int) -> float:
	var scale := 1
	for _i in range(nd):
		scale *= 10
	if x <= 0.0 or x >= 2.0:
		var mf := float(scale)
		return round_half_even(x * mf) / mf
	var bytes := PackedByteArray()
	bytes.resize(8)
	bytes.encode_double(0, x)
	var bits := bytes.decode_u64(0)
	var mant: int = bits & 0xFFFFFFFFFFFFF
	var exp: int = (bits >> 52) & 0x7FF
	var m: int
	var e: int
	if exp == 0:
		m = mant # subnormal (tak terjangkau, tapi total)
		e = -1074
	else:
		m = mant | 0x10000000000000
		e = exp - 1075
	var s := -e
	if s < 32 or s > 60:
		var mf := float(scale)
		return round_half_even(x * mf) / mf
	var hi := m >> 32
	var lo := m & 0xFFFFFFFF
	var lo_s := lo * scale
	var hi_p := hi * scale + (lo_s >> 32)
	var lo_p := lo_s & 0xFFFFFFFF
	var k := s - 32
	var q := hi_p >> k
	var t := 1 << (k - 1)
	var alo := hi_p & ((1 << k) - 1)
	var up := false
	if alo < t:
		up = false
	elif alo > t:
		up = true
	elif lo_p != 0 or (q & 1) != 0:
		up = true # sisa di atas half, atau tepat-half dengan q ganjil
	if up:
		q += 1
	return float(q) / float(scale)


static func _mix_chan(ch: int, amount: float) -> int:
	# Campur kanal 0-255 ke arah putih (amount>0) / hitam (amount<0).
	var v := float(ch)
	if amount >= 0.0:
		v = v + (255.0 - v) * amount
	else:
		v = v * (1.0 + amount)
	return int(round_half_even(clampf(v, 0.0, 255.0)))


static func _mix_color(col: Color, amount: float) -> Color:
	return Color8(_mix_chan(col.r8(), amount), _mix_chan(col.g8(), amount),
		_mix_chan(col.b8(), amount))


static func _lum(col: Color) -> float:
	# Luminance BT.601 — urutan op sama dengan converter.
	return (0.299 * float(col.r8()) + 0.587 * float(col.g8()) + 0.114 * float(col.b8())) / 255.0


## Dict tema mentah (skema Python) -> palet turunan 45 kunci (skema ArenaMap).
## `theme_key` = kunci THEMES (dipakai hanya sebagai fallback nama, persis
## converter — seluruh 54 tema punya "name" sehingga tak pernah terpakai).
static func derive_palette(theme_key: String, raw: Dictionary) -> Dictionary:
	var out := {}
	out["name"] = str(raw.get("name", theme_key))
	for src in THEME_KEY_MAP:
		var col: Color = raw.get(src, Color.MAGENTA)
		out[THEME_KEY_MAP[src]] = col if col is Color else Color.MAGENTA
	for flag in THEME_DECOR_FLAGS:
		out[flag] = bool(raw.get(flag, false))
	out["particle_type"] = str(raw.get("particle_type", "ash"))
	out["particle_count"] = _as_int(raw.get("particle_count", 40))
	# ── kabut (port _fog_from_theme; default = default pygame) ──
	var fog: Color = raw.get("fog_color", Color8(80, 60, 60, 30))
	if not (fog is Color):
		fog = Color8(80, 60, 60, 30)
	out["fog_enabled"] = bool(raw.get("fog_enabled", true))
	out["fog_color"] = Color(fog.r, fog.g, fog.b)
	out["fog_alpha"] = _round_nd(fog.a, 4)
	out["fog_count"] = _as_int(raw.get("fog_count", 15))
	# ── extras turunan (port _derive_theme_extras) ──
	var grass1: Color = raw.get("radiant_grass_1", Color.MAGENTA)
	var moss: Color = raw.get("radiant_moss", Color.MAGENTA)
	var ps2: Color = raw.get("path_stone_2", Color.MAGENTA)
	out["tree"] = _mix_color(grass1, -0.10)
	out["tree_light"] = moss if moss is Color else Color.MAGENTA
	out["stone"] = _mix_color(ps2, 0.08)
	var samples := [
		raw.get("radiant_grass_3", Color.BLACK), raw.get("radiant_grass_4", Color.BLACK),
		raw.get("dire_earth_3", Color.BLACK), raw.get("path_stone_3", Color.BLACK),
		raw.get("river_glow", Color.BLACK),
	]
	var avg := [0.0, 0.0, 0.0]
	for s in samples:
		var c: Color = s
		avg[0] += float(c.r8())
		avg[1] += float(c.g8())
		avg[2] += float(c.b8())
	avg[0] /= 5.0
	avg[1] /= 5.0
	avg[2] /= 5.0
	var peak: float = maxf(1.0, maxf(avg[0], maxf(avg[1], avg[2])))
	var light_ch := []
	for i in range(3):
		var norm := avg[i] / peak
		var lv := 1.0 - (1.0 - norm) * 0.45
		light_ch.append(int(round_half_even(clampf(lv * 255.0, 0.0, 255.0))))
	out["light"] = Color8(light_ch[0], light_ch[1], light_ch[2])
	var g3: Color = raw.get("radiant_grass_3", Color.BLACK)
	var g4: Color = raw.get("radiant_grass_4", Color.BLACK)
	var bright: float = maxf(_lum(g3), _lum(g4))
	out["energy"] = _round_nd(clampf(0.55 + 0.75 * bright, 0.55, 1.25), 3)
	var tint = raw.get("ambient_tint")
	var mod := [255, 255, 255]
	if tint is Color:
		var tc: Color = tint
		# .a8 lagi (alasan sama dengan fog_alpha di atas): urutan op
		# float(a8)/255.0*3.0 sama persis dengan converter.
		var a: float = minf(0.35, float(tc.a8) / 255.0 * 3.0)
		mod = [
			int(round_half_even(255.0 - (255.0 - float(tc.r8())) * a)),
			int(round_half_even(255.0 - (255.0 - float(tc.g8())) * a)),
			int(round_half_even(255.0 - (255.0 - float(tc.b8())) * a)),
		]
	out["modulate"] = Color8(mod[0], mod[1], mod[2])
	return out
