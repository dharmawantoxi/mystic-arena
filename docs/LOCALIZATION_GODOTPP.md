# Migrasi localization.py → Godot++ (GDScript)

> **Status:** DONE (2026-09-11, FASE 30) — port 1:1 tabel teks + API + jalur
> setting bahasa. 1 dari 24 kunci sudah punya pemakai UI di Godot; sisanya
> diport sebagai DATA dan menunggu permukaan UI-nya (daftar di bawah).

## Ringkasan localization.py (Python)

`localization.py` (100 baris) adalah modul lokalisasi ringan untuk teks UI:

- `_LANGUAGE = "id"` — satu variabel modul: bahasa aktif (`:7`).
- `LANGUAGES = ("id", "en")` + `LANGUAGE_LABELS` (`:9-13`) — daftar bahasa
  (urutannya dipakai cycler prev/next di layar PENGATURAN) dan label manusianya.
- `_TEXT` (`:15-74`) — kamus `{bahasa: {kunci: template}}`, **24 kunci × 2
  bahasa**: label setelan, status hero mati + antrean item, notifikasi Item
  Forge (beli/antre/kirim), banner & halaman toko, pelepasan item, dan 7 kunci
  popup detail item (DESKRIPSI / STAT & EFEK / RIWAYAT / DIMILIKI / hint).
- `set_language(language)` (`:77-81`) — nilai tidak valid **aman jatuh ke
  "id"** dan bahasa aktif dikembalikan.
- `get_language()` / `get_language_label(language=None)` (`:84-89`).
- `tr(key, **values)` (`:92-100`) — ambil template bahasa aktif, fallback ke
  tabel "id", lalu ke **kunci mentah**; `template.format(**values)` dibungkus
  `except (KeyError, ValueError)` sehingga **nilai placeholder yang hilang
  mengembalikan template mentah**, bukan crash dan bukan string kosong.

Bahasa aktif **tidak** disimpan modul ini: `GameSettings` yang menyinkronkan
(`_core.py:9116` saat singleton dibuat, `:9170` saat `settings.json` dibaca,
`:9276` saat pemain memilih bahasa) dan menyimpannya di `settings.json` GLOBAL
(`_core.py:9193`, bukan per slot save).

Pemanggil pygame:

| Pemanggil | Kunci |
|---|---|
| `_core.py:6321-6329` (baris "Interface language" di PENGATURAN) | `language` + `get_language_label` |
| `_core.py:7295-7303` (tombol `language_prev`/`language_next`) | urutan `LANGUAGES` |
| `_core.py:2185` (notifikasi item terkirim setelah respawn) | `forge_delivered` |
| `_core.py:8005` (notifikasi melepas item dari slot hero) | `item_dropped_short` |
| `hero_items.py:1632/3894` (`en = get_language() == "en"`) | bahasa popup mekanik/flavor item |
| `hero_items.py:3263-3685` (ItemShopUI: chip hero, banner, halaman, popup detail) | `dead`, `queued`, `shop_no_hero_yet`, `shop_no_hero_banner`, `shop_page_label`, `item_card_detail_hint`, `item_detail_*`, `item_inventory_hint`, `dead_delivery_hint`, `queued_item_count` |
| `hero_items.py:3977-4097` (notifikasi beli/antre/gagal) | `delivery_after_respawn`, `no_hero`, `inventory_full`, `magic_only_denied`, `forge_purchase`, `forge_queued`, `item_dropped` |

## Hasil migrasi

| Berkas Godot | Isi |
|---|---|
| `godot/scripts/utils/Localization.gd` | **Port 1:1** — `class_name MysticLocalization`, semua `static`: `TEXT`/`LANGUAGES`/`LANGUAGE_LABELS`/`DEFAULT_LANGUAGE`, `static var _language`, `set_language`, `get_language`, `get_language_label`, `tr_text`, `is_english`, `has_text`, aksesor data (`languages`/`language_labels`/`text_table`), dan `_py_format`/`_py_str` (semantik `str.format` + `str()` Python). |
| `godot/scripts/autoload/GameManager.gd` | Cermin `GameSettings.language`: `var language`, `apply_language()` (jalur load, tanpa tulis save), `set_language()` (validasi `("id","en")` → simpan → terapkan, paritas `_core.py:9272-9278`), `signal language_changed`, dan sinkronisasi di `_load_gameplay_settings()` (boot + tiap `start_level`). |
| `godot/scripts/autoload/SaveManager.gd` | `get_setting_str()` / `set_setting_str()` — pasangan string untuk `get_setting`/`set_setting` yang float-only (kunci `settings.language`). |
| `godot/scripts/autoload/AppShell.gd` | `_apply_interface_language()` saat boot (autoload PALING AKHIR, jadi `SaveManager` sudah selesai `load_save()`), kolom `bahasa` di banner boot, dan `lang=` di baris `SESSION START` `crash_log.txt`. |
| `godot/scenes/ui/MainMenu.gd` | `_language_row()` + `_cycle_language()` — baris **Bahasa / Bahasa Indonesia** dengan tombol `<` `>` di layar PENGATURAN, posisinya persis pygame: setelah Game Speed, sebelum seksi GRAPHICS. Layar dibangun ulang setelah bahasa berubah karena label barisnya sendiri terlokalisasi. |
| `godot/scripts/core/ItemDB.gd` | `item_mechanics_localized(item_id)` — padanan `en = get_language() == "en"` (`hero_items.py:1632`) untuk popup mekanik item. |
| `godot/tests/LocalizationParityTest.gd` + `.tscn` | Replay fixture di engine betulan (tabel, fallback, format, plumbing, baris SETTINGS). |
| `godot/tests/fixtures/localization.json` | Oracle: dihasilkan dari `localization.py` ASLI. |
| `tools/test_godot_localization_parity.py` | Oracle tanpa pygame/Godot: baca tabel GDScript → bandingkan baris demi baris, audit placeholder, cek kunci yang dipakai kode Godot, jaga fixture tetap segar. |

## Deviasi (semuanya disengaja + dikunci tes)

1. **`tr()` → `tr_text()`.** `Object.tr()` adalah method NATIVE Godot (pintu
   masuk `TranslationServer`). Memakai nama `tr` membuat `tr("dead")` di dalam
   script Node mana pun berisiko resolve ke method native dan diam-diam
   mengembalikan kunci mentah. Oracle **gagal** kalau `static func tr(` muncul
   di `Localization.gd`.
2. **`**values` → `Dictionary`.** GDScript tidak punya keyword arguments:
   `tr("queued", count=3)` menjadi `tr_text("queued", {"count": 3})`.
3. **`get_language_label(None)` → `get_language_label("")`.** String kosong =
   "pakai bahasa aktif", sama seperti `language or _LANGUAGE` Python (jadi
   `""` juga jatuh ke bahasa aktif, bukan ke label default).
4. **Subset `str.format`.** `_py_format` mengimplementasi `{nama}`, escape
   `{{`/`}}`, dan cabang "template mentah" untuk `KeyError`/`ValueError`.
   Format spec (`{count:>3}`), konversi (`{hero!r}`), dan penomoran posisional
   (`{0}`/`{}`) **tidak** dipakai tabel ini; oracle mengaudit setiap template
   supaya tetap begitu (placeholder baru yang bukan `{nama}` polos = gagal).
5. **`str()` Python dipertahankan.** Godot membuang `.0` float bulat
   (`str(3.0)` → `"3"`), menulis `true`/`false` huruf kecil, dan `str(null)` →
   `"<null>"`. `_py_str` mengoreksinya ke `3.0` / `True` / `None` (pola yang
   sama sudah dipakai `HeroItems._py_str`).
6. **Setting per slot, bukan global.** pygame menyimpan bahasa di
   `settings.json` GLOBAL; port Godot menyimpan SEMUA setting di
   `SaveManager.data["settings"]` per slot (precedent `game_speed`/`fps_limit`
   FASE 25). Konsekuensinya: ganti slot bisa ganti bahasa. Dicatat apa adanya,
   tidak dipalsukan sebagai "global".
7. **Tanpa `TranslationServer` / `.po` / `.csv`.** Tabel tetap inline di
   `Localization.gd` supaya diff terhadap `localization.py` bisa dibaca baris
   demi baris oleh oracle. Locale engine tidak diubah (tidak ada teks engine
   yang ikut terlokalisasi di project ini).
8. **`signal language_changed`.** pygame menggambar ulang seluruh UI tiap
   frame, jadi tidak butuh sinyal; Godot membangun Control sekali per layar,
   jadi layar yang teksnya terlokalisasi menyegarkan diri lewat sinyal ini
   (`MainMenu` memanggil `_show(State.SETTINGS)` langsung setelah cycler).

## Kunci yang sudah punya pemakai vs yang masih menunggu

Dilaporkan oracle setiap run (baris `[oracle] pemakai tr_text() di Godot:`):

- **Hidup sekarang (1):** `language` (baris BAHASA di PENGATURAN). Ditambah
  jalur non-kunci: `is_english()` untuk `ItemDB.item_mechanics_localized`.
- **Diport sebagai data, pemakainya belum ada di Godot (23):** `dead`,
  `queued`, `delivery_after_respawn`, `dead_delivery_hint`,
  `queued_item_count`, `no_hero`, `inventory_full`, `magic_only_denied`,
  `forge_purchase`, `forge_queued`, `forge_delivered`, `shop_no_hero_yet`,
  `shop_no_hero_banner`, `shop_page_label`, `item_dropped`,
  `item_dropped_short`, `item_card_detail_hint`, `item_detail_description`,
  `item_detail_stats`, `item_detail_flavor`, `item_detail_owned`,
  `item_detail_close_hint`, `item_inventory_hint`.

Alasan tiap kelompok (jangan "dipakai" sebelum permukaan UI-nya ada, supaya
teks tidak mengambang tanpa perilaku):

| Kelompok kunci | Permukaan pygame | Kondisi di port Godot |
|---|---|---|
| `forge_delivered` | `Game.update` mengirim pesanan item saat respawn (`_core.py:2178-2192`) | `_update_hero_respawns` belum memanggil `HeroItems.deliver_pending_forge_items` (logikanya sudah diport + dikunci `HeroItemsParityTest`, wiring runtime-nya masih terbuka — catatan yang sama ada di baris FASE 29 `GODOT_PARITY.md`) |
| `no_hero`, `inventory_full`, `magic_only_denied`, `forge_purchase`, `forge_queued`, `item_dropped`, `item_dropped_short`, `delivery_after_respawn` | `ui.add_notification(...)` — toast notifikasi UI | Port Godot **tidak punya** kanal notifikasi itu; kegagalan beli hanya `print("[Shop] ...")` dan pelepasan item belum ada UI-nya |
| `dead`, `queued`, `queued_item_count`, `dead_delivery_hint`, `shop_no_hero_yet`, `shop_no_hero_banner`, `shop_page_label` | `ItemShopUI.draw` (chip hero "MATI", antrean, banner tanpa hero, HAL n) | `ShopPanel.gd` tab ITEM adalah Control UI sendiri (satu scroll, tanpa halaman; hero mati tidak bisa terpilih karena `clear_selection()` saat mati) — deviasi yang sudah tercatat di `GODOT_PARITY.md` |
| `item_card_detail_hint`, `item_detail_*`, `item_inventory_hint` | Popup detail item Forge (deskripsi + stat + riwayat) | Popup detail belum diport; `ItemDB.item_mechanics_localized()` sudah siap sebagai sumber baris "STAT & EFEK"-nya |

## Verifikasi

```bash
# 1. Oracle TANPA engine (detik): tabel GDScript == localization.py,
#    audit placeholder, closed-world kunci tr_text(), fixture segar.
python3 tools/test_godot_localization_parity.py
#    regenerasi fixture HANYA kalau localization.py berubah:
python3 tools/test_godot_localization_parity.py --write-fixture

# 2. Parser GDScript asli (gdtoolkit) + lint scene/referensi repo
gdparse godot/scripts/utils/Localization.gd godot/tests/LocalizationParityTest.gd
python3 godot/tools/tscn_lint.py godot/tests/LocalizationParityTest.tscn
python3 godot/tools/check_refs.py godot

# 3. Replay fixture di engine (CI yang menjalankan; user:// terisolasi)
export XDG_DATA_HOME="$(mktemp -d)"
godot --headless --path godot res://tests/LocalizationParityTest.tscn --quit-after 120
#    wajib: "[LocalizationParityTest] PASS" tanpa SCRIPT ERROR / Parse Error
```

Isi fixture `localization.json` (semuanya dievaluasi `localization.py` ASLI,
bukan salinan):

| Seksi | Isi |
|---|---|
| `text` / `key_order` | 24 kunci × 2 bahasa + urutannya |
| `languages` / `labels` / `default_language` | `LANGUAGES`, `LANGUAGE_LABELS`, `"id"` |
| `placeholders` | daftar `{nama}` per kunci (kontrak subset `_py_format`) |
| `tr_cases` | 48 = setiap kunci × setiap bahasa dengan nilai contoh (`hero`/`item`/`items`/`count`/`page`) |
| `edge_cases` | 8 = kunci tak dikenal → kunci mentah, nilai hilang → template mentah, sebagian nilai hilang, nilai berlebih diabaikan, `count=0`, tanpa placeholder |
| `fallback_cases` | kunci yang hanya ada di satu bahasa → fallback tabel `id` (kosong selama tabel simetris; otomatis terisi kalau pygame menambah kunci sepihak) |
| `set_language_cases` | 7 = `id`/`en`/`invalid`/`""`/`"ID"`/`"en-US"`/`null` → bahasa aktif + nilai balik |
| `label_cases` | 7 = tanpa argumen (bahasa aktif), eksplisit, dan tak dikenal → label Indonesia |
| `format_cases` | 21 = semantik `str.format` + cabang `except` (escape `{{`, `{x` tak tertutup → ValueError, `a}b` → ValueError, placeholder berulang, persen, format spec, float `1.5`/`3.0`, `True`, `None`) |
| `py_str_cases` | 13 = `str()` Python untuk int/float/bool/None/str (termasuk `3.0` → `"3.0"`, `0.0` → `"0.0"`) |

Sisi Godot juga mengunci **plumbing**-nya (bukan cuma modul): bahasa aktif
setelah boot == setting tersimpan, `GameManager.set_language` menolak bahasa
invalid tanpa menyimpan/memancarkan sinyal, `apply_language` untuk nilai tak
dikenal jatuh ke `id`, `SaveManager.get/set_setting_str`, cycler `<`/`>`
membungkus ke dua arah seperti `(idx + delta) % len` Python, dan layar
PENGATURAN benar-benar memuat label `Bahasa` + `Bahasa Indonesia`.

CI (`.github/workflows/godot-check.yml`): oracle Python masuk langkah **Linter
statis** (jalan sebelum Godot diunduh), scene `LocalizationParityTest` jadi
langkah headless sendiri dengan gerbang log yang sama, dan `localization.py` +
`tools/test_godot_localization_parity.py` masuk filter `paths` supaya perubahan
di sisi pygame ikut memicu pemeriksaan.

> Binary Godot tidak tersedia di sandbox saat migrasi ini dibuat, jadi langkah
> 3 dijalankan CI. Sebagai gantinya logika `_py_format`/`_py_str`/`tr_text`
> diverifikasi dengan menerjemahkan algoritma GDScript itu 1:1 ke Python dan
> menjalankan seluruh kasus fixture terhadap oracle (159 cek, 0 selisih) —
> sisa risikonya hanya hal spesifik engine, bukan logika formatnya.

## Menambah kunci / bahasa baru

1. Tambah di `localization.py` (sumber kebenaran) — kedua bahasa, placeholder
   `{nama}` polos.
2. Salin ke `TEXT` di `Localization.gd` (baris panjang boleh dipecah `"..." \
   + "..."` seperti implicit-concat Python-nya).
3. `python3 tools/test_godot_localization_parity.py --write-fixture` → oracle
   membandingkan keduanya dan memperbarui fixture; tanpa langkah ini CI gagal
   dengan pesan "tabel teks Localization.gd != localization.py".
4. Kalau menambah **bahasa** baru: isi `LANGUAGES` + `LANGUAGE_LABELS` di kedua
   sisi (urutan `LANGUAGES` = urutan cycler pygame `_core.py:7297-7303`).
5. Pakai `MysticLocalization.tr_text("kunci", {"nama": nilai})` di UI — jangan
   menulis teks dua kali.
