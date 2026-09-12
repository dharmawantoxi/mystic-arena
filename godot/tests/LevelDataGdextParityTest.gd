# LevelDataGdextParityTest — levels/level_data.py -> godot++ (C++).
#
# Scene ini memutar ULANG LevelDataParityTest (oracle Python: katalog 54 level
# x 17 field + 4 helper) dengan backend DIPAKSA ke GDExtension C++
# (`MysticLevels`, lib hasil build godot/gdext/mystic_levels). Jadi yang diuji
# bukan "C++ sama dengan C++", melainkan "C++ sama dengan Python", lewat rantai:
#
#   levels/level_data.py --(tools/test_godot_level_data_parity.py)--> fixture
#   fixture <--dibandingkan--> LevelDBLoader -> MysticLevels (C++)
#
# BossDB/GameManager memanggil LevelDBLoader, jadi memaksa backend di loader
# sudah cukup untuk mengalihkan katalog + get_level_config/get_level_count/
# is_level_unlocked/get_next_level ke C++ tanpa menyentuh pemakainya.
#
# Ditambah baterai A/B backend: SEMUA permukaan API dikumpulkan dua kali (C++
# lalu GDScript) dan dibandingkan kunci demi kunci — katalog 54 baris
# (str(Dictionary) ikut mengunci URUTAN kunci), 22 kasus get_level_config,
# 20 kasus is_level_unlocked, 15 kasus py_contains, 2 deviasi bool, dan 17
# kasus get_next_level (tipe nilai balik ikut dibandingkan: Python mengembalikan
# 4.0 untuk input 3.0).
#
# Scene ini HANYA berarti kalau lib GDExt sudah dibuild:
#   cd godot/gdext/mystic_levels
#   git clone -b godot-4.3-stable --depth 1 \
#     https://github.com/godotengine/godot-cpp godot-cpp
#   scons platform=linux target=template_debug -j4
# Tanpa lib, scene GAGAL (bukan skip) — CI .github/workflows/godot-gdext.yml
# yang membuild lib lalu menjalankannya. Jalur GDScript murni tetap dijaga
# LevelDataParityTest di godot-check.yml (tanpa compiler).
#
# godot --headless --path godot res://tests/LevelDataGdextParityTest.tscn --quit-after 120
# Require "[LevelDataGdextParityTest] PASS" + "GDExtension MysticLevels aktif".
extends "res://tests/LevelDataParityTest.gd"

const LevelsLoader = preload("res://scripts/core/LevelDBLoader.gd")


func _boot() -> void:
	if not LevelsLoader.gdext_available():
		_fail_gdext("class MysticLevels tidak terdaftar engine",
			"build lib GDExt dulu (godot/gdext/mystic_levels/README.md) lalu "
			+ "jalankan scene ini — tanpa lib, jalur C++ tidak teruji")
		_abort()
		return
	LevelsLoader.force_backend("gdext")
	if not LevelsLoader.is_using_gdext():
		_fail_gdext("force_backend('gdext') tidak mengaktifkan jalur C++",
			"LevelDBLoader gagal instantiate MysticLevels")
		_abort()
		return
	backend_override = "gdext"
	print("[LevelDataGdextParityTest] backend=%s (class MysticLevels termuat, "
		% LevelsLoader.backend_name()
		+ "katalog %s)" % LevelsLoader.catalog_signature())

	# A/B butuh baterai fixture; base _boot() memuatnya lagi (murah, dan
	# snapshot save memang harus terjadi setelah jalur C++ terbukti aktif).
	_load_fixture()
	if _failures == 0:
		_ab_battery()

	# Sisa baterai = persis LevelDataParityTest, tapi tiap panggilan katalog
	# dan helper kini masuk ke C++.
	super._boot()


## A/B backend: kumpulkan seluruh permukaan API satu backend, lalu bandingkan.
## Backend DIPAKSA per-batch (bukan per panggilan) — force_backend() me-resolve
## loader + membuang cache katalog, jadi memanggilnya ribuan kali hanya
## memboroskan waktu dan menenggelamkan log.
func _ab_battery() -> void:
	var got_c := _collect("gdext")
	var got_g := _collect("gdscript")
	LevelsLoader.force_backend("gdext")
	var keys := got_c.keys()
	keys.sort()
	var mismatch := 0
	for k in keys:
		_checks += 1
		if str(got_c[k]) == str(got_g.get(k)):
			continue
		mismatch += 1
		_fail_gdext(str(k), "C++ %s vs GDScript %s"
			% [_canon(got_c[k]), _canon(got_g.get(k))])
	print("[LevelDataGdextParityTest] A/B backend: %d kunci (katalog + 4 helper "
		% keys.size()
		+ "+ py_contains), mismatch %d" % mismatch)


func _collect(backend: String) -> Dictionary:
	LevelsLoader.force_backend(backend)
	var out := {}
	out["backend"] = LevelsLoader.backend_name()
	out["count"] = LevelsLoader.get_level_count()
	var rows: Array = LevelsLoader.all_levels()
	out["all_levels.size"] = rows.size()
	for i in range(rows.size()):
		out["row:%02d" % i] = _row_signature(rows[i])
	for case in _fx["get_level_config_battery"]:
		var label := _probe_label(case[0])
		var got = LevelsLoader.get_level_config(_dec(case[0]))
		out["config:" + label] = "null" if got == null else _row_signature(got)
	for case in _fx["is_level_unlocked_battery"]:
		out["unlock:%d:%s" % [int(case[0]), str(case[1])]] = str(
			LevelsLoader.is_level_unlocked(int(case[0]), _dec_list(case[1])))
	for case in _fx["py_contains_battery"]:
		out["contains:%s:%s" % [str(case[0]), str(case[1])]] = str(
			LevelsLoader.py_contains(_dec_list(case[0]), _dec(case[1])))
	for case in _fx["deviation_battery"]:
		out["deviation:%s:%s" % [str(case[0]), str(case[1])]] = str(
			LevelsLoader.py_contains(_dec_list(case[0]), _dec(case[1])))
	for case in _fx["get_next_level_battery"]:
		var nxt = LevelsLoader.get_next_level(_dec(case[0]))
		# Tipe nilai balik ikut dibandingkan: Python get_next_level(3.0) -> 4.0.
		out["next:" + _probe_label(case[0])] = "%s:%s" % [_kind_name(nxt), str(nxt)]
	return out


func _fail_gdext(tag: String, message: String) -> void:
	# Lewat _fail() base supaya ikut terhitung di _failures (exit code 1) dan
	# tercetak dengan pola "[...Test] ..." yang dibaca godot_log_gate.
	_fail("gdext/" + tag, message)


func _abort() -> void:
	_done = true
	for msg in _error_messages:
		print(msg)
	print("[LevelDataGdextParityTest] FAIL: jalur C++ tidak bisa diuji")
	LevelsLoader.reload()
	LevelsLoader.reset_backend()
	get_tree().quit(1)


func _finish() -> void:
	if _done:
		return
	var failed := int(_failures)
	var checks := int(_checks)
	super._finish()
	LevelsLoader.reset_backend()
	if failed == 0:
		print("[LevelDataGdextParityTest] PASS: katalog %d level + 4 helper "
			% int(_fx.get("get_level_count", 0))
			+ "lewat MysticLevels (C++), %d check" % checks)
		print("[LevelDataGdextParityTest] PASS")
	else:
		print("[LevelDataGdextParityTest] FAIL: %d kegagalan di backend gdext"
			% failed)
