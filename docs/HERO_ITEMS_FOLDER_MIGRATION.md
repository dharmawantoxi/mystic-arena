# Migrasi `hero_items.py` ke Godot

`hero_items.py` (4133 baris) adalah **satu modul raksasa** yang memuat hampir seluruh sistem item Mystic Arena: katalog 33 item, 25 kategori + warna/labelnya, kelas toko (PHYSICAL/MAGIC/TANK), tracker miasma, inventory per-hero (`HeroItemInventory`), aura & helper item tingkatan hero, saran item untuk AI, renderer strip 6 slot (`HeroItemRenderer`), panel ITEM FORGE (`ItemShopUI`) dan router klik `handle_item_shop_click` beserta SFX-nya.

Porting-nya tidak dimulai di layer ini: jembatan item sudah dibangun bertahap di layer **5d–5f** (`hero_items.gd`, `hero_item_inventory.gd`, `item_effects.gd`, `battle_item_effects.gd`, `ai_items.gd`, `forge.gd`, `item_shop_ui.gd`, `item_forge_panel.gd`, `hero_panel_layout.gd` + 17 oracle/fixture item yang lebih tua). Yang **belum** ada sebelum layer **9ck** adalah dua hal yang justru paling terlihat pemain:

1. **Teks popup detail item** — sumber menyusun `[STAT]` / `[AKTIF] Blood Frenzy` + baris `• Label: nilai` berformat persen/detik dalam dua bahasa (`_build_item_mechanics`, `_fmt_mech_value`, `_FIELD_LABELS`, `_GROUP_LABELS`, `_MECH_GROUPS`, `_PCT_KEYS`, `_FRAME_KEYS`); rebuild hanya mencetak dict mentah (`Damage: 52, Crit Chance: 0.25, Duration: 180`).
2. **Klasifikasi eksplisit seluruh berkas** — 98 callable/kelas + 47 konstanta modul harus dinyatakan satu per satu (ported / data / folded / deviation / dead) dengan bukti target + token, bukan "sudah ada di beberapa modul".

Layer ini menutup keduanya, plus tiga celah perilaku klik/SFX yang ditemukan saat membandingkan `handle_item_shop_click` dengan `item_shop_ui.gd`.

Sumber kebenaran: `godot_rebuild/tests/hero_items_source_oracle.py` (mengeksekusi `hero_items.py` lewat `ai_item_source_oracle.source_namespace`). Fixture: `tests/fixtures/hero_items_source.json`. Data hasil bake: `godot_rebuild/data/ui/item_mechanics.json`. Suite native: `tests/hero_items_checks.gd`.

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `hero_items.py` | 4133 |
| Banner seksi (`# ═══ / judul / ═══`) | 8 (+ header katalog 1–1653) |
| Kelas | 3 (`HeroItemInventory` 44 metode, `ItemShopUI` 16, `HeroItemRenderer` 3) |
| Fungsi modul | 32 |
| Assign modul | 47 |
| Simbol terklasifikasi | 98 callable/kelas + 47 konstanta = **145 baris** |
| Item di `ITEM_CATALOG` | 33 (25 kategori) |
| Halaman toko | 6 (2 per kelas, `ITEMS_PER_PAGE` 8) |
| Baris mekanik popup | 600 (33 item × 2 bahasa) |
| Baris format nilai | 157 pasangan (key, nilai) |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 95 | fungsi/kelas yang punya padanan native (lihat tabel §4) |
| `data` | 43 | tabel/konstanta yang dipanggang ke `.json` / `.gd` |
| `folded` | 1 | `ITEM_SHOP_ORDER` dilipat ke `pages` (`_build_shop_pages`) |
| `deviation` | 3 | `_get_game`, `_ITEMS_DIR`, `_ICON_CACHE` (D1, D2) |
| `dead` | 3 | `HeroItemInventory.is_guarding`, `HeroItemRenderer.slot_index_at`, `_alive_player_heroes` (D4, D5) |

## 2. Peta seksi

| Seksi | Baris | Isi |
| --- | --- | --- |
| *(header, tanpa banner)* | 1–1653 | konstanta kategori, `MAGIC_ROLE_KEYWORDS`, `_MIASMA`, `ITEM_CATALOG`, kelas toko, `CATEGORY_INFO`, tabel label mekanik |
| `ICON LOADING & CACHE` | 1654–1701 | `_ITEMS_DIR`, `_ICON_CACHE`, `get_icon` |
| `INVENTARY per-hero` | 1705–2743 | `HeroItemInventory` (stat, tick, proc, miasma) |
| `Helper level multiplier` | 2747–2755 | `_hero_level_mult` |
| `AURA UPDATE` | 2759–2931 | `update_auras`, `_collect_all_units`, `_apply_stun_to` / `_apply_silence_to` / `_apply_shred_to` / `_apply_amp_to`, `_fx_notify` / `_fx_chain` |
| `AI HELPER: saran item untuk hero` | 2935–3001 | `suggest_item_for_hero` |
| `UI: RENDERER 6 SLOT di HeroPanel` | 3005–3187 | `HeroItemRenderer` (`width`, `draw`, `slot_index_at`) |
| `UI: ITEM SHOP OVERLAY` | 3191–3914 | `ItemShopUI` + `_build_item_mechanics` + `_fmt_mech_value` |
| `CLICK HANDLER untuk ItemShopUI` | 3918–4133 | `_touch_hit`, `handle_item_shop_click`, `_try_buy`, `_try_drop`, `_notify`, `_play_click/_buy/_error` |

## 3. Artefak baru

| Berkas | Isi |
| --- | --- |
| `scripts/match/item_mechanics.gd` | port `_FIELD_LABELS` (65), `_GROUP_LABELS` (8), `_MECH_GROUPS` (8, urutan sumber), `_PCT_KEYS` (28), `_FRAME_KEYS` (11), `fmt_value` (port `_fmt_mech_value`), `build` (port `_build_item_mechanics`) |
| `data/ui/item_mechanics.json` | delapan grup mekanik tiap item, verbatim dari katalog + urutan sumber |
| `tests/hero_items_source_oracle.py` | oracle: inventaris berkas, 145 klasifikasi, katalog/kelas/halaman, tabel label, 157 baris format, 600 baris mekanik (id + en), gerbang magic |
| `tests/fixtures/hero_items_source.json` | fixture hasil oracle |
| `tests/hero_items_checks.gd` | suite native (didaftarkan di `tests/run_all.gd`) |

`item_mechanics.gd` meniru `f"{value:g}"` Python: enam digit signifikan, nol ekor dibuang, persen ×100, frame ÷60 lalu `dtk`/`s`, dan `x` untuk `crit_mult`. `_plain()` mempertahankan bentuk Python `str()` (int tetap int, bool `True`/`False`, list `[a, b]`).

Pemakaian di UI: `scripts/ui/item_forge_panel.gd` kini membaca `data/ui/item_mechanics.json` dan merender hasil `ItemMechanics.build(groups, en)` — header grup + bullet — di dua kolom popup detail, menggantikan dump dict mentah. Bahasa diambil dari node `Localization` (`language`), fallback ke locale OS; teks deskripsi memakai jalur yang sama.

## 4. Klasifikasi simbol (ringkas per tujuan)

Semua 145 baris (dengan target + token) ada di `tests/fixtures/hero_items_source.json` → `classification`; validator memastikan setiap token benar-benar ada di berkas tujuan.

| Kelompok | Tujuan native | Contoh simbol |
| --- | --- | --- |
| Stat + tick inventory (41) | `scripts/match/hero_item_inventory.gd` | `get_bonus_damage`…`get_rend_crit`, `tick_timers` (=`update`), `tick_auto`, `notify_damage_taken`, `roll_crit`, `on_basic_attack_hit`, `_on_hit_common`, `on_ranged_attack_hit`, `add`, `remove`, `clear_on_death`, `sum_stat` (=`_sum_stat`) |
| Helper & efek global | `hero_item_inventory.gd`, `battle_item_effects.gd`, `item_effects.gd`, `prototype_battle.gd` | `apply_miasma`, `tick_miasma`, `level_hp_mult`, `update_auras`→`_update_auras`, `_collect_all_units`, `_apply_stun_to`, `_apply_silence_to`, `apply_armor_shred`, `apply_damage_amp`, `notify`, `chain_fx` |
| Gating & saran | `hero_items.gd` | `is_magic_hero`, `suggest_item_for_hero` |
| Toko & pembelian | `item_shop_ui.gd`, `forge.gd` | `item_class`, `_build_shop_pages`, `handle_click`, `resolve_target`, `buy`, `drop`, `pending_forge_items`, `deliver_pending_forge_items`, `_player_heroes`, `notice_text` |
| Popup & format | `item_mechanics.gd` | `fmt_value`, `build` |
| Renderer strip | `scripts/ui/hero_panel_layout.gd` | `item_slot_rect` (=`width`), `_item_slots` (=`draw`), `_draw_item_icon` |
| Panel Forge | `scripts/ui/item_forge_panel.gd` | `_build_chrome`, `_build_hero_chips`, `_build_page_tabs`, `_build_cards`, `_build_slots`, `_build_detail_content`, `_refresh_detail`, `_description`, `_icon`, `AUTOWRAP_WORD_SMART` (=`_wrap_text`) |
| Konstanta (43) | `data/ai/item_catalog.json`, `data/ui/item_shop_presentation.json`, `item_shop_ui.gd`, `item_mechanics.gd`, `hero_items.gd` | `ITEM_CATALOG`, `ITEM_FLAT_COST`, `MAX_ITEM_SLOTS`, 25 `CATEGORY_*`, `CATEGORY_INFO`, `CLASS_*`, `ITEM_CLASS_INFO`, `_ITEM_CLASS_OVERRIDES`, `_MAP_CATEGORY_TO_CLASS`, `ITEMS_PER_PAGE`, `CLASS_ITEM_ORDER`, tabel mekanik |

## 5. Deviasi terdokumentasi

| Kode | Simbol | Deviasi | Alasan |
| --- | --- | --- | --- |
| D1 | `_get_game` | tidak ada singleton `game` global; `world`/battle diteruskan eksplisit | struktur scene Godot tidak memakai modul global Pygame |
| D2 | `_ITEMS_DIR`, `_ICON_CACHE`, `get_icon` | ikon dipanggang ke `assets/art/items/*.png` dan dimuat `ResourceLoader` (`_icon()`), tanpa cache manual | aset diekspor, cache mesin menggantikan dict `_ICON_CACHE` |
| D3 | 3 baris `hp_regen` (`2.0`, `3.0`, `6.0`) | dicetak `2` / `3` / `6`, bukan `2.0` / `3.0` / `6.0` | angka JSON kehilangan pembeda int/float; hanya 3 baris, tercatat di `FLOAT_SUFFIX_DEVIATIONS` |
| D4 | `HeroItemRenderer.slot_index_at` | tidak diport | **tidak pernah dipanggil** di sumber Pygame (dead code) |
| D5 | `HeroItemInventory.is_guarding`, `_alive_player_heroes` | tidak diport | tidak pernah dipanggil di sumber |
| D6 | `_notify` teks `BUY FOR: {hero.name}` | `BUY FOR: hero {id}` (+ sufiks `delivery after respawn`) | hero rebuild belum menyimpan nama tampilan |

`update_auras` hanya dibandingkan lewat angka (bukan urutan gambar), `_wrap_text` diganti `TextServer.AUTOWRAP_WORD_SMART` (pembungkusan teks native), dan `_touch_hit` (hit-test 48 px) diganti hit-test Control Godot — keduanya sudah tercatat sebagai `ported` karena hasil interaksinya sama.

## 6. Perilaku klik & SFX (diperbaiki di layer ini)

| Perilaku sumber | Sebelum 9ck | Sesudah |
| --- | --- | --- |
| Ketuk kartu yang sama menutup popup detail | selalu membuka | toggle (`inspect_item = "" if sama`) |
| Klik kanan di mana pun menutup Forge | hanya di luar panel | menutup di dalam panel juga, kecuali di slot terisi (drop) |
| `_play_click` / `_play_buy` / `_play_error` | tidak ada SFX | `ItemShopUI.last_sound` = `ui_click` / `ui_buy` / `ui_error`, diputar `_play_sound()` dengan `volume_mult` 0.4 / 0.6 / 0.4 |
| `_try_buy` memainkan error untuk setiap penolakan | senyap | `forge.buy()` mengisi `result["sound"]` (`ui_error` untuk no-hero/gold/slot penuh/gate/gagal pasang, `ui_buy` untuk sukses, senyap untuk id tak dikenal) |

## 7. Cara menjalankan

```bash
python3 godot_rebuild/tests/hero_items_source_oracle.py --write   # tulis ulang fixture + data
python3 godot_rebuild/tests/hero_items_source_oracle.py           # cek sinkron dengan sumber
python3 godot_rebuild/tests/validate_project.py                   # blok 9ck + seluruh validator
godot --headless --script tests/run_all.gd                        # suite native (PC/CI, bukan sandbox)
```

`hero_items_checks.gd` memverifikasi: inventaris 4133 baris / 8 seksi / 3 kelas / 32 fungsi / 63 metode / 47 assign / 98 simbol, 145 klasifikasi + token hidup, 3 dead + 3 deviation, katalog 33 item + 25 kategori + 6 halaman + 2 override + daftar MAGIC_ONLY, 65 label field / 8 label grup / 28 kunci persen / 11 kunci frame, 157 baris format (6 toleransi D3), 600 baris mekanik id+en, dan gerbang `is_magic_hero` (termasuk pengecualian "Anti-Mage").

## 8. Status paritas

Yang terbukti di layer ini: seluruh 145 simbol punya klasifikasi + target/token hidup, dan teks popup detail item kini identik dengan sumber pada 600 baris (kecuali 3 baris D3 yang tercatat). Yang **belum** terbukti: tampilan piksel panel Forge, perilaku input di perangkat Android, dan audio di hardware — memerlukan run Godot + screenshot seed/state sama serta uji perangkat seperti kriteria paritas proyek. Validator statis dan keberadaan data **bukan** bukti paritas.
