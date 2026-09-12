# MapDataParityTest — paritas map_components/_bundle.py -> Godot (backend GDScript).
#
# Oracle = fixture `map_data.json`, direkam dari _bundle.py ASLI oleh
# tools/test_godot_map_data_parity.py (AST + eksekusi murni tanpa pygame).
# Oracle itu JUGA membandingkan themes_raw.json, KEY_KINDS MapDB.gd,
# waypoint/smoothness, struktur DecorationGenerator, stream MT19937, dan
# derive_palette dengan modul Python-nya, jadi drift data ketahuan bahkan
# sebelum engine diunduh; scene ini mengunci SEMANTIK RUNTIME-nya:
#
#   1. backend aktif == yang dipaksa (default "gdscript"; subclass GDExt "gdext")
#   2. catalog_signature + theme_count (gdext: "54:forest-hollowbane:2984")
#   3. tile_size + 52 palet (TIPE Color + r8/g8/b8 per kanal)
#   4. theme_names: 54 nama + URUTAN THEMES
#   5. katalog: 54 tema — NILAI, TIPE Variant (Color/PackedColorArray/int/
#      str/bool/nil), dan URUTAN kunci per tema (non-seragam: forest 55,
#      haunted 69 kunci)
#   6. theme_index: 54 nama + tak dikenal -> -1
#   7. get_theme: tak dikenal -> baris forest (paritas THEMES.get)
#   8. build_theme: 0/53 valid, -1/54/99 -> {} kosong
#   9. make_curved_path: 5 kasus (kosong, singleton, garis, sudut, diagonal)
#  10. generate_lanes/generate_river di 2 ukuran (1280x720 + ganjil 1025x769)
#      — titik PERSIS (ini baterai yang menangkap deviasi port lama: titik
#      float + smoothness mid 10, bukan trunc int + 8)
#  11. generate_decorations 14 kategori x 2 varian toko (posisi + ukuran +
#      varian + warna + bool, PERSIS — replika MT19937 hidup di sini)
#  12. isolasi mutasi: dict tema yang dikembalikan SEGAR (deviasi
#      terdokumentasi dari Python yang mengembalikan objek live)
#  13. derive vs themes.json: 54 palet turunan loader == converter,
#      kunci-per-kunci (independence check; termasuk royal.energy = 1.169
#      yang ditemukan oracle statis sebagai kasus batas double-rounding)
#  14. wiring produksi: ArenaMap(cost THEMES kurasi + loader + lane/river/
#      toko) — instance scene asli, bukan stub
#
# Tidak menyentuh SaveManager (tidak ada snapshot save seperti level test).
#
# python3 tools/test_godot_map_data_parity.py            (freshness fixture)
# godot --headless --path godot res://tests/MapDataParityTest.tscn --quit-after 120
# Require "[MapDataParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/map_data.json"
const THEMES_JSON := "res://data/themes.json"
const Loader = preload("res://scripts/core/MapDBLoader.gd")
const ArenaMapScene := preload("res://scenes/map/ArenaMap.tscn")
const ArenaMapScript := preload("res://scenes/map/ArenaMap.gd")

## Backend yang dipaksa saat boot. MapDataGdextParityTest menimpanya jadi
## "gdext" supaya seluruh baterai di bawah masuk ke MysticMaps (C++).
var backend_override := "gdscript"

var _fx: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua pesan kegagalan dikumpulkan supaya tercetak di ekor log CI.
var _error_messages: Array[String] = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_boot.call_deferred()


func _boot() -> void:
	_load_fixture()
	Loader.force_backend(backend_override)
	# Satu baterai gagal TIDAK menghentikan baterai lain (pola
	# LevelDataParityTest: kegagalan A/B dulu menyembunyikan 2.057 cek).
	if _fx.is_empty():
		_fail("fixture tidak termuat — seluruh baterai dilewati")
	else:
		_test_backend_active()
		_test_signature_and_count()
		_test_tile_and_palettes()
		_test_theme_names()
		_test_catalog_rows()
		_test_theme_index_battery()
		_test_get_theme_battery()
		_test_build_theme_battery()
		_test_curve_battery()
		_test_lanes_river()
		_test_decor()
		_test_mutation_isolation()
		_test_derive_vs_themes_json()
		_test_arena_wiring()
	_finish()


func _load_fixture() -> void:
	if not FileAccess.file_exists(FIXTURE):
		_fail("fixture %s tidak ada — jalankan " % FIXTURE
			+ "tools/test_godot_map_data_parity.py --write-fixture")
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (parsed is Dictionary) or not (parsed as Dictionary).has("catalog"):
		_fail("fixture map_data.json rusak (tidak punya 'catalog')")
		return
	_fx = parsed


# ══════════════════════════════════════════════════════════
#  1-2. Backend + tanda tangan + jumlah tema
# ══════════════════════════════════════════════════════════

func _test_backend_active() -> void:
	_compare_str(Loader.backend_name(), backend_override, "backend_name()")
	print("[MapDataParityTest] backend=%s" % Loader.backend_name())


func _test_signature_and_count() -> void:
	var want_signature := str((_fx["source"] as Dictionary)["catalog_signature"])
	var got_signature := Loader.catalog_signature()
	if backend_override == "gdext":
		# Dihitung MysticMaps::catalog_signature() dari tabel C++:
		# "<jumlah>:<awal>-<akhir>:<total kunci>". Sama dengan fixture
		# berarti lib yang termuat membawa tabel generasi yang sama.
		_compare_str(got_signature, want_signature, "catalog_signature()")
	else:
		_compare_str(got_signature, "", "catalog_signature() backend GDScript")
	_expect(Loader.theme_count() == int((_fx["source"] as Dictionary)["theme_count"]),
		"theme_count() %d != %d" % [Loader.theme_count(),
			int((_fx["source"] as Dictionary)["theme_count"])])


# ══════════════════════════════════════════════════════════
#  3-4. tile_size + palet + nama tema
# ══════════════════════════════════════════════════════════

func _test_tile_and_palettes() -> void:
	_expect(Loader.tile_size() == int(_fx["tile_size"]),
		"tile_size() %d != %d" % [Loader.tile_size(), int(_fx["tile_size"])])
	var want_pal: Dictionary = _fx["palettes"]
	var got_pal: Dictionary = Loader.palettes()
	_expect(got_pal.size() == want_pal.size(),
		"palettes() %d != %d" % [got_pal.size(), want_pal.size()])
	for name in want_pal:
		var tag := "palettes()[%s]" % name
		if not got_pal.has(name):
			_fail("%s hilang" % tag)
			continue
		_expect_color(got_pal[name], want_pal[name], tag)


func _test_theme_names() -> void:
	var want: Array = _fx["theme_names"]
	var got: Array = Loader.theme_names()
	_expect(got == want, "theme_names() != THEMES (awal %s vs %s)"
		% [str(got.slice(0, 3)), str(want.slice(0, 3))])
	if got.size() == want.size():
		for i in range(want.size()):
			if str(got[i]) != str(want[i]):
				_fail("theme_names()[%d] %s != %s" % [i, str(got[i]), str(want[i])])
				break


# ══════════════════════════════════════════════════════════
#  5. Katalog: nilai + tipe + urutan kunci per tema
# ══════════════════════════════════════════════════════════

func _test_catalog_rows() -> void:
	for row in _fx["catalog"]:
		var values: Dictionary = row["values"]
		var types: Dictionary = row["types"]
		var tag := "tema %s" % str(row["name"])
		var lv = Loader.get_theme(str(row["name"]))
		if not (lv is Dictionary):
			_fail("%s: get_theme tidak mengembalikan Dictionary" % tag)
			continue
		var got: Dictionary = lv
		var got_keys: Array = []
		for key in got.keys():
			got_keys.append(str(key))
		var want_keys: Array = []
		for key in row["keys"]:
			want_keys.append(str(key))
		_expect(got_keys == want_keys, "%s urutan kunci %s != %s"
			% [tag, str(got_keys), str(want_keys)])
		for key in want_keys:
			var want_kind := str(types[key])
			var sub_tag := "%s.%s" % [tag, key]
			if not got.has(key):
				_fail("%s hilang" % sub_tag)
				continue
			_expect_theme_value(got[key], values[key], want_kind, sub_tag)


func _expect_theme_value(got, want, want_kind: String, tag: String) -> void:
	match want_kind:
		"str":
			_expect_kind(got, "str", tag)
			_expect(str(got) == str(want), "%s nilai %s != %s"
				% [tag, _canon(got), _canon(want)])
		"bool":
			_expect_kind(got, "bool", tag)
			_expect(bool(got) == bool(want), "%s nilai %s != %s"
				% [tag, _canon(got), _canon(want)])
		"int":
			_expect_kind(got, "int", tag)
			_expect(int(got) == int(want), "%s nilai %s != %s (int)"
				% [tag, _canon(got), _canon(want)])
		"nil":
			_expect(got == null, "%s harus null, dapat %s" % [tag, _canon(got)])
		"color3":
			_expect_kind(got, "Color", tag)
			_expect_color(got, want, tag)
			if got is Color:
				_expect((got as Color).a8 == 255, "%s alpha %d != 255"
					% [tag, (got as Color).a8])
		"color4":
			_expect_kind(got, "Color", tag)
			_expect_color4(got, want, tag)
		"color4?":
			if want == null:
				_expect(got == null, "%s harus null, dapat %s" % [tag, _canon(got)])
			else:
				_expect_kind(got, "Color", tag)
				_expect_color4(got, want, tag)
		"colorlist3":
			_expect_kind(got, "PackedColorArray", tag)
			if got is PackedColorArray:
				var arr: PackedColorArray = got
				_expect(arr.size() == 3, "%s panjang %d != 3" % [tag, arr.size()])
				if want is Array and (want as Array).size() == 3:
					for i in range(mini(arr.size(), 3)):
						_expect_color(arr[i], (want as Array)[i],
							"%s[%d]" % [tag, i])
		_:
			_fail("%s kind tak dikenal: %s" % [tag, want_kind])


func _expect_color(got, want, tag: String) -> void:
	if not (got is Color):
		_fail("%s bukan Color (%s)" % [tag, _kind_name(got)])
		return
	if not (want is Array) or (want as Array).size() < 3:
		_fail("%s fixture rusak: %s" % [tag, _canon(want)])
		return
	var c: Color = got
	var w: Array = want
	_expect(c.r8 == int(w[0]) and c.g8 == int(w[1]) and c.b8 == int(w[2]),
		"%s rgb (%d,%d,%d) != (%d,%d,%d)" % [tag, c.r8, c.g8, c.b8,
			int(w[0]), int(w[1]), int(w[2])])


func _expect_color4(got, want, tag: String) -> void:
	_expect_color(got, want, tag)
	if (got is Color) and (want is Array) and (want as Array).size() >= 4:
		_expect((got as Color).a8 == int((want as Array)[3]),
			"%s alpha %d != %d" % [tag, (got as Color).a8, int((want as Array)[3])])


# ══════════════════════════════════════════════════════════
#  6-8. theme_index / get_theme / build_theme
# ══════════════════════════════════════════════════════════

func _test_theme_index_battery() -> void:
	for case in _fx["theme_index_battery"]:
		var got := Loader.theme_index(str(case[0]))
		_expect(got == int(case[1]), "theme_index(%s) %d != %d"
			% [str(case[0]), got, int(case[1])])


func _test_get_theme_battery() -> void:
	for case in _fx["get_theme_battery"]:
		var got = Loader.get_theme(str(case[0]))
		var want = Loader.get_theme(str(case[1]))
		var tag := "get_theme(%s)" % str(case[0])
		if not (got is Dictionary):
			_fail("%s bukan Dictionary" % tag)
			continue
		_compare_str(_row_signature(got), _row_signature(want),
			"%s == get_theme(%s)" % [tag, str(case[1])])


func _test_build_theme_battery() -> void:
	for case in _fx["build_theme_battery"]:
		var got := Loader.build_theme(int(case[0]))
		var tag := "build_theme(%d)" % int(case[0])
		if str(case[1]) == "empty":
			_expect(got.is_empty(), "%s harus {}, dapat %s" % [tag, _canon(got)])
			continue
		var want = Loader.get_theme(str(case[1]))
		_compare_str(_row_signature(got), _row_signature(want),
			"%s == get_theme(%s)" % [tag, str(case[1])])


# ══════════════════════════════════════════════════════════
#  9. make_curved_path
# ══════════════════════════════════════════════════════════

func _test_curve_battery() -> void:
	for case in _fx["curve_battery"]:
		var wps := _fixture_v2s(case["waypoints"])
		var got := Loader.make_curved_path(wps, int(case["smoothness"]))
		_expect_v2s(got, case["points"],
			"make_curved_path(%s, %d)" % [str(case["name"]), int(case["smoothness"])])


# ══════════════════════════════════════════════════════════
#  10. generate_lanes / generate_river (2 ukuran)
# ══════════════════════════════════════════════════════════

func _test_lanes_river() -> void:
	for size_key in ["1280x720", "1025x769"]:
		var dims := str(size_key).split("x")
		var w := int(dims[0])
		var h := int(dims[1])
		var lanes := Loader.generate_lanes(w, h)
		var tag := "generate_lanes(%d,%d)" % [w, h]
		if not (lanes is Dictionary):
			_fail("%s bukan Dictionary" % tag)
			continue
		var keys: Array = (lanes as Dictionary).keys()
		_expect(keys == ["top", "mid", "bot"], "%s kunci %s != [top,mid,bot]"
			% [tag, str(keys)])
		var want_lanes: Dictionary = (_fx["lanes"] as Dictionary)[size_key]
		for lane in ["top", "mid", "bot"]:
			if not (lanes as Dictionary).has(lane):
				_fail("%s kehilangan %s" % [tag, lane])
				continue
			_expect_v2s((lanes as Dictionary)[lane], want_lanes[lane],
				"%s.%s" % [tag, lane])
		var river := Loader.generate_river(w, h)
		_expect_v2s(river, (_fx["river"] as Dictionary)[size_key],
			"generate_river(%d,%d)" % [w, h])


func _expect_v2s(got, want, tag: String) -> void:
	if not (got is PackedVector2Array):
		_fail("%s bukan PackedVector2Array (%s)" % [tag, _kind_name(got)])
		return
	if not (want is Array):
		_fail("%s fixture rusak" % tag)
		return
	var arr: PackedVector2Array = got
	var w: Array = want
	_expect(arr.size() == w.size(), "%s panjang %d != %d"
		% [tag, arr.size(), w.size()])
	for i in range(mini(arr.size(), w.size())):
		var wp: Array = w[i]
		var exp := Vector2(int(wp[0]), int(wp[1]))
		if arr[i] != exp:
			_fail("%s[%d] %s != %s" % [tag, i, str(arr[i]), str(exp)])
			return


# ══════════════════════════════════════════════════════════
#  11. generate_decorations (14 kategori x 2 varian toko)
# ══════════════════════════════════════════════════════════

func _test_decor() -> void:
	var dims: Array = _fx["decor_size"]
	var w := int(dims[0])
	var h := int(dims[1])
	var size_key := "%dx%d" % [w, h]
	var want_lanes: Dictionary = (_fx["lanes"] as Dictionary)[size_key]
	# lane_points dari FIXTURE (bukan loader) supaya baterai dekor terisolasi
	# dari baterai lane; urutan konkatenasi paritas _render.py: top+bot+mid.
	var lane_pts := PackedVector2Array()
	for lane in ["top", "bot", "mid"]:
		lane_pts.append_array(_fixture_v2s(want_lanes[lane]))
	var river_pts := _fixture_v2s((_fx["river"] as Dictionary)[size_key])
	var shops: Array = []
	for s in _fx["decor_shops"]:
		shops.append(Vector2(int(s[0]), int(s[1])))
	_run_decor_variant(w, h, lane_pts, river_pts, shops, "shops")
	_run_decor_variant(w, h, lane_pts, river_pts, [], "no_shops")


func _run_decor_variant(w: int, h: int, lane_pts: PackedVector2Array,
		river_pts: PackedVector2Array, shops: Array, variant: String) -> void:
	var got := Loader.generate_decorations(w, h, lane_pts, river_pts, shops)
	var tag := "generate_decorations(%s)" % variant
	if not (got is Dictionary):
		_fail("%s bukan Dictionary" % tag)
		return
	var want: Dictionary = (_fx["decor"] as Dictionary)[variant]
	var got_keys: Array = (got as Dictionary).keys()
	var want_keys: Array = want.keys()
	_expect(got_keys == want_keys, "%s urutan kategori %s != fixture" % [tag, str(got_keys)])
	for cat in want_keys:
		if not (got as Dictionary).has(cat):
			_fail("%s kehilangan %s" % [tag, cat])
			continue
		var got_list = (got as Dictionary)[cat]
		var want_list: Array = want[cat]
		var ctag := "%s.%s" % [tag, cat]
		if not (got_list is Array):
			_fail("%s bukan Array" % ctag)
			continue
		_expect((got_list as Array).size() == want_list.size(),
			"%s %d entri != %d" % [ctag, (got_list as Array).size(), want_list.size()])
		for i in range(mini((got_list as Array).size(), want_list.size())):
			_expect_decor_entry((got_list as Array)[i], want_list[i],
				"%s[%d]" % [ctag, i])


## Entri dekor: [x, y] + ekor bervariasi (int / String / Color / bool).
## Bentuk per kategori dikunci tools/test_maps_cpp_selftest.py (C++) dan
## E1/E2 oracle statis; di sini nilainya dibuktikan terhadap oracle Python.
func _expect_decor_entry(got, want, tag: String) -> void:
	if not (got is Array) or not (want is Array):
		_fail("%s bukan Array" % tag)
		return
	var g: Array = got
	var w: Array = want
	_expect(g.size() == w.size(), "%s panjang %d != %d" % [tag, g.size(), w.size()])
	for i in range(mini(g.size(), w.size())):
		var e = w[i]
		var v = g[i]
		var etag := "%s[%d]" % [tag, i]
		if e is bool:
			_expect_kind(v, "bool", etag)
			_expect(bool(v) == bool(e), "%s %s != %s" % [etag, str(v), str(e)])
		elif e is float or e is int:
			_expect_kind(v, "int", etag)
			_expect(int(v) == int(e), "%s %s != %s" % [etag, str(v), str(e)])
		elif e is String:
			_expect_kind(v, "str", etag)
			_expect(str(v) == str(e), "%s %s != %s" % [etag, str(v), str(e)])
		elif e is Array:
			_expect_kind(v, "Color", etag)
			_expect_color(v, e, etag)
		else:
			_fail("%s tipe fixture tak dikenal" % etag)


# ══════════════════════════════════════════════════════════
#  12. Isolasi mutasi (deviasi terdokumentasi)
# ══════════════════════════════════════════════════════════

func _test_mutation_isolation() -> void:
	var first := Loader.get_theme("forest")
	var before := _row_signature(first)
	(first as Dictionary)["radiant_grass_1"] = Color.MAGENTA
	(first as Dictionary)["name"] = "rusak"
	var plist = (first as Dictionary)["particle_colors_radiant"]
	if plist is PackedColorArray:
		(plist as PackedColorArray).append(Color.BLACK)
	var second := Loader.get_theme("forest")
	_compare_str(_row_signature(second), before,
		"get_theme() mengembalikan salinan segar (mutasi tidak bocor)")
	var third := Loader.all_themes()
	_expect((third as Dictionary).has("forest"),
		"all_themes() kehilangan forest setelah mutasi")


# ══════════════════════════════════════════════════════════
#  13. derive vs themes.json (independence check, 54 tema)
# ══════════════════════════════════════════════════════════

func _test_derive_vs_themes_json() -> void:
	if not FileAccess.file_exists(THEMES_JSON):
		_fail("%s tidak ada — jalankan tools/convert_to_godot.py" % THEMES_JSON)
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(THEMES_JSON))
	if not (parsed is Dictionary) or not ((parsed as Dictionary).get("themes") is Dictionary):
		_fail("%s rusak" % THEMES_JSON)
		return
	var themes: Dictionary = (parsed as Dictionary)["themes"]
	_expect(themes.size() == 54, "themes.json %d tema != 54" % themes.size())
	for tname in Loader.theme_names():
		if not themes.has(tname):
			_fail("themes.json kehilangan %s" % tname)
			continue
		var want: Dictionary = themes[tname]
		var got := Loader.theme_palette(str(tname))
		var tag := "theme_palette(%s)" % tname
		_expect(got.keys() == want.keys(), "%s urutan kunci != themes.json" % tag)
		for k in want:
			if not got.has(k):
				_fail("%s.%s hilang" % [tag, k])
				continue
			_expect_derived(got[k], want[k], "%s.%s" % [tag, k])


func _expect_derived(got, want, tag: String) -> void:
	if want is String and (want as String).begins_with("#"):
		# Warna hex converter vs Color loader — bandingkan via r8 (to_html),
		# bukan float32, supaya tidak bergantung pada skema parsing hex.
		if not (got is Color):
			_fail("%s bukan Color (%s)" % [tag, _kind_name(got)])
			return
		_expect("#" + (got as Color).to_html(false) == str(want).to_lower(),
			"%s %s != %s" % [tag, "#" + (got as Color).to_html(false), str(want)])
	elif want is bool:
		_expect_kind(got, "bool", tag)
		_expect(bool(got) == bool(want), "%s %s != %s" % [tag, str(got), str(want)])
	elif want is float or want is int:
		# fog_alpha/energy: float PERSIS (royal.energy = 1.169 adalah kasus
		# batas yang hanya lolos dengan pembulatan desimal eksak).
		_expect(float(got) == float(want), "%s %s != %s"
			% [tag, _canon(got), _canon(want)])
	elif want is String:
		_expect(str(got) == str(want), "%s %s != %s" % [tag, str(got), str(want)])
	else:
		_fail("%s tipe themes.json tak dikenal" % tag)


# ══════════════════════════════════════════════════════════
#  14. Wiring produksi (scene ArenaMap asli)
# ══════════════════════════════════════════════════════════

func _test_arena_wiring() -> void:
	var map = ArenaMapScene.instantiate()
	add_child(map) # _ready: loader -> themes + weather + apply_theme
	_expect((map.themes as Dictionary).size() == 54,
		"ArenaMap.themes %d != 54" % (map.themes as Dictionary).size())
	_expect((map.themes as Dictionary).keys() == Loader.theme_names(),
		"ArenaMap.themes bukan dari MapDBLoader")
	# Tema non-kurasi = derive loader apa adanya.
	_compare_str(_row_signature(map.palette("royal")),
		_row_signature(Loader.theme_palette("royal")),
		"ArenaMap.palette(royal) == loader.theme_palette")
	# 4 tema kurasi: modulate/light/energy dari const (GDScript art direction,
	# bukan pygame) — rewrite loader TIDAK BOLEH mengubahnya.
	var curated: Array = (ArenaMapScript.THEMES as Dictionary).keys()
	_expect(curated == ["forest", "desert", "ice", "abyss"],
		"const THEMES kurasi %s != [forest,desert,ice,abyss]" % str(curated))
	for tname in ["forest", "desert", "ice", "abyss"]:
		for k in ["modulate", "light", "energy"]:
			var got = (map.palette(tname) as Dictionary)[k]
			var want = ((ArenaMapScript.THEMES as Dictionary)[tname] as Dictionary)[k]
			_expect(str(got) == str(want),
				"ArenaMap kurasi %s.%s berubah: %s != %s"
				% [tname, k, _canon(got), _canon(want)])
	# Fallback + lane/river + toko produksi.
	_compare_str(_row_signature(map.palette("no-such-theme")),
		_row_signature(map.palette("forest")), "ArenaMap.palette fallback forest")
	_expect(map.get_lane_path("top").size() == 111, "ArenaMap top != 111 titik")
	_expect(map.get_lane_path("mid").size() == 65,
		"ArenaMap mid != 65 titik (smoothness 8)")
	_expect(map.get_lane_path("bot").size() == 101, "ArenaMap bot != 101 titik")
	_expect(map.get_river_path().size() == 61, "ArenaMap river != 61 titik")
	_expect(map.get_lane_path("mid") == Loader.generate_lanes(1280, 720)["mid"],
		"ArenaMap mid != loader (bukan jalur MapDBLoader)")
	_expect(map.radiant_shop_pos == Vector2(340, 540)
		and map.dire_shop_pos == Vector2(940, 180),
		"ArenaMap toko != (340,540)/(940,180) paritas _render.py")
	map.queue_free()


# ══════════════════════════════════════════════════════════
#  Helper decode + assertion
# ══════════════════════════════════════════════════════════

func _fixture_v2s(rows) -> PackedVector2Array:
	var out := PackedVector2Array()
	if rows is Array:
		for p in rows:
			out.append(Vector2(int(p[0]), int(p[1])))
	return out


func _kind_name(value) -> String:
	match typeof(value):
		TYPE_NIL:
			return "nil"
		TYPE_BOOL:
			return "bool"
		TYPE_INT:
			return "int"
		TYPE_FLOAT:
			return "float"
		TYPE_STRING, TYPE_STRING_NAME:
			return "str"
		TYPE_DICTIONARY:
			return "dict"
		TYPE_ARRAY:
			return "array"
		TYPE_COLOR:
			return "Color"
		TYPE_PACKED_COLOR_ARRAY:
			return "PackedColorArray"
		TYPE_PACKED_VECTOR2_ARRAY:
			return "PackedVector2Array"
	return "type_%d" % typeof(value)


func _expect_kind(got, want_kind: String, tag: String) -> void:
	var got_kind := _kind_name(got)
	_expect(got_kind == want_kind, "%s tipe %s != %s (nilai %s)"
		% [tag, got_kind, want_kind, _canon(got)])


func _compare_str(got: String, want: String, tag: String) -> void:
	_expect(got == want, "%s: \"%s\" != \"%s\"" % [tag, got, want])


## str(Dictionary) mencetak kunci sesuai urutan insert — perbandingan ini ikut
## mengunci urutan + isi sekaligus.
func _row_signature(row) -> String:
	return str(row)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _fail(message: String) -> void:
	_failures += 1
	var line := "[MapDataParityTest] FAIL: %s" % message
	_error_messages.append(line)
	push_error(line)


## Ringkasan satu baris supaya kegagalan terbaca di tail log CI.
func _canon(v: Variant) -> String:
	var text := str(v)
	if text.length() > 300:
		return text.substr(0, 300) + "…(%d char)" % text.length()
	return text


func _finish() -> void:
	if _done:
		return
	_done = true
	Loader.reload()
	Loader.reset_backend()
	if _failures == 0:
		print("[MapDataParityTest] PASS: map_components/_bundle.py ↔ Godot "
			+ "backend %s (%d checks)" % [backend_override, _checks])
		print("[MapDataParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		print("[MapDataParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
