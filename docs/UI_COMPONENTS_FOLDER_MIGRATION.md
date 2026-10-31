# Migrasi Folder `ui_components/` ke Godot (Layer 9ce)

Folder oracle `ui_components/` (read-only) berisi **2 berkas / 4.300 baris**:
`_bundle.py` (4.160 baris, 11 modul komponen digabung) dan `__init__.py` (140 baris shim
`sys.modules`). Layer 9ce mengklasifikasikan **seluruh 122 simbol**, mem-port dua bagian
yang belum ada (**toolbox `BaseUIComponent`** dan **popup tower `PopupRenderer`**), dan
mengunci semuanya dengan oracle sumber + suite native.

Ringkasan hasil

| Item | Nilai |
| --- | --- |
| Berkas folder | 2 (`_bundle.py` 4.160, `__init__.py` 140) |
| Modul gabungan | 11 |
| Simbol terklasifikasi | 122 (11 modul, 14 kelas, 88 metode, 9 helper) |
| `native` | 17 |
| `ported` | 80 |
| `bake` | 5 |
| `dead` | 13 |
| `meta` | 6 |
| `deviation` | 1 |
| Frame popup tower di oracle | 10 frame, 253 op, 32 tombol |
| Berkas Godot baru | `scripts/ui/ui_component_base.gd`, `scripts/ui/tower_popup_layout.gd`, `data/towers/upgrade_paths.json` |

## 1. Peta modul di `_bundle.py`

| # | Modul | Baris | Isi |
| --- | --- | --- | --- |
| 1 | `base_ui` | 43-191 (149) | Toolbox `BaseUIComponent` + `_popup_di_panel`. Layer ini mem-port `_draw_shadow_rect`, `_draw_hp_bar`, `_draw_close_button`, `panel_position`. |
| 2 | `hero_portraits` | 192-662 (471) | `HeroPortraits` (statis, dipanggil `_core.py:5119`) merender potret toko hero; Godot sudah punya `hero_portrait.gd` + 40+ painter per-hero. |
| 3 | `build_popup` | 663-853 (191) | `BuildPopup.draw` + `_draw_tower_buttons` sudah native sejak 9bv7 (`build_popup_layout.gd`). |
| 4 | `build_slots` | 854-1057 (204) | `BuildSlots` di-bake ke atlas (`bake/bake_slot_atlas.py`) lalu digambar `slot_art.gd`. |
| 5 | `hero_panel` | 1058-1532 (475) | `HeroPanel` (skill slot, autocast, item shop, upgrade) sudah native sejak 9bv8 (`hero_panel_layout.gd`). |
| 6 | `hero_shop` | 1533-2534 (1002) | `HeroShop` digantikan Control node `hero_shop_panel.gd` / `hero_shop_card.gd`; painter op-level di-supersede. |
| 7 | `hover_indicators` | 2535-2764 (230) | `tower_hover_layout.gd` (9bv11) + `slot_hover_layout.gd` (9bv12) + `prototype_view.gd`. |
| 8 | `notification` | 2765-2790 (26) | Sistem notifikasi **dihapus** di sumber: `_core.UI.add_notification` no-op dan `draw_notifications` langsung `return`. |
| 9 | `overlay` | 2791-3537 (747) | `Overlay` (victory/defeat, unlock popup) sudah native sejak 9bv5/9bv10 (`end_overlay_layout.gd`). |
| 10 | `popup_renderer` | 3538-4071 (534) | `PopupRenderer`: cabang nexus sudah ada di `castle_panel_layout.gd`; **cabang tower** diport layer ini ke `tower_popup_layout.gd`. |
| 11 | `shop_hints` | 4072-4160 (89) | `ShopHints` sudah native sejak 9bv3 (`shop_hint_layout.gd`). |

Blok-blok itu bersambung tanpa celah (43-191, 192-662, ... 4072-4160); 42 baris pertama
adalah header + impor (`pygame`, `math`, `settings *`, `ui_theme`, guard `get_font`/`title_font`).

## 2. Oracle sumber

`tests/ui_components_source_oracle.py` memanen sumber dengan `ast` lalu **menjalankan kode asli**:

| Langkah | Sumber yang dijalankan | Hasil di fixture |
| --- | --- | --- |
| Inventaris | AST `_bundle.py` + `__init__.py` | 122 simbol, peta baris, konstanta, stub |
| Toolbox | `BaseUIComponent._draw_shadow_rect` / `_draw_hp_bar` / `_draw_close_button` | 3+7+5 kasus op |
| Panel | `_popup_di_panel` + `mobile.platform_utils.panel_popup_pos` | 5 kasus (dalam/luar panel) |
| Popup | `PopupRenderer.draw` dengan `popup_type == "tower"` | 10 frame (10 skenario) |
| Specials | `PopupRenderer._get_tower_specials` | 6 kasus |

`ui_theme.pill`, `hp_bar`, `draw_icon` dan `corner_ticks` direkam **satu op per panggilan**
(kode `ui_theme.py` sudah diport di layer lain), sedangkan `PopupRenderer` dan
`BaseUIComponent` berjalan tanpa modifikasi di atas shim `pygame` perekam
(`tests/draw_recorder.py`).

## 3. Klasifikasi seluruh simbol

| Simbol | Kind | Target | Catatan |
| --- | --- | --- | --- |
| `module:base_ui` | native | scripts/ui/ui_component_base.gd |  |
| `module:hero_portraits` | ported | scripts/ui/hero_portrait.gd | baked/native portrait painters take (id, definition) instead of a fake entity |
| `module:build_popup` | ported | scripts/ui/build_popup_layout.gd |  |
| `module:build_slots` | bake | bake/bake_slot_atlas.py |  |
| `module:hero_panel` | ported | scripts/ui/hero_panel_layout.gd |  |
| `module:hero_shop` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `module:hover_indicators` | ported | scripts/ui/tower_hover_layout.gd |  |
| `module:notification` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `module:overlay` | ported | scripts/ui/end_overlay_layout.gd |  |
| `module:popup_renderer` | native | scripts/ui/tower_popup_layout.gd | this layer ports the tower popup frame + content |
| `module:shop_hints` | ported | scripts/ui/shop_hint_layout.gd |  |
| `_bundle:_popup_di_panel` | native | scripts/ui/ui_component_base.gd |  |
| `bundle_alias:HeroPortraits` | meta | - | re-export of the hero_portraits class into hero_panel |
| `base_ui:BaseUIComponent` | native | scripts/ui/ui_component_base.gd |  |
| `base_ui:BaseUIComponent.__init__` | native | scripts/ui/ui_component_base.gd |  |
| `base_ui:BaseUIComponent._draw_close_button` | native | scripts/ui/ui_component_base.gd |  |
| `base_ui:BaseUIComponent._draw_hp_bar` | native | scripts/ui/ui_component_base.gd |  |
| `base_ui:BaseUIComponent._draw_shadow_rect` | native | scripts/ui/ui_component_base.gd |  |
| `base_ui:BaseUIComponent.draw` | meta | - | abstract hook; Godot uses op builders |
| `hero_portraits:HeroPortraits` | ported | scripts/ui/hero_portrait.gd | baked/native portrait painters take (id, definition) instead of a fake entity |
| `hero_portraits:HeroPortraits.draw` | ported | scripts/ui/hero_portrait.gd | baked/native portrait painters take (id, definition) instead of a fake entity |
| `hero_portraits:HeroPortraits._try_auto_render` | ported | scripts/ui/hero_portrait.gd |  |
| `hero_portraits:HeroPortraits._try_boss_renderer` | ported | scripts/ui/hero_portrait.gd |  |
| `hero_portraits:HeroPortraits._try_hero_renderer` | ported | scripts/ui/hero_portrait.gd |  |
| `hero_portraits:HeroPortraits._crop_and_scale` | ported | scripts/ui/hero_portrait.gd |  |
| `hero_portraits:HeroPortraits._apply_grayscale` | deviation | - | un-owned portrait desaturation is not reproduced; the locked card tint carries the state (see doc, deviation D1) |
| `hero_portraits:HeroPortraits.clear_cache` | meta | - | no portrait cache in Godot |
| `hero_portraits:HeroPortraits._draw_generic` | ported | scripts/ui/hero_portrait_generic.gd |  |
| `hero_portraits:_FakeEntity` | ported | scripts/ui/hero_portrait.gd | baked/native portrait painters take (id, definition) instead of a fake entity |
| `hero_portraits:_FakeEntity.__init__` | ported | scripts/ui/hero_portrait.gd | baked/native portrait painters take (id, definition) instead of a fake entity |
| `hero_portraits:_make_fake_boss` | ported | scripts/ui/hero_portrait.gd | baked/native portrait painters take (id, definition) instead of a fake entity |
| `hero_portraits:_make_fake_hero` | ported | scripts/ui/hero_portrait.gd | baked/native portrait painters take (id, definition) instead of a fake entity |
| `build_popup:BuildPopup` | ported | scripts/ui/build_popup_layout.gd |  |
| `build_popup:BuildPopup.draw` | ported | scripts/ui/build_popup_layout.gd |  |
| `build_popup:BuildPopup._draw_tower_buttons` | ported | scripts/ui/build_popup_layout.gd |  |
| `build_slots:BuildSlots` | bake | bake/bake_slot_atlas.py |  |
| `build_slots:BuildSlots.draw` | bake | bake/bake_slot_atlas.py |  |
| `build_slots:BuildSlots._render_blue_slot_surface` | bake | bake/bake_slot_atlas.py |  |
| `build_slots:BuildSlots._render_red_slot_surface` | bake | bake/bake_slot_atlas.py |  |
| `build_slots:BuildSlots._draw_blue_slot` | ported | scripts/ui/slot_art.gd |  |
| `build_slots:BuildSlots._draw_red_slot` | ported | scripts/ui/slot_art.gd |  |
| `hero_panel:HeroPanel` | ported | scripts/ui/hero_panel_layout.gd |  |
| `hero_panel:HeroPanel.draw` | ported | scripts/ui/hero_panel_layout.gd |  |
| `hero_panel:HeroPanel._draw_item_shop_button` | ported | scripts/ui/hero_panel_layout.gd |  |
| `hero_panel:HeroPanel._draw_upgrade_button` | ported | scripts/ui/hero_panel_layout.gd |  |
| `hero_panel:HeroPanel._draw_autocast_toggle` | ported | scripts/ui/hero_panel_layout.gd |  |
| `hero_panel:HeroPanel._skill_key_label` | ported | scripts/ui/hero_panel_layout.gd |  |
| `hero_panel:HeroPanel._draw_skill_slot` | ported | scripts/ui/hero_panel_layout.gd |  |
| `hero_panel:_FakeEntity` | dead | - | panel copy of the portrait fake entity |
| `hero_panel:_FakeEntity.__getattr__` | dead | - | panel copy of the portrait fake entity |
| `hero_panel:_make_fake_boss` | dead | - | panel copy of the portrait fake entity |
| `hero_panel:_make_fake_hero` | dead | - | panel copy of the portrait fake entity |
| `hero_shop:HeroShop` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop.draw` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._render_shop` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_overlay` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_panel` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_header` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_title` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_gold_info` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_owned_info` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_shop_close_button` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_hero_cards` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_compact_card` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_scroll_indicator` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_card` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_card_bg` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_card_border` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_card_portrait` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_card_info` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_card_stats` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_card_skill` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_card_button` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_button_owned` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_button_max` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_button_buy` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hero_shop:HeroShop._draw_button_cant_afford` | ported | scripts/ui/hero_shop_panel.gd | Control nodes paint the card; the op painter itself is superseded |
| `hover_indicators:HoverIndicators` | ported | scripts/ui/tower_hover_layout.gd |  |
| `hover_indicators:HoverIndicators.update` | ported | scenes/prototype/prototype_view.gd |  |
| `hover_indicators:HoverIndicators.draw` | ported | scenes/prototype/prototype_view.gd |  |
| `hover_indicators:HoverIndicators._draw_tower_range_hover` | ported | scripts/ui/tower_hover_layout.gd |  |
| `hover_indicators:HoverIndicators._draw_tower_tooltip` | ported | scripts/ui/tower_hover_layout.gd |  |
| `hover_indicators:HoverIndicators._draw_slot_hover` | ported | scripts/ui/slot_hover_layout.gd |  |
| `hover_indicators:Notification` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `hover_indicators:Notification.__init__` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `hover_indicators:Notification.add_notification` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `hover_indicators:Notification.draw` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `notification:Notification` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `notification:Notification.__init__` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `notification:Notification.add_notification` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `notification:Notification.draw` | dead | - | source disabled notifications (``_core.UI.add_notification`` is a no-op) |
| `overlay:Overlay` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay.__init__` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay.draw` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._update_unlock_popup` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._get_newly_unlocked_level` | ported | scenes/prototype/prototype_screen.gd |  |
| `overlay:Overlay._draw_rays` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._draw_central_glow` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._draw_title` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._draw_sparkles` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._draw_stats` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._draw_level_unlock_popup` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._draw_action_hint` | ported | scripts/ui/end_overlay_layout.gd |  |
| `overlay:Overlay._draw_achievements` | ported | scripts/ui/end_overlay_layout.gd |  |
| `popup_renderer:PopupRenderer` | native | scripts/ui/tower_popup_layout.gd | this layer ports the tower popup frame + content |
| `popup_renderer:PopupRenderer.draw` | native | scripts/ui/tower_popup_layout.gd | this layer ports the tower popup frame + content |
| `popup_renderer:PopupRenderer._draw_nexus_content` | ported | scripts/ui/castle_panel_layout.gd |  |
| `popup_renderer:PopupRenderer._draw_castle_shield_section` | ported | scripts/ui/castle_panel_layout.gd |  |
| `popup_renderer:PopupRenderer._draw_nexus_upgrade` | ported | scripts/ui/castle_panel_layout.gd |  |
| `popup_renderer:PopupRenderer._draw_tower_content` | native | scripts/ui/tower_popup_layout.gd | this layer ports the tower popup frame + content |
| `popup_renderer:PopupRenderer._draw_regen_shield_section` | native | scripts/ui/tower_popup_layout.gd |  |
| `popup_renderer:PopupRenderer._get_tower_specials` | native | scripts/ui/tower_popup_layout.gd |  |
| `popup_renderer:PopupRenderer._draw_tower_max_level` | native | scripts/ui/tower_popup_layout.gd |  |
| `popup_renderer:PopupRenderer._draw_tower_path_buttons` | native | scripts/ui/tower_popup_layout.gd |  |
| `popup_renderer:PopupRenderer._draw_single_path_button` | native | scripts/ui/tower_popup_layout.gd |  |
| `popup_renderer:PopupRenderer._draw_tower_upgrade_button` | native | scripts/ui/tower_popup_layout.gd |  |
| `shop_hints:ShopHints` | ported | scripts/ui/shop_hint_layout.gd |  |
| `shop_hints:ShopHints.draw` | ported | scripts/ui/shop_hint_layout.gd |  |
| `shop_hints:ShopHints._draw_single_hint` | ported | scripts/ui/shop_hint_layout.gd |  |
| `shim:_EXTRA` | meta | - | sys.modules shim for the 10 merged namespaces |
| `shim:_PLAIN_SYMS` | meta | - | sys.modules shim for base_ui |
| `shim:_install_aliases` | meta | - | no shim needed: Godot has real modules |

## 4. Toolbox `BaseUIComponent` -> `scripts/ui/ui_component_base.gd`

| Sumber | Perilaku yang dikunci oracle |
| --- | --- |
| `_draw_shadow_rect` | Satu rect hitam `alpha` pada rect aslinya; offset sumber saling meniadakan. 3 kasus. |
| `_draw_hp_bar` | Track `(40,0,0)`, isi `int(w*ratio)` dengan GREEN >50 persen, YELLOW >25 persen, RED sisanya, border putih 1 px. 7 kasus termasuk `ratio` 0, 1.8 dan `show_bg=False`. |
| `_draw_close_button` | Varian `rect` (merah, hover `(255,60,60)` + border 2) dan `circle` (glow `(255,80,80,100)` radius +3, dua garis X). 5 kasus. |
| `_popup_di_panel` | `panel_popup_pos(w,h)`: `w > panel_w - 8` -> tidak muat, `x` di tengah panel, `y = max(12, min(h_panel - h - 12, (h_panel - h)/2))`. 5 kasus. |

`_draw_shadow_rect` tercatat **tidak pernah dipanggil** oleh folder ini (lihat bagian 6).
`_draw_close_button` dipakai ulang oleh popup tower; `build_popup_layout.gd` (9bv7)
menginline versi 22 px-nya, jadi keduanya kini sepakat lewat test.

## 5. Popup tower -> `scripts/ui/tower_popup_layout.gd`

`PopupRenderer.draw` untuk `popup_type == "tower"` memuat seluruh alur popup:

| Tahap | Detail yang dikunci |
| --- | --- |
| Geometri panel | `popup_w = 380` di-clamp `min(380, panel_w - 16)`, `popup_h = 440`. |
| Relokasi dock | `panel_position`; bila muat -> `px, py` dari panel dan **tanpa** garis konektor. |
| Jangkar peta | `px = tx - popup_w/2`, `py = ty - 440 - 40`, lalu 4 clamp (kiri/kanan `10`, atas `TOP_BAR_HEIGHT+10`, bawah `720-10`). |
| Bingkai | `cheap_alpha` -> shadow `alpha 150` + `_vgrad (34,40,68)->(16,19,36)` r10; flat -> rect `(25,30,45)`. Border emas 2 px + `corner_ticks` `(255,233,158)` panjang 12. |
| Close | `_draw_close_button(px + popup_w - 26, py + 6, 22, 'popup_close', 'rect')`. |
| Judul | `"{name} Lv.{n}"`, fallback `"Lv.{n} {type.title()}"` bila > `popup_w - 90`, warna `min(255, c+40)`. |
| HP | Label `HP: {int}/{max}` 18 px di `py+46`, bar `(popup_w-30, 8)` di `py+70`, warna 120/255/100 per rasio. |
| Statistik | `DMG … Range …` dan `Kills … Lane …` 18 px `TEXT_DIM`, langkah 21 px, lalu specials `" | "` `GOLD_TEXT` langkah 22 px. |
| Tower musuh | Baris `Enemy Tower` 14 px `RED_LIGHT` di tengah, lalu `return` (tanpa upgrade). |
| Regen shield | Level >= 4: section di `py+300`, pill status `regen_shield_on` atau tombol `popup_regen_shield` (`gold`/`locked`). |
| MAX LEVEL | `letter("MAX LEVEL")` 22 px di tengah `y+14`, lalu pill `popup_sell_tower` `150x34` di `y+36`. |
| Path (Lv1) | Judul `CHOOSE PATH`, grid 2x2 `btn_w = (popup_w-46)/2`, `btn_h = 68`, gradasi `0.30c+18` / `0.45c+40`, hover radial 40, ticks emas, nama/nilai/harga/special. |
| Upgrade (Lv2+) | `Lv{n}: DMG … HP …` (`CYAN_SOFT`) + `desc` (`GOLD_TEXT`), lalu `popup_upgrade_tower` dan `popup_sell_tower` `(popup_w-46)/2 x 40`. |

Frame yang di-replay (op + rect tombol harus sama persis):

| Frame | Kondisi | Op | Tombol |
| --- | --- | --- | --- |
| `enemy` | level 3, gold 500, panel tidak, cheap true | 16 | 1 |
| `path_lv1` | level 1, gold 9999, panel tidak, cheap true | 50 | 5 |
| `upgrade_locked` | level 3, gold 100, panel tidak, cheap true | 20 | 3 |
| `upgrade_hover` | level 3, gold 9999, panel tidak, cheap false | 19 | 3 |
| `max_level` | level 6, gold 500, panel tidak, cheap true | 19 | 2 |
| `regen_buy` | level 4, gold 900, panel tidak, cheap true | 22 | 4 |
| `regen_on` | level 4, gold 100, panel tidak, cheap true | 22 | 3 |
| `specials` | level 5, gold 9999, panel tidak, cheap true | 22 | 3 |
| `panel_wide` | level 2, gold 9999, panel ya, cheap true | 19 | 3 |
| `panel_narrow` | level 1, gold 0, panel ya, cheap true | 44 | 5 |

Tabel `_core.py` yang dipakai tombol path/upgrade dikirim sebagai data:
`data/towers/upgrade_paths.json` (`TOWER_TYPE_INFO`, `TOWER_TYPE_COLORS`, `TOWER_UPGRADE_PATHS`),
ditulis oleh oracle (`--write`) supaya angka balance tidak disalin manual ke GDScript.

## 6. Bukti dead / stub / duplikat

| Temuan | Bukti |
| --- | --- |
| `Notification.draw` (2 salinan identik) | Body hanya `pass`; `_core.UI.draw_notifications` langsung `return` dan `add_notification` didokumentasikan "sistem notifikasi dihapus" (`_core.py:8677-8690`). |
| `Notification.add_notification` (2 salinan) | Antrean tidak pernah digambar; tidak ada jalur hidup. |
| `_FakeEntity`, `_make_fake_boss`, `_make_fake_hero` | Ada dua salinan (baris 466/1382, 490/1388, 565/1437); salinan `hero_panel` tidak dipanggil, salinan `hero_portraits` hanya jembatan ke renderer potret yang di Godot sudah native. |
| `BaseUIComponent._draw_shadow_rect` | Tidak ada satu pun call-site di folder maupun repo. |
| `BuildSlots._draw_blue_slot` / `_draw_red_slot` | Atlas bake memakai `_render_*_slot_surface`; kedua `_draw_*` tidak dipanggil. |
| `clear_cache` | Tidak ada cache potret di Godot; diganti painter native. |

## 7. Deviations (triage, bukan kegagalan diam)

| ID | Deviation | Alasan & rencana |
| --- | --- | --- |
| D1 | `HeroPortraits._apply_grayscale` tidak direproduksi | Potret non-owned di Pygame didesaturasi. Di Godot kartu terkunci memakai warna `LOCKED_*` (`hero_shop_card.gd`), potret tetap berwarna. Butuh shader `ShaderMaterial`/`modulate` desaturasi; dicatat sebagai deviation, bukan gap tersembunyi. |
| D2 | Popup tower belum dipasok screen | Layer ini menyediakan layout + op + rect tombol (`tower_popup_state` di `prototype_view.gd`), tetapi `prototype_screen.gd` belum membangun snapshot dari tower yang di-tap: interaksi tower di Godot masih lewat BottomBar desktop (`%UpgradeButton`/`%SellButton`). Menutup ini butuh routing tap tower + registrasi tombol di dock (pekerjaan layer berikut, sekarang murah karena layout sudah terkunci oracle). |
| D3 | Ellipsis `...` vs `…` | Oracle memakai `_has_glyph = False` seperti oracle 9bv7/9bv8, jadi teks terpotong diakhiri `...`. Font asli kemungkinan punya `…`; kosmetik, konsisten dengan layer sebelumnya. |

## 8. Berkas yang ditambahkan / diubah

| Berkas | Peran |
| --- | --- |
| `godot_rebuild/tests/ui_components_source_oracle.py` | Oracle AST + eksekusi kode sumber, menulis fixture dan data tower. |
| `godot_rebuild/tests/fixtures/ui_components_source.json` | Inventaris, klasifikasi 122 simbol, 15 op toolbox, 10 frame popup. |
| `godot_rebuild/scripts/ui/ui_component_base.gd` | `shadow_ops`, `hp_bar_ops`, `close_button_ops`, `panel_position`. |
| `godot_rebuild/scripts/ui/tower_popup_layout.gd` | `geometry`, `build`/`ops`, `tower_specials`, `regen_section`, `max_level_ops`, `path_buttons_ops`, `path_button_ops`, `upgrade_button_ops`. |
| `godot_rebuild/data/towers/upgrade_paths.json` | Tabel tipe/level tower dari `_core.py`. |
| `godot_rebuild/tests/ui_components_checks.gd` | Suite native: klasifikasi, toolbox, 10 frame popup, wiring view. |
| `godot_rebuild/scenes/prototype/prototype_view.gd` | `tower_popup_state`, `_draw_tower_popup`, `tower_popup_draw_ops`, painter `pill`/`corner_ticks`/`icon`/`hp_bar`. |
| `godot_rebuild/tests/run_all.gd` | Mendaftarkan `UiComponentsChecks`. |
| `godot_rebuild/tests/validate_project.py` | Blok `9ce`. |

## 9. Tes dan validasi

| Lapis | Isi |
| --- | --- |
| Oracle Python | `python3 godot_rebuild/tests/ui_components_source_oracle.py --write` (fixture 122 simbol, 10 frame) |
| Suite native | `UiComponentsChecks` - klasifikasi + target/token, toolbox 15 kasus, `panel_position` 5 kasus, 10 frame popup (op + tombol), specials, data tower, wiring view |
| Validator | blok `9ce` (inventaris, klasifikasi, drift fixture/data, geometri popup, laporan) |

Catatan metode: validator statis lulus **bukan** bukti parity. Parity untuk layer ini
berarti: setiap op/string/rect yang pygame minta sudah direproduksi modul Godot dan
diuji di suite native, sementara perilaku yang belum bisa diuji di sandbox (binding
tap tower di layar) dicatat sebagai deviation D2.
