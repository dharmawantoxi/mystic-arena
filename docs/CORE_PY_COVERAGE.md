# Peta cakupan `_core.py` → Godot

**Apa ini:** audit blok-per-blok `_core.py` (10.281 baris — gabungan 8 modul
lama: `settings`, `game`, `menu`, `game_input`, `game_ui`, `game_dev`,
`game_settings`, `controller_manager`) terhadap port Godot di `godot/`.
Dipakai untuk menjawab "bagian mana yang sudah pindah, mana yang belum" tanpa
menebak dari nama berkas.

**Cara baca:** setiap baris = kelas/blok pygame dengan rentang baris di
`_core.py`, padanannya di Godot, dan statusnya.

| Status | Arti |
|---|---|
| ✅ PORTED | Perilaku diport dan **dikunci fixture/oracle** (tes paritas menyebutnya) |
| 🟡 PARSIAL | Ada padanannya, tapi sebagian perilaku belum ada / belum diuji |
| ❌ BELUM | Tidak ada padanan di Godot |
| ⚪ N/A | Kode pygame-nya sendiri no-op / khusus renderer / tidak relevan di Godot |

Acuan audit lebih luas (bukan hanya `_core.py`):
[GODOT_PARITY.md](GODOT_PARITY.md). Entitas `_entity.py`:
[ENTITY_PY_COVERAGE.md](ENTITY_PY_COVERAGE.md). Sistem gabungan
(`performance`/`fps`/`sound`/`save`) `_system.py`:
[SYSTEM_PY_COVERAGE.md](SYSTEM_PY_COVERAGE.md). Roadmap komponen:
[GODOT_MIGRATION.md](GODOT_MIGRATION.md).

---

## 1. `settings.py` — `_core.py:28-1296` (konstanta + tabel)

| Blok | Padanan Godot | Status |
|---|---|---|
| Konstanta ekonomi (`STARTING_GOLD`, `MINION_WAVE_INTERVAL`, `compute_starting_gold`, `compute_gold_per_second`) | `GameManager.compute_starting_gold/compute_gold_per_second` + `godot/data/economy.json` | ✅ (fixture `economy`, 54 level × 3 difficulty; harness menolak drift `economy.json`) |
| Tabel menara (`*_LEVELS`, HP/shield/regen, `TOWER_REGEN_SHIELD_*`) | `TowerDB.gd` + `godot/data/towers.json` | ✅ (`Tower.regen_shield_*`, `GameManager.try_buy_tower_regen_shield`) |
| Katalog hero/boss/level | `HeroDB`/`BossDB` + `godot/data/*.json` (converter) | ✅ (`boss_core` 216 baris, `meta_shop_txn` 222 baris closed-world) |
| `TowerDebuffMixin` (`:775-1139`) — dipakai **Hero & Minion**, bukan Tower (`_entity.py:3235`, `:5400`) | `scripts/systems/StatusEffects.gd` (slow/stun/armor_shred/damage_amp/heal_amp/blind) | ✅ untuk hero/minion (fixture `hero_basic_attack`, `item_procs`, `hero_rng_guards`); FX debuff menara (`_draw_tower_debuff_fx`) ⚪ piksel |
| `_default_hero_unlock_cost` + `get_all_hero_types` (dua def; def kedua menimpa harga) | `HeroDB` + `MainMenu._try_unlock_hero` | ✅ (oracle `meta_shop_txn` mengunci def KEDUA: starter 0, mini/true 4500) |
| Palet warna / `SCREEN_*` / `TOP_BAR_HEIGHT` | `UiTheme.gd`, `HudLayout.gd`, `MobileLayout.gd` | 🟡 nilai tersebar, tidak ada satu tabel terkunci |

## 2. `game.py` — `class Game` `_core.py:1322-3040`

| Metode pygame | Padanan Godot | Status |
|---|---|---|
| `__init__`/`reset` (roster kosong, auto-grant Kaizen, wave 0, 5 dtk) | `GameManager.start_level` + `Main._start_battle` | ✅ (FASE 8-11; `GameplayParityTest`, `hero_catchup_unlocks`) |
| `try_build_tower`, `_generate_build_slots_from_lanes` | `GameManager.try_build_tower`, `Main._generate_build_slots` | ✅ (`LANE_SLOT_PCT` = angka `_core.py:1660-1676`) |
| `open_build_popup`/`close_build_popup` | Dilebur ke ShopPanel (tab MENARA) | 🟡 deviasi terdokumentasi (satu panel terpadu) |
| `update_waves`, `_get_wave_composition`, `_auto_scale_ai_castle`, `_roll_mini_boss_schedule`, `_try_spawn_pending_mini_boss` | `GameManager` + `Main._roll_mini_boss_schedule` | ✅ (fixture `waves`, `ai_castle`, `ai_income`) |
| `update` (ekonomi milli-gold, respawn hero, hit-stop, reward) | `GameManager._process` + `CombatSystem` | ✅ (FASE 13-16: `match_scoring`, `minion_tower_rewards`, `death_dispatch`) |
| `_grant_meta_reward`, `_unlock_achievement`, `_auto_unlock_defeated_boss_heroes` | `GameManager.grant_meta_reward`/`unlock_achievement` | ✅ (`boss_death_rewards`, `match_scoring`) |
| `handle_click`, `handle_key`, `handle_key_up` | `Main._on_click`/`_on_key`/`_on_key_release` | ✅ (`ui_hud`, `tactical_input`, **FASE 24 `controller_input`**) |
| `try_buy_hero`, `try_upgrade_nexus`, `try_activate_castle_shield` | `GameManager.try_buy_hero`/`try_upgrade_nexus`, `Nexus.activate_castle_shield` | ✅ |
| `_draw_input_hints`, `_input_label` | `HUD._hint_rows` + `ControllerManager.get_hints/get_action_label` | ✅ **FASE 24** (bar tampil hanya di mode controller, persis `_core.py:2709-2714`) |
| `draw`, `_draw_gold_hud` | `HUD.gd` (bar gold/nexus/wave) | 🟡 struktur diuji (`ui_hud`), piksel tidak |

## 3. `menu.py` — `MenuState` + `Menu` `_core.py:3097-7692`

| Layar / metode pygame | Padanan Godot | Status |
|---|---|---|
| `MenuState` (8 state) | `MainMenu.State` (8 state sama) | ✅ |
| MAIN (`_draw_main_menu`, `_on_button_click`) | `MainMenu._build_main` | ✅ + **FASE 24**: tombol **INPUT** (paritas `input_select` `_core.py:4774/7025`) + label `INPUT: …` kiri-bawah |
| SLOT_SELECT (`_draw_slot_select`, hapus slot) | `MainMenu._build_slot_select` | ✅ (`save_slots`: 8 kasus migrasi, 15 kartu) |
| LEVEL_SELECT (`_draw_level_select`, `_draw_level_card`) | `MainMenu._build_level_select`, `_level_card` | ✅ (`level_select_stats`) |
| HERO_SHOP (`_draw_hero_shop`, `_draw_meta_hero_card`, `_unlock_hero_in_meta_shop`) | `MainMenu._build_hero_shop`, `_try_unlock_hero` | ✅ (`meta_shop_txn`) |
| SETTINGS (`_draw_settings`, `_draw_volume_slider`, `_draw_toggle_setting`, `_draw_option_setting`) | `MainMenu._build_settings` | ✅ (volume master/sfx/bgm/voice, game speed, fps limit, screen shake, damage numbers) |
| HOW_TO_PLAY / CREDITS / PAUSE | `_build_how_to_play` / `_build_credits` / `_build_pause` | ✅ (teks bahasa Indonesia = deviasi disengaja) |
| Top-up (`_draw_topup_*`, `_topup_http`, `_redeem_*`) | `scenes/ui/TopupDialog.gd` | 🟡 UI ada; alur HTTP server top-up tidak diuji paritas |
| Cloud save (`_draw_cloud_*`, `_do_cloud_*`, `_poll_cloud_restore`) | Baris status inert di SETTINGS | ❌ (Play Games plugin belum diport — di pygame PC pun tombolnya tanpa akses) |
| `_is_difficulty_locked` / `_draw_difficulty_confirm_dialog` | — | ❌ deviasi terdokumentasi: Godot memilih difficulty bebas di PILIH LEVEL |
| `_toggle_input_mode` (`:7630-7647`) | `MainMenu._toggle_input_mode` → `ControllerManager.toggle_input_mode` | ✅ **FASE 24** |
| Partikel/portal/rune crystal (`_init_particles`, `_draw_portal`, `_draw_rune_crystal`) | `widgets/MenuBackground.gd` | 🟡 aproksimasi; piksel tidak diuji |
| `_adjust_volume` | `AudioManager.apply_settings` | ✅ |

## 4. `game_input.py` — `InputHandler` `_core.py:7709-8506`

| Metode pygame | Padanan Godot | Status |
|---|---|---|
| `handle_click`/`_handle_left_click` (prioritas toko → slot → nexus → hero → menara) | `Main._on_click` | ✅ (`ui_hud` 31 kasus klik) |
| `_handle_right_click`, `_handle_hero_command` | `Main._on_right_click`, `Hero.set_destination` | ✅ |
| `handle_hero_panel_click`, `_try_upgrade_hero` | `ShopPanel` (tab HERO) + `MobileLayout.hero_panel_rect` | ✅ (`MobileSidePanelParityTest`) |
| `handle_build_popup_click`, `handle_popup_click`, `_try_upgrade_tower*`, `_try_sell_tower`, `_try_activate_regen_shield` | `ShopPanel` + `GameManager` | ✅ (`test_sell_tower` pygame; panel terpadu Godot) |
| `handle_shop_click`, `_try_buy_hero` | `ShopPanel` + `GameManager.try_buy_hero` | ✅ |
| `handle_key`/`handle_key_up` (skill QWER, taktis G/F/T/C/B/D, toko H) | `Main._on_key`/`_on_key_release`/`_tactical_hotkey` | ✅ (`tactical_input`, `ui_hud`) |
| `get_hints` (`:10102`, milik ControllerManager) | `HUD._hint_rows` + `ControllerManager.get_hints` | ✅ **FASE 24** |

## 5. `game_ui.py` — `UIRenderer` `_core.py:8542-8691`

Koordinator tipis yang mendelegasi ke `ui_components/`. Padanan Godot =
`scenes/ui/HUD.gd` + `ShopPanel.gd` + widget di `scenes/ui/widgets/`.
`draw_tactical_commands`, `draw_notifications`, dan `add_notification` di
pygame sendiri **no-op** (⚪). Status keseluruhan: 🟡 — semua delegasi punya
padanan, tapi tidak ada fixture yang mengunci "urutan delegate" UIRenderer
(urutan Z HUD dikunci `UiHudParityTest`/`TouchHudParityTest`).

## 6. `game_dev.py` — `DevMode` `_core.py:8704-9084` — ❌ BELUM

Blok `_core.py` terbesar yang belum punya padanan (±380 baris):

* F1 toggle dev mode, F2 panel, F3 debug info (`:8726-8738`)
* Cheat gold F5/F6/F7 (+500/+2000/+10000), F8 AI +2000 (`:8745-8760`, dst.)
* Panel dev + indikator + `_draw_debug_info` (`:8897-9084`)
* Tombol rescan controller di dalam panel (`:8880-8883`) — **kini tersedia di
  Godot lewat tombol INPUT menu utama** (FASE 24), jadi satu-satunya fungsi
  DevMode yang sudah punya padanan.

Yang ada di Godot hanya sebagian kecil esensinya: `Main.enable_debug_controls`
(default mati) dan overlay FPS `HUD.toggle_debug_overlay()` (target tombol
TouchHUD, env `MYSTIC_DEBUG=1`).

## 7. `game_settings.py` — `GameSettings` `_core.py:9102-9299`

| Metode pygame | Padanan Godot | Status |
|---|---|---|
| `set_difficulty`/`cycle_difficulty`/`get_difficulty_label` | `GameManager.set_difficulty`/`cycle_difficulty`, `MainMenu._difficulty_row` | ✅ |
| `set_screen_shake`, `set_damage_numbers` | `GameManager.set_screen_shake`/`set_damage_numbers` | ✅ (live ke camera trauma & `world_popups`) |
| `set_game_speed` (quirk `int(mult)-1`), `set_fps_limit`, `get_*_label` | `GameManager.apply_game_speed`/`apply_fps_limit`, `MainMenu._cycler_row` | ✅ (quirk pygame dipertahankan) |
| `set_language` | — | ❌ (UI Godot memang bahasa Indonesia) |
| `_load`/`save` (persist per slot) | `SaveManager` per slot | ✅ (`save_slots`) |

## 8. `controller_manager.py` — `_core.py:9299-10234` — ✅ **FASE 24**

Sebelum FASE 24 blok ini **tidak ada padanannya sama sekali** (komentar lama
`HUD._build_hint_bar`: "Godot belum punya lapisan input gamepad"). Kini:

| Blok pygame | Padanan Godot |
|---|---|
| `InputMode`, `XBOX_MAP`/`PS_MAP`/`GENERIC_MAP` | `ControllerManager.MODE_*`, `BUTTON_MAP` (indeks SDL — deviasi terdokumentasi) |
| `init_joystick`, `_scan_controllers` (deteksi nama/GUID/layout), `rescan`, `debug_print` | `ControllerManager.init_joystick/_scan_controllers/rescan/debug_print` |
| `set_mode`, `is_controller_mode` | sama |
| `update` (kursor: 12 → 25, kurva `magnitude^1.5`, deadzone 0.25, clamp) | sama |
| `get_pressed_actions` (edge tombol, D-PAD fresh + repeat 22/5, trigger > 0.5, scroll 0.55/0.18/1.0 guard 8) | sama (D-PAD disintesis dari 4 tombol SDL) |
| `_resolve_scroll_axis` | sama (mapped → 3,2,4,5; lewati \|v\| > 0.95; cache) |
| `rumble` (`int(frames × 16.67)` ms + stop otomatis) | `rumble` → `Input.start_joy_vibration` (low↔strong, high↔weak) |
| `draw_cursor` (glow/crosshair/bracket) | `scenes/ui/VirtualCursor.gd` |
| `find_ui_button_at_cursor`, `snap_to_nearest_button` | sama (Rect2) |
| `_LABELS`/`_KEY_LABELS`/`ACTION_BINDINGS`/`get_button_label`/`get_action_label`/`get_hints` | sama (7 konteks) |
| Routing aksi di `main_desktop_legacy.py:146-320` | `scripts/systems/ControllerRouter.gd` |

Dikunci `controller_input` + `ControllerInputParityTest` (60 skenario routing,
138 frame aksi, 136 label, 28 konteks hint).

---

## Ringkasan yang masih terbuka di `_core.py`

1. **`DevMode` (`game_dev.py`, ±380 baris)** — cheat F5-F8, panel dev, debug
   info. Belum ada padanan (selain rescan controller via tombol INPUT).
2. **Cloud save (`Menu._draw_cloud_*`/`_do_cloud_*`)** — status inert saja.
3. **Difficulty lock pygame** (`_is_difficulty_locked`) — deviasi disengaja.
4. **`set_language`** — tidak ada (UI Godot satu bahasa).
5. **Alur HTTP top-up** — UI ada (`TopupDialog.gd`), jalur server tidak diuji.
6. **Piksel** semua layar (menu, HUD, kursor controller) — bucket piksel,
   di luar cakupan fixture.

Yang **bukan** bagian `_core.py` tapi bersebelahan dan juga masih terbuka:
`splash_screen.py` (`scenes/ui/SplashScreen.gd` sudah ada + kini masuk grup
`splash` untuk routing pad, tetapi **belum dipasang di `main.tscn`**),
`lighting.py`, dan `mobile/debug.py` (4 mode + grafik frame).
