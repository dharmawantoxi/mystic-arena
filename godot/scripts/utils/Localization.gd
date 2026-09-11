# Localization.gd — port 1:1 localization.py (pygame) ke Godot 4.
#
# Kenapa modul ini ada (paritas localization.py:1-100):
# Teks UI game tidak boleh ditulis dua kali. Di pygame satu modul kecil
# memegang kamus teks id/en + bahasa aktif, dan pemanggil cukup menulis
# ``tr("kunci", hero=..., item=...)``. Modul ini adalah kembar GDScript-nya:
# tabel teks, daftar bahasa, label bahasa, dan SEMUA aturan fallback-nya
# disalin apa adanya supaya port Godot bisa menambah bahasa baru atau
# mengubah kalimat di SATU tempat, sama seperti pygame.
#
# PETA API (localization.py -> Localization.gd):
#   _LANGUAGE = "id"                -> static var _language
#   LANGUAGES = ("id", "en")        -> const LANGUAGES
#   LANGUAGE_LABELS                 -> const LANGUAGE_LABELS
#   _TEXT = {"id": {...}, "en": {}} -> const TEXT
#   set_language(language)          -> set_language(language) -> String
#   get_language()                  -> get_language() -> String
#   get_language_label(language)    -> get_language_label(language) -> String
#   tr(key, **values)               -> tr_text(key, values) -> String
#   get_language() == "en"          -> is_english()  (hero_items.py:1632)
#
# DEVIASI NAMA (satu-satunya, disengaja): fungsi Python bernama ``tr``,
# di Godot bernama ``tr_text``. ``Object.tr()`` adalah method NATIVE engine
# (pintu masuk TranslationServer .po/.csv): kalau port ini memakai nama
# ``tr``, panggilan ``tr("dead")`` di dalam script Node mana pun berisiko
# resolves ke method native itu dan diam-diam mengembalikan kunci mentah.
# ``tr_text`` tidak bisa bentrok, dan tidak ada terjemahan engine yang
# dipakai — tabel teks tetap inline persis localization.py.
#
# DEVIASI ARGUMEN: Python memakai ``**values`` (keyword args). GDScript
# tidak punya keyword args, jadi nilai pengganti placeholder dikirim sebagai
# Dictionary: ``tr_text("queued", {"count": 3})``.
#
# Semantik fallback yang DIPERTAHANKAN bit-per-bit (localization.py:77-100):
#   * bahasa tidak dikenal -> "id" (set_language mengembalikan bahasa aktif),
#   * kunci tidak ada di bahasa aktif -> cari di "id" -> kalau tetap tidak
#     ada, kembalikan KUNCI itu sendiri,
#   * placeholder tidak punya nilai (KeyError) atau template rusak
#     (ValueError) -> kembalikan TEMPLATE MENTAH, bukan crash dan bukan "".
#
# Yang TIDAK diport dari ``str.format`` Python (tidak dipakai tabel ini, dan
# dikunci oracle tools/test_godot_localization_parity.py supaya tetap begitu):
# format spec (``{count:>3}``), konversi (``{hero!r}``), dan penomoran
# posisional (``{0}``/``{}``). Semua template di sini hanya memakai
# ``{nama}`` polos — _py_format menolak (template mentah) begitu bertemu
# bentuk lain, sama seperti cabang except localization.tr.
#
# KONSUMEN (pygame -> Godot):
#   * label + nilai baris BAHASA di layar PENGATURAN
#     (_core.py:6321-6329 -> MainMenu._language_row),
#   * bahasa popup mekanik item (_build_item_mechanics hero_items.py:1632 ->
#     ItemDB.item_mechanics_localized),
#   * sinkron bahasa aktif saat boot/load setting
#     (GameSettings.__new__/_load/set_language _core.py:9116/9170/9276 ->
#     AppShell._apply_interface_language + GameManager.apply_language /
#     GameManager.set_language).
#   Kunci lain (notifikasi forge, banner toko, popup detail item, "MATI"/
#   antrean chip hero) ikut diport sebagai DATA karena permukaan UI
#   pemakainya belum ada di port Godot — lihat docs/LOCALIZATION_GODOTPP.md.
#
# Twin Pygame: localization.py. Dikunci: godot/tests/LocalizationParityTest.gd
# (+ fixture godot/tests/fixtures/localization.json) dan oracle tanpa engine
# tools/test_godot_localization_parity.py (membandingkan tabel di berkas ini
# dengan localization.py baris demi baris).
extends RefCounted
class_name MysticLocalization


# ─── BAHASA (localization.py:7-13) ────────────────────────────────────
## Bahasa bawaan + fallback — literal "id" di localization.py:7/80/89/94-96.
const DEFAULT_LANGUAGE := "id"
## LANGUAGES = ("id", "en") — localization.py:9. Urutan DIPAKAI cycler
## bahasa prev/next (_core.py:7297-7303), jadi jangan diacak.
const LANGUAGES := ["id", "en"]
## LANGUAGE_LABELS — localization.py:10-13.
const LANGUAGE_LABELS := {
	"id": "Bahasa Indonesia",
	"en": "English",
}

# ─── TABEL TEKS (localization.py:15-74) ───────────────────────────────
## _TEXT — disalin PERSIS (kunci, urutan, tanda baca, spasi ganda, "—" dan
## "•"). Baris panjang memakai continuasi "\" + "+" persis pemenggalan
## implicit-concat Python-nya supaya diff terhadap localization.py tetap
## terbaca. Oracle membandingkan hasil concatenation, bukan bentuk barisnya.
const TEXT := {
	"id": {
		"language": "Bahasa",
		"dead": "MATI",
		"queued": "+{count} antrean",
		"delivery_after_respawn": "(dikirim setelah respawn)",
		"dead_delivery_hint": "MATI — pembelian baru dikirim setelah respawn",
		"queued_item_count": "({count} item diantrikan)",
		"no_hero": "Tidak ada hero untuk menerima item.",
		"inventory_full": "Inventory {hero} penuh.",
		"magic_only_denied": "{hero} bukan hero beratribut Magic - " \
			+ "item ini tidak bisa dipakai.",
		"forge_purchase": "{hero} membeli {item}!",
		"forge_queued": "{item} untuk {hero} dikirim setelah respawn!",
		"forge_delivered": "Item Forge dikirim ke {hero}: {items}!",
		"shop_no_hero_yet": "(belum ada hero - summon dulu di HERO SHOP)",
		"shop_no_hero_banner": "TIDAK ADA HERO HIDUP - summon hero di HERO SHOP " \
			+ "dulu; item di bawah tetap bisa dilihat.",
		"shop_page_label": "HAL {page}",
		"item_dropped": "Melepas {item} (tanpa refund)",
		"item_dropped_short": "Melepas {item}",
		# ═══ DETAIL POPUP ITEM FORGE (info lengkap item) ═══
		"item_card_detail_hint": "TAP KARTU ITEM = INFO LENGKAP",
		"item_detail_description": "DESKRIPSI",
		"item_detail_stats": "STAT & EFEK",
		"item_detail_flavor": "RIWAYAT",
		"item_detail_owned": "DIMILIKI: {count}",
		"item_detail_close_hint": "Ketuk di luar kotak untuk menutup detail",
		"item_inventory_hint": "(ketuk: info  •  tahan/kanan: drop)",
	},
	"en": {
		"language": "Language",
		"dead": "DEAD",
		"queued": "+{count} queued",
		"delivery_after_respawn": "(delivered after respawn)",
		"dead_delivery_hint": "DEAD — new purchases are delivered after respawn",
		"queued_item_count": "({count} item(s) queued)",
		"no_hero": "There is no hero to receive this item.",
		"inventory_full": "{hero}'s inventory is full.",
		"magic_only_denied": "{hero} is not a Magic-attribute hero - " \
			+ "this item cannot be equipped.",
		"forge_purchase": "{hero} purchased {item}!",
		"forge_queued": "{item} for {hero} will be delivered after respawn!",
		"forge_delivered": "Forge items delivered to {hero}: {items}!",
		"shop_no_hero_yet": "(no heroes yet - summon one at HERO SHOP first)",
		"shop_no_hero_banner": "NO HEROES ALIVE - summon a hero at HERO SHOP " \
			+ "first; items below can still be browsed.",
		"shop_page_label": "PAGE {page}",
		"item_dropped": "Dropped {item} (no refund)",
		"item_dropped_short": "Dropped {item}",
		# ═══ ITEM FORGE DETAIL POPUP (full item info) ═══
		"item_card_detail_hint": "TAP AN ITEM CARD = FULL INFO",
		"item_detail_description": "DESCRIPTION",
		"item_detail_stats": "STATS & EFFECTS",
		"item_detail_flavor": "LORE",
		"item_detail_owned": "OWNED: {count}",
		"item_detail_close_hint": "Tap outside the box to close details",
		"item_inventory_hint": "(tap: info  •  hold/right-click: drop)",
	},
}

## Bahasa aktif — padanan `_LANGUAGE` (localization.py:7). `static var`
## (bukan const) supaya satu nilai dipakai seluruh project selama proses
## hidup, persis variabel modul Python.
static var _language: String = DEFAULT_LANGUAGE


# ══════════════════════════════════════════════════════════
#  API (localization.py:77-100)
# ══════════════════════════════════════════════════════════

## Set bahasa aktif. Nilai tidak valid aman kembali ke Indonesia
## (localization.py:77-81) dan MENGEMBALIKAN bahasa yang akhirnya aktif.
static func set_language(language: String) -> String:
	_language = language if LANGUAGES.has(language) else DEFAULT_LANGUAGE
	return _language


## Bahasa aktif sekarang (localization.py:84-85).
static func get_language() -> String:
	return _language


## Label manusia untuk pemilih bahasa (localization.py:88-89). String kosong
## = padanan `None` Python (pakai bahasa aktif); bahasa tak dikenal jatuh ke
## label Indonesia, persis `LANGUAGE_LABELS.get(x, LANGUAGE_LABELS["id"])`.
static func get_language_label(language: String = "") -> String:
	var code := language if language != "" else _language
	return str(LANGUAGE_LABELS.get(code, LANGUAGE_LABELS[DEFAULT_LANGUAGE]))


## Ambil teks bahasa aktif dengan fallback aman ke bahasa Indonesia
## (localization.py:92-100). `values` = padanan `**values` Python.
static func tr_text(key: String, values: Dictionary = {}) -> String:
	var table: Dictionary = TEXT.get(_language, TEXT[DEFAULT_LANGUAGE])
	var template: Variant = table.get(key)
	if template == null:
		template = (TEXT[DEFAULT_LANGUAGE] as Dictionary).get(key, key)
	return _py_format(str(template), values)


## true kalau bahasa aktif English — padanan pola pemanggil pygame
## `get_language() == "en"` (hero_items.py:1632/3894).
static func is_english() -> bool:
	return _language == "en"


## Kunci `key` ada di tabel? (dipakai oracle + alat bantu UI).
static func has_text(key: String) -> bool:
	return (TEXT[DEFAULT_LANGUAGE] as Dictionary).has(key)


# ─── aksesor data (dipakai tes/paritas, tabel tetap read-only) ─────────

## Daftar bahasa (urutan cycler pygame) — localization.py:9.
static func languages() -> Array:
	return LANGUAGES


## Label per kode bahasa — localization.py:10-13.
static func language_labels() -> Dictionary:
	return LANGUAGE_LABELS


## Seluruh tabel teks — localization.py:15-74.
static func text_table() -> Dictionary:
	return TEXT


# ══════════════════════════════════════════════════════════
#  FORMAT (subset str.format Python yang dipakai tabel ini)
# ══════════════════════════════════════════════════════════

## Padanan `template.format(**values)` + `except (KeyError, ValueError):
## return template` (localization.py:97-100).
##
## Aturan yang disalin:
##   * `{nama}` diganti `values["nama"]`,
##   * `{{` / `}}` jadi literal `{` / `}`,
##   * nilai hilang (KeyError) ATAU kurung tunggal/cacat (ValueError) ->
##     TEMPLATE MENTAH dikembalikan apa adanya,
##   * nilai tak terpakai di `values` diabaikan (Python juga begitu).
static func _py_format(template: String, values: Dictionary) -> String:
	var out := ""
	var i := 0
	var n := template.length()
	while i < n:
		var c := template[i]
		if c == "{":
			if i + 1 < n and template[i + 1] == "{":
				out += "{"
				i += 2
				continue
			var close := template.find("}", i + 1)
			if close < 0:
				# Python: ValueError("Single '{' in format string").
				return template
			var field := template.substr(i + 1, close - i - 1)
			if not values.has(field):
				# Python: KeyError -> cabang except localization.tr.
				return template
			out += _py_str(values[field])
			i = close + 1
			continue
		if c == "}":
			if i + 1 < n and template[i + 1] == "}":
				out += "}"
				i += 2
				continue
			# Python: ValueError("Single '}' in format string").
			return template
		out += c
		i += 1
	return out


## `str()` Python untuk nilai yang disisipkan placeholder.
## Godot membuang ".0" float bulat (3.0 -> "3") padahal Python mempertahankannya
## (3.0 -> "3.0") — selisih yang sama sudah ditangani HeroItems._py_str.
static func _py_str(value: Variant) -> String:
	if value == null:
		return "None"
	if value is bool:
		return "True" if value else "False"
	if value is float:
		var s := str(value)
		if not (s.contains(".") or s.contains("e") or s.contains("E")):
			return s + ".0"
		return s
	return str(value)
