# MapDBLoader.gd — pilih implementasi katalog peta: GDExt (MysticMaps,
# godot++ C++) atau GDScript (MapDB.gd + data/themes_raw.json).
#
# Bagian dari migrasi map_components/ -> godot++ (FASE 35):
#   python side   map_components/_bundle.py             (sumber kebenaran)
#   GDScript side godot/scripts/core/MapDB.gd          (data: themes_raw.json)
#   C++ side      godot/gdext/mystic_maps/src/*        (tools/gen_maps_cpp.py)
# C++ dibangkitkan dari AST _bundle.py, jadi angka di kedua backend berasal
# dari satu sumber; loader ini murni saklar — ArenaMap tidak tahu backend
# mana yang jalan (pola HeroSkillKitLoader.gd/LevelDBLoader.gd).
#
# Kapan pakai C++: mystic/maps/use_gdext_maps=true DI project.godot DAN lib
# hasil scons ada di addons/mystic_maps/bin/ (lihat
# godot/gdext/mystic_maps/README.md + .github/workflows/godot-gdext.yml).
# Kalau lib belum dibuild, fallback ke GDScript — tidak ada error, tidak ada
# perubahan perilaku.
#
# PENTING: tidak boleh menyebut `MysticMaps` sebagai IDENTIFIER di sini. Di
# CI headless lib .so tidak ikut repo, jadi referensi langsung ke class GDExt
# akan Parse Error dan mematikan seluruh project. Semua akses lewat
# ClassDB.class_exists/instantiate dengan string.

extends RefCounted

const MapDBGD = preload("res://scripts/core/MapDB.gd")

## Nama class yang didaftarkan register_types.cpp (GDCLASS MysticMaps).
const GDEXT_CLASS := "MysticMaps"
## Setting project yang menyalakan jalur C++.
const SETTING := "mystic/maps/use_gdext_maps"

static var _use_gdext: bool = false
static var _checked: bool = false
## "" = ikut ProjectSettings; "gdext"/"gdscript" = paksa (harness paritas
## butuh ini karena project.godot default-nya false).
static var _forced: String = ""
## Instance GDExt di-cache: semua method MysticMaps static, tapi Godot butuh
## sebuah Object untuk callv() (pola sama dengan HeroSkillKitLoader).
static var _inst: Object = null
## Backend terakhir yang DIUMUMKAN ke log — harness A/B memanggil
## force_backend() ratusan kali, satu baris log per panggilan menenggelamkan
## error sungguhan (plus CI me-require baris pengumuman ini).
static var _announced: String = "__belum__"
## Katalog di-cache per backend: all_themes() membangun 54 Dictionary, dan
## MainMenu/ArenaMap memanggilnya berkali-kali per layar.
static var _catalog: Dictionary = {}
static var _catalog_backend: String = "__kosong__"


## True kalau lib C++ termuat engine (terlepas dari setting/force).
static func gdext_available() -> bool:
	return ClassDB.class_exists(GDEXT_CLASS)


static func _resolve() -> void:
	_checked = true
	_use_gdext = false
	_inst = null
	var want := _forced
	if want == "":
		var flag := false
		if ProjectSettings.has_setting(SETTING):
			flag = bool(ProjectSettings.get_setting(SETTING))
		want = "gdext" if flag else "gdscript"
	if want == "gdext":
		if not ClassDB.class_exists(GDEXT_CLASS):
			if _forced == "":
				_announce("gdext-hilang", "[MapDBLoader] flag "
					+ "use_gdext_maps=true tapi GDExt tidak ditemukan, "
					+ "fallback GDScript")
		else:
			var inst = ClassDB.instantiate(GDEXT_CLASS)
			if inst == null:
				_announce("gdext-gagal", "[MapDBLoader] GAGAL instantiate "
					+ "%s, fallback GDScript" % GDEXT_CLASS)
			else:
				_inst = inst
				_use_gdext = true
				# Baris ini di-require CI (godot-gdext.yml): bukti jalur C++
				# benar-benar dipakai, bukan fallback diam-diam. Frasa
				# "GDExtension MysticMaps aktif" harus SATU literal utuh
				# (dicek statis tools/test_godot_map_data_parity.py).
				var signature := str(_call_gdext("catalog_signature", []))
				_announce("gdext", "[MapDBLoader] GDExtension MysticMaps aktif "
					+ "(godot++ C++) — katalog " + signature)
	if not _use_gdext:
		_announce("gdscript", "[MapDBLoader] backend GDScript "
			+ "(MapDB.gd + data/themes_raw.json)")


## Cetak sekali per PERUBAHAN backend (bukan sekali per panggilan _resolve).
static func _announce(key: String, message: String) -> void:
	if _announced == key:
		return
	_announced = key
	print(message)


static func _ensure_checked() -> void:
	if not _checked:
		_resolve()


## Paksa backend — dipakai harness paritas supaya jalur C++ bisa diuji tanpa
## mengubah project.godot (yang default-nya false demi CI tanpa compiler).
## backend: "gdext" | "gdscript" | "" (kembali ikut ProjectSettings).
static func force_backend(backend: String) -> void:
	_forced = backend
	_checked = false
	_inst = null
	# Katalog ikut dibuang: isinya milik backend lama.
	_catalog = {}
	_catalog_backend = "__kosong__"
	_resolve()


static func reset_backend() -> void:
	force_backend("")


## "gdext" kalau jalur C++ aktif, selain itu "gdscript".
static func backend_name() -> String:
	_ensure_checked()
	return "gdext" if _use_gdext else "gdscript"


static func is_using_gdext() -> bool:
	_ensure_checked()
	return _use_gdext


## Buang cache katalog (setelah convert_to_godot.py / ganti backend).
static func reload() -> void:
	_catalog = {}
	_catalog_backend = "__kosong__"
	MapDBGD.reload()


## Panggil method static MysticMaps lewat instance cache.
## Return null kalau backend GDScript aktif / method tidak ada — pemanggil
## menerjemahkan null menjadi "pakai fallback GDScript".
static func _call_gdext(method: String, args: Array):
	_ensure_checked()
	if _inst == null:
		return null
	if not _inst.has_method(method):
		push_error("[MapDBLoader] %s tidak punya method %s — regenerasi "
			% [GDEXT_CLASS, method]
			+ "tools/gen_maps_cpp.py lalu build ulang lib")
		return null
	return _inst.callv(method, args)


## Backend C++ siap untuk `method` (lib termuat + methodnya ada).
static func _gdext_ready(method: String) -> bool:
	_ensure_checked()
	if not _use_gdext or _inst == null:
		return false
	if not _inst.has_method(method):
		push_error("[MapDBLoader] %s tidak punya method %s — regenerasi "
			% [GDEXT_CLASS, method]
			+ "tools/gen_maps_cpp.py lalu build ulang lib")
		return false
	return true


# ══════════════════════════════════════════════════════════
#  API palettes/themes/generators
# ══════════════════════════════════════════════════════════

## TILE_SIZE (palettes.py).
static func tile_size() -> int:
	if _gdext_ready("tile_size"):
		return int(_call_gdext("tile_size", []))
	return MapDBGD.tile_size()


## Konstanta warna palettes.py {NAMA: Color}.
static func palettes() -> Dictionary:
	if _gdext_ready("palettes"):
		var got = _call_gdext("palettes", [])
		if got is Dictionary:
			return got
	return MapDBGD.palettes()


## 54 nama tema, urutan THEMES (Array of String di kedua backend; C++
## mengembalikan PackedStringArray jadi dinormalkan di sini).
static func theme_names() -> Array:
	if _gdext_ready("theme_names"):
		var got = _call_gdext("theme_names", [])
		if got is Array or got is PackedStringArray:
			var names: Array = []
			for n in got:
				names.append(str(n))
			return names
	return MapDBGD.theme_names()


## Jumlah tema (len(THEMES)).
static func theme_count() -> int:
	if _gdext_ready("theme_count"):
		return int(_call_gdext("theme_count", []))
	return MapDBGD.theme_count()


## Tema ke-`index` (skema Python mentah); {} kalau di luar jangkauan.
static func build_theme(index: int) -> Dictionary:
	if _gdext_ready("build_theme"):
		var got = _call_gdext("build_theme", [index])
		if got is Dictionary:
			return got
	return MapDBGD.build_theme(index)


## Indeks tema untuk nama, -1 kalau tidak ada.
static func theme_index(theme_name: String) -> int:
	if _gdext_ready("theme_index"):
		return int(_call_gdext("theme_index", [theme_name]))
	return MapDBGD.theme_index(theme_name)


## Config tema dengan fallback forest (paritas THEMES.get(nama, FOREST_THEME)).
static func get_theme(theme_name: String) -> Dictionary:
	if _gdext_ready("get_theme"):
		var got = _call_gdext("get_theme", [theme_name])
		if got is Dictionary:
			return got
	return MapDBGD.get_theme(theme_name)


## Seluruh katalog {nama: tema} (paritas THEMES).
static func all_themes() -> Dictionary:
	_ensure_checked()
	var backend := backend_name()
	if _catalog_backend == backend:
		return _catalog
	var rows: Dictionary = {}
	if _gdext_ready("all_themes"):
		var got = _call_gdext("all_themes", [])
		if got is Dictionary and not (got as Dictionary).is_empty():
			rows = got
		else:
			push_warning("[MapDBLoader] MysticMaps.all_themes() kosong — "
				+ "fallback MapDB.gd (lib basi? regenerasi "
				+ "tools/gen_maps_cpp.py)")
	if rows.is_empty():
		rows = MapDBGD.all_themes()
	_catalog = rows
	_catalog_backend = backend
	return _catalog


## Interpolasi Catmull-Rom (port make_curved_path).
static func make_curved_path(waypoints: PackedVector2Array, smoothness: int) -> PackedVector2Array:
	if _gdext_ready("make_curved_path"):
		var got = _call_gdext("make_curved_path", [waypoints, smoothness])
		if got is PackedVector2Array:
			return got
	return MapDBGD.make_curved_path(waypoints, smoothness)


## Tiga lane (top/mid/bot) — paritas generate_lanes.
static func generate_lanes(map_w: int, map_h: int) -> Dictionary:
	if _gdext_ready("generate_lanes"):
		var got = _call_gdext("generate_lanes", [map_w, map_h])
		if got is Dictionary:
			return got
	return MapDBGD.generate_lanes(map_w, map_h)


## Jalur sungai — paritas generate_river.
static func generate_river(map_w: int, map_h: int) -> PackedVector2Array:
	if _gdext_ready("generate_river"):
		var got = _call_gdext("generate_river", [map_w, map_h])
		if got is PackedVector2Array:
			return got
	return MapDBGD.generate_river(map_w, map_h)


## 14 kategori dekorasi — paritas DecorationGenerator.generate_all.
## shop_positions: Array of Vector2.
static func generate_decorations(map_w: int, map_h: int, lane_points: PackedVector2Array,
		river_points: PackedVector2Array, shop_positions: Array) -> Dictionary:
	if _gdext_ready("generate_decorations"):
		var got = _call_gdext("generate_decorations",
			[map_w, map_h, lane_points, river_points, shop_positions])
		if got is Dictionary:
			return got
	return MapDBGD.generate_decorations(map_w, map_h, lane_points, river_points, shop_positions)


## Palet turunan 45 kunci (skema ArenaMap) dari dict tema mentah. Implementasi
## tunggal di MapDB.gd — dict dari kedua backend sudah setipe (Color/int/
## String/bool) sehingga derivasinya backend-agnostik.
static func derive_palette(theme_key: String, raw: Dictionary) -> Dictionary:
	return MapDBGD.derive_palette(theme_key, raw)


## Jalan pintas: get_theme(nama) + derive_palette — yang dipakai ArenaMap.
static func theme_palette(theme_name: String) -> Dictionary:
	return derive_palette(theme_name, get_theme(theme_name))


## Tanda tangan katalog C++ ("54:forest-hollowbane:2984"), "" kalau backend
## GDScript — dipakai harness membuktikan lib yang termuat membawa tabel
## generasi yang sama dengan data repo.
static func catalog_signature() -> String:
	if _gdext_ready("catalog_signature"):
		return str(_call_gdext("catalog_signature", []))
	return ""
