# FASE 21 — MULTI-SLOT SAVE + MIGRASI LEGACY vs oracle SaveManager pygame
# ASLI (seksi fixture `save_slots`).
# python tools/test_godot_match_parity.py   (freshness)
# godot --headless --path godot res://tests/SaveSlotParityTest.tscn --quit-after 300
#
# Oracle pygame: `_system.SaveManager` SUNGGUHAN (menulis/membaca berkas
# slot di direktori terisolasi, jam ter-pin, TZ=UTC) + jalur draw ASLI
# `Menu._draw_slot_select`. Yang direplay di sini lewat JALUR PRODUKSI
# Godot — TIDAK ADA duplikasi rumus di harness:
#
#   * JALUR BERKAS : NUM_SLOTS, slot_path, get_empty_save (kunci + nilai
#                    default; timestamp "sekarang").
#   * MIGRASI      : 8 kasus — kapan migrasi jalan, metadata slot yang
#                    ditambahkan, rename legacy -> backup, slot 1 yang
#                    sudah ada TIDAK ditimpa, legacy korup -> gagal tanpa
#                    efek, kunci asing ikut tersalin, idempotensi.
#   * SAVE / LOAD  : 9 skenario — slot default vs eksplisit, metadata
#                    slot_created/slot_last_played, isolasi antar slot,
#                    load slot kosong/korup -> get_empty_save + backfill,
#                    nomor slot invalid diabaikan.
#   * HAPUS / INFO : delete_slot + get_slot_info/get_all_slot_info
#                    (slot korup -> null).
#   * FORMAT       : baterai format_playtime (17) dan format_last_played
#                    (15) — string relatif direproduksi dari OFFSET
#                    terhadap waktu nyata, cabang tanggal dari timestamp
#                    absolut (UTC).
#   * KARTU SLOT   : 5 layar x 3 kartu — nilai DATA kartu produksi
#                    (MainMenu._slot_card) dibandingkan dengan hasil
#                    render pygame.
#
# Beda disengaja yang dikunci eksplisit:
#   * Nama berkas legacy Godot = `mystic_save.json` (port Godot tidak
#     pernah punya `progress.json`), backup = `mystic_save_backup.json.old`
#     — pola rename-nya yang diuji, bukan namanya.
#   * Label UI kartu berbahasa Indonesia (KOSONG / LANJUTKAN / HAPUS SAVE)
#     dengan pemetaan eksplisit LABEL_MAP terhadap label pygame.
#   * Truncasi nama level (`ui_theme.fit_ellipsis`) adalah FITUR PIKSEL —
#     yang dibandingkan nama level MENTAHNYA.
#   * Cloud save (mobile/cloud_save.py) TIDAK diport — di luar scope.
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainMenuScript = preload("res://scenes/ui/MainMenu.gd")

## Label tombol pygame -> label Godot (beda bahasa yang disengaja, data
## keputusannya — tombol mana yang ada — tetap wajib identik).
const LABEL_MAP := {
	"CONTINUE": "LANJUTKAN",
	"START NEW GAME": "MULAI BARU",
	"DELETE SAVE": "HAPUS SAVE",
}

## Kunci khusus port Godot yang tidak ada di save pygame — tidak ikut
## dibandingkan saat memeriksa hasil load.
const GODOT_ONLY_KEYS := ["unlocked_heroes", "gold", "settings",
	"replay_reward_counts"]

## Kunci yang nilainya adalah "waktu sekarang" pada save baru.
const TIME_KEYS := ["slot_created", "slot_last_played"]

var _fx: Dictionary = {}
var _failures := 0
var _checks := 0
var _save_before: Dictionary = {}
var _slot_before: Dictionary = {}   # path user:// -> isi berkas (String)
var _current_slot_before := 1
var _now_pin := 0.0
var _menu = null


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _expect(cond: bool, tag: String) -> void:
	_checks += 1
	if not cond:
		_failures += 1
		printerr("[SaveSlotParityTest] FAIL: ", tag)


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	_current_slot_before = SaveManager.get_current_slot()
	for raw_path in _known_paths():
		var path := str(raw_path)
		if FileAccess.file_exists(path):
			_slot_before[path] = FileAccess.get_file_as_string(path)
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("save_slots"):
		_expect(false, "fixture save_slots belum ada — jalankan "
			+ "tools/test_godot_match_parity.py --write-fixture")
		_finish()
		return
	_fx = fixture["save_slots"]
	_now_pin = float(_fx["meta"]["now_pin"])
	_expect(int(_fx["meta"]["cloud_save"]) == 0,
		"scope FASE 21: oracle dibuat TANPA cloud save")

	_menu = MainMenuScript.new()
	add_child(_menu)

	_test_paths_and_empty_save()
	for case in _fx["migration_cases"]:
		_test_migration(case)
	for case in _fx["save_load_cases"]:
		_test_save_load(case)
	for case in _fx["delete_cases"]:
		_test_delete(case)
	for case in _fx["info_cases"]:
		_test_slot_info(case)
	_test_formats()
	for case in _fx["card_cases"]:
		_test_cards(case)

	_finish()


# ══════════════════════════════════════════════════════════
#  BERKAS & SAVE KOSONG
# ══════════════════════════════════════════════════════════

func _test_paths_and_empty_save() -> void:
	var meta := _fx["meta"] as Dictionary
	_expect(SaveManager.NUM_SLOTS == int(meta["num_slots"]),
		"NUM_SLOTS (dapat %d, mau %d)"
		% [SaveManager.NUM_SLOTS, int(meta["num_slots"])])
	var paths := _fx["paths"] as Dictionary
	for key in paths["slot_files"]:
		var want := str(paths["slot_files"][key])
		var got := SaveManager.slot_path(int(key)).get_file()
		_compare(got, want, "slot_path(%s)" % key)
	_expect(SaveManager.LEGACY_SAVE_FILE.get_file()
		!= str(paths["legacy_file"]),
		"nama legacy Godot memang beda (mystic_save.json) — tercatat")
	_expect(SaveManager.LEGACY_BACKUP_FILE.begins_with("user://"),
		"jalur backup legacy absolut user://")

	# get_empty_save: semua kunci pygame wajib ada dengan nilai default.
	var empty := SaveManager.get_empty_save()
	var want_empty := _fx["empty_save"] as Dictionary
	for key in want_empty:
		_expect(empty.has(key), "get_empty_save punya kunci %s" % key)
		if not empty.has(key):
			continue
		if key in TIME_KEYS and _is_pin(float(want_empty[key])):
			_expect_near_now(float(empty[key]), "empty_save %s" % key)
		else:
			_compare(_norm(empty[key]), _norm(want_empty[key]),
				"empty_save %s" % key)


# ══════════════════════════════════════════════════════════
#  MIGRASI LEGACY
# ══════════════════════════════════════════════════════════

func _test_migration(case: Dictionary) -> void:
	var tag := str(case["name"])
	_clear_all()
	SaveManager.set_current_slot(1)
	if case["legacy_before"] != null:
		if str(case["legacy_before"]) == "corrupt":
			_write_raw(SaveManager.LEGACY_SAVE_FILE, "{ rusak")
		else:
			_write_json(SaveManager.LEGACY_SAVE_FILE, case["legacy_before"])
	if case["pre_slot1"] != null:
		_write_json(SaveManager.slot_path(1), case["pre_slot1"])

	var got := false
	if case.has("first_call"):
		# Kasus idempoten: dua panggilan berturut-turut.
		var first := SaveManager.migrate_legacy_save()
		_compare(first, bool(case["first_call"]),
			"%s: panggilan pertama" % tag)
		got = SaveManager.migrate_legacy_save()
	else:
		got = SaveManager.migrate_legacy_save()
	_compare(got, bool(case["migrated"]), "%s: hasil migrasi" % tag)

	_compare(_files_after(), _norm_files(case["files_after"]),
		"%s: berkas setelah migrasi" % tag)
	_compare(FileAccess.file_exists(SaveManager.LEGACY_SAVE_FILE),
		bool(case["legacy_exists_after"]), "%s: legacy masih ada" % tag)
	_compare(FileAccess.file_exists(SaveManager.LEGACY_BACKUP_FILE),
		bool(case["backup_exists_after"]), "%s: backup dibuat" % tag)
	_compare_slot_file(1, case["slot1_after"], "%s: slot_1" % tag)
	_compare_slot_file_raw(SaveManager.LEGACY_BACKUP_FILE,
		case["backup_content"], "%s: isi backup" % tag)
	_compare_save_dict(SaveManager.load_slot(1), case["load_after"],
		"%s: load(1) setelah migrasi" % tag)


# ══════════════════════════════════════════════════════════
#  SAVE / LOAD PER-SLOT
# ══════════════════════════════════════════════════════════

func _test_save_load(case: Dictionary) -> void:
	var tag := str(case["name"])
	_clear_all()
	SaveManager.set_current_slot(1)
	for step in case["trace"]:
		var kind := str(step[0])
		if kind == "set_slot":
			SaveManager.set_current_slot(int(step[1]))
		elif kind == "current_slot":
			_compare(SaveManager.get_current_slot(), int(step[1]),
				"%s: slot aktif" % tag)
		elif kind == "save":
			# `save()` produksi menulis `SaveManager.data` ke slot aktif
			# (atau slot eksplisit) — payloadnya berasal dari oracle.
			_apply_save_step(step[1], step[2])
		elif kind == "write":
			_write_json(SaveManager.slot_path(int(step[1])), step[2])
		elif kind == "write_raw":
			_write_raw(SaveManager.slot_path(int(step[1])), str(step[2]))
		elif kind == "exists":
			_compare(SaveManager.slot_exists(int(step[1])), bool(step[2]),
				"%s: slot_exists(%s)" % [tag, str(step[1])])
		elif kind == "load":
			_compare_save_dict(SaveManager.load_slot(int(step[1])),
				step[2], "%s: load(%s)" % [tag, str(step[1])])
		elif kind == "delete":
			_compare(SaveManager.delete_slot(int(step[1])), bool(step[2]),
				"%s: delete(%s)" % [tag, str(step[1])])
		elif kind == "files":
			_compare(_files_after(), _norm_files(step[1]),
				"%s: daftar berkas" % tag)
		elif kind == "read":
			_compare_slot_file(int(step[1]), step[2],
				"%s: isi slot %s" % [tag, str(step[1])])
	_compare(_files_after(), _norm_files(case["files"]),
		"%s: daftar berkas akhir" % tag)


## Menjalankan satu langkah "save": `data` pygame di-set dulu ke save
## manager lalu dipanggil `save()` produksi (tanpa argumen = slot aktif).
func _apply_save_step(data, slot) -> void:
	SaveManager.data = _clone_pygame_save(data)
	if slot == null:
		SaveManager.save()
	else:
		SaveManager.save(int(slot))


# ══════════════════════════════════════════════════════════
#  HAPUS SLOT
# ══════════════════════════════════════════════════════════

func _test_delete(case: Dictionary) -> void:
	var tag := str(case["name"])
	_clear_all()
	SaveManager.set_current_slot(1)
	for key in case["pre"]:
		_write_json(SaveManager.slot_path(int(key)), case["pre"][key])
	var got := SaveManager.delete_slot(int(case["target"]))
	_compare(got, bool(case["result"]), "%s: hasil hapus" % tag)
	_compare(_files_after(), _norm_files(case["files_after"]),
		"%s: berkas setelah hapus" % tag)
	for key in case["exists_after"]:
		_compare(SaveManager.slot_exists(int(key)),
			bool(case["exists_after"][key]),
			"%s: slot_exists(%s)" % [tag, key])
	var info = SaveManager.get_slot_info(int(case["target"]))
	if case["info_after"] == null:
		_expect(info == null, "%s: info slot kosong -> null" % tag)
	else:
		_compare_value(_norm(info), _norm(case["info_after"]),
			"%s: info slot" % tag)
	_compare_save_dict(SaveManager.load_slot(int(case["target"])),
		case["load_after"], "%s: load setelah hapus" % tag)


# ══════════════════════════════════════════════════════════
#  GET_SLOT_INFO / GET_ALL_SLOT_INFO
# ══════════════════════════════════════════════════════════

func _test_slot_info(case: Dictionary) -> void:
	var tag := str(case["name"])
	_clear_all()
	SaveManager.set_current_slot(1)
	if case["pre"] != null:
		for key in case["pre"]:
			_write_json(SaveManager.slot_path(int(key)), case["pre"][key])
	if case["raw"] != null:
		# Kasus slot korup: isi berkasnya memang bukan JSON valid.
		_write_raw(SaveManager.slot_path(int(case["query"])),
			str(case["raw"]))
	if str(case["query"]) == "all":
		var got: Array = SaveManager.get_all_slot_info()
		_compare(got.size(), (case["info"] as Array).size(),
			"%s: jumlah slot" % tag)
		if got.size() != (case["info"] as Array).size():
			return
		for i in range(got.size()):
			_compare_slot_info(got[i], (case["info"] as Array)[i],
				"%s: slot %d" % [tag, i + 1])
	else:
		_compare_slot_info(SaveManager.get_slot_info(int(case["query"])),
			case["info"], "%s: info" % tag)


func _compare_slot_info(got, want, tag: String) -> void:
	if want == null:
		_expect(got == null, "%s: null" % tag)
		return
	_expect(got is Dictionary, "%s: info berupa Dictionary" % tag)
	if not (got is Dictionary):
		return
	_compare_value(_norm(got), _norm(want), tag)


# ══════════════════════════════════════════════════════════
#  BATERAI FORMAT
# ══════════════════════════════════════════════════════════

func _test_formats() -> void:
	for row in _fx["format_playtime_battery"]:
		_compare(SaveManager.format_playtime(float(row[0])), str(row[1]),
			"format_playtime(%s)" % str(row[0]))
	for row in _fx["format_last_played_battery"]:
		var row_d := row as Dictionary
		var want := str(row_d["text"])
		if row_d["offset"] == null:
			# Cabang tanggal / timestamp 0: tidak bergantung waktu kini.
			_compare(SaveManager.format_last_played(
				float(row_d["timestamp"])), want,
				"format_last_played(%s)" % str(row_d["timestamp"]))
		else:
			# Cabang relatif: direproduksi dari OFFSET terhadap now.
			var ts := Time.get_unix_time_from_system() \
				- float(row_d["offset"])
			_compare(SaveManager.format_last_played(ts), want,
				"format_last_played(now-%s)" % str(row_d["offset"]))


# ══════════════════════════════════════════════════════════
#  KARTU SLOT (jalur produksi MainMenu._slot_card)
# ══════════════════════════════════════════════════════════

func _test_cards(case: Dictionary) -> void:
	var tag := str(case["name"])
	_clear_all()
	SaveManager.set_current_slot(1)
	for card in case["cards"]:
		var cd := card as Dictionary
		var slot_num := int(cd["slot_num"])
		if cd["info"] == null:
			continue
		var payload := (cd["info"] as Dictionary).duplicate(true)
		var expect := cd["expect"] as Dictionary
		# String relatif dihitung dari now yang NYATA; cabang tanggal
		# memakai timestamp absolut dari fixture (lihat oracle).
		if not bool(expect.get("last_played_absolute", false)):
			payload["slot_last_played"] = Time.get_unix_time_from_system() \
				- float(expect["last_played_offset"])
		_write_json(SaveManager.slot_path(slot_num), payload)

	_menu._slot_delete_confirm = -1
	_menu._show(_menu.State.SLOT_SELECT)
	for card in case["cards"]:
		var cd2 := card as Dictionary
		var num := int(cd2["slot_num"])
		var expect := cd2["expect"] as Dictionary
		var node := _find_slot_card(num)
		_expect(node != null, "%s: kartu slot %d ada" % [tag, num])
		if node == null:
			continue
		_compare(bool(node.get_meta("is_empty")), bool(expect["is_empty"]),
			"%s/%d: is_empty" % [tag, num])
		_compare(int(node.get_meta("highest_level")),
			int(expect["highest_level"]), "%s/%d: highest_level" % [tag, num])
		_compare(str(node.get_meta("level_name")),
			"" if expect["level_name"] == null else str(expect["level_name"]),
			"%s/%d: nama level" % [tag, num])
		if bool(expect["is_empty"]):
			_compare(str(node.get_meta("gold_text")), "0 Gold",
				"%s/%d: gold_text kosong" % [tag, num])
		else:
			_compare(str(node.get_meta("gold_text")),
				str(expect["gold_text"]), "%s/%d: gold_text" % [tag, num])
			_compare(int(node.get_meta("heroes")), int(expect["heroes"]),
				"%s/%d: jumlah hero" % [tag, num])
			_compare(int(node.get_meta("bosses")), int(expect["bosses"]),
				"%s/%d: jumlah boss" % [tag, num])
			_compare(str(node.get_meta("last_played")),
				str(expect["last_played"]),
				"%s/%d: terakhir dimainkan" % [tag, num])
		_compare(str(node.get_meta("play_label")),
			_mapped(str(expect["play_label"])),
			"%s/%d: label tombol main" % [tag, num])
		_compare(bool(node.get_meta("has_delete")), bool(expect["has_delete"]),
			"%s/%d: ada tombol hapus" % [tag, num])
		_compare(str(node.get_meta("delete_label")),
			_mapped(str(expect["delete_label"])),
			"%s/%d: label tombol hapus" % [tag, num])


func _find_slot_card(slot_num: int) -> Control:
	for node in _menu._root.find_children("*", "PanelContainer", true, false):
		if node.has_meta("slot_num") \
				and int(node.get_meta("slot_num")) == slot_num:
			return node
	return null


## Label pygame -> label Godot; "" (tidak ada tombol) tetap "".
func _mapped(pygame_label: String) -> String:
	if pygame_label == "" or pygame_label == "<null>":
		return ""
	if LABEL_MAP.has(pygame_label):
		return str(LABEL_MAP[pygame_label])
	return pygame_label


# ══════════════════════════════════════════════════════════
#  UTIL
# ══════════════════════════════════════════════════════════

func _known_paths() -> Array:
	var out: Array = []
	for i in range(1, SaveManager.NUM_SLOTS + 1):
		out.append(SaveManager.slot_path(i))
	out.append(SaveManager.LEGACY_SAVE_FILE)
	out.append(SaveManager.LEGACY_BACKUP_FILE)
	return out


func _clear_all() -> void:
	for raw_path in _known_paths():
		var path := str(raw_path)
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _write_json(path: String, payload) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		_expect(false, "gagal menulis " + path)
		return
	f.store_string(JSON.stringify(_clone_variant(payload), "\t"))
	f.close()


func _write_raw(path: String, text: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		_expect(false, "gagal menulis " + path)
		return
	f.store_string(text)
	f.close()


## Daftar nama berkas (tanpa direktori) yang ada di user:// — dibandingkan
## dengan daftar oracle setelah dinormalisasi pola nama legacy Godot.
func _files_after() -> Array:
	var out: Array = []
	for raw_path in _known_paths():
		var path := str(raw_path)
		if FileAccess.file_exists(path):
			out.append(_norm_name(path.get_file()))
	out.sort()
	return out


func _norm_files(raw) -> Array:
	var out: Array = []
	for name in raw:
		out.append(_norm_name(str(name)))
	out.sort()
	return out


## progress.json -> mystic_save.json, progress_backup.json.old ->
## mystic_save_backup.json.old (peta nama legacy, lihat kepala berkas).
func _norm_name(name: String) -> String:
	if name == "progress.json":
		return SaveManager.LEGACY_SAVE_FILE.get_file()
	if name == "progress_backup.json.old":
		return SaveManager.LEGACY_BACKUP_FILE.get_file()
	return name


func _compare_slot_file(slot_num: int, want, tag: String) -> void:
	var path := SaveManager.slot_path(slot_num)
	if want == null:
		_expect(not FileAccess.file_exists(path), "%s: berkas absen" % tag)
		return
	_expect(FileAccess.file_exists(path), "%s: berkas ada" % tag)
	if not FileAccess.file_exists(path):
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	_expect(parsed is Dictionary, "%s: isi JSON valid" % tag)
	if not (parsed is Dictionary):
		return
	var got := parsed as Dictionary
	var want_d := want as Dictionary
	for key in want_d:
		_expect(got.has(key), "%s: kunci %s" % [tag, key])
		if not got.has(key):
			continue
		if key in TIME_KEYS and _is_pin(float(want_d[key])):
			_expect_near_now(float(got[key]), "%s: %s" % [tag, key])
		else:
			_compare(_norm(got[key]), _norm(want_d[key]),
				"%s: %s" % [tag, key])


func _compare_slot_file_raw(path: String, want, tag: String) -> void:
	if want == null:
		_expect(not FileAccess.file_exists(path), "%s: berkas absen" % tag)
		return
	_expect(FileAccess.file_exists(path), "%s: berkas ada" % tag)
	if not FileAccess.file_exists(path):
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	_compare(_norm(parsed), _norm(want), tag)


## Bandingkan hasil load/save: nilai per kunci (bukan urutan kunci), dan
## timestamp "now" dibandingkan dengan toleransi.
func _compare_save_dict(got: Dictionary, want, tag: String) -> void:
	var want_d := want as Dictionary
	for key in want_d:
		_expect(got.has(key), "%s: kunci %s" % [tag, key])
		if not got.has(key):
			continue
		if key in TIME_KEYS and _is_pin(float(want_d[key])):
			_expect_near_now(float(got[key]), "%s: %s" % [tag, key])
		else:
			_compare(_norm(got[key]), _norm(want_d[key]),
				"%s: %s" % [tag, key])


func _is_pin(value: float) -> bool:
	return is_equal_approx(value, _now_pin)


func _expect_near_now(value: float, tag: String) -> void:
	var now := Time.get_unix_time_from_system()
	_expect(abs(value - now) <= 5.0,
		"%s (dapet %s, now %s)" % [tag, str(value), str(now)])


## JSON Godot mengembalikan semua angka sebagai float — normalisasi angka
## bulat ke int supaya bisa dibandingkan dengan angka Python.
func _norm(value):
	var t := typeof(value)
	if t == TYPE_FLOAT:
		if abs(value) < 9.0e15 and is_equal_approx(value, round(value)):
			return int(round(value))
		return value
	if t == TYPE_ARRAY:
		var out: Array = []
		for item in value:
			out.append(_norm(item))
		return out
	if t == TYPE_DICTIONARY:
		var out_d: Dictionary = {}
		for key in value:
			out_d[str(key)] = _norm(value[key])
		return out_d
	return value


func _compare_value(got, want, tag: String) -> void:
	if typeof(got) == TYPE_DICTIONARY and typeof(want) == TYPE_DICTIONARY:
		var keys_got: Array = []
		for key in (got as Dictionary):
			keys_got.append(str(key))
		var keys_want: Array = []
		for key in (want as Dictionary):
			keys_want.append(str(key))
		keys_got.sort()
		keys_want.sort()
		_compare(keys_got, keys_want, "%s: kunci" % tag)
		if keys_got != keys_want:
			return
		for key in keys_got:
			_compare_value((got as Dictionary)[key],
				(want as Dictionary)[key], "%s.%s" % [tag, key])
		return
	if typeof(got) == TYPE_ARRAY and typeof(want) == TYPE_ARRAY:
		_compare((got as Array).size(), (want as Array).size(),
			"%s: jumlah" % tag)
		if (got as Array).size() != (want as Array).size():
			return
		for i in range((got as Array).size()):
			_compare_value((got as Array)[i], (want as Array)[i],
				"%s[%d]" % [tag, i])
		return
	_compare(got, want, tag)


func _clone_variant(value):
	if typeof(value) == TYPE_DICTIONARY:
		return (value as Dictionary).duplicate(true)
	if typeof(value) == TYPE_ARRAY:
		return (value as Array).duplicate(true)
	return value


## `SaveManager.data` untuk satu langkah "save": isinya PERSIS payload
## oracle (bukan merge dengan data lama) supaya aturan pygame berlaku apa
## adanya — `slot_created` hanya "dibuat kalau belum ada", jadi sisa
## langkah sebelumnya tidak boleh terbawa. Kunci khusus Godot ditambahkan
## kalau absen agar sistem produksi tetap valid.
func _clone_pygame_save(value) -> Dictionary:
	var out: Dictionary = {}
	if typeof(value) == TYPE_DICTIONARY:
		var src: Dictionary = value
		for key in src:
			out[key] = _clone_variant(src[key])
	for key in GODOT_ONLY_KEYS:
		if not out.has(key) and SaveManager.data.has(key):
			out[key] = SaveManager.data[key]
	return out


func _compare(got, want, tag: String) -> void:
	_expect(str(got) == str(want),
		"%s (dapet %s, mau %s)" % [tag, str(got), str(want)])


func _finish() -> void:
	_menu.queue_free()
	SaveManager.data = _save_before
	SaveManager.set_current_slot(_current_slot_before)
	for raw_path in _known_paths():
		var path := str(raw_path)
		if _slot_before.has(path):
			var f := FileAccess.open(path, FileAccess.WRITE)
			if f != null:
				f.store_string(str(_slot_before[path]))
				f.close()
		elif FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	print("[SaveSlotParityTest] %s: %d cek, %d gagal"
		% ["PASS" if _failures == 0 else "FAIL", _checks, _failures])
	get_tree().quit(0 if _failures == 0 else 1)
