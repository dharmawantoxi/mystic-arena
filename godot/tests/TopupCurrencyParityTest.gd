# TopupCurrencyParityTest — replay fixture mata uang top-up (Fase 33).
#
# Fixture ditulis oleh tools/test_godot_topup_currency_parity.py yang menghitung
# angkanya dengan `topup_currency.py` pygame ASLI (import nyata; `detect_currency`
# dijalankan dengan sumber locale di-stub, jadi badan fungsinya yang dipakai).
# Berkas ini hanya memutar ulang hasil itu pada produksi Godot:
#   1. tabel const `TopupCurrency` (IDR_PER_UNIT, CURRENCY_SYMBOLS, NO_DECIMAL,
#      REGION_CURRENCY, LANG_CURRENCY, DEFAULT_CURRENCY) — dibandingkan sebagai
#      DATA, plus jumlah kunci (tabel yang kehilangan satu mata uang tidak boleh
#      lolos);
#   2. `TopupCurrency.format_price` — 432 kasus (harga x mata uang), termasuk
#      "Rp 10.000" vs bug lama "Rp10.000", "₫16,129" (koma tetap koma),
#      tanda "-0.00" untuk nilai minus yang membulat ke nol, dan kapitalisasi
#      "idr"/"usd" (quirk lookup tanpa normalisasi);
#   3. `TopupCurrency.convert_idr` — nilai + MATA UANG FINAL (fallback
#      DEFAULT_CURRENCY, bukan flag ok);
#   4. `parse_locale_name` + `currency_for` — 32 nama locale (UTF-8/1252/@
#      modifier, "en-US" dengan tanda hubung, "C"/"C.UTF-8" ditolak, "  id_ID  "
#      tanpa strip, "ca_ES" case-sensitive), kedua jalur (currency_for dan
#      detect_from_locale_name) harus sepakat;
#   5. `HudLayout.round_half_even_scaled` — 50 kasus pembulatan ties-to-even
#      termasuk 2.5 -> 2 (engine `round()` menghasilkan 3 = FAIL oleh test ini);
#   6. invarian dokumentasi pygame `format_price(x, "IDR") == fmt_idr(x)`;
#   6b. tabel simbol — fallback "XXX " diuji di sini, bukan lewat
#       format_price (lihat komentar di TopupCurrency.format_price);
#   7. `TopupDialog` PRODUKSI: `_price_str` per mata uang (dialog sungguhan,
#     bukan duplikasi rumus) + baris riwayat dari `_topup_complete()` (cur +
#     price_cur 2 desimal) + `MYSTIC_FORCE_LOCALE` -> deteksi di `_ready`
#     (ID_ID -> IDR, en_US -> USD, C -> USD, persis cabang pygame).
#
# godot --headless --path godot res://tests/TopupCurrencyParityTest.tscn --quit-after 300
# Require "[TopupCurrencyParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/topup_currency.json"
const TopupDialogScript = preload("res://scenes/ui/TopupDialog.gd")
## Toleransi pembanding float: fixture membawa double CPython,Godot membaca
## JSON ke double yang sama, jadi sisanya nol — 1e-9 hanya penampung noise
## parser, bukan kelonggaran pembulatan (kasus ties dibandingkan EKSAK).
const EPS := 1e-9

var _fx: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done := false
var _messages: Array[String] = []
var _save_before: Dictionary = {}
var _dialog: TopupDialog = null


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	var text := FileAccess.get_file_as_string(FIXTURE)
	if text.is_empty():
		_fail("fixture belum ada — jalankan "
			+ "tools/test_godot_topup_currency_parity.py --write-fixture")
		_finish()
		return
	var parsed = JSON.parse_string(text)
	if not (parsed is Dictionary) or not (parsed as Dictionary).has("prices"):
		_fail("fixture rusak/tidak lengkap")
		_finish()
		return
	_fx = parsed
	_test_tables()
	_test_prices()
	_test_convert()
	_test_locale()
	_test_round()
	_test_idr_invariant()
	_test_symbols()
	_test_dialog()
	_finish()


# ══════════════════════════════════════════════════════════
#  1) tabel const
# ══════════════════════════════════════════════════════════

func _test_tables() -> void:
	var tables: Dictionary = _fx["tables"]
	_checks += 1
	if not tables.has("IDR_PER_UNIT"):
		_fail("fixture tanpa tabel — tulis ulang fixture")
		return
	_cmp_dict_float("IDR_PER_UNIT", TopupCurrency.IDR_PER_UNIT,
			tables["IDR_PER_UNIT"])
	_cmp_dict_str("CURRENCY_SYMBOLS", TopupCurrency.CURRENCY_SYMBOLS,
			tables["CURRENCY_SYMBOLS"])
	_cmp_dict_str("REGION_CURRENCY", TopupCurrency.REGION_CURRENCY,
			tables["REGION_CURRENCY"])
	_cmp_dict_str("LANG_CURRENCY", TopupCurrency.LANG_CURRENCY,
			tables["LANG_CURRENCY"])
	_checks += 1
	var fixture_no_decimal: Array = Array(tables["NO_DECIMAL"])
	var expected_no_decimal: Array = TopupCurrency.NO_DECIMAL.duplicate()
	fixture_no_decimal.sort()
	expected_no_decimal.sort()
	if fixture_no_decimal != expected_no_decimal:
		_fail("NO_DECIMAL beda: %s vs %s" % [TopupCurrency.NO_DECIMAL,
				tables["NO_DECIMAL"]])
	_checks += 1
	if TopupCurrency.DEFAULT_CURRENCY != str(tables["DEFAULT_CURRENCY"]):
		_fail("DEFAULT_CURRENCY %s != %s" % [TopupCurrency.DEFAULT_CURRENCY,
				tables["DEFAULT_CURRENCY"]])


func _cmp_dict_float(tag: String, got: Dictionary, want: Dictionary) -> void:
	_checks += 1
	if got.size() != want.size():
		_fail("%s jumlah kunci %d != %d" % [tag, got.size(), want.size()])
		return
	for k in want.keys():
		_checks += 1
		if not got.has(k):
			_fail("%s kehilangan %s" % [tag, k])
			continue
		if absf(float(got[k]) - float(want[k])) > EPS:
			_fail("%s[%s] %f != %f" % [tag, k, float(got[k]), float(want[k])])


func _cmp_dict_str(tag: String, got: Dictionary, want: Dictionary) -> void:
	_checks += 1
	if got.size() != want.size():
		_fail("%s jumlah kunci %d != %d" % [tag, got.size(), want.size()])
		return
	for k in want.keys():
		_checks += 1
		if not got.has(k):
			_fail("%s kehilangan %s" % [tag, k])
		elif str(got[k]) != str(want[k]):
			_fail("%s[%s] %s != %s" % [tag, k, str(got[k]), str(want[k])])


# ══════════════════════════════════════════════════════════
#  2-4) fungsi murni
# ══════════════════════════════════════════════════════════

func _test_prices() -> void:
	for case in _fx["prices"]:
		var inp: Array = case["in"]
		var got := TopupCurrency.format_price(float(inp[0]), str(inp[1]))
		_checks += 1
		if got != str(case["out"]):
			_fail("format_price(%s, \"%s\") = \"%s\", pygame \"%s\""
				% [inp[0], inp[1], got, case["out"]])


func _test_convert() -> void:
	for case in _fx["convert"]:
		var inp: Array = case["in"]
		var got: Array = TopupCurrency.convert_idr(float(inp[0]), str(inp[1]))
		_checks += 1
		if absf(float(got[0]) - float(case["val"])) > EPS:
			_fail("convert_idr(%s, \"%s\") nilai %f != %f"
				% [inp[0], inp[1], float(got[0]), float(case["val"])])
		_checks += 1
		if str(got[1]) != str(case["cur"]):
			_fail("convert_idr(%s, \"%s\") mata uang akhir \"%s\" != \"%s\""
				% [inp[0], inp[1], str(got[1]), case["cur"]])


func _test_locale() -> void:
	for case in _fx["locale"]:
		var name := str(case["in"])
		var pair: Array = TopupCurrency.parse_locale_name(name)
		# pygame memakai None, port ini "" (deviasi #5) — keduanya "kosong".
		var want_lang := "" if case["lang"] == null else str(case["lang"])
		var want_region := "" if case["region"] == null else str(case["region"])
		_checks += 1
		if str(pair[0]) != want_lang or str(pair[1]) != want_region:
			_fail("parse_locale_name(\"%s\") = [%s, %s], pygame [%s, %s]"
				% [name, pair[0], pair[1], want_lang, want_region])
		_checks += 1
		var by_pair := TopupCurrency.currency_for(str(pair[0]), str(pair[1]))
		if by_pair != str(case["cur"]):
			_fail("currency_for(%s) = \"%s\", pygame \"%s\""
				% [name, by_pair, case["cur"]])
		_checks += 1
		var by_name := TopupCurrency.detect_from_locale_name(name)
		if by_name != str(case["cur"]):
			_fail("detect_from_locale_name(\"%s\") = \"%s\", pygame \"%s\""
				% [name, by_name, case["cur"]])


func _test_round() -> void:
	for case in _fx["round"]:
		var got := HudLayout.round_half_even_scaled(float(case["v"]),
				int(case["d"]))
		_checks += 1
		if got != int(case["out"]):
			_fail("round_half_even_scaled(%s, %d) = %d, CPython %d"
				% [case["v"], int(case["d"]), got, int(case["out"])])


func _test_idr_invariant() -> void:
	for case in _fx["idr"]:
		var got := TopupCurrency.format_price(float(case["amount"]), "IDR")
		_checks += 1
		if got != str(case["fmt_idr"]):
			_fail("fmt_idr(%s): Godot \"%s\", pygame \"%s\""
				% [case["amount"], got, case["fmt_idr"]])


func _test_symbols() -> void:
	for case in _fx["symbols"]:
		var cur := str(case["cur"])
		var got := str(TopupCurrency.CURRENCY_SYMBOLS.get(cur, cur + " "))
		_checks += 1
		if got != str(case["symbol"]):
			_fail("simbol %s: \"%s\" != \"%s\"" % [cur, got, case["symbol"]])


# ══════════════════════════════════════════════════════════
#  5) dialog produksi
# ══════════════════════════════════════════════════════════

func _test_dialog() -> void:
	# Tipe eksplisit (bukan `var` bebas) supaya analyzer memeriksa nama
	# metode/properti dialog — test parity tidak boleh gagal senyap karena
	# salah ketik di jalur produksi.
	_dialog = TopupDialogScript.new()
	add_child(_dialog)
	var pkg: Dictionary = _dialog.PACKAGES[0]
	for case in _fx["history"]:
		_dialog.currency = str(case["currency_in"])
		# label harga yang dilihat pemain di kartu/pilih/bayar
		var want := str(case["price_fmt"])
		var got := _dialog._price_str(float(pkg["price"]))
		_checks += 1
		if got != want:
			_fail("TopupDialog._price_str(%s) dengan currency \"%s\" = "
					+ "\"%s\", pygame \"%s\"" % [pkg["price"],
							case["currency_in"], got, want])
		# baris riwayat: jalur produksi _topup_complete() (bukan rumus ulang)
		SaveManager.data["topup_history"] = []
		_dialog.phase = "select"
		_dialog.pkg_idx = 0
		_dialog.method_idx = 0
		_dialog._topup_complete()
		var hist: Array = SaveManager.data.get("topup_history", [])
		_checks += 1
		if hist.size() != 1:
			_fail("riwayat hasil _topup_complete() = %d baris (harus 1)"
				% hist.size())
			continue
		var row: Dictionary = hist[0]
		_checks += 1
		if str(row.get("cur", "")) != str(case["cur"]):
			_fail("riwayat[%s] cur \"%s\" != \"%s\"" % [case["currency_in"],
					row.get("cur", ""), case["cur"]])
		_checks += 1
		if absf(float(row.get("price_cur", -1.0)) - float(case["price_cur"])) \
				> EPS:
			_fail("riwayat[%s] price_cur %s != %s" % [case["currency_in"],
					row.get("price_cur", "?"), case["price_cur"]])
		_checks += 1
		if int(row.get("price", -1)) != int(case["price"]):
			_fail("riwayat[%s] price base IDR %s != %s (harga paket tidak "
					+ "boleh ikut terkonversi)" % [case["currency_in"],
							row.get("price", "?"), case["price"]])
	_test_dialog_detect_locale()


## Cabang deteksi lewat env (deviasi #3 port): MYSTIC_FORCE_LOCALE dibaca
## TopupCurrency.device_locale() -> sama seperti pygame membaca LANG/LC_ALL.
func _test_dialog_detect_locale() -> void:
	var want_by_locale := {}
	for case in _fx["locale"]:
		want_by_locale[str(case["in"])] = str(case["cur"])
	for name in ["id_ID", "en_US", "C", "th_TH"]:
		if not want_by_locale.has(name):
			_fail("fixture tidak memuat locale %s" % name)
			continue
		OS.set_environment("MYSTIC_FORCE_LOCALE", name)
		var fresh: TopupDialog = TopupDialogScript.new()
		add_child(fresh)
		_checks += 1
		if fresh.currency != str(want_by_locale[name]):
			_fail("MYSTIC_FORCE_LOCALE=%s -> currency \"%s\", pygame \"%s\""
				% [name, fresh.currency, want_by_locale[name]])
		fresh.free()
	OS.set_environment("MYSTIC_FORCE_LOCALE", "")


func _finish() -> void:
	if _done:
		return
	_done = true
	if _dialog != null and is_instance_valid(_dialog):
		remove_child(_dialog)
		_dialog.free()
	SaveManager.data = _save_before
	SaveManager.save()
	if _failures == 0:
		print(("[TopupCurrencyParityTest] PASS: %d cek "
				+ "tabel/format/locale/pembulatan/riwayat") % _checks)
		print("[TopupCurrencyParityTest] PASS")
	else:
		for msg in _messages:
			print(msg)
		push_error("[TopupCurrencyParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[TopupCurrencyParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)


func _fail(message: String) -> void:
	_failures += 1
	_messages.append("  FAIL " + message)
