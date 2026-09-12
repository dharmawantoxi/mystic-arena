# LevelDBLoader.gd — pilih implementasi katalog level: GDExt (MysticLevels,
# godot++ C++) atau GDScript (LevelDB.gd + data/levels.json).
#
# Bagian dari migrasi levels/level_data.py -> godot++ (FASE 34):
#   python side   levels/level_data.py                  (sumber kebenaran)
#   GDScript side godot/scripts/core/LevelDB.gd         (data: data/levels.json)
#   C++ side      godot/gdext/mystic_levels/src/*       (tools/gen_levels_cpp.py)
# C++ dibangkitkan dari AST level_data.py, jadi angka di kedua backend berasal
# dari satu sumber; loader ini murni saklar — BossDB/GameManager tidak tahu
# backend mana yang jalan (pola HeroSkillKitLoader.gd).
#
# Kapan pakai C++: mystic/levels/use_gdext_levels=true DI project.godot DAN
# lib hasil scons ada di addons/mystic_levels/bin/ (lihat
# godot/gdext/mystic_levels/README.md + .github/workflows/godot-gdext.yml).
# Kalau lib belum dibuild, fallback ke GDScript — tidak ada error, tidak ada
# perubahan perilaku.
#
# PENTING: tidak boleh menyebut `MysticLevels` sebagai IDENTIFIER di sini.
# Di CI headless lib .so tidak ikut repo, jadi referensi langsung ke class
# GDExt akan Parse Error dan mematikan seluruh project. Semua akses lewat
# ClassDB.class_exists/instantiate dengan string.

extends RefCounted

const LevelDBGD = preload("res://scripts/core/LevelDB.gd")

## Nama class yang didaftarkan register_types.cpp (GDCLASS MysticLevels).
const GDEXT_CLASS := "MysticLevels"
## Setting project yang menyalakan jalur C++.
const SETTING := "mystic/levels/use_gdext_levels"

static var _use_gdext: bool = false
static var _checked: bool = false
## "" = ikut ProjectSettings; "gdext"/"gdscript" = paksa (harness paritas
## LevelDataGdextParityTest butuh ini karena project.godot default-nya false).
static var _forced: String = ""
## Instance GDExt di-cache: semua method MysticLevels static, tapi Godot butuh
## sebuah Object untuk callv() (pola sama dengan HeroSkillKitLoader).
static var _inst: Object = null
## Backend terakhir yang DIUMUMKAN ke log — harness A/B memanggil
## force_backend() ratusan kali, satu baris log per panggilan menenggelamkan
## error sungguhan (plus CI me-require baris pengumuman ini).
static var _announced: String = "__belum__"
## Katalog di-cache per backend: all_levels() membangun 54 Dictionary, dan
## BossDB/GameManager/MainMenu memanggilnya berkali-kali per layar.
static var _catalog: Array = []
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
				_announce("gdext-hilang", "[LevelDBLoader] flag "
					+ "use_gdext_levels=true tapi GDExt tidak ditemukan, "
					+ "fallback GDScript")
		else:
			var inst = ClassDB.instantiate(GDEXT_CLASS)
			if inst == null:
				_announce("gdext-gagal", "[LevelDBLoader] GAGAL instantiate "
					+ "%s, fallback GDScript" % GDEXT_CLASS)
			else:
				_inst = inst
				_use_gdext = true
				# Baris ini di-require CI (godot-gdext.yml): bukti jalur C++
				# benar-benar dipakai, bukan fallback diam-diam. Frasa
				# "GDExtension MysticLevels aktif" harus SATU literal utuh
				# (dicek statis tools/test_godot_level_data_parity.py).
				var signature := str(_call_gdext("catalog_signature", []))
				_announce("gdext", "[LevelDBLoader] GDExtension MysticLevels aktif "
					+ "(godot++ C++) — katalog " + signature)
	if not _use_gdext:
		_announce("gdscript", "[LevelDBLoader] backend GDScript "
			+ "(LevelDB.gd + data/levels.json)")


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
	# Katalog ikut dibuang: isinya milik backend lama (dan tipe nilainya
	# berbeda kalau salah satu jalur belum dinormalkan).
	_catalog = []
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
	_catalog = []
	_catalog_backend = "__kosong__"
	LevelDBGD.reload()


## Panggil method static MysticLevels lewat instance cache.
## Return null kalau backend GDScript aktif / method tidak ada — pemanggil
## menerjemahkan null menjadi "pakai fallback GDScript".
static func _call_gdext(method: String, args: Array):
	_ensure_checked()
	if _inst == null:
		return null
	if not _inst.has_method(method):
		push_error("[LevelDBLoader] %s tidak punya method %s — regenerasi "
			% [GDEXT_CLASS, method]
			+ "tools/gen_levels_cpp.py lalu build ulang lib")
		return null
	return _inst.callv(method, args)


## Backend C++ siap untuk `method` (lib termuat + methodnya ada).
static func _gdext_ready(method: String) -> bool:
	_ensure_checked()
	if not _use_gdext or _inst == null:
		return false
	if not _inst.has_method(method):
		push_error("[LevelDBLoader] %s tidak punya method %s — regenerasi "
			% [GDEXT_CLASS, method]
			+ "tools/gen_levels_cpp.py lalu build ulang lib")
		return false
	return true


## Kunci int untuk API C++ (parameternya int64). null = input di luar domain
## C++ (float non-bulat / bukan angka) -> pemakai memakai jalur GDScript yang
## meniru Python penuh. Contoh: get_level_config(3.0) -> 3 (Python cocok),
## get_level_config(3.5) -> null (Python: tidak ada level 3.5).
static func _int_key(value):
	match typeof(value):
		TYPE_INT:
			return int(value)
		TYPE_FLOAT:
			var f := float(value)
			if f == float(int(f)):
				return int(f)
			return null
		_:
			return null


# ══════════════════════════════════════════════════════════
#  API levels/__init__.py
# ══════════════════════════════════════════════════════════

## ALL_LEVELS — katalog 54 level (Array of Dictionary, tipe Python).
static func all_levels() -> Array:
	_ensure_checked()
	var backend := backend_name()
	if _catalog_backend == backend:
		return _catalog
	var rows: Array = []
	if _gdext_ready("all_levels"):
		var got = _call_gdext("all_levels", [])
		if got is Array:
			rows = got
		if rows.is_empty():
			push_warning("[LevelDBLoader] MysticLevels.all_levels() kosong — "
				+ "fallback LevelDB.gd (lib basi? regenerasi "
				+ "tools/gen_levels_cpp.py)")
	if rows.is_empty():
		rows = LevelDBGD.all_levels()
	_catalog = rows
	_catalog_backend = backend
	return _catalog


## get_level_config — Dictionary, atau null kalau level tidak ada
## (Python: None). BossDB.get_level() menerjemahkan null menjadi {}.
static func get_level_config(level_number):
	if _gdext_ready("get_level_config"):
		var key = _int_key(level_number)
		if key == null:
			return LevelDBGD.get_level_config(level_number)
		return _call_gdext("get_level_config", [key])
	return LevelDBGD.get_level_config(level_number)


## get_level_count — len(ALL_LEVELS).
static func get_level_count() -> int:
	if _gdext_ready("get_level_count"):
		return int(_call_gdext("get_level_count", []))
	return LevelDBGD.get_level_count()


## is_level_unlocked — required in completed_levels (semantik == Python,
## BUKAN Array.has() yang strict-tipe; lihat LevelDB.py_contains).
static func is_level_unlocked(level_number, completed_levels) -> bool:
	if _gdext_ready("is_level_unlocked"):
		var key = _int_key(level_number)
		if key != null and (completed_levels is Array):
			return bool(_call_gdext("is_level_unlocked", [key, completed_levels]))
	return LevelDBGD.is_level_unlocked(level_number, completed_levels)


## get_next_level — nomor level berikutnya, atau null kalau sudah terakhir.
## Python mengembalikan `current_level + 1` APA ADANYA: int tetap int, float
## tetap float (get_next_level(3.0) -> 4.0). API C++ bertanda tangan int64,
## jadi jalur native hanya dipakai untuk input int; float diserahkan ke
## LevelDB.gd yang meniru Python penuh. Semua call site Godot mengirim int.
static func get_next_level(current_level):
	if typeof(current_level) == TYPE_INT and _gdext_ready("get_next_level"):
		return _call_gdext("get_next_level", [int(current_level)])
	return LevelDBGD.get_next_level(current_level)


## `needle in haystack` semantik Python — diekspos supaya harness paritas bisa
## A/B kedua backend tanpa menebak implementasinya.
static func py_contains(haystack, needle) -> bool:
	if _gdext_ready("py_contains") and (haystack is Array):
		return bool(_call_gdext("py_contains", [haystack, needle]))
	if haystack is Array:
		return LevelDBGD.py_contains(haystack, needle)
	return false


## Tanda tangan katalog C++ ("<jumlah>:<awal>-<akhir>:<total mini boss>"),
## "" kalau backend GDScript — dipakai harness membuktikan lib yang termuat
## membawa tabel generasi yang sama dengan data repo.
static func catalog_signature() -> String:
	if _gdext_ready("catalog_signature"):
		return str(_call_gdext("catalog_signature", []))
	return ""
