# MapDataGdextParityTest — map_components/_bundle.py -> godot++ (C++).
#
# Scene ini memutar ULANG MapDataParityTest (oracle Python: katalog 54 tema +
# PathGenerator + DecorationGenerator + derive) dengan backend DIPAKSA ke
# GDExtension C++ (`MysticMaps`, lib hasil build godot/gdext/mystic_maps).
# Jadi yang diuji bukan "C++ sama dengan C++", melainkan "C++ sama dengan
# Python", lewat rantai:
#
#   map_components/_bundle.py --(tools/test_godot_map_data_parity.py)--> fixture
#   fixture <--dibandingkan--> MapDBLoader -> MysticMaps (C++)
#
# ArenaMap memanggil MapDBLoader, jadi memaksa backend di loader sudah cukup
# untuk mengalihkan tema + lane + river + dekor ke C++ tanpa menyentuh
# pemakainya.
#
# Ditambah baterai A/B backend: SEMUA permukaan API dikumpulkan dua kali (C++
# lalu GDScript) dan dibandingkan kunci demi kunci — 54 baris katalog
# (str(Dictionary) ikut mengunci URUTAN kunci), palet, nama tema, baterai
# index/get/build, 5 kasus kurva, lane/river 2 ukuran, dekor 2 varian, dan
# 54 palet turunan (derive_palette GDScript-only tapi input mentahnya dari
# backend masing-masing — A/B ini membuktikan baris C++ memberi derive yang
# identik, termasuk royal.energy = 1.169).
#
# Scene ini HANYA berarti kalau lib GDExt sudah dibuild:
#   cd godot/gdext/mystic_maps
#   ln -s ../godot-cpp godot-cpp   (atau clone godot-4.3-stable)
#   scons platform=linux target=template_debug -j4
# Tanpa lib, scene GAGAL (bukan skip) — CI .github/workflows/godot-gdext.yml
# yang membuild lib lalu menjalankannya. Jalur GDScript murni tetap dijaga
# MapDataParityTest di godot-check.yml (tanpa compiler).
#
# godot --headless --path godot res://tests/MapDataGdextParityTest.tscn --quit-after 120
# Require "[MapDataGdextParityTest] PASS" + "GDExtension MysticMaps aktif".
extends "res://tests/MapDataParityTest.gd"

const MapsLoader = preload("res://scripts/core/MapDBLoader.gd")


func _boot() -> void:
	if not MapsLoader.gdext_available():
		_fail_gdext("class MysticMaps tidak terdaftar engine",
			"build lib GDExt dulu (godot/gdext/mystic_maps/README.md) lalu "
			+ "jalankan scene ini — tanpa lib, jalur C++ tidak teruji")
		_abort()
		return
	MapsLoader.force_backend("gdext")
	if not MapsLoader.is_using_gdext():
		_fail_gdext("force_backend('gdext') tidak mengaktifkan jalur C++",
			"MapDBLoader gagal instantiate MysticMaps")
		_abort()
		return
	backend_override = "gdext"
	print("[MapDataGdextParityTest] backend=%s (class MysticMaps termuat, "
		% MapsLoader.backend_name()
		+ "katalog %s)" % MapsLoader.catalog_signature())

	# A/B butuh baterai fixture; base _boot() memuatnya lagi (murah).
	_load_fixture()
	if not _fx.is_empty():
		_ab_battery()

	# Sisa baterai = persis MapDataParityTest, tapi tiap panggilan kini
	# masuk ke C++.
	super._boot()


## A/B backend: kumpulkan seluruh permukaan API satu backend, lalu bandingkan.
## Backend DIPAKSA per-batch (bukan per panggilan) — force_backend() me-resolve
## loader + membuang cache katalog, jadi memanggilnya ribuan kali hanya
## memboroskan waktu dan menenggelamkan log.
func _ab_battery() -> void:
	var got_c := _collect("gdext")
	var got_g := _collect("gdscript")
	# Label backend BUKAN bagian permukaan API yang dibandingkan — isinya justru
	# HARUS beda. Kalau sama, force_backend() tidak benar-benar berpindah dan
	# seluruh A/B ini tidak berarti, jadi labelnya dijadikan assertion sendiri
	# lalu dibuang dari kamus sebelum perbandingan kunci demi kunci.
	_expect(str(got_c.get("backend")) == "gdext"
		and str(got_g.get("backend")) == "gdscript",
		"force_backend() tidak mengganti backend (A=%s, B=%s) — A/B tidak berarti"
		% [str(got_c.get("backend")), str(got_g.get("backend"))])
	got_c.erase("backend")
	got_g.erase("backend")
	MapsLoader.force_backend("gdext")
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
	print("[MapDataGdextParityTest] A/B backend: %d kunci (katalog + palet + "
		% keys.size()
		+ "kurva + lane/river + dekor + derive), mismatch %d" % mismatch)


func _collect(backend: String) -> Dictionary:
	MapsLoader.force_backend(backend)
	var out := {}
	# Kunci "backend" = label batch ini (dipakai _ab_battery sebagai bukti
	# force_backend() bekerja); dihapus sebelum kamus A dan B dibandingkan.
	out["backend"] = MapsLoader.backend_name()
	out["count"] = MapsLoader.theme_count()
	out["tile"] = MapsLoader.tile_size()
	out["palettes"] = _row_signature(MapsLoader.palettes())
	out["names"] = str(MapsLoader.theme_names())
	var catalog: Dictionary = MapsLoader.all_themes()
	for tname in MapsLoader.theme_names():
		out["row:" + str(tname)] = _row_signature(catalog.get(tname))
	for case in _fx["theme_index_battery"]:
		out["index:" + str(case[0])] = str(MapsLoader.theme_index(str(case[0])))
	for case in _fx["get_theme_battery"]:
		out["get:" + str(case[0])] = _row_signature(MapsLoader.get_theme(str(case[0])))
	for case in _fx["build_theme_battery"]:
		out["build:" + str(case[0])] = _row_signature(
			MapsLoader.build_theme(int(case[0])))
	for case in _fx["curve_battery"]:
		var pts := MapsLoader.make_curved_path(_fixture_v2s(case["waypoints"]),
			int(case["smoothness"]))
		out["curve:" + str(case["name"])] = str(pts)
	for size_key in ["1280x720", "1025x769"]:
		var dims := str(size_key).split("x")
		var lanes := MapsLoader.generate_lanes(int(dims[0]), int(dims[1]))
		out["lanes:" + size_key] = str(lanes)
		out["river:" + size_key] = str(MapsLoader.generate_river(int(dims[0]), int(dims[1])))
	# Dekor A/B memakai lane_points FIXTURE (terisolasi dari lane).
	var want_lanes: Dictionary = (_fx["lanes"] as Dictionary)["1280x720"]
	var lane_pts := PackedVector2Array()
	for lane in ["top", "bot", "mid"]:
		lane_pts.append_array(_fixture_v2s(want_lanes[lane]))
	var river_pts := _fixture_v2s((_fx["river"] as Dictionary)["1280x720"])
	var shops: Array = []
	for s in _fx["decor_shops"]:
		shops.append(Vector2(int(s[0]), int(s[1])))
	out["decor:shops"] = str(MapsLoader.generate_decorations(
		1280, 720, lane_pts, river_pts, shops))
	out["decor:no_shops"] = str(MapsLoader.generate_decorations(
		1280, 720, lane_pts, river_pts, []))
	for tname in MapsLoader.theme_names():
		out["derive:" + str(tname)] = _row_signature(
			MapsLoader.theme_palette(str(tname)))
	return out


func _fail_gdext(tag: String, message: String) -> void:
	# Lewat _fail() base supaya ikut terhitung di _failures (exit code 1) dan
	# tercetak dengan pola "[...Test] ..." yang dibaca godot_log_gate.
	# PENTING: _fail() base hanya menerima SATU argumen (message) — tag
	# dirangkai di sini. Salah jumlah argumen = Parse Error saat scene dimuat
	# (GDScript memeriksa arity lintas berkas, gdparse tidak), jadi bentuk ini
	# dikunci tools/test_godot_map_data_parity.py.
	_fail("gdext/%s: %s" % [tag, message])


func _abort() -> void:
	_done = true
	for msg in _error_messages:
		print(msg)
	print("[MapDataGdextParityTest] FAIL: jalur C++ tidak bisa diuji")
	MapsLoader.reload()
	MapsLoader.reset_backend()
	get_tree().quit(1)


func _finish() -> void:
	if _done:
		return
	var failed := int(_failures)
	var checks := int(_checks)
	super._finish()
	MapsLoader.reset_backend()
	if failed == 0:
		print("[MapDataGdextParityTest] PASS: katalog %d tema + PathGenerator + "
			% int((_fx["source"] as Dictionary).get("theme_count", 0))
			+ "DecorationGenerator + derive lewat MysticMaps (C++), %d check" % checks)
		print("[MapDataGdextParityTest] PASS")
	else:
		print("[MapDataGdextParityTest] FAIL: %d kegagalan di backend gdext"
			% failed)
