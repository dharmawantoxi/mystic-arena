# Migrasi folder `_core.py` ke Godot

`_core.py` bukan folder: satu berkas 10.281 baris di root repo yang berisi **delapan modul pygame** yang digabung (`settings`, `game`, `menu`, `game_input`, `game_ui`, `game_dev`, `game_settings`, `controller_manager`) plus shim alias `sys.modules` di ekornya. Dokumen ini mencatat bagaimana seluruh isinya diklasifikasikan dan dipetakan ke rebuild Godot.

Sumber kebenaran angka: `godot_rebuild/tests/core_source_oracle.py`. Oracle menjalankan blok `settings.py` **sungguhan** (baris 28–1291, di bawah stub `pygame`) lalu membandingkan inventaris AST dengan berkas sumber. Fixture: `tests/fixtures/core_source.json`; data hasil eksekusi: `data/core/settings.json`.

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `_core.py` | 10281 |
| Modul gabungan | 8 |
| Kelas top-level | 10 |
| Method kelas | 218 |
| Fungsi top-level | 11 |
| Assign konstanta `settings.py` | 144 |
| Simbol terklasifikasi | 391 |
| Konstanta diekspor ke JSON | 139 |
| Konstanta dipin modul Godot (parity) | 16 |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `data` | 140 | dikirim sebagai data (`data/core/settings.json`) |
| `ported` | 47 | ada fungsi/konstanta yang benar-benar sama di Godot (target + token `func`) |
| `folded` | 181 | tanggung jawabnya dikerjakan alur modul pengganti, tanpa fungsi 1:1 |
| `dead` | 6 | tidak pernah dipanggil di pohon pygame (dibuktikan call-site AST) |
| `deviation` | 8 | sengaja tidak diportir, alasannya didokumentasikan |
| `meta` | 9 | bookkeeping modul (shim alias), tidak perlu di Godot |

## 2. Peta delapan modul

| Modul | Baris | Kelas | Fungsi | Kind | Target Godot |
| --- | --- | --- | --- | --- | --- |
| `settings.py` | 28–1296 (1269 baris) | 1 (`TowerDebuffMixin`) | 23 | `data` | `godot_rebuild/data/core/settings.json` + `scripts/data/core_settings.gd` |
| `game.py` | 1297–3042 (1746 baris) | 1 (`Game`) | 32 | `ported` | `scripts/match/prototype_battle.gd` (174 func) + 37 modul match |
| `menu.py` | 3043–7694 (4652 baris) | 2 (`MenuState`, `Menu`) | 87 | `ported` | `scenes/menu/main_menu.gd` + `scripts/ui/menu_*` layout |
| `game_input.py` | 7695–8505 (811 baris) | 1 (`InputHandler`) | 24 | `ported` | `scenes/prototype/prototype_screen.gd` (92 func) |
| `game_ui.py` | 8506–8690 (185 baris) | 1 (`UIRenderer`) | 16 | `ported` | `scripts/ui/side_panel.gd` + `tower_popup_layout.gd` |
| `game_dev.py` | 8691–9083 (393 baris) | 1 (`DevMode`) | 6 | `deviation` | tidak diportir — perkakas developer (F1/F2/F3 + cheat) |
| `game_settings.py` | 9084–9298 (215 baris) | 1 (`GameSettings`) | 19 | `ported` | `scripts/settings/*` (presentation/quality/frame rate/language/localization) |
| `controller_manager.py` | 9299–10281 (983 baris) | 2 (`InputMode`, `ControllerManager`) | 22 | `ported` | `scripts/input/controller_runtime.gd` (26 func) |

| Kelas | Simbol method | Padanan Godot | Catatan |
| --- | --- | --- | --- |
| `TowerDebuffMixin` | 14 | godot_rebuild/scripts/combat/unit_state.gd | matematika debuff/status ada di unit state bersama |
| `Game` | 32 | godot_rebuild/scripts/match/prototype_battle.gd | simulasi match menggantikan loop Game pygame |
| `MenuState` | 0 | godot_rebuild/scenes/menu/main_menu.gd | layar menu berupa scene, bukan string state |
| `Menu` | 86 | godot_rebuild/scenes/menu/main_menu.gd | scene menu + layout `scripts/ui/menu_*` yang menggambar |
| `InputHandler` | 24 | godot_rebuild/scenes/prototype/prototype_screen.gd | routing tap/drag ada di lapisan input prototype screen |
| `UIRenderer` | 16 | godot_rebuild/scripts/ui/side_panel.gd | dock panel memegang permukaan koordinator |
| `DevMode` | 6 | — | cheat F1-F12 adalah perkakas developer, bukan perilaku pemain |
| `GameSettings` | 19 | godot_rebuild/scripts/settings/presentation_settings_store.gd | setelan dipersist lewat settings store |
| `InputMode` | 0 | godot_rebuild/scripts/input/controller_runtime.gd | adapter controller memodelkan mode, bukan enum string |
| `ControllerManager` | 20 | godot_rebuild/scripts/input/controller_runtime.gd | Godot menormalisasi pad, jadi adapter memindahkan perilakunya |

Catatan peta: blok 28–1296 memang rentang `settings.py`, tetapi karena penggabungan berkas, blok itu juga memuat kelas `TowerDebuffMixin` (baris 775) dan delapan helper top-level (`compute_starting_gold`, `compute_gold_per_second`, `format_gold_rate`, `get_all_hero_types`, `get_hero_shop_order`, ...). Konstanta yang dikirim sebagai data tetap 139 — semuanya `Assign` di rentang tersebut.

## 3. `settings.py` sebagai data

139 konstanta dijalankan nyata oleh oracle lalu ditulis ke `godot_rebuild/data/core/settings.json`; `godot_rebuild/scripts/data/core_settings.gd` membacanya kembali lewat `reload()`, `all()`, `count()`, `has()`, `names()`, `value()`, `number()`, `integer()`, `flag()`, `text()`, `color()`, `list()` dan `block()` — semuanya dengan fallback eksplisit, tanpa satu pun nama GDScript yang ditulis ulang.

| Konstanta | Nilai | Dipakai untuk |
| --- | --- | --- |
| `SCREEN_WIDTH / SCREEN_HEIGHT` | `1280 / 720` | kanvas pygame; Godot memakai viewport 1624x720 |
| `TOP_BAR_HEIGHT` | `40` | tinggi bar atas; sama di `tower_popup_layout.gd` |
| `FPS` | `60` | `Engine.physics_ticks_per_second == 60` |
| `TOWER_HP_MULTIPLIER` | `2.5` | HP tower = base * 2.5 |
| `TOWER_SHIELD_HP_RATIO` | `0.4` | shield = 40% HP |
| `TOWER_SHIELD_REGEN_DELAY / RATE` | `180 / 1.8` | regen shield pasif |
| `TOWER_REGEN_SHIELD_ENABLED / MIN_LEVEL` | `True / 4` | shield beli manual mulai level 4 |
| `TOWER_REGEN_SHIELD_COST` | `850` | harga shield; `structure_state.gd` juga 850 |
| `TOWER_VISUAL_SCALE` | `0.7` | `tower_render_catalog.gd` SCALE |
| `META_REPLAY_REPEAT_REWARD` | `200` | `level_progress.gd` REPEAT_REWARD |
| `STARTER_HERO_UNLOCK_COST` | `0` | hero starter gratis |
| `MINI_BOSS / TRUE_BOSS_HERO_UNLOCK_COST` | `4500 / 4500` | semua boss hero 4500 |
| `DEV_UNLIMITED_HERO_GOLD` | `False` | switch dev; default mati |
| `GOLD / WHITE / RED` | `(255,200,50) / (255,255,255) / (220,50,50)` | palet HUD & HP bar |
| `MAX_HERO_LEVEL / MAX_HEROES_OWNED` | `15 / 5` | batas roster |
| `GOLD_PER_SECOND / AI_THINK_INTERVAL` | `3 / 90` | ekonomi & irama AI |
| `TITLE` | `Mystic Arena` | judul window |

### 3.1 Paritas konstanta yang sudah dipin Godot

Enam belas konstanta di bawah ini juga hidup sebagai `const` di modul Godot. Oracle mencocokkan nama-akhiran **dan** nilainya, lalu `tests/core_checks.gd` membaca ulang berkasnya dan membandingkan literalnya — jadi JSON dan konstanta tangan tidak bisa menyimpang diam-diam.

| Konstanta `_core` | Nilai | Konstanta Godot | Berkas |
| --- | --- | --- | --- |
| `AI_MAX_HEROES` | `5` | `MAX_HEROES` | `godot_rebuild/scripts/match/ai_policy.gd`:6 |
| `AI_THINK_INTERVAL` | `90` | `THINK_INTERVAL` | `godot_rebuild/scripts/match/ai_policy.gd`:5 |
| `GOLD_PER_SECOND` | `3` | `GOLD_PER_SECOND` | `godot_rebuild/scripts/ui/level_intro_screen.gd`:27 |
| `MAX_HEROES_OWNED` | `5` | `MAX_HEROES_OWNED` | `godot_rebuild/scripts/match/prototype_battle.gd`:95 |
| `MAX_HERO_LEVEL` | `15` | `MAX_HERO_LEVEL` | `godot_rebuild/scripts/data/hero_definition.gd`:9 |
| `META_REPLAY_REPEAT_REWARD` | `200` | `REPEAT_REWARD` | `godot_rebuild/scripts/match/level_progress.gd`:6 |
| `MINION_SPAWN_DELAY` | `20` | `SPAWN_DELAY` | `godot_rebuild/scripts/match/wave_scheduler.gd`:6 |
| `MINION_WAVE_INTERVAL` | `1500` | `WAVE_INTERVAL` | `godot_rebuild/scripts/match/wave_scheduler.gd`:5 |
| `SCREEN_HEIGHT` | `720` | `HEIGHT` | `godot_rebuild/scenes/splash/splash_screen.gd`:15 |
| `SCREEN_WIDTH` | `1280` | `SCREEN_WIDTH` | `godot_rebuild/scripts/ui/boss_entrance_layout.gd`:25 |
| `TOP_BAR_HEIGHT` | `40` | `TOP_BAR_HEIGHT` | `godot_rebuild/scripts/ui/tower_popup_layout.gd`:26 |
| `TOWER_DEBUFF_FPS` | `60.0` | `DEBUFF_FPS` | `godot_rebuild/scripts/match/boss_state.gd`:18 |
| `TOWER_MAX_LEVEL` | `6` | `TOWER_MAX_LEVEL` | `godot_rebuild/scripts/match/ai_upgrades.gd`:9 |
| `TOWER_REGEN_SHIELD_COST` | `850` | `REGEN_SHIELD_COST` | `godot_rebuild/scripts/combat/structure_state.gd`:6 |
| `TOWER_REGEN_SHIELD_MIN_LEVEL` | `4` | `REGEN_SHIELD_MIN_LEVEL` | `godot_rebuild/scripts/combat/structure_state.gd`:5 |
| `TOWER_VISUAL_SCALE` | `0.7` | `SCALE` | `godot_rebuild/scripts/ui/tower_render_catalog.gd`:28 |

## 4. Kelas dan fungsi top-level

| Simbol | Kind | Target | Token / catatan |
| --- | --- | --- | --- |
| `class:ControllerManager` | `ported` | `godot_rebuild/scripts/input/controller_runtime.gd` | func rumble( |
| `class:DevMode` | `deviation` | — | cheat F1-F12 adalah perkakas developer, bukan perilaku pemain |
| `class:Game` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | func _roll_mini_boss_schedule( |
| `class:GameSettings` | `ported` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | static func defaults() |
| `class:InputHandler` | `ported` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | func _primary_action( |
| `class:InputMode` | `ported` | `godot_rebuild/scripts/input/controller_runtime.gd` | signal action_requested( |
| `class:Menu` | `ported` | `godot_rebuild/scenes/menu/main_menu.gd` | func _toggle_input_mode( |
| `class:MenuState` | `ported` | `godot_rebuild/scenes/menu/main_menu.gd` | func _open_how_to_play( |
| `class:TowerDebuffMixin` | `ported` | `godot_rebuild/scripts/combat/unit_state.gd` | func apply_armor_shred( |
| `class:UIRenderer` | `ported` | `godot_rebuild/scripts/ui/side_panel.gd` | func update_snapshot( |
| `shim:_CORE_MOD` | `meta` | — | referensi diri modul untuk peta alias |
| `shim:_install_root_aliases` | `meta` | — | peta alias sys.modules untuk 25 nama modul lama |
| `shim:install_aliases` | `meta` | — | pembungkus idempoten _install_root_aliases |
| `top:_PANEL_AKTIF@79` | `ported` | `godot_rebuild/scripts/ui/side_panel.gd` | func is_active() |
| `top:_default_hero_unlock_cost@1139` | `ported` | `godot_rebuild/scripts/match/hero_unlock_store.gd` | static func entry( |
| `top:_install_root_aliases@10234` | `meta` | — | Godot punya modul nyata, tanpa shim alias |
| `top:compute_gold_per_second@256` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | compute_gold_per_second |
| `top:compute_starting_gold@232` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | compute_starting_gold |
| `top:fmt_idr@3083` | `ported` | `godot_rebuild/scripts/match/topup_currency.gd` | fmt_idr |
| `top:format_gold_rate@271` | `ported` | `godot_rebuild/scripts/match/match_economy.gd` | format_gold_rate |
| `top:get_all_hero_types@1153` | `ported` | `godot_rebuild/scripts/match/hero_unlock_store.gd` | static func entry( |
| `top:get_all_hero_types@1255` | `meta` | — | definisi kedua menimpa yang pertama; override kebijakan shop yang menang |
| `top:get_hero_shop_order@1228` | `ported` | `godot_rebuild/scripts/match/hero_unlock_store.gd` | static func ids_for_tab( |
| `top:install_aliases@10279` | `meta` | — | pemasang alias idempoten, tidak perlu di Godot |

## 5. Tabel klasifikasi lengkap

Tiap simbol punya kind, target dan token yang diverifikasi `tests/core_checks.gd`: berkas target harus ada di dalam `godot_rebuild/` dan benar-benar memuat tokennya.

| Simbol | Kind | Target | Token |
| --- | --- | --- | --- |
| `class:ControllerManager.__init__` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager._resolve_scroll_axis` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager._scan_controllers` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.debug_print` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.draw_cursor` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.draw_hint_bar` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.find_ui_button_at_cursor` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.get_action_label` | `ported` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func get_action_label(` |
| `class:ControllerManager.get_button_label` | `ported` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func get_button_label(` |
| `class:ControllerManager.get_controller_info` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.get_cursor_pos` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.get_hints` | `ported` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func get_hints(` |
| `class:ControllerManager.get_pressed_actions` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.init_joystick` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.is_controller_mode` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.rescan` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.rumble` | `ported` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.set_mode` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.snap_to_nearest_button` | `folded` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func rumble(` |
| `class:ControllerManager.update` | `ported` | `godot_rebuild/scripts/input/controller_runtime.gd` | `func advance_frame(` |
| `class:DevMode.__init__` | `deviation` | — | cheat F1-F12 adalah perkakas developer |
| `class:DevMode._draw_debug_info` | `deviation` | — | cheat F1-F12 adalah perkakas developer |
| `class:DevMode._draw_indicator` | `deviation` | — | cheat F1-F12 adalah perkakas developer |
| `class:DevMode._draw_panel` | `deviation` | — | cheat F1-F12 adalah perkakas developer |
| `class:DevMode.draw` | `deviation` | — | cheat F1-F12 adalah perkakas developer |
| `class:DevMode.handle_hotkey` | `deviation` | — | cheat F1-F12 adalah perkakas developer |
| `class:Game.__init__` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._auto_scale_ai_castle` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _auto_scale_ai_castle(` |
| `class:Game._auto_unlock_defeated_boss_heroes` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _auto_unlock_defeated_boss_heroes(` |
| `class:Game._draw_gold_hud` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._draw_input_hints` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._generate_build_slots_from_lanes` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._get_wave_composition` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._grant_meta_reward` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._input_label` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._killer_is_hero` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._process_boss_kill` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _process_boss_kill(` |
| `class:Game._process_hero_kill` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._roll_mini_boss_schedule` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game._try_spawn_pending_mini_boss` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _try_spawn_pending_mini_boss(` |
| `class:Game._unlock_achievement` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _unlock_achievement(` |
| `class:Game._update_gameplay` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.close_build_popup` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.close_popup` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.draw` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.get_all_heroes` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.handle_click` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func clicked_shop_at(` |
| `class:Game.handle_key` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.handle_key_up` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.open_build_popup` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.open_popup` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.reset` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _init(` |
| `class:Game.try_activate_castle_shield` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.try_build_tower` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.try_buy_hero` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.try_upgrade_nexus` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:Game.update` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func step_tick(` |
| `class:Game.update_waves` | `folded` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _roll_mini_boss_schedule(` |
| `class:GameSettings.__new__` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings._init_defaults` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings._load` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.cycle_difficulty` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.get_difficulty_label` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:GameSettings.get_difficulty_short_label` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.get_fps_label` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.get_speed_label` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.is_easy_mode` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.is_hard_mode` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:GameSettings.is_scaling_on` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.save` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.set_damage_numbers` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.set_difficulty` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.set_fps_limit` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.set_game_speed` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.set_language` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.set_screen_shake` | `folded` | `godot_rebuild/scripts/settings/presentation_settings_store.gd` | `static func defaults()` |
| `class:GameSettings.toggle_difficulty` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:InputHandler.__init__` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._cast_hero_skill` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._get_clicked_build_slot` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._get_clicked_hero` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._get_clicked_tower` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._handle_hero_command` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._handle_left_click` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._handle_right_click` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._kena` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._select_hero` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._touch_rect` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._try_activate_regen_shield` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._try_buy_hero` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._try_sell_tower` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._try_upgrade_hero` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._try_upgrade_tower` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler._try_upgrade_tower_path` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler.handle_build_popup_click` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler.handle_click` | `ported` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler.handle_hero_panel_click` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler.handle_key` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler.handle_key_up` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler.handle_popup_click` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:InputHandler.handle_shop_click` | `folded` | `godot_rebuild/scenes/prototype/prototype_screen.gd` | `func _primary_action(` |
| `class:Menu.__init__` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._adjust_volume` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._all_slots_empty` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._apply_cloud_payload` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._blit_shadow` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:Menu._build_main_background` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._build_menu_fog` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._confirm_difficulty_change` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._dev_topup_gold` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._do_cloud_download` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._do_cloud_signin` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._do_cloud_upload` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_cloud_buttons` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_cloud_confirm_dialog` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_cloud_restore_prompt_dialog` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_confirm_buttons` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_credits` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_delete_confirm_dialog` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_difficulty_confirm_dialog` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_empty_slot_content` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_exit_confirm_dialog` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_hero_shop` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_how_to_play` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_level_card` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_level_scroll_indicator` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_level_select` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_main_background` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_main_menu` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_meta_hero_card` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_meta_scroll_indicator` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_option_setting` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_pause_background` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_pause_menu` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_paying_button_row` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_portal` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_reset_confirm_dialog` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_rune_crystal` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_settings` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_slot_action_buttons` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_slot_card` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_slot_content` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_slot_select` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_toggle_setting` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_topup_dialog` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_topup_paying` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_topup_processing` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_topup_redeem` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_topup_select` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_topup_success` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._draw_volume_slider` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._get_continue_level` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._get_locked_difficulty` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._init_particles` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._is_difficulty_locked` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._kena` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._on_button_click` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._on_cloud_auth` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._on_cloud_download` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._on_cloud_peek` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._on_cloud_upload` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._poll_cloud_restore` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._redeem_append` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._redeem_backspace` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._redeem_grant` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._redeem_handle_key` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._redeem_submit` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._render_gradient_text` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:Menu._set_cloud_status` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._toggle_input_mode` | `ported` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._topup_http` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._topup_pay_fail` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._topup_price_str` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._topup_send_create` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._topup_send_poll` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._topup_server_tick` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._unlock_hero_in_meta_shop` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu._update_particles` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu.draw` | `ported` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _layout_source_menu(` |
| `class:Menu.handle_click` | `ported` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _click_and_emit(` |
| `class:Menu.handle_key` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu.reload_progress` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu.reset` | `ported` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _refresh_localized_labels(` |
| `class:Menu.show_main` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu.show_pause` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu.topup_complete` | `folded` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _toggle_input_mode(` |
| `class:Menu.update` | `ported` | `godot_rebuild/scenes/menu/main_menu.gd` | `func _process(` |
| `class:TowerDebuffMixin._draw_tower_debuff_fx` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin._eff_attack_cd` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin._eff_speed` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin._init_tower_debuffs` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin._tick_tower_debuffs` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin.apply_armor_shred` | `ported` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin.apply_damage_amp` | `ported` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_damage_amp(` |
| `class:TowerDebuffMixin.apply_debuff` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin.apply_heal_amp` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin.apply_miss_chance` | `ported` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_miss_chance(` |
| `class:TowerDebuffMixin.apply_slow` | `ported` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_slow(` |
| `class:TowerDebuffMixin.apply_stun` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin.clear_tower_debuffs` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:TowerDebuffMixin.hp` | `folded` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_armor_shred(` |
| `class:UIRenderer.__init__` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer._init_components` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer._init_fonts` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.add_notification` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_build_popup` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_build_slots` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_hero_info` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_hero_shop` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_hover_indicators` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_item_shop` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_notifications` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:UIRenderer.draw_overlay` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_popup` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_shop_hints` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.draw_tactical_commands` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |
| `class:UIRenderer.update_hover_states` | `folded` | `godot_rebuild/scripts/ui/side_panel.gd` | `func update_snapshot(` |

Tabel di atas memuat 217 baris method untuk 218 `def` di AST: `TowerDebuffMixin.hp` adalah pasangan getter/setter dengan nama sama (baris 834 dan 840), jadi satu simbol dengan dua baris definisi. Hal yang sama terjadi pada `settings:FPS` (baris 92 dan 349) yang dicatat di `reassignments`.

### 5.1 Fungsi top-level

| Simbol | Kind | Target | Token / catatan |
| --- | --- | --- | --- |
| `shim:_CORE_MOD` | `meta` | — | referensi diri modul untuk peta alias |
| `shim:_install_root_aliases` | `meta` | — | peta alias sys.modules untuk 25 nama modul lama |
| `shim:install_aliases` | `meta` | — | pembungkus idempoten _install_root_aliases |
| `top:_PANEL_AKTIF@79` | `ported` | `godot_rebuild/scripts/ui/side_panel.gd` | `func is_active()` |
| `top:_default_hero_unlock_cost@1139` | `ported` | `godot_rebuild/scripts/match/hero_unlock_store.gd` | `static func entry(` |
| `top:_install_root_aliases@10234` | `meta` | — | Godot punya modul nyata, tanpa shim alias |
| `top:compute_gold_per_second@256` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `compute_gold_per_second` |
| `top:compute_starting_gold@232` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `compute_starting_gold` |
| `top:fmt_idr@3083` | `ported` | `godot_rebuild/scripts/match/topup_currency.gd` | `fmt_idr` |
| `top:format_gold_rate@271` | `ported` | `godot_rebuild/scripts/match/match_economy.gd` | `format_gold_rate` |
| `top:get_all_hero_types@1153` | `ported` | `godot_rebuild/scripts/match/hero_unlock_store.gd` | `static func entry(` |
| `top:get_all_hero_types@1255` | `meta` | — | definisi kedua menimpa yang pertama; override kebijakan shop yang menang |
| `top:get_hero_shop_order@1228` | `ported` | `godot_rebuild/scripts/match/hero_unlock_store.gd` | `static func ids_for_tab(` |
| `top:install_aliases@10279` | `meta` | — | pemasang alias idempoten, tidak perlu di Godot |

## 6. Dead code dan duplikat

Enam helper di bawah tidak punya satu pun call-site di pohon pygame (AST `Name` + `Attribute`), jadi tidak ada yang perlu dipindahkan:

- `class:GameSettings.get_difficulty_label`
- `class:GameSettings.is_hard_mode`
- `class:GameSettings.toggle_difficulty`
- `class:Menu._blit_shadow`
- `class:Menu._render_gradient_text`
- `class:UIRenderer.draw_notifications`

| Duplikat | Baris | Arti |
| --- | --- | --- |
| `get_all_hero_types` | 1153, 1255 | definisi kedua menimpa yang pertama untuk menetapkan harga shop final: starter 0, semua boss 4500 — persis kebijakan yang tercermin di `data/heroes/*.tres` |
| `class:TowerDebuffMixin.hp` | 834, 840 | pasangan `@property` getter/setter; diklasifikasikan sekali |
| `settings:FPS` | 92, 349 | nama yang sama di-assign dua kali di blok settings |

## 7. Deviasi yang didokumentasikan

### D1 — `game_dev.py` (`DevMode`) tidak diportir

`DevMode` adalah panel debug F1/F2/F3 + cheat (tambah gold, unlock hero, skip wave) yang hanya hidup saat `state != "playing"`. Bukan perilaku player-facing, jadi delapan simbolnya ber-`kind` `deviation`: kelas, lima method, satu method modul `game_dev`, dan satu baris modul. Bila suatu saat dibutuhkan, cheat ini masuk sebagai debug overlay terpisah, bukan bagian build pemain.

### D2 — dua `GOLD` berbeda

Ada dua emas di sumber dan keduanya nyata di rebuild. `_core.GOLD` = `(255, 200, 50)` dipakai HP bar/treasure, dan `build_popup_layout.gd` sudah meminnya sebagai `GOLD`. Aksen UI = `(255, 205, 85)` dipakai `UI_GOLD` di berkas yang sama, lalu `GOLD` di `gold_hud_layout.gd`, `hero_panel_layout.gd` dan `menu_foreground.gd`. Keduanya dipertahankan apa adanya; `CoreSettings.color("GOLD")` mengembalikan `(255,200,50)` dan tes membandingkannya dengan konstanta popup, bukan dengan aksen.

### D3 — shim alias `sys.modules` tidak diportir

`_install_root_aliases`/`install_aliases` mendaftarkan 25 nama modul lama (`settings`, `game`, `menu`, ...) ke `sys.modules` supaya bundel lain bisa `from settings import *`. Godot memakai `preload`/`class_name` nyata, jadi dua fungsi dan satu variabel `_CORE_MOD` ber-`kind` `meta`.

### D4 — 181 method ber-`kind` `folded`

Method ini tidak punya fungsi 1:1 di Godot karena tanggung jawabnya sudah dikerjakan alur modul pengganti (mis. `Menu._draw_hero_shop_card` digambar oleh `main_menu.gd` + `hero_panel_layout.gd`). Target + token menunjuk modul yang menjalankannya, dan `tests/core_checks.gd` memverifikasi file serta token itu benar-benar ada. Yang benar-benar hilang hanya enam helper tanpa call site (`dead`).

## 8. Verifikasi

| Langkah | Perintah | Status |
| --- | --- | --- |
| Oracle sumber | `python3 godot_rebuild/tests/core_source_oracle.py --write` | 391 simbol, 139 konstanta, 16 parity |
| Suite native | `godot_rebuild/tests/core_checks.gd` (lewat `tests/run_all.gd`) | terdaftar; belum dieksekusi di sandbox (tidak ada binary Godot) |
| Validator statis | `python3 godot_rebuild/tests/validate_project.py` | blok `9cf`; PASS: 22454 static checks |
| Lint GDScript | `gdlint`/`gdparse` (gdtoolkit 4.5.0) | bersih |

Karena sandbox tidak punya binary Godot, suite native harus dijalankan di PC/CI. Validator statis **bukan** bukti paritas: ia hanya menjaga inventaris, token klasifikasi, dan nilai konstanta.

## 9. Cara regenerasi

```bash
python3 godot_rebuild/tests/core_source_oracle.py --write   # fixture + settings.json
python3 godot_rebuild/tests/core_source_oracle.py --check   # deteksi drift
python3 godot_rebuild/tests/validate_project.py           # guardrail statis
```

