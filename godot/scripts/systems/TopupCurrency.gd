# TopupCurrency.gd — port 1:1 dari `topup_currency.py` (root repo, 221 baris).
#
# Harga paket top-up disimpan dalam IDR (mata uang dasar) dan DITAMPILKAN
# dalam mata uang lokal pemain. Semua tabel, urutan fallback, dan string
# literal di bawah dipin oleh tools/test_godot_topup_currency_parity.py: kalau
# salah satu berubah di pygame, alat itu gagal lebih dulu; kalau berubah di
# sini, fixture-nya (godot/tests/fixtures/topup_currency.json — dihitung oleh
# modul pygame asli) yang gagal. Jadi tidak ada angka yang boleh "dikira".
#
# DEVIASI ENGINE YANG SENGAJA (jangan dianggap bug):
#  1. Tidak ada format `%` sama sekali untuk pembulatan uang. Python
#     `f"{val:,.2f}"` dan `int(round(val))` membulatkan NILAI BINER EKSAK
#     dengan ties-to-even; GDScript `%.2f` / `round()` tidak terverifikasi sama
#     (`round()` engine membulatkan .5 MENJAUHI nol, jadi 2.5 -> 3, bukan 2).
#     Semua pembulatan lewat HudLayout.round_half_even_scaled() yang membaca
#     bit IEEE-754 — triks yang sama sudah dipakai format_gold_rate().
#  2. `_device_locale()` pygame: (a) pyjnius -> Locale Java di Android,
#     (b) `locale.setlocale(LC_ALL, "")` lalu `setlocale(LC_CTYPE)` di PC,
#     (c) fallback env LC_ALL/LC_CTYPE/LANG. Godot tidak punya (a) dan (b):
#     sumbernya `DisplayServer.get_locale()` (Android: Java Locale; desktop:
#     env), LALU jalur (c) tetap ditiru persis — urutan, `.strip()`, dan
#     penolakan nilai berawalan "C". Beda bentuk: pygame (b) mengembalikan
#     hasil parse `setlocale` yang sudah berupa "lang_REGION.CODESET"; Godot
#     mengumpankan nama mentah ke parse_locale_name() (fungsi yang sama), jadi
#     "C"/"C.UTF-8" tetap ditolak.
#  3. `MYSTIC_FORCE_LOCALE` (env) dibaca PALING AWAL. Tidak ada padanannya di
#     pygame; ini cermin `MYSTIC_FORCE_TOUCH` yang sudah dipakai AppShell —
#     tanpa ini cabang deteksi tidak bisa diuji deterministik di CI headless.
#  4. `detect_currency()` pygame tanpa argumen. Di sini badannya dipecah jadi
#     `currency_for(lang, region)` + `detect_from_locale_name(name)` supaya
#     fixture bisa memutar ulang cabang yang sama tanpa env. `detect_currency()`
#     tetap ada dengan perilaku identik (baca device_locale -> currency_for).
#  5. None -> "": pygame memakai None untuk "tidak terdeteksi"; GDScript
#     memakai string kosong. Semua pembanding pygame hanya menguji
#     truthiness (`if region:` / `lang or None`), jadi "" ekuivalen.
class_name TopupCurrency
extends RefCounted

## 1 unit mata uang = X rupiah (kurs statis pendekatan, boleh di-update lewat
## tabelnya saja). Salinan persis topup_currency.py:21-42 — termasuk
## "VND": 0.62 (1 dong = 0,62 rupiah, jadi 10.000 rupiah tampil "₫16,129")
## yang terlihat terbalik kalau dibaca cepat: bukan 16.129 dong per rupiah,
## satuannya memang paling kecil di tabel ini.
const IDR_PER_UNIT: Dictionary = {
	"IDR": 1.0,
	"USD": 16200,
	"EUR": 17800,
	"GBP": 20900,
	"SGD": 12200,
	"MYR": 3950,
	"THB": 480,
	"VND": 0.62,
	"PHP": 270,
	"JPY": 108,
	"KRW": 11.5,
	"CNY": 2240,
	"AUD": 10400,
	"CAD": 11900,
	"BRL": 3050,
	"INR": 190,
	"MXN": 830,
	"ZAR": 900,
	"AED": 4400,
	"SAR": 4300,
}

## Simbol display (prefix). topup_currency.py:45-66 — yang ber-spasi trailing
## ("Rp ", "RM ", "R " untuk rand Afrika Selatan, "AED ", "SAR ") bukan typo:
## spasinya bagian dari simbol, dan "$"/"S$"/"₩" memang tanpa spasi. CNY dan
## CAD berbagi "C$" — kesamaan itu ada di pygame, jadi ikut dipertahankan.
const CURRENCY_SYMBOLS: Dictionary = {
	"IDR": "Rp ",
	"USD": "$",
	"EUR": "€",
	"GBP": "£",
	"SGD": "S$",
	"MYR": "RM ",
	"THB": "฿",
	"VND": "₫",
	"PHP": "₱",
	"JPY": "¥",
	"KRW": "₩",
	"CNY": "C$",
	"AUD": "A$",
	"CAD": "C$",
	"BRL": "R$",
	"INR": "₹",
	"MXN": "MX$",
	"ZAR": "R ",
	"AED": "AED ",
	"SAR": "SAR ",
}

## Mata uang tanpa digit desimal (topup_currency.py:69).
const NO_DECIMAL: Array = ["IDR", "JPY", "KRW", "VND"]

## Region ISO 3166-1 alpha-2 -> mata uang (topup_currency.py:73-95, 29 kunci;
## hanya mata uang yang ada di tabel kurs).
const REGION_CURRENCY: Dictionary = {
	"ID": "IDR",
	"US": "USD",
	"CA": "CAD",
	"GB": "GBP",
	"DE": "EUR", "FR": "EUR", "NL": "EUR", "BE": "EUR", "IE": "EUR",
	"ES": "EUR", "IT": "EUR", "PT": "EUR", "AT": "EUR", "FI": "EUR",
	"SG": "SGD",
	"MY": "MYR",
	"TH": "THB",
	"VN": "VND",
	"PH": "PHP",
	"JP": "JPY",
	"KR": "KRW",
	"CN": "CNY",
	"AU": "AUD",
	"BR": "BRL",
	"IN": "INR",
	"MX": "MXN",
	"ZA": "ZAR",
	"AE": "AED",
	"SA": "SAR",
}

## Bahasa -> mata uang, dipakai HANYA kalau region tidak diketahui
## (topup_currency.py:100-109). "en"/"es"/"pt"/"fr" TIDAK ada di sini karena
## ambigu lintas region, jadi en_US terdeteksi lewat REGION (USD) sementara
## "en" saja jatuh ke DEFAULT_CURRENCY; de_DE -> EUR lewat region, "de" saja
## -> USD. Beda kecil inilah yang bikin daftar kasus di fixture tidak boleh
## cuma menguji bahasa Indonesia.
const LANG_CURRENCY: Dictionary = {
	"ja": "JPY",
	"ko": "KRW",
	"zh": "CNY",
	"th": "THB",
	"vi": "VND",
	"id": "IDR",
	"ms": "MYR",
	"hi": "INR",
}

## Fallback global saat region tidak bisa dideteksi (topup_currency.py:112).
const DEFAULT_CURRENCY := "USD"


## 'id_ID.UTF-8' / 'en-US' / 'ind_ID.1252' -> ["id", "ID"]
## (padanan `_parse_locale_name`, topup_currency.py:115-126).
## Kode berawalan "C" (locale POSIX netral) dianggap TIDAK terdeteksi supaya
## pengembang non-Indonesia tidak disalahartikan jadi IDR.
## Return [language, region]; "" = None-nya Python (deviasi #5).
static func parse_locale_name(locale_name: String) -> Array:
	if locale_name == "" or locale_name.begins_with("C"):
		return ["", ""] # case-SENSITIF seperti Python: "ca_ES" tetap sah
	var first := locale_name.split(".")[0].replace("-", "_")
	var parts: PackedStringArray = first.split("_")
	var language := parts[0].to_lower()
	var region := ""
	# Python: len(parts) > 1 and len(parts[1]) == 2 and parts[1].isalpha()
	# -> "C.UTF-8" tidak menghasilkan region "UTF"; sufiks locale selalu
	# ASCII jadi cek huruf ASCII di sini setara isalpha() untuk masukan sah.
	if parts.size() > 1 and parts[1].length() == 2 and _is_alpha(parts[1]):
		region = parts[1].to_upper()
	return [language, region]


## (language, region) dari perangkat (padanan `_device_locale`,
## topup_currency.py:129-176). Aman: tidak pernah gagal, ["", ""] bila tidak
## terdeteksi. Return [language, region] — lihat deviasi #2 di header.
static func device_locale() -> Array:
	# 0) MYSTIC_FORCE_LOCALE — tes headless/screenshot memaksa locale (deviasi #3).
	if OS.has_environment("MYSTIC_FORCE_LOCALE"):
		var forced := str(OS.get_environment("MYSTIC_FORCE_LOCALE")).strip_edges()
		if forced != "" and not forced.begins_with("C"):
			return parse_locale_name(forced)

	# 1) locale sistem: Android = Locale Java, desktop = SDL/XDG. Ini padanan
	#    jalur `locale.setlocale` pygame (deviasi #2): hasilnya "C"/kosong di
	#    lingkungan minim, dan itu memang ditolak pygame juga.
	var lang_code := str(DisplayServer.get_locale()).strip_edges()
	if lang_code != "" and not lang_code.begins_with("C"):
		return parse_locale_name(lang_code)

	# 2) fallback env, urutan PERSIS seperti topup_currency.py:169-172:
	#    LC_ALL > LC_CTYPE > LANG, pertama yang terisi DAN lolos penyaringan
	#    "C" menang (bukan "terakhir menimpa").
	for var_name in ["LC_ALL", "LC_CTYPE", "LANG"]:
		lang_code = ""
		if OS.has_environment(var_name):
			lang_code = str(OS.get_environment(var_name)).strip_edges()
		if lang_code != "" and not lang_code.begins_with("C"):
			return parse_locale_name(lang_code)
	return ["", ""]


## Mata uang pemain dari (lang, region) — badan `detect_currency`
## (topup_currency.py:187-195): region dulu, baru bahasa, lalu DEFAULT.
static func currency_for(lang: String, region: String) -> String:
	if region != "":
		var cur := str(REGION_CURRENCY.get(region.to_upper(), ""))
		if cur != "":
			return cur
	if lang != "":
		var hit := str(LANG_CURRENCY.get(lang.to_lower(), ""))
		if hit != "":
			return hit
	return DEFAULT_CURRENCY


## `detect_currency()` pygame: baca locale perangkat lalu currency_for.
static func detect_currency() -> String:
	var pair := device_locale()
	return currency_for(str(pair[0]), str(pair[1]))


## Padanan `detect_currency` tapi dari nama locale mentah (dipakai tes &
## tempat yang sudah punya nama locale, mis. MYSTIC_FORCE_LOCALE).
static func detect_from_locale_name(locale_name: String) -> String:
	var pair := parse_locale_name(locale_name)
	return currency_for(str(pair[0]), str(pair[1]))


## Konversi IDR -> mata uang (padanan `convert_idr`, topup_currency.py:198-205).
## Return [nilai, mata_uang_final]. TIDAK ada to_upper() di lookup: memang
## begitu di pygame, jadi "usd" (huruf kecil) TIDAK ketemu dan jatuh ke
## DEFAULT_CURRENCY — kebetulan tetap "USD", tapi "idr" huruf kecil hasilnya
## rupiah-ke-dolar. Quirk ini dipertahankan (lihat fixture: kasus "idr"/"usd").
static func convert_idr(amount_idr: float, currency: String) -> Array:
	var rate: Variant = IDR_PER_UNIT.get(currency, null)
	if rate == null or float(rate) == 0.0: # Python: `if not rate:`
		return [amount_idr / float(IDR_PER_UNIT[DEFAULT_CURRENCY]),
				DEFAULT_CURRENCY]
	return [amount_idr / float(rate), currency]


## Format harga ke mata uang pemain (padanan `format_price`,
## topup_currency.py:208-221). Contoh pygame:
##   10000 IDR -> "Rp 10.000" | "$0.62" (US) | "S$0.82" (SG) | "¥93" (JP)
##   "₩870" (KR) | "₫16,129" (VN, koma TETAP koma) | "XXX" tak dikenal -> "$0.62"
static func format_price(amount_idr: float, currency: String) -> String:
	var conv := convert_idr(amount_idr, currency)
	var val := float(conv[0])
	var cur := str(conv[1])
	var num := ""
	if NO_DECIMAL.has(cur):
		# f"{int(round(val)):,}" -> ties-to-even lewat round_half_even_scaled
		num = HudLayout.format_thousands(round_half_even_scaled(val, 0))
		if cur == "IDR":
			num = num.replace(",", ".")
	else:
		num = fmt_fixed_grouped(val, 2)
	# CURRENCY_SYMBOLS.get(cur, cur + " "): fallback "nama + spasi" hanya
	# kepakai kalau ada mata uang di tabel kurs tanpa simbol — saat ini tidak
	# ada (20 vs 20, dijaga oracle), dan nama tak dikenal sudah diganti
	# DEFAULT_CURRENCY di convert_idr ("XXX" -> "$0.62"). Barisnya tetap ada
	# supaya strukturnya 1:1 dengan pygame.
	var symbol := str(CURRENCY_SYMBOLS.get(cur, cur + " "))
	return symbol + num


## f"{val:,.{digits}f}" (grouping koma gaya AS + desimal tetap titik).
## Dibangun dari integer hasil pembulatan supaya tidak ada double-rounding.
static func fmt_fixed_grouped(value: float, digits: int) -> String:
	var scaled := round_half_even_scaled(value, digits)
	# Tanda dari DOUBLE aslinya, bukan dari hasil bulat: -0,004 tetap tampil
	# "-0.00" seperti f"{val:,.2f}" (jalur tanpa-desimal di format_price boleh
	# kehilangan tanda karena memang int(round())pygame menghasilkan 0).
	var neg := HudLayout.has_sign_bit(value)
	var abs_scaled := absi(scaled)
	var unit := 1
	for _i in digits:
		unit *= 10
	var whole := int(abs_scaled / unit)
	var frac := int(abs_scaled - whole * unit)
	var text := HudLayout.format_thousands(whole)
	if digits > 0:
		var frac_s := str(frac)
		while frac_s.length() < digits:
			frac_s = "0" + frac_s
		text += "." + frac_s
	return ("-" if neg else "") + text


## Pembulat ties-to-even -> integer terSkala 10^digits (lihat HudLayout).
static func round_half_even_scaled(value: float, digits: int) -> int:
	return HudLayout.round_half_even_scaled(value, digits)


static func _is_alpha(s: String) -> bool:
	if s.is_empty():
		return false
	for i in range(s.length()):
		var c := s.unicode_at(i)
		var ok := (c >= 65 and c <= 90) or (c >= 97 and c <= 122)
		if not ok:
			return false
	return true
