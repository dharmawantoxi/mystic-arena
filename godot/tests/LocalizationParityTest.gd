# LocalizationParityTest — paritas port localization.py ->
# godot/scripts/utils/Localization.gd + plumbing bahasa antarmuka.
#
# Oracle = fixture `localization.json`, dihasilkan dari localization.py ASLI
# oleh tools/test_godot_localization_parity.py (tanpa pygame, tanpa Godot —
# oracle itu juga membandingkan tabel di Localization.gd baris demi baris
# dengan localization.py, jadi drift teks ketahuan bahkan tanpa engine).
#
# Yang dikunci di sini:
#   1. boot sync — bahasa aktif == bahasa tersimpan di save, GameManager
#      mengaca Localization (paritas GameSettings.__new__/_load yang
#      memanggil localization.set_language, _core.py:9116/9170).
#   2. tabel teks: 2 bahasa x 24 kunci, ISI + URUTAN kunci (urutan dipakai
#      diff manusia terhadap localization.py:15-74).
#   3. LANGUAGES (urutan cycler _core.py:7297-7303) + LANGUAGE_LABELS.
#   4. set_language: 7 masukan (id/en/invalid/""/"ID"/"en-US"/null) —
#      semuanya aman jatuh ke "id" (localization.py:80).
#   5. get_language_label: bahasa aktif (None Python == "" GDScript),
#      eksplisit, dan tak dikenal -> label Indonesia (localization.py:89).
#   6. tr_text: 48 kasus (setiap kunci x setiap bahasa dengan nilai contoh)
#      + 8 kasus tepi (kunci tak dikenal -> kunci mentah, nilai hilang ->
#      template mentah, nilai berlebih diabaikan) (localization.py:92-100).
#   7. placeholder tiap template == `{nama}` polos yang tercatat oracle —
#      kontrak subset yang diimplementasi _py_format.
#   8. _py_format / _py_str: semantik str.format + str() Python (escape
#      `{{`, kurung tunggal -> ValueError -> mentah, float bulat 3.0 ->
#      "3.0", bool -> "True", None -> "None").
#   9. plumbing: GameManager.set_language (valid -> Localization + save +
#      signal; invalid -> diabaikan, paritas _core.py:9272-9278),
#      SaveManager.get/set_setting_str, ItemDB.item_mechanics_localized
#      mengikuti bahasa aktif (paritas hero_items.py:1632), baris BAHASA di
#      layar PENGATURAN + cyclernya (paritas _core.py:6321-6329/7295-7303).
#
# Save TIDAK boleh berubah: data + berkas slot di-snapshot dan dipulihkan
# (pola SaveSlotParityTest), dan CI menjalankan scene ini dengan
# XDG_DATA_HOME sementara.
#
# godot --headless --path godot res://tests/LocalizationParityTest.tscn --quit-after 120
# Require "[LocalizationParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/localization.json"
const MainMenuScript = preload("res://scenes/ui/MainMenu.gd")

## Item wakil untuk cek ItemDB.item_mechanics_localized (id katalognya
## sudah dikunci HeroItemsParityTest).
const PROBE_ITEM := "moon_shard"

var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua pesan kegagalan dikumpulkan supaya tercetak di ekor log CI.
var _error_messages: Array[String] = []

var _fx: Dictionary = {}
var _menu = null
var _signal_log: Array = []

# ── snapshot (dipulihkan di _finish) ──
var _language_before: String = "id"
var _gm_language_before: String = "id"
var _save_before: Dictionary = {}
var _slot_path_before: String = ""
var _slot_text_before: String = ""
var _slot_existed_before: bool = false


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_snapshot()
	_load_fixture()
	if _failures == 0:
		_test_boot_sync()
		_test_table()
		_test_languages_and_labels()
		_test_set_language()
		_test_labels()
		_test_tr_battery()
		_test_edge_cases()
		_test_placeholders()
		_test_format_cases()
		_test_py_str_cases()
		_test_helpers()
		_test_settings_plumbing()
		_test_settings_screen_row()
	_finish()


# ══════════════════════════════════════════════════════════
#  PERSIAPAN
# ══════════════════════════════════════════════════════════

func _snapshot() -> void:
	_language_before = MysticLocalization.get_language()
	_gm_language_before = GameManager.language
	_save_before = SaveManager.data.duplicate(true)
	_slot_path_before = SaveManager.SAVE_PATH
	_slot_existed_before = FileAccess.file_exists(_slot_path_before)
	if _slot_existed_before:
		_slot_text_before = FileAccess.get_file_as_string(_slot_path_before)


func _load_fixture() -> void:
	var parsed: Variant = JSON.parse_string(
		FileAccess.get_file_as_string(FIXTURE))
	_expect(parsed is Dictionary,
		"fixture localization.json terbaca (jalankan tools/"
		+ "test_godot_localization_parity.py --write-fixture)")
	_fx = parsed if parsed is Dictionary else {}


func _typed(value: Variant, kind: String) -> Variant:
	## JSON Godot melebur tipe Python (angka -> float), jadi fixture menyimpan
	## tipe aslinya dan harness membangunnya kembali di sini.
	match kind:
		"int":
			return int(value)
		"float":
			return float(value)
		"bool":
			return bool(value)
		"null":
			return null
	return str(value)


func _values_from(encoded: Variant) -> Dictionary:
	var out := {}
	if not (encoded is Array):
		return out
	for entry in (encoded as Array):
		var row: Array = entry
		if row.size() < 3:
			continue
		out[str(row[0])] = _typed(row[2], str(row[1]))
	return out


# ══════════════════════════════════════════════════════════
#  1. BOOT SYNC
# ══════════════════════════════════════════════════════════

func _test_boot_sync() -> void:
	var default_lang := str(_fx.get("default_language", "id"))
	_expect(default_lang == MysticLocalization.DEFAULT_LANGUAGE,
		"DEFAULT_LANGUAGE == localization._LANGUAGE awal (%s)" % default_lang)
	# AppShell._apply_interface_language jalan saat boot autoload terakhir.
	# Nilai tersimpan yang tidak valid tetap jatuh ke bahasa bawaan
	# (localization.py:80), jadi ekspektasinya divalidasi lebih dulu —
	# harness tidak boleh gagal hanya karena save pengembang berisi nilai di
	# luar ("id", "en").
	var stored := SaveManager.get_setting_str("language", default_lang)
	var expected := stored if MysticLocalization.LANGUAGES.has(stored) \
		else default_lang
	_expect(MysticLocalization.get_language() == expected,
		"bahasa aktif == setting tersimpan (dapat %s, mau %s)"
		% [MysticLocalization.get_language(), expected])
	_expect(GameManager.language == MysticLocalization.get_language(),
		"GameManager.language mengaca Localization")
	_expect(MysticLocalization.LANGUAGES.has(
		MysticLocalization.get_language()), "bahasa aktif anggota LANGUAGES")


# ══════════════════════════════════════════════════════════
#  2-3. TABEL + BAHASA + LABEL
# ══════════════════════════════════════════════════════════

func _test_table() -> void:
	var want: Dictionary = _fx["text"]
	var got: Dictionary = MysticLocalization.text_table()
	_expect_deep(got, want, "tabel teks (id + en, semua kunci)")
	var order: Dictionary = _fx["key_order"]
	for lang in order:
		var entries: Dictionary = got.get(str(lang), {})
		_expect_deep(entries.keys(), order[lang],
			"urutan kunci tabel %s" % str(lang))


func _test_languages_and_labels() -> void:
	_expect_deep(MysticLocalization.languages(), _fx["languages"],
		"LANGUAGES (urutan dipakai cycler bahasa pygame)")
	_expect_deep(MysticLocalization.language_labels(), _fx["labels"],
		"LANGUAGE_LABELS")


# ══════════════════════════════════════════════════════════
#  4-5. set_language + get_language_label
# ══════════════════════════════════════════════════════════

func _test_set_language() -> void:
	for c in (_fx["set_language_cases"] as Array):
		var raw: Variant = c["in"]
		# `None` Python == `""` GDScript: keduanya di luar LANGUAGES, jadi
		# hasilnya sama (jatuh ke "id"). Signature Godot memang String.
		var arg := "" if raw == null else str(raw)
		var got := MysticLocalization.set_language(arg)
		_expect(got == str(c["out"]),
			"set_language(%s) -> %s (dapat %s)" % [arg, str(c["out"]), got])
		_expect(MysticLocalization.get_language() == str(c["active"]),
			"get_language() setelah set_language(%s) -> %s (dapat %s)"
			% [arg, str(c["active"]), MysticLocalization.get_language()])


func _test_labels() -> void:
	for c in (_fx["label_cases"] as Array):
		MysticLocalization.set_language(str(c["active"]))
		var raw: Variant = c["lang"]
		var got: String
		if raw == null:
			# `get_language_label()` tanpa argumen == `None` Python.
			got = MysticLocalization.get_language_label()
		else:
			got = MysticLocalization.get_language_label(str(raw))
		_expect(got == str(c["out"]),
			"get_language_label(%s) aktif=%s -> %s (dapat %s)"
			% [str(raw), str(c["active"]), str(c["out"]), got])


# ══════════════════════════════════════════════════════════
#  6. tr_text: baterai kunci + kasus tepi
# ══════════════════════════════════════════════════════════

func _test_tr_battery() -> void:
	for c in (_fx["tr_cases"] as Array):
		MysticLocalization.set_language(str(c["lang"]))
		var got := MysticLocalization.tr_text(str(c["key"]),
			_values_from(c["values"]))
		_expect(got == str(c["out"]),
			"tr[%s] %s -> %s (mau %s)"
			% [str(c["lang"]), str(c["key"]), got, str(c["out"])])


func _test_edge_cases() -> void:
	for section in ["edge_cases", "fallback_cases"]:
		for c in (_fx[section] as Array):
			MysticLocalization.set_language(str(c["lang"]))
			var got := MysticLocalization.tr_text(str(c["key"]),
				_values_from(c["values"]))
			_expect(got == str(c["out"]),
				"tr[%s] %s (%s) -> %s (mau %s)"
				% [str(c["lang"]), str(c["key"]), str(c.get("note", "")),
					got, str(c["out"])])


# ══════════════════════════════════════════════════════════
#  7. PLACEHOLDER
# ══════════════════════════════════════════════════════════

func _test_placeholders() -> void:
	var want: Dictionary = _fx["placeholders"]
	var rx := RegEx.create_from_string("\\{([^{}]*)\\}")
	var table: Dictionary = MysticLocalization.text_table()
	for lang in table:
		var entries: Dictionary = table[lang]
		for key in entries:
			var found: Array = []
			for m in rx.search_all(str(entries[key])):
				var field := m.get_string(1)
				if not found.has(field):
					found.append(field)
			_expect_deep(found, want.get(str(key), []),
				"placeholder %s.%s" % [str(lang), str(key)])


# ══════════════════════════════════════════════════════════
#  8. FORMAT + str() PYTHON
# ══════════════════════════════════════════════════════════

func _test_format_cases() -> void:
	for c in (_fx["format_cases"] as Array):
		var got := MysticLocalization._py_format(str(c["template"]),
			_values_from(c["values"]))
		_expect(got == str(c["out"]),
			"_py_format(%s) [%s] -> %s (mau %s)"
			% [str(c["template"]), str(c.get("note", "")), got,
				str(c["out"])])


func _test_py_str_cases() -> void:
	for c in (_fx["py_str_cases"] as Array):
		var got := MysticLocalization._py_str(_typed(c["in"], str(c["kind"])))
		_expect(got == str(c["out"]),
			"_py_str(%s:%s) -> %s (mau %s)"
			% [str(c["in"]), str(c["kind"]), got, str(c["out"])])


# ══════════════════════════════════════════════════════════
#  9a. HELPER + KONSUMEN
# ══════════════════════════════════════════════════════════

func _test_helpers() -> void:
	MysticLocalization.set_language("en")
	_expect(MysticLocalization.is_english(), "is_english() true saat en")
	MysticLocalization.set_language("id")
	_expect(not MysticLocalization.is_english(), "is_english() false saat id")
	_expect(MysticLocalization.has_text("language"), "has_text kunci dikenal")
	_expect(not MysticLocalization.has_text("kunci_tak_ada"),
		"has_text kunci tak dikenal")
	# ItemDB.item_mechanics_localized == bahasa aktif (hero_items.py:1632)
	MysticLocalization.set_language("id")
	_expect_deep(ItemDB.item_mechanics_localized(PROBE_ITEM),
		ItemDB.item_mechanics(PROBE_ITEM, false),
		"mekanik item %s mengikuti bahasa id" % PROBE_ITEM)
	MysticLocalization.set_language("en")
	_expect_deep(ItemDB.item_mechanics_localized(PROBE_ITEM),
		ItemDB.item_mechanics(PROBE_ITEM, true),
		"mekanik item %s mengikuti bahasa en" % PROBE_ITEM)
	MysticLocalization.set_language("id")


# ══════════════════════════════════════════════════════════
#  9b. PLUMBING SETTING (GameSettings.set_language pygame)
# ══════════════════════════════════════════════════════════

func _on_language_changed(code: String) -> void:
	_signal_log.append(code)


func _test_settings_plumbing() -> void:
	GameManager.language_changed.connect(_on_language_changed)
	MysticLocalization.set_language("id")
	GameManager.language = "id"

	GameManager.set_language("en")
	_expect(MysticLocalization.get_language() == "en",
		"set_language('en') menyinkron Localization")
	_expect(GameManager.language == "en", "GameManager.language -> en")
	_expect(SaveManager.get_setting_str("language", "id") == "en",
		"bahasa tersimpan di settings save")
	_expect_deep(_signal_log, ["en"], "signal language_changed(en)")

	# Paritas _core.py:9273 (`if language in ('id','en')`): nilai di luar
	# daftar DIABAIKAN — tidak disimpan, tidak diterapkan, tidak dipancarkan.
	GameManager.set_language("jp")
	_expect(MysticLocalization.get_language() == "en",
		"bahasa invalid tidak mengubah Localization")
	_expect(SaveManager.get_setting_str("language", "id") == "en",
		"bahasa invalid tidak disimpan")
	_expect_deep(_signal_log, ["en"], "bahasa invalid tidak memancarkan signal")

	GameManager.set_language("id")
	_expect_deep(_signal_log, ["en", "id"], "kembali ke id")

	# apply_language = jalur load (tanpa tulis save): nilai tak dikenal
	# jatuh ke "id" di dalam Localization (localization.py:80).
	GameManager.apply_language("jp")
	_expect(MysticLocalization.get_language() == "id",
		"apply_language('jp') -> id")
	_expect(GameManager.language == "id", "GameManager.language fallback id")
	GameManager.language_changed.disconnect(_on_language_changed)


# ══════════════════════════════════════════════════════════
#  9c. LAYAR PENGATURAN (baris BAHASA + cycler)
# ══════════════════════════════════════════════════════════

func _test_settings_screen_row() -> void:
	GameManager.apply_language("id")
	_menu = MainMenuScript.new()
	add_child(_menu)
	_menu._show(_menu.State.SETTINGS)
	_expect(_count_labels(_menu, "Bahasa") == 1,
		"layar SETTINGS punya label baris 'Bahasa' (tr('language'))")
	_expect(_count_labels(_menu, "Bahasa Indonesia") == 1,
		"layar SETTINGS menampilkan label bahasa aktif")

	# Baris dibangun dari bahasa aktif — label barisnya SENDIRI ikut
	# terlokalisasi (pygame: tr("language") = "Bahasa" / "Language").
	var row: HBoxContainer = _menu._language_row()
	_expect_deep(_row_label_texts(row), ["Bahasa", "Bahasa Indonesia"],
		"baris bahasa saat id")
	row.free()
	GameManager.apply_language("en")
	row = _menu._language_row()
	_expect_deep(_row_label_texts(row), ["Language", "English"],
		"baris bahasa saat en")
	row.free()

	# Cycler — paritas _core.py:7295-7303: urutan LANGUAGES + bungkus
	# modulo ke dua arah (Python: (0 - 1) % 2 == 1). set_language di
	# dalamnya yang menulis save; berkas slot dipulihkan di _finish.
	GameManager.apply_language("en")
	_menu._cycle_language(1)
	_expect(MysticLocalization.get_language() == "id",
		"cycler > dari en membungkus ke id")
	_expect(SaveManager.get_setting_str("language", "en") == "id",
		"cycler menyimpan bahasa hasil putaran")
	_menu._cycle_language(-1)
	_expect(MysticLocalization.get_language() == "en",
		"cycler < dari id membungkus ke en (modulo negatif Python)")
	GameManager.apply_language("id")


func _row_label_texts(row: Node) -> Array:
	var out: Array = []
	for child in row.get_children():
		if child is Label:
			out.append((child as Label).text)
	return out


func _count_labels(node: Node, text: String) -> int:
	var count := 0
	for child in node.get_children():
		if child is Label and (child as Label).text == text:
			count += 1
		count += _count_labels(child, text)
	return count


# ══════════════════════════════════════════════════════════
#  UTIL HARNESS (pola HeroItemsParityTest)
# ══════════════════════════════════════════════════════════

func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		var line := "[LocalizationParityTest] " + message
		_error_messages.append(line)
		_failures += 1
		push_error(line)


func _deep_eq(a: Variant, b: Variant) -> bool:
	if a == null and b == null:
		return true
	if a == null or b == null:
		return false
	if a is Array and b is Array:
		if (a as Array).size() != (b as Array).size():
			return false
		for i in range((a as Array).size()):
			if not _deep_eq(a[i], b[i]):
				return false
		return true
	if a is Dictionary and b is Dictionary:
		if (a as Dictionary).size() != (b as Dictionary).size():
			return false
		for k in (a as Dictionary):
			if not (b as Dictionary).has(k) \
					or not _deep_eq(a[k], (b as Dictionary)[k]):
				return false
		return true
	return a == b


func _expect_deep(a: Variant, b: Variant, message: String) -> void:
	_checks += 1
	if not _deep_eq(a, b):
		var line := "[LocalizationParityTest] %s\n    dapat: %s\n    mau  : %s" \
			% [message, _canon(a), _canon(b)]
		_error_messages.append(line)
		_failures += 1
		push_error(line)


## Ringkasan satu baris supaya kegagalan terbaca di tail log CI.
func _canon(v: Variant) -> String:
	var text := str(v)
	if text.length() > 400:
		return text.substr(0, 400) + "…(%d char)" % text.length()
	return text


func _finish() -> void:
	if _done:
		return
	_done = true
	# Pulihkan state + berkas: harness tidak boleh meninggalkan jejak.
	MysticLocalization.set_language(_language_before)
	GameManager.language = _gm_language_before
	SaveManager.data = _save_before
	if _slot_existed_before:
		var f := FileAccess.open(_slot_path_before, FileAccess.WRITE)
		if f != null:
			f.store_string(_slot_text_before)
			f.close()
	elif FileAccess.file_exists(_slot_path_before):
		DirAccess.remove_absolute(
			ProjectSettings.globalize_path(_slot_path_before))
	if _menu != null and is_instance_valid(_menu):
		_menu.queue_free()
	if _failures == 0:
		print("[LocalizationParityTest] PASS: localization.py ↔ Godot "
			+ "(%d checks)" % _checks)
	else:
		for msg in _error_messages:
			print(msg)
		print("[LocalizationParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
