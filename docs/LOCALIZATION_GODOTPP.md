# Migrasi localization.py → Godot++ (GDScript)

> **Status:** DONE (2026-09-11, FASE 30) — port 1:1 tabel teks + API + jalur
> setting bahasa, lalu **DILANJUTKAN 2026-09-13**: bahasa yang dipilih sekarang
> benar-benar berlaku DI DALAM GAME **dan di SEMUA layar menu**. Tabel tumbuh
> dari 24 kunci pygame jadi **209 kunci × 2 bahasa**: 82 kunci in-match (81
> pygame yang sebelumnya hard-code di Godot + chrome panel Godot) + 103 kunci
> layar MENU (Main, SLOT_SELECT, LEVEL_SELECT, HERO SHOP, SETTINGS,
> HOW_TO_PLAY, CREDITS, PAUSE + tooltip rail/taktis/top-up + label kartu ITEM
> FORGE). 179 kunci sudah punya pemakai (MainMenu, HUD, ShopPanel,
> ItemForgeCard, SkillBar, TacticalBar, TopupDialog, SidePanel,
> GameOverOverlay, ItemDB); 30 sisanya masih diport sebagai DATA dan menunggu
> permukaan UI-nya (daftar di bawah).

## Ringkasan localization.py (Python)

`localization.py` (100 baris) adalah modul lokalisasi ringan untuk teks UI:

- `_LANGUAGE = "id"` — satu variabel modul: bahasa aktif (`:7`).
- `LANGUAGES = ("id", "en")` + `LANGUAGE_LABELS` (`:9-13`) — daftar bahasa
  (urutannya dipakai cycler prev/next di layar PENGATURAN) dan label manusianya.
- `_TEXT` (`:15-…`) — kamus `{bahasa: {kunci: template}}`; **24 kunci × 2
  bahasa** saat FASE 30 (label setelan, status hero mati + antrean item, notifikasi Item
  Forge (beli/antre/kirim), banner & halaman toko, pelepasan item, dan 7 kunci
  popup detail item (DESKRIPSI / STAT & EFEK / RIWAYAT / DIMILIKI / hint));
  sejak 2026-09-13 **209 kunci** — 82 kunci in-match mengikuti string yang di
  pygame di-`tr()` atau teks Indonesia buatan port Godot (baris hint HUD, empat
  tab toko + konteksnya, alasan kartu item, nexus, SkillBar, layar
  menang/kalah), lalu **103 kunci menu** mengikuti SEMUA string yang selama ini
  di-hardcode Indonesia di `MainMenu.gd` (judul layar, tombol, kartu slot,
  kartu level, legenda + status HERO SHOP, label PENGATURAN, tujuh seksi CARA
  MAIN, layar PAUSE, tooltip) + label kartu ITEM FORGE. Permintaan user: "saat
  ganti ke English, semuanya Inggris, starting dari main menu" — karena kolom
  `id` persis string lama, pemain Indonesia tidak melihat perubahan apa pun.
  Sumber kebenaran tetap `localization.py`;
  `Localization.gd` salinan baris-per-baris dengan KUNCI PADA URUTAN SAMA.
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

Pemakai Godot (setelah 2026-09-13) — semuanya membaca lewat
`MysticLocalization.tr_text()`; empat panel juga tersambung ke
`GameManager.language_changed` jadi teksnya berganti TANPA buka ulang layar:

| Panel Godot | Yang dibaca |
|---|---|
| `scenes/ui/MainMenu.gd` (`_loc` + `_language_row` + `_on_language_changed`) | SEMUANYA: 103 kunci `menu_*`/`slot_*`/`lvl_*`/`hshop_*`/`set_*`/`howto_*`/`pause_*` untuk delapan state layar, plus `language` + `get_language_label` di baris Bahasa. Ganti bahasa -> `_show(state)` — layar AKTIF yang dibangun ulang, bukan hanya SETTINGS |
| `scenes/ui/widgets/ItemForgeCard.gd` | `shop_card_buy`/`shop_card_owned`/`shop_card_poor`/`shop_card_no_hero` + `shop_reason_*` — pill dan "Dimiliki: n" pada kartu yang digambar, ikut bahasa aktif |
| `scenes/ui/TacticalBar.gd` (`TOOLTIPS` -> `tr_text`) | `tac_toggle_tip` + lima tooltip perintah (kunci dinamis lewat konstanta, sama seperti `TABS` ShopPanel) |
| `scenes/ui/TopupDialog.gd` / `scenes/ui/SidePanel.gd` | `topup_subtitle` (dialog TOP UP) / `rail_pause_tip` (tooltip tombol pause rail) |
| `scenes/ui/HUD.gd` (`_hint_rows`, `_on_language_changed`) | 10 kunci `hud_hint_*` untuk baris petunjuk keycap |
| `scenes/ui/ShopPanel.gd` (`_loc`, `_apply_chrome_texts`, `_build_*_tab`) | judul/tutup/empat tab, konteks, strip BUY FOR, semua alasan kartu item, tab MENARA/NEXUS/HERO |
| `scenes/ui/SkillBar.gd` (`_loc`, `_refresh_static`) | label "tidak ada hero", petunjuk beli, tooltip 6 slot item + AUTO-CAST + FORGE |
| `scenes/ui/GameOverOverlay.gd` (`_loc`, `_on_language_changed`) | tiga tombol aksi, tiga baris hint keycap, catatan kalah + meta reward |
| `scripts/core/ItemDB.gd` (`item_mechanics_localized`) | `is_english()` — bahasa teks mekanik item |

## Hasil migrasi

| Berkas Godot | Isi |
|---|---|
| `godot/scripts/utils/Localization.gd` | **Port 1:1** — `class_name MysticLocalization`, semua `static`: `TEXT`/`LANGUAGES`/`LANGUAGE_LABELS`/`DEFAULT_LANGUAGE`, `static var _language`, `set_language`, `get_language`, `get_language_label`, `tr_text`, `is_english`, `has_text`, aksesor data (`languages`/`language_labels`/`text_table`), dan `_py_format`/`_py_str` (semantik `str.format` + `str()` Python). |
| `godot/scripts/autoload/GameManager.gd` | Cermin `GameSettings.language`: `var language`, `apply_language()` (jalur load, tanpa tulis save), `set_language()` (validasi `("id","en")` → simpan → terapkan, paritas `_core.py:9272-9278`), `signal language_changed`, dan sinkronisasi di `_load_gameplay_settings()` (boot + tiap `start_level`). |
| `godot/scripts/autoload/SaveManager.gd` | `get_setting_str()` / `set_setting_str()` — pasangan string untuk `get_setting`/`set_setting` yang float-only (kunci `settings.language`). |
| `godot/scripts/autoload/AppShell.gd` | `_apply_interface_language()` saat boot (autoload PALING AKHIR, jadi `SaveManager` sudah selesai `load_save()`), kolom `bahasa` di banner boot, dan `lang=` di baris `SESSION START` `crash_log.txt`. |
| `godot/scenes/ui/MainMenu.gd` | Delapan state layar dibangun 100% lewat `_loc(kunci)`; `_language_row()` + `_cycle_language()` tetap baris **Bahasa / Bahasa Indonesia** dengan tombol `<` `>` persis posisi pygame (setelah Game Speed, sebelum seksi GRAPHICS). `_on_language_changed()` -> `_show(state)` membangun ulang layar yang sedang tampil, jadi CONTINUE/MULAI GAME/PILIH SLOT/PILIH LEVEL/HERO SHOP/PENGATURAN/CARA MAIN/KREDIT/PAUSE ikut bahasa tanpa menutup lalu membuka menu. |
| `godot/scripts/core/ItemDB.gd` | `item_mechanics_localized(item_id)` — padanan `en = get_language() == "en"` (`hero_items.py:1632`) untuk popup mekanik item; `item_desc_localized(item_id)` — padanan `ItemShopUI._localized_desc` (`hero_items.py:3894-3899`: `desc_en` untuk English, fallback `desc`) yang dipakai kartu ITEM FORGE; `item_class_badge(item_id)` — `[label, warna]` badge kelas dari `ITEM_CLASS_INFO`. |
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
   jadi layar yang teksnya terlokalisasi menyegarkan diri lewat sinyal ini:
   `MainMenu` memanggil `_show(state)` untuk SEMUA state (dulu hanya
   `_show(State.SETTINGS)` setelah cycler), dan panel in-match punya penyegaran
   tertarget — `HUD` (baris hint), `SkillBar` (`_refresh_static`), `ShopPanel`
   (`_apply_chrome_texts` + rebuild isi, termasuk kartu ITEM FORGE),
   `GameOverOverlay` (hint + tombol aksi, tanpa mengulang animasi intro),
   `TacticalBar` (tooltip dibangun ulang; label tombol perintah sudah Inggris
   di kedua bahasa). `TopupDialog` tidak menyambung sinyal — dialognya dibuat
   ulang tiap dibuka; `SidePanel` membangun rail tiap `_ready`/perubahan state,
   jadi tooltipnya ikut tanpa handler khusus.
9. **Yang TIDAK ikut diterjemahkan.** pygame sendiri menyimpan beberapa teks
   apa adanya, dan port mengikutinya: `ITEM FORGE  (%d/6)`, `TIER I/II`,
   `SHIELD n%` di atas kastil, `AUTO-CAST ON`, `MAX LEVEL`, `Lv.%d`, baris
   `VICTORY!`/`DEFEAT` + lima nama statistik layar hasil, dan judul badge HUD
   `LEVEL n`/`WAVE n` (dikunci `UiHudParityTest` + `HudLayout.wave_title`).
   Dari sisi menu, yang TIDAK diberi kunci karena memang sudah Inggris di kedua
   bahasa: "MYSTIC ARENA", "v2.0 • MOBA Tower Defense", "BATTLE ARENA",
   "INPUT", "HERO SHOP", "TOP UP", "HERO GOLD", "BOSSES DEFEATED", "SAVE GAME",
   "LV. %d", "%s Gold", "Hero: %d", "Boss: %d", "LEVEL %d", "ATTEMPT",
   "WIN RATE", "PAUSED", badge OWNED/LOCKED kartu hero, "TRUE BOSS"/"MINI
   BOSS"/"STARTER", dan blok teks CREDITS. Dua label kartu ITEM FORGE yang di
   pygame juga literal — "MELEE ONLY"/"MAGIC ONLY" — sengaja tetap literal
   (`ShopPanel._item_card_label`).
   Teks Godot yang diberi pasangan id/en padahal pygame tidak men-`tr()`-nya:
   `shop_buy_for` ("BELI UNTUK:" / "BUY FOR:"), `shop_card_*`, `pause_*`,
   `howto_*`, `slot_*`, `lvl_*`, `hshop_*`, `set_*`, `tac_*`, `topup_*`,
   `rail_pause_tip` — permukaan itu teks Indonesia buatan port yang harus ikut
   English.

## Kunci yang sudah punya pemakai vs yang masih menunggu

Dilaporkan oracle setiap run (baris `[oracle] pemakai tr_text()/loc() di
Godot:` — audit closed-world yang juga menangkap pintasan `_loc()` per panel,
jadi kunci salah ketik di jalur itu tetap gagal di CI):

- **Hidup sekarang (179):** SELURUH menu utama (103 kunci `menu_*`, `slot_*`,
  `lvl_*`, `hshop_*`, `set_*`, `howto_*`, `pause_*`) + seluruh teks ShopPanel
  dan label kartu `ItemForgeCard`, baris hint HUD, label/tooltip SkillBar,
  tombol + hint GameOverOverlay, subtitle TopupDialog, tooltip pause rail, dan
  `dead`/`shop_no_hero_banner` di tab ITEM. Ditambah jalur non-kunci:
  `is_english()` untuk `ItemDB.item_mechanics_localized` dan
  `ItemDB.item_desc_localized`. Kunci yang dipakai lewat konstanta —
  `shop_tab_*` (ShopPanel `TABS`) dan `tac_*` (TacticalBar `TOOLTIPS`) — muncul
  sebagai "belum ada pemakainya" di audit literal: sengaja, karena labelnya
  harus berganti bersama tab/aksinya, dan keabsahannya tetap dijaga fixture +
  tes di engine.
- **Diport sebagai data, pemakainya belum ada di Godot (25):**
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
| `queued`, `queued_item_count`, `dead_delivery_hint`, `shop_no_hero_yet`, `shop_page_label` | `ItemShopUI.draw` (antrean item, hint pengiriman, banner "ketik H dulu", HAL n) | `ShopPanel.gd` tab ITEM adalah Control UI sendiri (satu scroll, tanpa halaman) dan TIDAK punya antrean Item Forge, jadi chip hero mati menampilkan status `dead` saja (diklik: disabled + tooltip `shop_dead_no_forge`). Yang SUDAH hidup: `dead` (chip strip BUY FOR) + `shop_no_hero_banner` (tanpa hero katalog tetap tampil, persis pygame) — deviasi antrean tercatat di `GODOT_PARITY.md` |
| `item_card_detail_hint`, `item_detail_*`, `item_inventory_hint` | Popup detail item Forge (deskripsi + stat + riwayat) | Popup detail belum diport; `ItemDB.item_mechanics_localized()` sudah siap sebagai sumber baris "STAT & EFEK"-nya |

## Verifikasi

```bash
# 1. Oracle TANPA engine (detik): tabel GDScript == localization.py,
#    audit placeholder, closed-world kunci tr_text()/loc(), fixture segar.
python3 tools/test_godot_localization_parity.py
#    regenerasi fixture HANYA kalau localization.py berubah:
python3 tools/test_godot_localization_parity.py --write-fixture

# 2. Parser GDScript asli (gdtoolkit) + lint scene/referensi repo
gdparse godot/scripts/utils/Localization.gd godot/tests/LocalizationParityTest.gd
python3 godot/tools/map_clutter_lint.py godot
python3 godot/tools/tscn_lint.py godot/tests/LocalizationParityTest.tscn
python3 godot/tools/check_refs.py godot

# 3. Replay fixture di engine (CI yang menjalankan; user:// terisolasi)
export XDG_DATA_HOME="$(mktemp -d)"
godot --headless --path godot res://tests/LocalizationParityTest.tscn --quit-after 120
#    wajib: "[LocalizationParityTest] PASS" tanpa SCRIPT ERROR / Parse Error
```

Gate "semua layar menu ikut bahasa" (`_test_menu_surfaces_localized`,
FASE 40): tiap state `MainMenu` — MAIN, SLOT_SELECT, LEVEL_SELECT, HERO_SHOP,
SETTINGS, HOW_TO_PLAY, CREDITS, PAUSE — dibangun dua kali (`en` lalu `id`) di
atas instance baru, SEMUA teks yang tergambar dikumpulkan dari `_root` +
panel PAUSE (Label/Button/RichTextLabel), dinormalisasi (huruf besar, spasi
dibuang — supaya `UiTheme.letter()` tidak mengecoh), lalu

- sentinel per layar harus ADA di bahasa yang benar. Sentinelnya literal di
  dalam tes, BUKKAN dibaca dari tabel — jadi "menerjemahkan" tabel dengan
  memindahkan teks Indonesia ke kolom `en` tetap gagal; dan
- di mode `en` tidak boleh ada satu pun teks yang sama persis dengan nilai
  `id` yang beda dari nilai `en` (himpunan larangan dibangun dari fixture;
  kunci ber-placeholder dilewati karena teksnya terformat).

Isi fixture `localization.json` (semuanya dievaluasi `localization.py` ASLI,
bukan salinan):

| Seksi | Isi |
|---|---|
| `text` / `key_order` | 209 kunci × 2 bahasa + urutannya (urutannya ikut dikunci: sisip kunci di satu file saja = gagal) |
| `languages` / `labels` / `default_language` | `LANGUAGES`, `LANGUAGE_LABELS`, `"id"` |
| `placeholders` | daftar `{nama}` per kunci (kontrak subset `_py_format`) |
| `tr_cases` | 418 = setiap kunci × setiap bahasa dengan nilai contoh (`hero`/`item`/`items`/`count`/`page`) |
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
   menulis teks dua kali. Panel dengan banyak situs pemanggil boleh menambah
   pintasan `func _loc(key) -> String: return MysticLocalization.tr_text(key)`
   (pola ShopPanel/SkillBar/GameOverOverlay/HUD) — audit closed-world oracle
   mengikuti `_loc()`/`loc()` juga, jadi pintasan tidak menutupi typo.
6. Angka yang dihitung di call site TIDAK lewat `{placeholder}`: pakai
   `%d`/`%s`/`%.2f` di template lalu `template % [a, b]` (subset `str.format`
   oracle hanya mengenal `{nama}` dengan contoh baku). Hati-hati: template
   yang mengandung `%` literal harus `%%`, dan jangan pernah memakai `%` pada
   template yang belum di-escape (mis. `shop_tower_sell_note` "Refund 50%
   dari…" dipakai apa adanya, tanpa format).
