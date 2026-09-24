#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Oracle paritas mata uang dialog top-up (Fase 33) — pygame = ground truth.

Gap #2 di docs/AUDIT_ULANG_DARI_AWAL.md: dialog top-up pygame menampilkan
harga dalam MATA UANG PENGUNA (`topup_currency.py` di root repo), sedangkan
Godot dulu hanya punya satu angka IDR yang diformat sendiri — dan string-nya
salah: "Rp10.000" tanpa spasi, padahal simbol pygame "Rp " (dengan spasi).
Tes ini menjaga `godot/scripts/systems/TopupCurrency.gd` +
`godot/scenes/ui/TopupDialog.gd` + `godot/scripts/utils/HudLayout.gd`
mengulang hasil modul pygame secara BIT-eksak, bukan perkiraan.

Dua lapis, keduanya wajib:
  1) PIN SUMBER (statis). Tabel kurs/simbol/region/bahasa, `NO_DECIMAL`,
     `DEFAULT_CURRENCY`, dan barikode implementasi yang menentukan hasil
     string (lookup TANPA normalisasi kapital, `if not rate:`,
     `f"{int(round(val)):,}"`, `num.replace(",", ".")` khusus IDR,
     `f"{val:,.2f}"`, `CURRENCY_SYMBOLS.get(cur, cur + " ")`, penolakan
     locale berawalan "C", urutan env LC_ALL > LC_CTYPE > LANG) harus ADA
     VERBATIM di sumbernya. Pin berupa NEEDLE string persis (bukan regex
     panjang) supaya perubahan kecil di sekitar pin tidak membuatnya lepas.
     Sisi Godot di-pin juga: tabel const, titik panggilan TopupCurrency di
     dialog, dan pembulat ties-even di HudLayout. Baris implementasi Godot
     TIDAK dibandingkan teksnya dengan Python (beda bahasa, memang begitu) —
     yang diikat hanyalah tabel, string literal, angka, urutan, dan perilaku.
  2) FIXTURE PERILAKU. (harga IDR, mata uang) -> string; (locale) ->
     (lang, region) -> mata uang; (IDR, cur) -> (nilai, mata uang final);
     kasus pembulatan ties-to-even; dan invarian "format_price(x,'IDR') ==
     fmt_idr(x)" — semuanya dihitung LANGSUNG oleh modul pygame yang
     diimport (detect_currency dijalankan dengan `_device_locale` di-stub,
     jadi badan aslinya yang dieksekusi, bukan reimplementasi di sini).
     `godot/tests/TopupCurrencyParityTest.tscn` menjalankan fungsi Godot atas
     input yang sama dan membandingkan byte-per-byte. Angka harapan fixture
     BUKAN source of truth: kalau kode pygame berubah, pin lebih dulu
     menjatuhkan tes ini dan fixture ditulis ulang sadar (`--write-fixture`).

Deterministik: hanya fungsi murni (tabel + argumen -> hasil). Tidak ada
random, waktu, state modul, atau statistik runtime yang ikut di-serialize —
dua kali `--write-fixture` wajib menghasilkan berkas identik (dicek di
bawah). Locale mesin TIDAK dibaca saat fixture ditulis: kasus kosong
mengirim "" sehingga kedua mesin jatuh ke DEFAULT_CURRENCY, dan nama locale
selalu lewat argumen/env yang di-set eksplisit.

TIDAK DIPORT (sengaja; lihat header TopupCurrency.gd untuk daftar lengkap):
jalur pyjnius `androidjnius` di `_device_locale` (Godot memakai
`DisplayServer.get_locale()`), `locale.setlocale(LC_ALL, "")` yang mengubah
locale proses (efek samping global, tidak ada padanannya yang perlu), dan
cloud save (`CloudSaveManager` + plugin Android) yang merupakan subsistem
terpisah dan bukan wewenang tes mata uang ini.

Cara jalan (dari root repo):
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \\
      python3 tools/test_godot_topup_currency_parity.py
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \\
      python3 tools/test_godot_topup_currency_parity.py --write-fixture
  XDG_DATA_HOME=$(mktemp -d) godot --headless --path godot \\
      res://tests/TopupCurrencyParityTest.tscn
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GODOT = os.path.join(ROOT, "godot")
SRC = {
    "topup_currency.py": os.path.join(ROOT, "topup_currency.py"),
    "_core.py": os.path.join(ROOT, "_core.py"),
    "TopupCurrency.gd": os.path.join(GODOT, "scripts", "systems", "TopupCurrency.gd"),
    "HudLayout.gd": os.path.join(GODOT, "scripts", "utils", "HudLayout.gd"),
    "TopupDialog.gd": os.path.join(GODOT, "scenes", "ui", "TopupDialog.gd"),
}
FIXTURE = os.path.join(GODOT, "tests", "fixtures", "topup_currency.json")
PY, CORE = "topup_currency.py", "_core.py"
GD, HUD, DLG = "TopupCurrency.gd", "HudLayout.gd", "TopupDialog.gd"

sys.path.insert(0, ROOT)

# ── tabel yang harus ada 1:1 di kedua mesin ──
IDR_PER_UNIT = {"IDR": 1.0, "USD": 16200, "EUR": 17800, "GBP": 20900,
                "SGD": 12200, "MYR": 3950, "THB": 480, "VND": 0.62,
                "PHP": 270, "JPY": 108, "KRW": 11.5, "CNY": 2240,
                "AUD": 10400, "CAD": 11900, "BRL": 3050, "INR": 190,
                "MXN": 830, "ZAR": 900, "AED": 4400, "SAR": 4300}
SYMBOLS = {"IDR": "Rp ", "USD": "$", "EUR": "\u20ac", "GBP": "\u00a3",
           "SGD": "S$", "MYR": "RM ", "THB": "\u0e3f", "VND": "\u20ab",
           "PHP": "\u20b1", "JPY": "\u00a5", "KRW": "\u20a9", "CNY": "C$",
           "AUD": "A$", "CAD": "C$", "BRL": "R$", "INR": "\u20b9",
           "MXN": "MX$", "ZAR": "R ", "AED": "AED ", "SAR": "SAR "}
REGIONS = {"ID": "IDR", "US": "USD", "CA": "CAD", "GB": "GBP", "DE": "EUR",
           "FR": "EUR", "NL": "EUR", "BE": "EUR", "IE": "EUR", "ES": "EUR",
           "IT": "EUR", "PT": "EUR", "AT": "EUR", "FI": "EUR", "SG": "SGD",
           "MY": "MYR", "TH": "THB", "VN": "VND", "PH": "PHP", "JP": "JPY",
           "KR": "KRW", "CN": "CNY", "AU": "AUD", "BR": "BRL", "IN": "INR",
           "MX": "MXN", "ZA": "ZAR", "AE": "AED", "SA": "SAR"}
LANGS = {"ja": "JPY", "ko": "KRW", "zh": "CNY", "th": "THB", "vi": "VND",
         "id": "IDR", "ms": "MYR", "hi": "INR"}


def _lit(v) -> str:
    """Tulisan literal angka persis seperti di sumber (1.0 vs 16200)."""
    return repr(v) if isinstance(v, float) else str(int(v))


# ── 1) pin sumber: (label, berkas, needle, jumlah kemunculan minimal, apa
#       yang dipertahankan + nomor baris pygame-nya) ──
PINS: list[tuple[str, str, str, int, str]] = [
    # tabel kurs (topup_currency.py:21-42) — satu pin per mata uang
    ("buka tabel kurs", PY, "IDR_PER_UNIT = {", 1,
     "kalau strukturnya berubah, pin per-mata-uang harus ditulis ulang, bukan "
     "dibiarkan lepas"),
    *[(f"kurs {c}", PY, f'"{c}": {_lit(v)},', 1,
       "IDR_PER_UNIT[%r] tetap %r (topup_currency.py:21-42; nilai di tabel "
       "Godot dibandingkan sebagai DATA lewat fixture, pin ini mengikat "
       "TULISANNya juga: 1.0 != 1, 16200 != 16200.0)" % (c, v))
      for c, v in IDR_PER_UNIT.items()],
    ("NO_DECIMAL", PY, 'NO_DECIMAL = ("IDR", "JPY", "KRW", "VND")', 1,
     "isi+urutan daftar tanpa-desimal (:69); menentukan int(round()) vs .2f"),
    # simbol (:45-66) — yang ber-spasi trailing paling rawan "dirapikan"
    ("simbol Rp+spasi", PY, '"IDR": "Rp ",', 1,
     "spasi setelah Rp BAGIAN dari simbol (:46). Ini sumber bug Godot lama "
     "(\"Rp10.000\"); format_price men concatenate tanpa pemisah (:221)"),
    ("simbol RM+spasi", PY, '"MYR": "RM ",', 1, "id. (:51)"),
    ("simbol R+spasi", PY, '"ZAR": "R ",', 1,
     "rand Afrika Selatan pakai R+spasi, BUKAN \"R$\" (itu Brazil) (:63)"),
    ("simbol AED+spasi", PY, '"AED": "AED ",', 1, "id. (:64)"),
    ("simbol SAR+spasi", PY, '"SAR": "SAR ",', 1, "id. (:65)"),
    ("simbol USD", PY, '"USD": "$",', 1, "tanpa spasi -> \"$0.62\" (:47)"),
    ("simbol SGD", PY, '"SGD": "S$",', 1, "-> \"S$0.82\" (:50)"),
    ("simbol CNY=CAD", PY, '"CNY": "C$",', 1,
     "CNY dan CAD berbagi \"C$\" — kembar ini ada di pygame, jangan \""
     "diperbaiki\" (:57, :59)"),
    ("simbol JPY", PY, '"JPY": "\u00a5",', 1, "-> \"\u00a593\" (:55)"),
    ("simbol KRW", PY, '"KRW": "\u20a9",', 1, "-> \"\u20a9870\" (:56)"),
    ("simbol VND", PY, '"VND": "\u20ab",', 1, "-> \"\u20ab16,129\" (:53)"),
    # region & bahasa (:73-95, :100-109)
    ("region ID", PY, '"ID": "IDR",', 1, "REGION_CURRENCY (:74)"),
    ("region baris rangkap 5", PY,
     '"DE": "EUR", "FR": "EUR", "NL": "EUR", "BE": "EUR", "IE": "EUR",', 1,
     "lima kunci dalam satu baris (:78); jangan dipecah lalu salah salin"),
    ("region SA", PY, '"SA": "SAR",', 1, "kunci terakhir tabel region (:94)"),
    ("bahasa id", PY, '"id": "IDR",', 1,
     "bahasa = \"id\", BUKAN \"in\" (kludge Java \"in\" tidak dipakai "
     "modul ini) (:106)"),
    ("bahasa hi", PY, '"hi": "INR",', 1, "baris terakhir LANG_CURRENCY (:108)"),
    ("default USD", PY, 'DEFAULT_CURRENCY = "USD"', 1,
     "jatuh-pilih bila region+bahasa tak dikenali (:112)"),
    # _parse_locale_name (:115-126)
    ("pl tolak C", PY, 'if not lang_code or lang_code.startswith("C"):', 1,
     "locale POSIX \"C\" = tidak terdeteksi, dan penolakan ini case-SENSITIF "
     "tanpa strip (:118) -> \"ca_ES\" sah, \"C.UTF-8\" tidak"),
    ("pl titik+dash", PY, 'first = lang_code.split(".")[0].replace("-", "_")',
     1, "modifier .UTF-8 dibuang lalu - dinormalisasi (\"en-US\" == "
     "\"en_US\") (:120)"),
    ("pl lower", PY, "language = parts[0].lower() or None", 1,
     "kosong -> None (:122)"),
    ("pl region 2 huruf", PY,
     "if len(parts) > 1 and len(parts[1]) == 2 and parts[1].isalpha():", 1,
     "region HANYA anak kunci \"_\" tepat 2 huruf alpha; ini yang membuat "
     "\"C.UTF-8\"/\"id_ID.1252\" tidak menghasilkan region ngawur (:124)"),
    ("pl return", PY, "return language, region", 1,
     "(lang, region) — bukan nama locale mentah (:126)"),
    # _device_locale (:129-176) — urutan pencarian, bukan isinya
    ("dl jnius", PY, "from jnius import autoclass", 1,
     "jalur Android ADA di pygame (tidak diport: lihat docstring alat ini) "
     "(:142)"),
    ("dl setlocale", PY, 'locale.setlocale(locale.LC_ALL, "")  # baca locale sistem',
     1, "pygame menanyakan locale libc ke proses; Godot tidak boleh meniru "
     "efek samping global ini (:157)"),
    ("dl setlocale ctype", PY, 'lang_code = locale.setlocale(locale.LC_CTYPE) or ""',
     1, "hasil pembacaan dibaca ulang lewat LC_CTYPE (:160)"),
    ("dl saring C", PY, 'if lang_code and not lang_code.startswith("C"):', 2,
     "penyaringan yang sama dipakai jalur setlocale dan jalur env, dua-duanya "
     "harus tetap ada (:163, :171)"),
    ("dl urutan env", PY, 'for var in ("LC_ALL", "LC_CTYPE", "LANG"):', 1,
     "urutan prioritas env: LC_ALL > LC_CTYPE > LANG, yang pertama terisi "
     "menang (:169)"),
    ("dl strip env", PY, 'lang_code = (os.environ.get(var) or "").strip()', 1,
     "env di-strip sebelum disaring; TIDAK ada strip di _parse_locale_name "
     "(:170)"),
    # detect_currency (:179-195)
    ("dc ambil locale", PY, "lang, region = _device_locale()", 1,
     "badannya membaca (lang, region) sekali (:183)"),
    ("dc region dulu", PY, "cur = REGION_CURRENCY.get(region.upper())", 1,
     "REGION menang atas bahasa, dan .upper() di sini (bukan di tabel "
     "lookup harga!) (:188)"),
    ("dc bahasa", PY, "cur = LANG_CURRENCY.get(lang.lower())", 1, ":192"),
    ("dc default", PY, "return DEFAULT_CURRENCY", 1,
     "daerah netral (mis. hanya \"de\") -> USD, BUKAN IDR (:195)"),
    # convert_idr (:198-205)
    ("ci lookup mentah", PY, "rate = IDR_PER_UNIT.get(currency)", 1,
     "TANPA .upper(): \"usd\"/\"idr\" huruf kecil tidak ketemu dan jatuh ke "
     "DEFAULT — quirk yang harus tetap begini (:201)"),
    ("ci not rate", PY, "if not rate:", 1,
     "0/None masuk jalur fallback, bukan dikali nol (:202)"),
    ("ci fallback", PY, "rate = IDR_PER_UNIT[DEFAULT_CURRENCY]", 1, ":204"),
    ("ci return", PY, "return amount_idr / rate, currency", 1,
     "(nilai, mata_uang_final) — bukan (nilai, ok); pemanggil yang memilih "
     "menyimpan `cur` aslinya (:205 vs _core.py:6108, 6117)"),
    # format_price (:208-221)
    ("fp convert", PY, "val, cur = convert_idr(amount_idr, currency)", 1,
     "satu-satunya sumber angka: TIDAK ada jalur `amount = ...` kedua "
     "(:214); kalau sebuah edit melewatkan IDR mentah, USD/SGD berhenti "
     "terkonversi"),
    ("fp cabang no-decimal", PY, "if cur in NO_DECIMAL:", 1, ":215"),
    ("fp int round", PY, 'num = f"{int(round(val)):,}"', 1,
     "tanpa desimal: pembulatan ties-to-even milik CPython (:216) — Godot "
     "harus lewat HudLayout.round_half_even_scaled, `round()` engine "
     "membulatkan .5 menjauhi nol dan mengubah \"\u00a593\" jadi \"\u00a594\" "
     "di angka yang tepat tie"),
    ("fp idr dots", PY, 'num = num.replace(",", ".")', 1,
     "HANYA IDR yang bertukar pemisah (:218) -> VND tetap koma "
     "(\"\u20ab16,129\")"),
    ("fp dua desimal", PY, 'num = f"{val:,.2f}"', 1,
     "grup koma + desimal titik untuk semua mata uang berdesimal (:220)"),
    ("fp simbol concat", PY,
     'return CURRENCY_SYMBOLS.get(cur, cur + " ") + num', 1,
     "nama tak dikenal -> \"XXX \" jadi simbolnya (:221); pemisah tambahan "
     "tidak ada, spasi datang dari tabel"),
    # konsumen pygame (_core.py) — titik yang dibaca dialog Godot
    ("core field", CORE, "self.topup_currency = None", 1,
     "awal sesi: belum terdeteksi (:3190)"),
    ("core price str", CORE,
     'return format_price(amount_idr, self.topup_currency or "IDR")', 1,
     "`or \"IDR\"`: kosong = tampilkan rupiah apa adanya (:5347)"),
    ("core lazy", CORE, "if self.topup_currency is None:", 1,
     "deteksi malas sekali per sesi di dalam draw (:5583)"),
    ("core detect", CORE, "self.topup_currency = detect_currency()", 1,
     ":5586"),
    ("core except usd", CORE, 'self.topup_currency = "USD"', 1,
     "kegagalan total -> USD, bukan crash (:5589)"),
    ("core hist cur", CORE, 'cur = self.topup_currency or "IDR"', 1,
     "riwayat mencatat mata uang yang dilihat pemain (:6107)"),
    ("core hist conv", CORE, 'price_cur, _ = convert_idr(pkg["price"], cur)',
     1, "nilai konversi disimpan TERPISAH dari `price` base IDR (:6108)"),
    ("core hist round", CORE, '"price_cur": round(price_cur, 2),', 1,
     "dibulatkan 2 desimal ties-even, bukan 0, bukan mentah (:6119)"),
    ("core redeem idr", CORE, '            "cur": "IDR",', 1,
     "riwayat REDEEM tetap IDR + price 0 (:6071)"),
    ("core fmt_idr", CORE, 'return f"Rp {int(amount):,}".replace(",", ".")',
     1, "format rupiah standar game (:3085) — invarian \"format_price(x,"
     "\"IDR\") == fmt_idr(x)\" di fixtures berasal dari sini"),
    ("core paket", CORE, '{"label": "PAKET 50K", "gold": 50000, "bonus": 0, "price": 10_000},',
     1, "harga dasar (IDR) yang diformat dialog: 10_000, BUKAN 10000.0/10e3 "
     "— dipakai fixture `history` (:3069)"),
    ("dlg paket", DLG, '{"label": "PAKET 50K", "gold": 50000, "bonus": 0, "price": 10000},',
     1, "satu-satunya paket Godot = satu-satunya paket pygame; kalau angkanya "
     "beda, semua string harga di bawah meaningless"),
    # Godot: tabel const harus literal yang sama
    ("gd kurs", GD, "const IDR_PER_UNIT: Dictionary = {", 1,
     "tabel Godot dibuka sebagai Dictionary literal satu baris per mata uang"),
    *[(f"gd kurs {c}", GD, f'"{c}": {_lit(v)},', 1,
       "salinan literal tabel pygame (angka ditulis sama: 1.0/16200/0.62)")
      for c, v in IDR_PER_UNIT.items()],
    *[(f"gd simbol {c}", GD, '"%s": "%s",' % (c, v), 1,
       "simbol Godot = simbol pygame, spasi trailing termasuk")
      for c, v in sorted(SYMBOLS.items()) if c in ("IDR", "MYR", "ZAR", "AED",
                                                   "SAR", "USD", "SGD")],
    ("gd NO_DECIMAL", GD, 'const NO_DECIMAL: Array = ["IDR", "JPY", "KRW", "VND"]',
     1, "harus 1:1 dengan pygame"),
    ("gd default", GD, 'const DEFAULT_CURRENCY := "USD"', 1, "id."),
    ("gd region ID", GD, '"ID": "IDR",', 1, "REGION_CURRENCY Godot (:74 pygame)"),
    ("gd region baris 5", GD,
     '"DE": "EUR", "FR": "EUR", "NL": "EUR", "BE": "EUR", "IE": "EUR",', 1,
     "baris rangkap lima ikut dipertahankan apa adanya"),
    ("gd bahasa id", GD, '"id": "IDR",', 1, "LANG_CURRENCY Godot"),
    # Godot: implementasi
    ("gd lookup mentah", GD, "var rate: Variant = IDR_PER_UNIT.get(currency, null)",
     1, "TANPA to_upper, sama seperti pygame"),
    ("gd not rate", GD, "if rate == null or float(rate) == 0.0:", 1,
     "padanan `if not rate:` (None ATAU nol) — urutan cek juga penting"),
    ("gd urutan env", GD, 'for var_name in ["LC_ALL", "LC_CTYPE", "LANG"]:', 1,
     "urutan prioritas env sama dengan pygame:169"),
    ("gd saring C", GD, 'if lang_code != "" and not lang_code.begins_with("C"):',
     2, "penyaringan yang sama di jalur sistem DAN jalur env (min. 2x)"),
    ("gd tolak C", GD, 'if locale_name == "" or locale_name.begins_with("C"):',
     1, "case-sensitive seperti Python: \"ca_ES\" tetap sah"),
    ("gd strip di parse", GD, "static func parse_locale_name(locale_name: String) -> Array:",
     1, "parse TIDAK men-strip ( pygame juga ) — kasus \"  id_ID  \" di "
     "fixture memastikan perilaku itu tetap sama"),
    ("gd no-decimal", GD, "if NO_DECIMAL.has(cur):", 1, "posisi cabang sama"),
    ("gd idr dots", GD, 'num = num.replace(",", ".")', 1,
     "hanya IDR; kalau ini hilang, USD/VND ikut bertukar pemisah"),
    ("gd simbol concat", GD, 'var symbol := str(CURRENCY_SYMBOLS.get(cur, cur + " "))',
     1, "fallback \"XXX \" tetap ada"),
    ("gd group helper", GD,
     "static func fmt_fixed_grouped(value: float, digits: int) -> String:", 1,
     "pemformatan desimal dibangun dari integer, bukan dari %f"),
    # Godot: dialog benar-benar memakainya (kalau salah satu hilang, dialog
    # kembali ke "Rp10.000" dan fixture tidak akan menangkap itu)
    ("dlg field", DLG, 'var currency: String = ""', 1,
     "padanan `Game.topup_currency` (_core.py:3190)"),
    ("dlg lazy", DLG, 'if currency == "":', 1,
     "deteksi sekali per sesi, seperti `is None` di _core.py:5583"),
    ("dlg resolve", DLG, "\t\tcurrency = TopupCurrency.detect_currency()", 1,
     "satu-satunya titik deteksi dialog"),
    ("dlg price", DLG, "return TopupCurrency.format_price(amount_idr,", 1,
     "`_price_str` delegasi (dulu memformat sendiri -> \"Rp10.000\")"),
    ("dlg fallback", DLG, '			currency if currency != "" else "IDR")', 1,
     "`or \"IDR\"` pygame dipertahankan: kosong = tampilkan rupiah"),
    ("dlg hist cur", DLG, 'var cur := currency if currency != "" else "IDR"',
     1, "_core.py:6107"),
    ("dlg hist conv", DLG,
     "var converted: Array = TopupCurrency.convert_idr(price_idr, cur)", 1,
     "_core.py:6108"),
    ("dlg hist round", DLG,
     "var price_cur := float(HudLayout.round_half_even_scaled(", 1,
     "round(price_cur, 2) _core.py:6119"),
    ("dlg redeem", DLG,
     '"bonus": 0, "price": 0, "cur": "IDR", "price_cur": 0,', 1,
     "redeem tetap IDR/0 seperti _core.py:6065-6072"),
    # Godot: pembulat bit-eksak
    ("hud helper", HUD,
     "static func round_half_even_scaled(value: float, digits: int) -> int:",
     1, "satu-satunya pembulat uang di proyek ini"),
    ("hud skala 5", HUD, "\t\td *= 5", 1,
     "10^digits dibangun lewat 5^digits di integer -> tidak ada "
     "double-rounding (triks yang sama dengan format_gold_rate)"),
    ("hud ties", HUD, "\t\t\t\tres = q0 if q0 % 2 == 0 else q0 + 1", 1,
     "tepat setengah -> genap (ties-to-even), BUKAN menjauhi nol"),
    ("hud strip", HUD, "static func format_thousands(value: int) -> String:",
     1, "pemgrouping yang dipakai bersama HUD; kalau perilakunya berubah, "
     "banyak tes lain (bukan cuma ini) yang harus ikut diperbarui"),
]

# Yang TIDAK boleh muncul di sisi Godot (perbedaan engine = kontrak).
FORBIDDEN: list[tuple[str, str, str, str]] = [
    ("setlocale", GD, r"setlocale",
     "Godot tidak mengubah locale proses (deviasi #2 di header port)"),
    ("jnius", GD, r"jnius|autoclass",
     "tidak ada jalur Java di Godot; locale dari DisplayServer.get_locale()"),
    ("percent", GD, r'%\.\d+f"|"\.[0-9]+f" %',
     "tanpa format % untuk uang (deviasi #1): hasilnya tidak terverifikasi "
     "sama dengan CPython"),
    ("round mentah", GD, r"round\([a-z_]+\)(?!\s*\/)",
     "tanpa round() float langsung untuk angka uang — lewat "
     "round_half_even_scaled (int(round()) pygame = ties-to-even)"),
    ("upper di konversi", GD, r"convert_idr\(.*\.to_upper|currency\.to_upper",
     "lookup kurs sengaja TIDAK menormalisasi kapital (quirk pygame:201)"),
]

# ── 2) kasus perilaku (dihitung modul pygame nyata; tanpa angka harapan di
#       berkas ini) ──
CURRENCIES = list(IDR_PER_UNIT) + ["XXX", "idr", "usd", ""]
LOCALES = ["id_ID", "id_ID.UTF-8", "id-id", "ID_ID", "in_ID", "en_US",
           "en_US.UTF-8", "en-US", "ms_MY", "th_TH", "vi_VN", "zh_CN",
           "ja_JP", "ko_KR", "fil_PH", "hi_IN", "en_SG", "de_DE", "fr_FR",
           "es_ES", "ar_EG", "xx_YY", "C", "C.UTF-8", "", "id", "de",
           "en_US@collation", "ca_ES", "id_ID.1252", "  id_ID  ", "en_GB"]
PRICES = [10000, 0, 1, 120000, 999, 999.999, 123456789, 28.75, 11.5, 13.5,
          2.5, 3.5, -12345, -0.5, 0.005, 0.015, 0.025, 1.005]
HISTORY_CURRENCIES = ["IDR", "USD", "SGD", "JPY", "VND", "XXX", ""]


def topup_packages() -> list:
    """Paket TOPUP_PACKAGES diambil dari literal _core.py (bukan angka yang
    dikira benar): label + harga IDR yang diformat dialog."""
    text = open(SRC[CORE], encoding="utf-8").read()
    m = re.search(r"^TOPUP_PACKAGES = \(\n(.*?)^\)", text, re.S | re.M)
    if not m:
        die("TOPUP_PACKAGES tidak ditemukan sebagai literal di _core.py")
    rows = re.findall(r'\{"label": "([^"]+)", "gold": (\d+), "bonus": (\d+),'
                      r' "price": (\d[\d_]*)\}', m.group(1))
    if not rows:
        die("baris TOPUP_PACKAGES tidak terparse: %r" % m.group(1)[:120])
    return [{"label": r[0], "gold": int(r[1]), "bonus": int(r[2]),
             "price": int(r[3].replace("_", ""))} for r in rows]


ROUND_VALUES = [2.675, 2.665, 0.5, 1.5, 2.5, 3.5, -2.5, 0.125, 0.375, 28.75,
                11.5, 13.5, 0.005, 0.015, 0.025, 1.005, 1234.565, 16200.0,
                0.6172, 200.0, 93.05, 870.4, -0.125, 2.5e14, 1.0]
ROUND_DIGITS = [0, 2]


# ── 3) shadow-run algoritma Godot ──
# Transkripsi MEKANIS baris-per-baris dari TopupCurrency.gd + HudLayout.gd ke
# Python (semantik GDScript: int64 wrap, integer division menuju nol, round()
# engine menjauhi nol, tidak ada format %), dijalankan atas TABEL HASIL BACAAN
# FILE .GD dan dibandingkan dengan fixture pygame. Ini BUKAN pengganti tes
# headless (`res://tests/TopupCurrencyParityTest.tscn` yang membuktikan GDScript
# sungguhan) — gunanya supaya deviasi ALGORITMA (tanda "-0.00", pembagian
# integer, ties-to-even, pemisah ribuan) ketahuan di mesin tanpa Godot, karena
# di CI linter ini engine tidak tersedia.


def _i64(x: int) -> int:
    x &= (1 << 64) - 1
    return x - (1 << 64) if x >> 63 else x


def gd_double_bits(value: float) -> int:
    import struct
    return _i64(int.from_bytes(struct.pack("<d", value), "little"))


def _gd_round_away(x: float) -> int:  # round() GDScript: .5 menjauhi nol
    import math
    return int(math.copysign(math.floor(abs(x) + 0.5), x))


def gd_round_half_even_scaled(value: float, digits: int) -> int:
    import math
    if math.isnan(value) or math.isinf(value):
        return 0
    bits = gd_double_bits(value)
    neg = bits < 0
    exp = (bits >> 52) & 0x7FF
    mant = bits & 0xFFFFFFFFFFFFF
    if exp == 0:
        m, e = mant, -1074
    else:
        m, e = mant | (1 << 52), exp - 1075
    if m == 0:
        return 0
    d = m
    for _ in range(max(0, digits)):
        d *= 5
    k = e + max(0, digits)
    if k >= 0:
        room = ((1 << 63) - 1) >> k if k < 63 else 0
        if k >= 63 or d > room:
            res = _gd_round_away(value * 10.0 ** digits)
        else:
            res = _i64(d << k)
    else:
        sh = -k
        if sh >= 63:
            res = 0
        else:
            q0 = d >> sh
            r = d - (q0 << sh)
            twice, half = r * 2, 1 << sh
            res = q0 + 1 if twice > half else (
                q0 if twice < half else (q0 if q0 % 2 == 0 else q0 + 1))
    return _i64(-res) if neg else res


def gd_format_thousands(value: int) -> str:
    neg = value < 0
    digits = str(abs(int(value)))
    out = ""
    while len(digits) > 3:
        out = "," + digits[-3:] + out
        digits = digits[:-3]
    return ("-" if neg else "") + digits + out


def gd_has_sign_bit(value: float) -> bool:
    return gd_double_bits(value) < 0


def gd_fmt_fixed_grouped(tables: dict, value: float, digits: int) -> str:
    scaled = gd_round_half_even_scaled(value, digits)
    neg = gd_has_sign_bit(value)
    abs_scaled = -scaled if scaled < 0 else scaled
    unit = 1
    for _ in range(digits):
        unit *= 10
    whole = int(abs_scaled / unit)  # GDScript: int/int -> int (menuju nol)
    frac = int(abs_scaled - whole * unit)
    text = gd_format_thousands(whole)
    if digits > 0:
        frac_s = str(frac)
        while len(frac_s) < digits:
            frac_s = "0" + frac_s
        text += "." + frac_s
    return ("-" if neg else "") + text


def gd_convert_idr(tables: dict, amount_idr: float, currency: str):
    table = tables["IDR_PER_UNIT"]
    rate = table.get(currency)
    if rate is None or float(rate) == 0.0:
        return amount_idr / float(table[tables["DEFAULT_CURRENCY"]]), \
            tables["DEFAULT_CURRENCY"]
    return amount_idr / float(rate), currency


def gd_format_price(tables: dict, amount_idr: float, currency: str) -> str:
    val, cur = gd_convert_idr(tables, amount_idr, currency)
    if cur in tables["NO_DECIMAL"]:
        num = gd_format_thousands(gd_round_half_even_scaled(val, 0))
        if cur == "IDR":
            num = num.replace(",", ".")
    else:
        num = gd_fmt_fixed_grouped(tables, val, 2)
    symbol = tables["CURRENCY_SYMBOLS"].get(cur, cur + " ")
    return symbol + num


def gd_parse_locale_name(locale_name: str):
    if locale_name == "" or locale_name.startswith("C"):
        return "", ""
    first = locale_name.split(".")[0].replace("-", "_")
    parts = first.split("_")
    language = parts[0].lower()
    region = ""
    if len(parts) > 1 and len(parts[1]) == 2 and parts[1].isalpha():
        region = parts[1].upper()
    return language, region


def gd_currency_for(tables: dict, lang: str, region: str) -> str:
    if region != "":
        cur = tables["REGION_CURRENCY"].get(region.upper(), "")
        if cur != "":
            return cur
    if lang != "":
        hit = tables["LANG_CURRENCY"].get(lang.lower(), "")
        if hit != "":
            return hit
    return tables["DEFAULT_CURRENCY"]


def shadow_checks(gd_tables: dict, fixture: dict) -> int:
    """Semua kasus fixture diputar lewat transkripsi algoritma Godot."""
    n = 0
    for case in fixture["prices"]:
        got = gd_format_price(gd_tables, float(case["in"][0]), str(case["in"][1]))
        n += 1
        if got != case["out"]:
            die("shadow Godot format_price(%s, %r) = %r, pygame %r"
                % (case["in"][0], case["in"][1], got, case["out"]))
    for case in fixture["convert"]:
        val, cur = gd_convert_idr(gd_tables, float(case["in"][0]),
                                  str(case["in"][1]))
        n += 2
        if abs(val - float(case["val"])) > 1e-9 or cur != case["cur"]:
            die("shadow Godot convert_idr(%r) = (%r, %r), pygame (%r, %r)"
                % (case["in"], val, cur, case["val"], case["cur"]))
    for case in fixture["locale"]:
        lang, region = gd_parse_locale_name(str(case["in"]))
        want_lang = "" if case["lang"] is None else case["lang"]
        want_region = "" if case["region"] is None else case["region"]
        n += 1
        if (lang, region) != (want_lang, want_region):
            die("shadow Godot parse_locale_name(%r) = %r, pygame %r"
                % (case["in"], (lang, region), (want_lang, want_region)))
        n += 1
        if gd_currency_for(gd_tables, lang, region) != case["cur"]:
            die("shadow Godot detect(%r) = %r, pygame %r"
                % (case["in"], gd_currency_for(gd_tables, lang, region),
                   case["cur"]))
    for case in fixture["round"]:
        got = gd_round_half_even_scaled(float(case["v"]), int(case["d"]))
        n += 1
        if got != int(case["out"]):
            die("shadow Godot round_half_even_scaled(%r, %d) = %d, CPython %d"
                % (case["v"], int(case["d"]), got, int(case["out"])))
    for case in fixture["idr"]:
        got = gd_format_price(gd_tables, float(case["amount"]), "IDR")
        n += 1
        if got != case["fmt_idr"]:
            die("shadow Godot format_price(%s, IDR) = %r, fmt_idr %r"
                % (case["amount"], got, case["fmt_idr"]))
    for case in fixture["history"]:
        n += 1
        if gd_format_price(gd_tables, case["price"], case["cur"]) != case["price_fmt"]:
            die("shadow Godot harga dialog %s = %r, pygame %r"
                % (case["cur"], gd_format_price(gd_tables, case["price"],
                                                case["cur"]), case["price_fmt"]))
        n += 1
        val = gd_convert_idr(gd_tables, case["price"], case["cur"])[0]
        got = gd_round_half_even_scaled(val, 2) / 100.0
        if abs(got - float(case["price_cur"])) > 1e-9:
            die("shadow Godot price_cur %s = %r, pygame %r"
                % (case["cur"], got, case["price_cur"]))
    return n


def die(msg: str) -> None:
    raise SystemExit("GAGAL: %s" % msg)


def check_pins(texts: dict) -> int:
    n = 0
    for label, src, needle, want, what in PINS:
        got = texts[src].count(needle)
        if got < want:
            die("pin \"%s\" %dx di %s (butuh >=%d) — %s"
                % (label, got, src, want, what))
        n += 1
    for label, src, pattern, what in FORBIDDEN:
        # Komentar/prosa justru BOLEH menyebut yang dilarang (header port
        # wajib menjelaskan deviasinya); yang dilarang adalah memakainya di
        # kode.
        hits = [ln for ln in texts[src].splitlines()
                if not ln.strip().startswith("#") and re.search(pattern, ln)]
        if hits:
            die("pola terlarang \"%s\" muncul di %s (%s) — %s"
                % (label, src, hits[0].strip()[:90], what))
        n += 1
    return n


def tables_from_python() -> dict:
    """Literal tabel DIAMBIL DARI SUMBER (ast), bukan dari objek hasil import,
    supaya komentar/hard-code di konsumen tidak bisa menyamarkan tabel."""
    text = open(SRC[PY], encoding="utf-8").read()
    tree = ast.parse(text)
    out: dict = {}
    want = {"IDR_PER_UNIT": "dict", "CURRENCY_SYMBOLS": "dict",
            "NO_DECIMAL": "tuple", "REGION_CURRENCY": "dict",
            "LANG_CURRENCY": "dict", "DEFAULT_CURRENCY": "str"}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in want:
                out[name] = ast.literal_eval(node.value)
    for name, kind in want.items():
        if name not in out:
            die("tabel %s tidak ditemukan sebagai literal di %s" % (name, PY))
    return out


def tables_from_godot(text: str) -> dict:
    """Const Godot dibaca sebagai DATA (regex per-baris, urutan bebas)."""
    out: dict = {}
    for name in ("IDR_PER_UNIT", "CURRENCY_SYMBOLS", "REGION_CURRENCY",
                 "LANG_CURRENCY"):
        body = _gd_block(text, "const %s: Dictionary = {" % name)
        # TIDAK di-anchor ke awal baris: REGION_CURRENCY pygame menaruh lima
        # kunci dalam satu baris ("DE": "EUR", "FR": "EUR", ...) dan salinan
        # Godot wajib begitu juga — anchor ^ akan kehilangan 8 kunci.
        pairs = re.findall(r'"([A-Za-z]{2,3})": ("[^"]*"|[-0-9.]+),', body)
        if not pairs:
            die("const %s kosong/tak terparse di TopupCurrency.gd" % name)
        out[name] = {}
        for k, v in pairs:
            out[name][k] = v[1:-1] if v.startswith('"') else _as_num(v)
    m = re.search(r'^const NO_DECIMAL: Array = \[(.*)\]$', text, re.M)
    if not m:
        die("const NO_DECIMAL tidak ditemukan di TopupCurrency.gd")
    out["NO_DECIMAL"] = tuple(re.findall(r'"(\w+)"', m.group(1)))
    out["DEFAULT_CURRENCY"] = re.search(
        r'^const DEFAULT_CURRENCY := "(\w+)"$', text, re.M).group(1)
    return out


def _gd_block(text: str, opener: str) -> str:
    i = text.find(opener)
    if i < 0:
        die("blok \"%s\" tidak ditemukan" % opener)
    j = text.find("\n}", i)
    if j < 0:
        die("blok \"%s\" tidak tertutup" % opener)
    return text[i + len(opener):j]


def _as_num(v: str):
    f = float(v)
    return f if ("." in v) else int(v)


def build_fixture(mod) -> dict:
    """Semua angka harapan dihitung oleh modul pygame asli."""
    prices = [{"in": [a, c], "out": mod.format_price(a, c)}
              for c in CURRENCIES for a in PRICES]
    # invarian dokumentasi modul (:212-213): IDR == fmt_idr
    idr = [{"amount": a, "out": mod.format_price(a, "IDR"),
            "fmt_idr": f"Rp {int(a):,}".replace(",", ".")}
           for a in (10000, 120000, 0, 1, 999, 123456789, 1000000000,
                     45000, 1500000)]
    for case in idr:
        if case["out"] != case["fmt_idr"]:
            die("invarian format_price(x,'IDR') == fmt_idr(x) patah di "
                "pygame sendiri: %r vs %r" % (case["out"], case["fmt_idr"]))
    convert = [{"in": [10000, c], "val": mod.convert_idr(10000, c)[0],
                "cur": mod.convert_idr(10000, c)[1]} for c in CURRENCIES]
    convert += [{"in": [0, ""], "val": mod.convert_idr(0, "")[0],
                 "cur": mod.convert_idr(0, "")[1]},
                {"in": [-12345, "IDR"], "val": mod.convert_idr(-12345, "IDR")[0],
                 "cur": mod.convert_idr(-12345, "IDR")[1]},
                {"in": [10000, "VND"], "val": mod.convert_idr(10000, "VND")[0],
                 "cur": mod.convert_idr(10000, "VND")[1]}]
    # detect_currency DIEKSEKUSI apa adanya; hanya sumber locale yang di-stub
    real = mod._device_locale
    locale_cases = []
    try:
        for loc in LOCALES:
            mod._device_locale = (lambda value=loc: mod._parse_locale_name(value))
            lang, region = mod._parse_locale_name(loc)
            locale_cases.append({"in": loc, "lang": lang, "region": region,
                                 "cur": mod.detect_currency()})
    finally:
        mod._device_locale = real
    rnd = []
    for v in ROUND_VALUES:
        for d in ROUND_DIGITS:
            text = "%.*f" % (d, v)  # CPython: ties-to-even atas nilai biner
            rnd.append({"v": v, "d": d, "out": int(Decimal(text).scaleb(d))})
    # jalur riwayat dialog: padanan _core.py:6107-6119 (cur = topup_currency
    # or "IDR"; price_cur = round(convert_idr(...)[0], 2)) — harga disimpan
    # sebagai float 2 desimal dan `cur` ASLI (bukan hasil akhir convert_idr).
    history = []
    for pkg in topup_packages():
        for cur_in in HISTORY_CURRENCIES:
            stored = cur_in or "IDR"
            val = mod.convert_idr(pkg["price"], stored)[0]
            history.append({"pkg": pkg["label"], "price": pkg["price"],
                            "currency_in": cur_in, "cur": stored,
                            "price_cur": round(val, 2),
                            "price_fmt": mod.format_price(pkg["price"], stored)})
    tables = tables_from_python()
    return {
        "tables": {k: (list(v) if isinstance(v, tuple) else
                       (v if not isinstance(v, dict) else
                        {kk: vv for kk, vv in v.items()}))
                   for k, v in tables.items()},
        "prices": prices,
        "idr": idr,
        "convert": convert,
        "locale": locale_cases,
        "round": rnd,
        "history": history,
        "symbols": [{"cur": c, "symbol": mod.CURRENCY_SYMBOLS.get(c, c + " ")}
                    for c in CURRENCIES],
        "pin_count": len(PINS) + len(FORBIDDEN),
    }


def main(argv: list) -> int:
    write = "--write-fixture" in argv
    texts = {}
    for name, path in SRC.items():
        if not os.path.isfile(path):
            die("berkas sumber hilang: %s" % path)
        texts[name] = open(path, encoding="utf-8").read()
    checks = check_pins(texts)

    py = tables_from_python()
    gd = tables_from_godot(texts[GD])
    for key in ("IDR_PER_UNIT", "CURRENCY_SYMBOLS", "NO_DECIMAL",
                "REGION_CURRENCY", "LANG_CURRENCY", "DEFAULT_CURRENCY"):
        pv = list(py[key]) if isinstance(py[key], tuple) else py[key]
        gv = list(gd[key]) if isinstance(gd[key], tuple) else gd[key]
        if pv != gv:
            only_py = {k: v for k, v in pv.items() if gv.get(k) != v} \
                if isinstance(pv, dict) else None
            die("tabel %s berbeda pygame vs Godot: hanya-di-pygames=%r "
                "godot=%r" % (key, only_py, gv if not isinstance(gv, dict)
                              else {k: v for k, v in
                                    (gv.items() if isinstance(gv, dict) else [])
                                    if pv.get(k) != v}
                              if isinstance(pv, dict) else gv))
        checks += 1
    if set(py["IDR_PER_UNIT"]) != set(IDR_PER_UNIT):
        die("tabel kurs pygame berubah isinya: pin di alat ini harus "
            "ditambah/diperbarui (IDR_PER_UNIT punya %d kunci, pin %d)"
            % (len(py["IDR_PER_UNIT"]), len(IDR_PER_UNIT)))
    checks += 1

    import topup_currency as mod  # noqa: E402  (sys.path.insert di atas)
    for name in ("IDR_PER_UNIT", "CURRENCY_SYMBOLS", "NO_DECIMAL",
                 "REGION_CURRENCY", "LANG_CURRENCY", "DEFAULT_CURRENCY"):
        live = getattr(mod, name)
        src = py[name]
        if (list(live) if isinstance(live, tuple) else live) != \
                (list(src) if isinstance(src, tuple) else src):
            die("modul yang diimport berbeda dari literal di sumber (%s) — "
                "ada mutate tabel?!" % name)
        checks += 1

    fixture = build_fixture(mod)
    # shadow-run dijalankan SEBELUM fixture ditulis supaya angka di berkas
    # hanya berisi data, bukan hasil hitungan alat ini (determinisme)
    shadow_n = shadow_checks(gd, fixture)
    checks += shadow_n
    for case in fixture["history"]:
        if case["currency_in"] in ("IDR", "") and case["price_cur"] \
                != float(case["price"]):
            die("riwayat IDR harus menyimpan harga mentah round(x,2)=%r "
                "(kasus %r)" % (case["price_cur"], case["currency_in"]))
    blob = json.dumps(fixture, ensure_ascii=False, indent=1, sort_keys=True)
    n_cases = (len(fixture["prices"]) + len(fixture["convert"])
               + len(fixture["locale"]) + len(fixture["round"])
               + len(fixture["idr"]) + len(fixture["symbols"])
               + len(fixture["history"]))
    if write:
        os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
        old = open(FIXTURE, encoding="utf-8").read() if os.path.isfile(FIXTURE) else None
        with open(FIXTURE, "w", encoding="utf-8") as fh:
            fh.write(blob + "\n")
        # determinisme: tulis ulang kedua kali harus identik
        tmp = blob + "\n"
        if tmp != open(FIXTURE, encoding="utf-8").read():
            die("penulisan fixture tidak stabil")
        if old is not None and old != blob + "\n":
            print("CATATAN: fixture berubah (perilaku pygame/Godot bergeser) "
                  "— ini bukan kegagalan, tapi wajib direview")
        print("fixture ditulis: %s (%d byte, %d kasus, %d pin)"
              % (os.path.relpath(FIXTURE, ROOT), len(blob.encode()) + 1,
                 n_cases, len(PINS) + len(FORBIDDEN)))
    checks += n_cases
    print("OK: %d cek (pin %d + tabel %d + kasus fixture %d + shadow Godot "
          "%d) — %s" % (checks, len(PINS) + len(FORBIDDEN), len(py), n_cases,
                        shadow_n, " ".join(sorted(SRC))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
