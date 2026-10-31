# Migrasi `localization.py` ke Godot

`localization.py` (589 baris) adalah **lapisan teks dua bahasa** milik Pygame: konstanta `LANGUAGES = ("id", "en")`, `LANGUAGE_LABELS`, tabel `_TEXT` berisi 224 kunci untuk tiap bahasa, lalu empat fungsi publik — `set_language` (nilai tak dikenal → `"id"`), `get_language`, `get_language_label`, dan `tr` (fallback ke `_TEXT["id"]` → key, interpolasi `template.format(**values)` dengan `KeyError`/`ValueError` → template mentah).

Port awal hanya membawa **data** `_TEXT` ke `data/localization_catalog.json` plus `language_store.gd` (persistensi atomik) dan `localization_runtime.gd` (lookup + `cycle_language`). Yang belum tersambung adalah **pemakainya**: di Pygame ada 23 kunci `tr()` yang hidup di UI (`hero_items.py` 20, `_core.py` 3), sedangkan di Godot hanya panel audio yang memakai runtime. Layer **9cm** menutup celah itu: `tr()` sekarang benar-benar dipakai oleh ITEM FORGE, dan seluruh perilaku `tr` diverifikasi baris-per-baris terhadap sumber yang **dieksekusi**.

Sumber kebenaran: `godot_rebuild/tests/localization_source_oracle.py`. Oracle pertama memakai AST untuk tabel/persistensi (tidak berubah), lalu **menjalankan** `localization.py` (modul ini tidak mengimpor apa pun) untuk merekam keluaran `tr()` dalam `tests/fixtures/localization_translate_source.json`. Suite native: `tests/localization_checks.gd` (blok lama + blok 9cm).

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `localization.py` | 589 |
| Kelas | 0 (modul fungsional) |
| Fungsi | 4 |
| Konstanta modul | 4 (`_LANGUAGE`, `LANGUAGES`, `LANGUAGE_LABELS`, `_TEXT`) |
| Impor | 0 |
| Kunci `_TEXT` per bahasa | 224 (`id` dan `en` set-nya identik) |
| Kunci berformat `{nama}` | 22 (nama: `count`, `hero`, `item`, `items`, `page`) |
| Kunci bergaya `%s`/`%d` | 64 (template dibiarkan apa adanya, lihat D3) |
| Render yang dipin fixture | 448 (224 × 2 bahasa) + 8 kasus tepi |
| Kunci `tr()` yang dipakai UI Python | 23 (`hero_items.py` 20, `_core.py` 3) |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 4 | `set_language`, `get_language`, `get_language_label`, `tr` |
| `data` | 2 | `LANGUAGES`, `LANGUAGE_LABELS` |
| `folded` | 2 | `_LANGUAGE` (state runtime), `_TEXT` (katalog JSON) |

## 2. Klasifikasi simbol

| Simbol | Kind | Target native | Token bukti |
| --- | --- | --- | --- |
| `LANGUAGES` | data | `scripts/settings/language_store.gd` | `const LANGUAGES` |
| `LANGUAGE_LABELS` | data | `data/localization_catalog.json` | `"language_labels"` |
| `_LANGUAGE` | folded | `scripts/settings/localization_runtime.gd` | `var language :=` |
| `_TEXT` | folded | `data/localization_catalog.json` | `"texts"` |
| `set_language` | ported | `scripts/settings/localization_runtime.gd` | `func set_language(value: String) -> bool` |
| `get_language` | ported | `scripts/settings/localization_runtime.gd` | `func get_language() -> String` |
| `get_language_label` | ported | `scripts/settings/localization_runtime.gd` | `func get_language_label(code: String = "")` |
| `tr` | ported | `scripts/settings/localization_runtime.gd` | `func translate(key: String, values: Dictionary = {})` |

## 3. Yang diport di layer ini

| Bagian | Perilaku sumber yang dipertahankan |
| --- | --- |
| `translate` | lookup bahasa aktif → fallback `_TEXT["id"]` → key; placeholder `{nama}` diganti hanya bila **semua** nilai ada, kalau tidak template dikembalikan mentah (padanan `except KeyError`) |
| `translate` nilai | `str()` ala Python: `True`/`False` untuk boolean, `4.0` untuk float, `4` untuk int |
| `translate` template `%` | 64 entri `%s`/`%d` tidak disentuh — `%`-formatting tetap tugas pemanggil, persis seperti `str.format` yang tidak menyentuhnya |
| `get_language` | getter kode aktif baru (sebelumnya hanya properti `language`) |
| `set_language` | memilih bahasa + menyimpan preferensi atomik (lihat D1 untuk arah nilai kembalian) |
| `get_language_label` | kode kosong → bahasa aktif; kode tak dikenal → label `"id"` (`"Bahasa Indonesia"`) |
| Bridge `scripts/settings/localization_text.gd` | `tr()` untuk Control: mengambil autoload `Localization` secara lazy, jatuh ke copy pemanggil bila runtime tidak terpasang |
| ITEM FORGE `scripts/ui/item_forge_panel.gd` | 11 kunci sumber: `item_card_detail_hint`, `shop_no_hero_banner`, `shop_no_hero_yet`, `item_detail_owned`, `item_detail_description`, `item_detail_stats`, `item_detail_flavor`, `item_detail_close_hint`, `item_inventory_hint`, `delivery_after_respawn`, `dead_delivery_hint` (+ `queued`, `shop_card_poor`, `shop_card_no_hero` untuk pil kartu) |
| Chip hero `scripts/match/item_shop_ui.gd` | `tr("dead")` untuk status mati dan `tr("queued", count=n)` untuk sisa antrean; `notice_text(suffix)` memakai `delivery_after_respawn` |
| `status_text(status, values)` | setiap notice Forge dipetakan ke kunci `tr()` sumber (`dead` → `dead_delivery_hint`), copy pendek Indonesia hanya dipakai bila runtime tidak ada |

Copy yang di Pygame memang **literal** tetap literal: judul `"ITEM FORGE"`, pil `"BUY"`, `"BUY FOR:"`, `"X"`, dan baris `Item used/max` — jadi paritas tidak "diperbaiki" menjadi lebih lokal daripada sumbernya.

## 4. Deviasi terdokumentasi

| Kode | Hal | Deviasi | Alasan |
| --- | --- | --- | --- |
| D1 | `set_language` | mengembalikan `bool` dan **menolak** kode asing (bahasa tetap), bukan memaksa `"id"` seperti sumber | konteks pemanggil native adalah tombol siklus bahasa yang selalu mengirim `"id"`/`"en"`; jalur yang bisa membawa kode asing — preferensi tersimpan — sudah jatuh ke `"id"` lewat `Store.decode_language` sehingga perilaku pemain identik |
| D2 | `tr` | nama native `translate` (dan `_text` di panel) | `tr()` adalah method bawaan `Object` di Godot; nama berbeda, semantik sama |
| D3 | 64 entri `%s`/`%d` | tidak diformat oleh runtime | sumber juga tidak memformatnya di `tr()`; pemanggil Pygame yang memakai `%` berada di jalur UI yang belum diport, jadi kunci dibiarkan verbatim agar tidak ada teks yang "setengah terjemahan" |
| D4 | notice Forge | nama hero diganti `hero <id>` | rebuild belum punya nama tampilan hero (deviasi 9ck D6); kunci `{hero}`/`{item}` tetap diisi nilai yang tersedia |
| D5 | notifikasi pembelian | `status_text()` memetakan kunci + fallback, tetapi belum ada sistem notifikasi yang menampilkannya di layar | notifikasi Pygame (`forge_purchase`, `forge_queued`, `item_dropped`, `forge_delivered`) adalah subsistem UI terpisah yang belum diport; teksnya sudah tersedia lewat API |
| D6 | panel detail | label bagian memakai kunci `item_detail_*` yang sama, urutan/posisi mengikuti 9ck | tidak ada perubahan tata letak di layer ini |

## 5. Cara menjalankan

```bash
python3 godot_rebuild/tests/localization_source_oracle.py --write   # tulis fixture render tr()
python3 godot_rebuild/tests/localization_source_oracle.py --check   # cek sinkron sumber (AST + eksekusi)
python3 godot_rebuild/tests/validate_project.py                     # blok lokalisasi + 9cm
godot --headless --script tests/run_all.gd                          # suite native (PC/CI)
```

`tests/localization_checks.gd` (9cm) me-replay **448 render** hasil `tr()` yang dieksekusi oracle, lalu menutup kasus tepi: nilai boolean/float, nilai berlebih, nilai kurang (template mentah), template `%s`, label bahasa tak dikenal, `get_language()`, penolakan kode asing + fallback preferensi tersimpan ke `"id"`, bridge `LocalizationText` dengan/tanpa runtime, dan copy ITEM FORGE/chip hero yang harus lewat kunci sumber.

## 6. Status paritas

Terbukti: seluruh keluaran `tr()` untuk 224 kunci × 2 bahasa identik dengan sumber, termasuk fallback key/template dan pemetaan label; 23 kunci `tr()` milik UI Python semuanya ada di katalog; ITEM FORGE memakai kunci yang sama dengan `hero_items.py`. Belum terbukti: tampilan akhir layar (posisi/panjang teks setelah lokalisasi), notifikasi pembelian (D5), dan perilaku di perangkat Android — ketiganya butuh run Godot + screenshot seed/state sama, sesuai kriteria paritas proyek. Validator statis dan fixture **bukan** bukti paritas visual.
