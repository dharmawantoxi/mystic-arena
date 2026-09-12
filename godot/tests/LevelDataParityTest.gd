# LevelDataParityTest — paritas levels/level_data.py -> Godot (backend GDScript).
#
# Oracle = fixture `level_data.json`, direkam dari levels/level_data.py ASLI oleh
# tools/test_godot_level_data_parity.py (tanpa pygame, tanpa Godot). Oracle itu
# JUGA membandingkan levels.json, FIELD_KINDS LevelDB.gd, dan tabel C++
# levels_processor.cpp dengan modul Python-nya, jadi drift data ketahuan bahkan
# sebelum engine diunduh; scene ini mengunci SEMANTIK RUNTIME-nya:
#
#   1. backend aktif == yang dipaksa (default "gdscript"; subclass GDExt "gdext")
#   2. katalog: 54 level x 17 field — NILAI, TIPE Variant (typeof), dan URUTAN
#      kunci (Dictionary Godot ordered; urutan mini_bosses level 3 memang
#      25, 10, 17 dan Main._roll_mini_boss_schedule bergantung pada urutan itu)
#   3. get_level_config: 22 input (level 0/55/-1/999, float bulat 3.0, float
#      non-bulat 3.5) -> Dictionary atau null (Python: None)
#   4. get_level_count == len(ALL_LEVELS)
#   5. is_level_unlocked: 20 kasus — unlock_after_level None (level 1 selalu
#      terbuka), syarat terpenuhi/belum, completed_levels berisi FLOAT (bentuk
#      save hasil JSON.parse_string), STRING, level tidak ada
#   6. py_contains (`x in list` Python): 15 kasus — int/float saling cocok,
#      string tidak, null tidak
#   7. get_next_level: 17 input — int DAN float (Python mengembalikan 4.0 untuk
#      input 3.0), level terakhir -> null
#   8. deviasi bool: Python True == 1, Godot tidak punya evaluator == bool/int;
#      yang dikunci di sini KEDUA backend Godot sepakat (False)
#   9. wiring produksi: BossDB.levels / BossDB.get_level / GameManager
#      level_count + next_level_number + is_level_unlocked (termasuk kasus
#      completed_levels FLOAT yang dulu membuat level terkunci lagi setelah
#      restart) dan SaveManager.is_level_completed
#
# Save TIDAK boleh berubah: data + berkas slot di-snapshot dan dipulihkan
# (pola LocalizationParityTest), dan CI menjalankan scene ini dengan
# XDG_DATA_HOME sementara.
#
# python3 tools/test_godot_level_data_parity.py            (freshness fixture)
# godot --headless --path godot res://tests/LevelDataParityTest.tscn --quit-after 120
# Require "[LevelDataParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/level_data.json"
const Loader = preload("res://scripts/core/LevelDBLoader.gd")

## Backend yang dipaksa saat boot. LevelDataGdextParityTest menimpanya jadi
## "gdext" supaya seluruh baterai di bawah masuk ke MysticLevels (C++).
var backend_override := "gdscript"

var _fx: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua pesan kegagalan dikumpulkan supaya tercetak di ekor log CI.
var _error_messages: Array[String] = []

# ── snapshot save (dipulihkan di _finish) ──
var _save_before: Dictionary = {}
var _slot_path_before: String = ""
var _slot_text_before: String = ""
var _slot_existed_before: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_boot.call_deferred()


func _boot() -> void:
	_snapshot()
	_load_fixture()
	Loader.force_backend(backend_override)
	if _failures == 0:
		_test_backend_active()
		_test_signature_and_count()
		_test_all_levels()
		_test_catalog_rows()
		_test_get_level_config_battery()
		_test_is_level_unlocked_battery()
		_test_py_contains_battery()
		_test_deviation_agreement()
		_test_get_next_level_battery()
		_test_production_wiring()
	_finish()


# ══════════════════════════════════════════════════════════
#  Fixture + snapshot
# ══════════════════════════════════════════════════════════

func _load_fixture() -> void:
	if not FileAccess.file_exists(FIXTURE):
		_fail("fixture %s tidak ada — jalankan " % FIXTURE
			+ "tools/test_godot_level_data_parity.py --write-fixture")
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (parsed is Dictionary) or not (parsed as Dictionary).has("catalog"):
		_fail("fixture level_data.json rusak (tidak punya 'catalog')")
		return
	_fx = parsed


func _snapshot() -> void:
	_save_before = SaveManager.data.duplicate(true)
	_slot_path_before = SaveManager.slot_path(SaveManager.get_current_slot())
	_slot_existed_before = FileAccess.file_exists(_slot_path_before)
	if _slot_existed_before:
		_slot_text_before = FileAccess.get_file_as_string(_slot_path_before)


func _restore() -> void:
	SaveManager.data = _save_before
	if _slot_existed_before:
		var f := FileAccess.open(_slot_path_before, FileAccess.WRITE)
		if f != null:
			f.store_string(_slot_text_before)
			f.close()
	elif FileAccess.file_exists(_slot_path_before):
		DirAccess.remove_absolute(
			ProjectSettings.globalize_path(_slot_path_before))


# ══════════════════════════════════════════════════════════
#  1-2. Backend + tanda tangan katalog + jumlah level
# ══════════════════════════════════════════════════════════

func _test_backend_active() -> void:
	_compare_str(Loader.backend_name(), backend_override, "backend_name()")
	print("[LevelDataParityTest] backend=%s" % Loader.backend_name())


func _test_signature_and_count() -> void:
	var want_signature := str((_fx["source"] as Dictionary)["catalog_signature"])
	var got_signature := Loader.catalog_signature()
	if backend_override == "gdext":
		# Tanda tangan dihitung MysticLevels::catalog_signature() dari tabel
		# C++: "<jumlah>:<awal>-<akhir>:<total mini boss>". Sama dengan fixture
		# berarti lib yang termuat membawa tabel generasi yang sama.
		_compare_str(got_signature, want_signature, "catalog_signature()")
	else:
		_compare_str(got_signature, "", "catalog_signature() backend GDScript")
	_expect(Loader.get_level_count() == int(_fx["get_level_count"]),
		"get_level_count() %d != %d" % [Loader.get_level_count(),
			int(_fx["get_level_count"])])


# ══════════════════════════════════════════════════════════
#  3. ALL_LEVELS
# ══════════════════════════════════════════════════════════

func _test_all_levels() -> void:
	var catalog: Array = _fx["catalog"]
	var rows: Array = Loader.all_levels()
	_expect(rows.size() == catalog.size(),
		"all_levels() %d baris != %d" % [rows.size(), catalog.size()])
	for i in range(mini(rows.size(), catalog.size())):
		var want_number := int(((catalog[i] as Dictionary)["values"] as Dictionary)["level_number"])
		if not (rows[i] is Dictionary):
			_fail("all_levels()[%d] bukan Dictionary" % i)
			continue
		var got_number := int((rows[i] as Dictionary).get("level_number", -1))
		_expect(got_number == want_number,
			"all_levels()[%d].level_number %d != %d (urutan ALL_LEVELS)"
			% [i, got_number, want_number])
	# Cache loader: panggilan kedua harus menghasilkan katalog yang sama
	# (BossDB menyimpan Array ini; MainMenu/GameManager membacanya berulang).
	var again: Array = Loader.all_levels()
	_expect(again.size() == rows.size(), "all_levels() tidak stabil: %d lalu %d"
		% [rows.size(), again.size()])
	if again.size() == rows.size() and not rows.is_empty():
		_compare_str(_row_signature(again[0]), _row_signature(rows[0]),
			"all_levels()[0] panggilan kedua")


# ══════════════════════════════════════════════════════════
#  4. Katalog: nilai + tipe + urutan kunci per level
# ══════════════════════════════════════════════════════════

func _test_catalog_rows() -> void:
	var field_order: Array = _fx["field_order"]
	for row in _fx["catalog"]:
		var values: Dictionary = row["values"]
		var types: Dictionary = row["types"]
		var number := int(values["level_number"])
		var tag := "level %d" % number
		var lv = Loader.get_level_config(number)
		if not (lv is Dictionary):
			_fail("%s: get_level_config tidak mengembalikan Dictionary" % tag)
			continue
		var got: Dictionary = lv
		# Urutan kunci = urutan literal dict level_data.py (dikunci juga oleh
		# tools/test_godot_level_data_parity.py untuk levels.json + tabel C++).
		var got_keys: Array = []
		for key in got.keys():
			got_keys.append(str(key))
		var want_keys: Array = []
		for key in row["keys"]:
			want_keys.append(str(key))
		_expect(got_keys == want_keys, "%s urutan kunci %s != %s"
			% [tag, str(got_keys), str(want_keys)])
		_expect(got_keys == _as_str_array(field_order),
			"%s urutan kunci != field_order fixture" % tag)
		for key in want_keys:
			var want_kind := str(types[key])
			var sub_tag := "%s.%s" % [tag, key]
			if key == "mini_bosses":
				_compare_mini_bosses(got.get(key), row["mini_bosses"], sub_tag)
				continue
			if not got.has(key):
				_fail("%s hilang (Python menulis kuncinya walau None)" % sub_tag)
				continue
			_expect_kind(got[key], want_kind, sub_tag)
			_expect_value(got[key], values[key], want_kind, sub_tag)


func _compare_mini_bosses(got, want_pairs: Array, tag: String) -> void:
	if not (got is Dictionary):
		_fail("%s bukan Dictionary (%s)" % [tag, _kind_name(got)])
		return
	var mini: Dictionary = got
	var got_pairs: Array = []
	for wave in mini.keys():
		got_pairs.append([str(wave), str(mini[wave])])
	var want: Array = []
	for pair in want_pairs:
		want.append([str(pair[0]), str(pair[1])])
	_expect(got_pairs == want, "%s %s != %s (kunci STRING + urutan insert)"
		% [tag, str(got_pairs), str(want)])


# ══════════════════════════════════════════════════════════
#  5. get_level_config battery
# ══════════════════════════════════════════════════════════

func _test_get_level_config_battery() -> void:
	for case in _fx["get_level_config_battery"]:
		var probe = _dec(case[0])
		var want_kind := str(case[1])
		var got = Loader.get_level_config(probe)
		var tag := "get_level_config(%s)" % _probe_label(case[0])
		if want_kind == "nil":
			_expect(got == null, "%s harus null (Python None), dapat %s"
				% [tag, _canon(got)])
			continue
		if not (got is Dictionary):
			_fail("%s harus Dictionary, dapat %s" % [tag, _canon(got)])
			continue
		var got_number := int((got as Dictionary).get("level_number", -1))
		_expect(got_number == int(case[2]), "%s -> level %d != %d"
			% [tag, got_number, int(case[2])])


# ══════════════════════════════════════════════════════════
#  6. is_level_unlocked battery
# ══════════════════════════════════════════════════════════

func _test_is_level_unlocked_battery() -> void:
	for case in _fx["is_level_unlocked_battery"]:
		var level := int(case[0])
		var completed := _dec_list(case[1])
		var want := bool(case[2])
		var note := str(case[3]) if case.size() > 3 else ""
		var got := Loader.is_level_unlocked(level, completed)
		var tag := "is_level_unlocked(%d, %s)" % [level, str(case[1])]
		if got != want:
			_fail("%s -> %s, oracle Python %s%s"
				% [tag, str(got), str(want), "" if note.is_empty() else " (" + note + ")"])
		else:
			_checks += 1


# ══════════════════════════════════════════════════════════
#  7. py_contains (`x in list` Python) battery
# ══════════════════════════════════════════════════════════

func _test_py_contains_battery() -> void:
	for case in _fx["py_contains_battery"]:
		var haystack := _dec_list(case[0])
		var needle = _dec(case[1])
		var want := bool(case[2])
		var note := str(case[3]) if case.size() > 3 else ""
		var got := Loader.py_contains(haystack, needle)
		var tag := "py_contains(%s, %s)" % [str(case[0]), _probe_label(case[1])]
		if got != want:
			_fail("%s -> %s, oracle Python %s%s"
				% [tag, str(got), str(want), "" if note.is_empty() else " (" + note + ")"])
		else:
			_checks += 1


## Kasus yang Python dan Godot BEDA dengan sengaja (bool == int). Yang dikunci:
## kedua backend Godot SEPAKAT, dan hasilnya nilai yang terdokumentasi (false).
func _test_deviation_agreement() -> void:
	for case in _fx["deviation_battery"]:
		var haystack := _dec_list(case[0])
		var needle = _dec(case[1])
		var want := bool(case[2])
		var got := Loader.py_contains(haystack, needle)
		_expect(got == want, "py_contains(%s, %s) -> %s, deviasi terkunci %s"
			% [str(case[0]), _probe_label(case[1]), str(got), str(want)])


# ══════════════════════════════════════════════════════════
#  8. get_next_level battery
# ══════════════════════════════════════════════════════════

func _test_get_next_level_battery() -> void:
	for case in _fx["get_next_level_battery"]:
		var probe = _dec(case[0])
		var want_kind := str(case[1])
		var tag := "get_next_level(%s)" % _probe_label(case[0])
		var got = Loader.get_next_level(probe)
		if want_kind == "nil":
			_expect(got == null, "%s harus null (Python None), dapat %s"
				% [tag, _canon(got)])
			continue
		_expect_kind(got, want_kind, tag)
		_expect_value(got, case[2], want_kind, tag)


# ══════════════════════════════════════════════════════════
#  9. Wiring produksi
# ══════════════════════════════════════════════════════════

func _test_production_wiring() -> void:
	var count := int(_fx["get_level_count"])
	# BossDB memegang katalog dari loader (bukan parse levels.json sendiri).
	BossDB.load_levels()
	_expect(BossDB.levels.size() == count,
		"BossDB.levels %d != %d level" % [BossDB.levels.size(), count])
	for number in [1, 2, 27, 54]:
		var via_boss: Dictionary = BossDB.get_level(number)
		var via_loader = Loader.get_level_config(number)
		if via_loader is Dictionary:
			_compare_str(_row_signature(via_boss), _row_signature(via_loader),
				"BossDB.get_level(%d) == LevelDBLoader.get_level_config" % number)
	_expect(BossDB.get_level(0).is_empty(), "BossDB.get_level(0) harus {}")
	_expect(BossDB.get_level(count + 1).is_empty(),
		"BossDB.get_level(%d) harus {}" % (count + 1))
	# Jadwal mini boss (BossData.schedule_from_levels) tetap int-keyed.
	var schedule: Array = BossData.schedule_from_levels(BossDB.levels)
	_expect(schedule.size() == count,
		"schedule_from_levels %d != %d" % [schedule.size(), count])
	if schedule.size() == count:
		var first: Dictionary = schedule[0]
		var mini: Dictionary = first.get("mini_bosses", {})
		var waves: Array = mini.keys()
		_expect(not waves.is_empty() and typeof(waves[0]) == TYPE_INT,
			"schedule_from_levels kunci wave harus int, dapat %s"
			% _kind_name(waves[0] if not waves.is_empty() else null))

	# GameManager = tiga helper Python yang didelegasikan ke loader.
	_expect(GameManager.level_count() == count,
		"GameManager.level_count() %d != %d" % [GameManager.level_count(), count])
	_expect(GameManager.next_level_number(1) == 2, "next_level_number(1) != 2")
	_expect(GameManager.next_level_number(count - 1) == count,
		"next_level_number(%d) != %d" % [count - 1, count])
	_expect(GameManager.next_level_number(count) == 0,
		"next_level_number(%d) harus 0 (Python None)" % count)
	_expect(GameManager.next_level_number(count + 5) == 0,
		"next_level_number(%d) harus 0" % (count + 5))
	_expect(GameManager.next_level_number(0) == 1, "next_level_number(0) != 1")

	# Kunci level lewat save — termasuk bentuk FLOAT yang dihasilkan
	# JSON.parse_string (bug lama: Array.has() strict-tipe membuat level
	# tampak terkunci lagi setelah game dimuat ulang).
	var completed_before = SaveManager.data.get("completed_levels", [])
	SaveManager.data["completed_levels"] = []
	_expect(GameManager.is_level_unlocked(1),
		"level 1 harus selalu terbuka (unlock_after_level null)")
	_expect(not GameManager.is_level_unlocked(2),
		"level 2 harus terkunci saat completed_levels kosong")
	SaveManager.data["completed_levels"] = [1]
	_expect(GameManager.is_level_unlocked(2),
		"level 2 terbuka setelah level 1 tamat (int)")
	_expect(SaveManager.is_level_completed(1),
		"SaveManager.is_level_completed(1) dengan [1]")
	SaveManager.data["completed_levels"] = [1.0]
	_expect(GameManager.is_level_unlocked(2),
		"level 2 harus tetap terbuka dengan completed_levels [1.0] — save "
		+ "Godot hasil JSON.parse_string berisi float (Python 1 in [1.0] True)")
	_expect(SaveManager.is_level_completed(1),
		"SaveManager.is_level_completed(1) dengan [1.0] (bentuk save reload)")
	SaveManager.data["completed_levels"] = ["1"]
	_expect(not GameManager.is_level_unlocked(2),
		"string '1' tidak boleh membuka level 2 (Python '1' != 1)")
	SaveManager.data["completed_levels"] = _range_floats(count - 1)
	_expect(GameManager.is_level_unlocked(count),
		"level terakhir terbuka kalau %d level sebelumnya tamat (save float)"
		% (count - 1))
	SaveManager.data["completed_levels"] = completed_before


## [1.0, 2.0, ..., upto] — bentuk completed_levels setelah reload save.
func _range_floats(upto: int) -> Array:
	var out: Array = []
	for i in range(1, upto + 1):
		out.append(float(i))
	return out


# ══════════════════════════════════════════════════════════
#  Helper decode + assertion
# ══════════════════════════════════════════════════════════

## [kind, nilai] dari fixture -> Variant dengan tipe Python yang dimaksud.
## JSON Godot mengubah semua angka jadi float, jadi kind-nya dicatat oracle.
func _dec(pair) -> Variant:
	if not (pair is Array) or (pair as Array).size() < 2:
		_fail("entri baterai bukan [kind, nilai]: %s" % _canon(pair))
		return null
	var kind := str((pair as Array)[0])
	var value = (pair as Array)[1]
	match kind:
		"int":
			return int(value)
		"float":
			return float(value)
		"str":
			return str(value)
		"bool":
			return bool(value)
		"nil":
			return null
	_fail("kind tak dikenal di fixture: %s" % kind)
	return value


func _dec_list(rows) -> Array:
	var out: Array = []
	if rows is Array:
		for row in rows:
			out.append(_dec(row))
	return out


func _probe_label(pair) -> String:
	if pair is Array and (pair as Array).size() >= 2:
		return "%s %s" % [str((pair as Array)[0]), str((pair as Array)[1])]
	return str(pair)


func _as_str_array(rows: Array) -> Array:
	var out: Array = []
	for row in rows:
		out.append(str(row))
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
	return "type_%d" % typeof(value)


func _expect_kind(got, want_kind: String, tag: String) -> void:
	var got_kind := _kind_name(got)
	_expect(got_kind == want_kind, "%s tipe %s != %s (nilai %s)"
		% [tag, got_kind, want_kind, _canon(got)])


## Nilai dibandingkan menurut kind-nya: numerik lewat angka (fixture JSON
## mengirim float untuk int), string lewat teks, nil lewat null.
func _expect_value(got, want, want_kind: String, tag: String) -> void:
	match want_kind:
		"int":
			_expect(int(got) == int(want), "%s nilai %s != %s (int)"
				% [tag, _canon(got), _canon(want)])
		"float":
			_expect(float(got) == float(want), "%s nilai %s != %s (float)"
				% [tag, _canon(got), _canon(want)])
		"str":
			_expect(str(got) == str(want), "%s nilai %s != %s"
				% [tag, _canon(got), _canon(want)])
		"nil":
			_expect(got == null, "%s harus null, dapat %s" % [tag, _canon(got)])
		_:
			_expect(str(got) == str(want), "%s nilai %s != %s"
				% [tag, _canon(got), _canon(want)])


func _compare_str(got: String, want: String, tag: String) -> void:
	_expect(got == want, "%s: \"%s\" != \"%s\"" % [tag, got, want])


## Signature satu baris level: str(Dictionary) Godot mencetak kunci sesuai urutan
## insert, jadi perbandingan ini ikut mengunci urutan + isi sekaligus.
func _row_signature(row) -> String:
	if row is Dictionary:
		return str(row)
	return str(row)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _fail(message: String) -> void:
	_failures += 1
	var line := "[LevelDataParityTest] FAIL: %s" % message
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
	# Pulihkan state + berkas: harness tidak boleh meninggalkan jejak.
	_restore()
	Loader.reload()
	Loader.reset_backend()
	if _failures == 0:
		print("[LevelDataParityTest] PASS: levels/level_data.py ↔ Godot "
			+ "backend %s (%d checks)" % [backend_override, _checks])
		print("[LevelDataParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		print("[LevelDataParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
