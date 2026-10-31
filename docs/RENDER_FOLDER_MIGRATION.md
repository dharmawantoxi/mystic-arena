# Migrasi `_render.py` ke Godot

`_render.py` adalah berkas **3.671 baris** di root repo yang berisi **tujuh modul render** pygame yang digabung, plus sistem font bundle di prelude: `map_renderer.py`, `effects.py`, `effects_death.py`, `effects_intro.py`, `effects_level_intro.py`, `sprite_cache.py` dan `render_cache.py`. Dokumen ini mencatat bagaimana seluruh isinya diklasifikasikan dan dibuktikan di rebuild Godot.

Sumber kebenaran: `godot_rebuild/tests/render_source_oracle.py`. Oracle **mengimpor modul aslinya** (stub `pygame`, namespace `settings.py` dari `_core.py`) dan mengeksekusi bagian yang tidak dicakup oracle per-kelas: sistem font, empat kurva easing, dua label input-mode, dan dua singleton cache. Fixture: `tests/fixtures/render_source.json`. Suite native: `tests/render_checks.gd` (dijalankan `run_all.gd`).

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `_render.py` | 3671 |
| Seksi gabungan (font system + 7 modul) | 8 |
| Kelas | 17 |
| `def` di kelas | 108 |
| Fungsi top-level | 16 |
| Assign modul | 7 |
| Simbol terklasifikasi | 156 |
| Kelas dengan oracle + checks sendiri | 17 |
| Sampel easing dieksekusi | 11 nilai x 4 kurva |
| Kelas cache dieksekusi | 2 (`SpriteCache`, `RenderCache`) |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 140 | ada fungsi/konstanta dengan nama sama di modul Godot target |
| `data` | 7 | tabel/konstanta data (peta font, singleton modul) |
| `dead` | 8 | tidak terjangkau dari API publik / `draw()` kelas di pohon pygame |
| `deviation` | 1 | perilaku sengaja berbeda, didokumentasikan (fallback SysFont) |
| `folded` | 0 | dijalankan alur modul pengganti tanpa fungsi 1:1 |

## 2. Peta delapan seksi

| Seksi | Baris | Baris total | Modul pygame | Target Godot |
| --- | --- | --- | --- | --- |
| `font_system` | 1–77 | 77 | `font system` (prelude) | `scripts/ui/source_fonts.gd` + `render_cache.gd` |
| `map_renderer` | 78–270 | 193 | `map_renderer.py` | `scripts/ui/map_renderer.gd` + `dynamic_map_renderer.gd` |
| `effects` | 271–1572 | 1302 | `effects.py` | `scripts/ui/effect_manager.gd` + 10 kelas efek + 7 `*_layout.gd` |
| `effects_death` | 1573–2139 | 567 | `effects_death.py` | `scripts/ui/boss_death_animation.gd` + `boss_death_sequence_layout.gd` + `boss_celebration_layout.gd` |
| `effects_intro` | 2140–2666 | 527 | `effects_intro.py` | `scripts/ui/boss_intro_cinematic.gd` + `boss_intro_layout.gd` |
| `effects_level_intro` | 2667–3379 | 713 | `effects_level_intro.py` | `scripts/ui/level_intro_screen.gd` + `level_intro_layout.gd` |
| `sprite_cache` | 3380–3548 | 169 | `sprite_cache.py` | `scripts/ui/sprite_cache.gd` |
| `render_cache` | 3549–3671 | 123 | `render_cache.py` | `scripts/ui/render_cache.gd` |

## 3. Kelas

| Kelas | Baris | `def` | Kind | Modul native |
| --- | --- | --- | --- | --- |
| `MapRenderer` | 90 | 7 | `ported` | `map_renderer.gd` |
| `FloatingText` | 283 | 3 | `ported` | `floating_text.gd` |
| `HitParticle` | 418 | 3 | `ported` | `hit_particle.gd` |
| `DeathExplosion` | 494 | 4 | `ported` | `death_explosion.gd` |
| `ScreenShake` | 572 | 4 | `ported` | `screen_shake.gd` |
| `EffectManager` | 601 | 15 | `ported` | `effect_manager.gd` |
| `ComboCounter` | 840 | 4 | `ported` | `combo_counter.gd` |
| `WaveAnnouncer` | 990 | 4 | `ported` | `wave_announcer.gd` |
| `KillFeed` | 1103 | 4 | `ported` | `kill_feed.gd` |
| `PopupAnimation` | 1202 | 6 | `ported` | `popup_animation.gd` |
| `PathPreview` | 1275 | 4 | `ported` | `path_preview.gd` |
| `AchievementPopup` | 1371 | 5 | `ported` | `achievement_popup.gd` |
| `BossDeathAnimation` | 1622 | 10 | `ported` | `boss_death_animation.gd` |
| `BossIntroCinematic` | 2152 | 12 | `ported` | `boss_intro_cinematic.gd` |
| `LevelIntroScreen` | 2679 | 9 | `ported` | `level_intro_screen.gd` |
| `SpriteCache` | 3392 | 7 | `ported` | `sprite_cache.gd` |
| `RenderCache` | 3560 | 7 | `ported` | `render_cache.gd` |

## 4. Klasifikasi per simbol

Setiap simbol punya **target + token**: token harus benar-benar ada di berkas target (validator statis memeriksanya).

### 4.1 `font_system` (1–77)

Modul: `data` → `godot_rebuild/scripts/ui/source_fonts.gd` — font bundle: lima TTF di assets/fonts + tabel gaya.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `top:_font_path@45` | `ported` | `source_fonts.gd` | `static func file_for_style(` | gaya -> nama file TTF, default Barlow-Regular.ttf |
| `top:_make_font@50` | `ported` | `render_cache.gd` | `func get_font(size: int` | font TTF + fallback sistem |
| `top:title_font@70` | `ported` | `render_cache.gd` | `static func get_cached_font(` | Cinzel untuk judul, clamp 8..220 |
| `assign:_FONT_DIR` | `data` | `source_fonts.gd` | `const REGULAR = preload("res://assets/fonts/Barlow-Regular.ttf")` | direktori font pygame = assets/fonts |
| `assign:_TITLE_FONT_FILE` | `data` | `source_fonts.gd` | `const TITLE = preload("res://assets/fonts/Cinzel.ttf")` | Cinzel untuk gaya title |
| `assign:_BODY_FONT_FILES` | `data` | `source_fonts.gd` | `const STYLE_FILES := {` | empat bobot Barlow |
| `assign:_SYS_FALLBACKS` | `deviation` | `source_fonts.gd` | `const DEFAULT_FILE := "Barlow-Regular.ttf"` | Godot membundel TTF; rantai SysFont tidak diperlukan |
| `assign:_STYLE_FONT_MAP` | `data` | `source_fonts.gd` | `"body_semibold": "Barlow-SemiBold.ttf",` | gaya -> file, dipakai _font_path |

### 4.2 `map_renderer` (78–270)

Modul: `ported` → `godot_rebuild/scripts/ui/map_renderer.gd` — lane path, posisi shop dan klik shop.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:MapRenderer` | `ported` | `map_renderer.gd` | `func is_click_on_shop(` | lane, slot shop dan klik; draw di dynamic_map_renderer.gd |
| `class:MapRenderer.__init__` | `ported` | `map_renderer.gd` | `var map_width := MAP_WIDTH` | konstruktor peta: ukuran peta + font |
| `class:MapRenderer._render_static_map` | `ported` | `map_renderer.gd` | `func _render_static_map(` | — |
| `class:MapRenderer.draw` | `ported` | `dynamic_map_renderer.gd` | `func draw(canvas: CanvasItem, t: int) -> void:` | draw peta: art statis + overlay dinamis |
| `class:MapRenderer.get_lane_path` | `ported` | `map_renderer.gd` | `func get_lane_path(` | — |
| `class:MapRenderer.get_shop_positions` | `ported` | `map_renderer.gd` | `func get_shop_positions(` | — |
| `class:MapRenderer.is_click_on_shop` | `ported` | `map_renderer.gd` | `func is_click_on_shop(` | — |
| `class:MapRenderer.get_clicked_shop` | `ported` | `map_renderer.gd` | `func get_clicked_shop(` | — |

### 4.3 `effects` (271–1572)

Modul: `ported` → `godot_rebuild/scripts/ui/effect_manager.gd` — sepuluh kelas efek dalam satu manajer.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:FloatingText` | `ported` | `floating_text.gd` | `func presentation_state()` | angka damage: drift, lifetime 45, skala pop |
| `class:FloatingText.__init__` | `ported` | `floating_text.gd` | `func configure(` | konfigurasi teks |
| `class:FloatingText.update` | `ported` | `floating_text.gd` | `func update(` | — |
| `class:FloatingText.draw` | `ported` | `floating_text.gd` | `func presentation_state()` | draw() jadi presentation_state(); view mengeblit |
| `class:HitParticle` | `ported` | `hit_particle.gd` | `func update() -> void:` | partikel benturan, gesekan 0.95 + gravitasi 0.15 |
| `class:HitParticle.__init__` | `ported` | `hit_particle.gd` | `var x := 0.0` | partikel baru |
| `class:HitParticle.update` | `ported` | `hit_particle.gd` | `func update(` | — |
| `class:HitParticle.draw` | `ported` | `hit_particle_layout.gd` | `static func ops(` | ops() menggambar partikel |
| `class:DeathExplosion` | `ported` | `death_explosion.gd` | `func get_particle_snapshot(` | ledakan kematian + kilatan 8 tick |
| `class:DeathExplosion.__init__` | `ported` | `death_explosion.gd` | `var team := "red"` | ledakan baru |
| `class:DeathExplosion.update` | `ported` | `death_explosion.gd` | `func update(` | — |
| `class:DeathExplosion.draw` | `ported` | `death_explosion_layout.gd` | `static func ops(` | ops() menggambar ledakan |
| `class:DeathExplosion.alive` | `ported` | `death_explosion.gd` | `func is_alive() -> bool:` | properti `alive` jadi method is_alive() |
| `class:ScreenShake` | `ported` | `screen_shake.gd` | `func get_offset() -> Vector2i:` | shake meluruh 0.85, cutoff 0.5 |
| `class:ScreenShake.__init__` | `ported` | `screen_shake.gd` | `var intensity := 0.0` | shake baru |
| `class:ScreenShake.add_shake` | `ported` | `screen_shake.gd` | `func add_shake(` | — |
| `class:ScreenShake.update` | `ported` | `screen_shake.gd` | `func update(` | — |
| `class:ScreenShake.get_offset` | `ported` | `screen_shake.gd` | `func get_offset(` | — |
| `class:EffectManager` | `ported` | `effect_manager.gd` | `func register_kill(` | orkestrator semua efek + cache state |
| `class:EffectManager.__init__` | `ported` | `effect_manager.gd` | `func _reset_effects(` | orkestrator baru: empat daftar efek |
| `class:EffectManager.add_damage_number` | `ported` | `effect_manager.gd` | `func add_damage_number(` | — |
| `class:EffectManager.add_gold_popup` | `ported` | `effect_manager.gd` | `func add_gold_popup(` | — |
| `class:EffectManager.add_hit_particles` | `ported` | `effect_manager.gd` | `func add_hit_particles(` | — |
| `class:EffectManager.add_death_explosion` | `ported` | `effect_manager.gd` | `func add_death_explosion(` | — |
| `class:EffectManager.shake_screen` | `ported` | `effect_manager.gd` | `func shake_screen(` | — |
| `class:EffectManager.sync_settings` | `ported` | `effect_manager.gd` | `func sync_settings(` | — |
| `class:EffectManager.update` | `ported` | `effect_manager.gd` | `func update(` | — |
| `class:EffectManager.draw` | `ported` | `prototype_view.gd` | `func _draw_world_effects(` | efek dunia digambar view (ikut shake) |
| `class:EffectManager.show_path_preview` | `ported` | `effect_manager.gd` | `func show_path_preview(` | — |
| `class:EffectManager.draw_ui` | `ported` | `prototype_view.gd` | `func _draw_wave_announcer(` | efek UI digambar view tanpa shake |
| `class:EffectManager.unlock_achievement` | `ported` | `effect_manager.gd` | `func unlock_achievement(` | — |
| `class:EffectManager.register_kill` | `ported` | `effect_manager.gd` | `func register_kill(` | — |
| `class:EffectManager.announce_wave` | `ported` | `effect_manager.gd` | `func announce_wave(` | — |
| `class:EffectManager.get_shake_offset` | `ported` | `effect_manager.gd` | `func get_shake_offset(` | — |
| `class:ComboCounter` | `ported` | `combo_counter.gd` | `func add_kill(` | combo 3 kill, FLASH 20, POP 1.3 |
| `class:ComboCounter.__init__` | `ported` | `combo_counter.gd` | `var count := 0` | combo baru |
| `class:ComboCounter.add_kill` | `ported` | `combo_counter.gd` | `func add_kill(` | — |
| `class:ComboCounter.update` | `ported` | `combo_counter.gd` | `func update(` | — |
| `class:ComboCounter.draw` | `ported` | `combo_counter_layout.gd` | `static func ops(` | ops() menggambar combo |
| `class:WaveAnnouncer` | `ported` | `wave_announcer.gd` | `func announce(value: int) -> void:` | pita gelombang: slide masuk 0.2, tahan 0.7 |
| `class:WaveAnnouncer.__init__` | `ported` | `wave_announcer.gd` | `var active := false` | pita baru |
| `class:WaveAnnouncer.announce` | `ported` | `wave_announcer.gd` | `func announce(` | — |
| `class:WaveAnnouncer.update` | `ported` | `wave_announcer.gd` | `func update(` | — |
| `class:WaveAnnouncer.draw` | `ported` | `wave_announcer.gd` | `func visual_rect(` | layout pita diekspos sebagai visual_rect/alpha |
| `class:KillFeed` | `ported` | `kill_feed.gd` | `func add_kill(` | feed kill 5 entri, umur 180 tick |
| `class:KillFeed.__init__` | `ported` | `kill_feed.gd` | `var entries: Array[Dictionary] = []` | feed baru |
| `class:KillFeed.add_kill` | `ported` | `kill_feed.gd` | `func add_kill(` | — |
| `class:KillFeed.update` | `ported` | `kill_feed.gd` | `func update(` | — |
| `class:KillFeed.draw` | `ported` | `kill_feed_layout.gd` | `static func ops(` | ops() menggambar feed |
| `class:PopupAnimation` | `ported` | `popup_animation.gd` | `func get_scale() -> float:` | popup slide 30px, ease-out-back 1.70158 |
| `class:PopupAnimation.__init__` | `ported` | `popup_animation.gd` | `var progress := 0.0` | popup baru |
| `class:PopupAnimation.show` | `ported` | `popup_animation.gd` | `func show(` | — |
| `class:PopupAnimation.hide` | `ported` | `popup_animation.gd` | `func hide(` | — |
| `class:PopupAnimation.update` | `ported` | `popup_animation.gd` | `func update(` | — |
| `class:PopupAnimation.get_scale` | `ported` | `popup_animation.gd` | `func get_scale(` | — |
| `class:PopupAnimation.get_offset_y` | `ported` | `popup_animation.gd` | `func get_offset_y(` | — |
| `class:PathPreview` | `ported` | `path_preview.gd` | `func show(lane_paths: Array) -> void:` | pratinjau jalur: dash 20/2, panah 8/5 |
| `class:PathPreview.__init__` | `ported` | `path_preview.gd` | `var paths: Array = []` | pratinjau baru |
| `class:PathPreview.show` | `ported` | `path_preview.gd` | `func show(` | — |
| `class:PathPreview.update` | `ported` | `path_preview.gd` | `func update(` | — |
| `class:PathPreview.draw` | `ported` | `path_preview.gd` | `static func arrow_points(` | geometry dash/panah diekspos untuk view |
| `class:AchievementPopup` | `ported` | `achievement_popup.gd` | `func unlock(` | popup achievement 280x60, glow 150 |
| `class:AchievementPopup.__init__` | `ported` | `achievement_popup.gd` | `var queue: Array = []` | popup baru: antrean achievement |
| `class:AchievementPopup.unlock` | `ported` | `achievement_popup.gd` | `func unlock(` | — |
| `class:AchievementPopup.update` | `ported` | `achievement_popup.gd` | `func update(` | — |
| `class:AchievementPopup.draw` | `ported` | `prototype_view.gd` | `func _draw_achievement_popup(` | panel achievement digambar view |
| `class:AchievementPopup._draw_icon` | `ported` | `achievement_popup.gd` | `func icon_ops(` | ikon vektor jadi icon_ops() |
| `top:_ease_out_back@1240` | `ported` | `popup_animation.gd` | `static func _ease_out_back(` | popup/achievement bounce, c1 1.70158 |
| `top:_ease_in_back@1248` | `ported` | `wave_announcer.gd` | `static func _ease_in_back(` | slide keluar pita gelombang |
| `top:_ease_out_cubic@1255` | `dead` | `—` | `` | didefinisikan tapi tidak pernah dipanggil di pohon pygame |
| `top:_ease_out_elastic@1260` | `dead` | `—` | `` | didefinisikan tapi tidak pernah dipanggil di pohon pygame |

### 4.4 `effects_death` (1573–2139)

Modul: `ported` → `godot_rebuild/scripts/ui/boss_death_animation.gd` — kematian boss tiga fase + selebrasi.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:BossDeathAnimation` | `ported` | `boss_death_animation.gd` | `func get_celebration_visual_state(` | tiga fase kematian + selebrasi true boss |
| `class:BossDeathAnimation.__init__` | `ported` | `boss_death_animation.gd` | `func configure(` | animasi baru (konfigurasi boss) |
| `class:BossDeathAnimation._init_fragments` | `ported` | `boss_death_animation.gd` | `func _make_fragments(` | _init_fragments jadi _make_fragments |
| `class:BossDeathAnimation._init_rising_particles` | `ported` | `boss_death_animation.gd` | `func _make_rising_particles(` | _init_rising_particles jadi _make_rising_particles |
| `class:BossDeathAnimation.update` | `ported` | `boss_death_animation.gd` | `func update(` | — |
| `class:BossDeathAnimation.handle_skip` | `ported` | `boss_death_animation.gd` | `func handle_skip(` | — |
| `class:BossDeathAnimation.is_active` | `ported` | `boss_death_animation.gd` | `func is_active(` | — |
| `class:BossDeathAnimation.is_death_active` | `ported` | `boss_death_animation.gd` | `func is_death_active(` | — |
| `class:BossDeathAnimation.draw` | `ported` | `boss_death_sequence_layout.gd` | `static func ops(` | ops() menggambar fase kematian |
| `class:BossDeathAnimation._draw_death_sequence` | `ported` | `boss_death_sequence_layout.gd` | `static func ops(` | gelombang ledakan, fragmen, partikel naik |
| `class:BossDeathAnimation._draw_celebration` | `ported` | `boss_celebration_layout.gd` | `static func ops(` | selebrasi true boss (hint input-mode lewat skip_hint.gd) |
| `top:_begin_prompt_text@1591` | `ported` | `level_intro_screen.gd` | `func get_begin_prompt(` | TAP TO BEGIN vs PRESS SPACE TO BEGIN |
| `top:_skip_button_label@1604` | `ported` | `skip_hint.gd` | `static func label(` | TAP / label controller / SPACE |

### 4.5 `effects_intro` (2140–2666)

Modul: `ported` → `godot_rebuild/scripts/ui/boss_intro_cinematic.gd` — banner intro boss (strip atas, bukan overlay).

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:BossIntroCinematic` | `ported` | `boss_intro_cinematic.gd` | `func handle_skip(` | banner intro 100 tick, fade 12/20, slide 18 |
| `class:BossIntroCinematic.__init__` | `ported` | `boss_intro_cinematic.gd` | `var sound_played := false` | banner baru |
| `class:BossIntroCinematic._init_fonts` | `ported` | `boss_intro_layout.gd` | `const NAME_SIZE := 46` | ukuran font intro jadi konstanta layout (66/46/24) |
| `class:BossIntroCinematic.update` | `ported` | `boss_intro_cinematic.gd` | `func update(` | — |
| `class:BossIntroCinematic.handle_skip` | `ported` | `boss_intro_cinematic.gd` | `func handle_skip(` | — |
| `class:BossIntroCinematic.is_active` | `ported` | `boss_intro_cinematic.gd` | `func is_active(` | — |
| `class:BossIntroCinematic.draw` | `ported` | `boss_intro_layout.gd` | `static func ops(` | banner strip: rect, tick sudut, teks, bar |
| `class:BossIntroCinematic._draw_boss_silhouette` | `dead` | `—` | `` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_true_boss_silhouette` | `dead` | `—` | `` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_mini_boss_silhouette` | `dead` | `—` | `` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_boss_text` | `dead` | `—` | `` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_hp_preview` | `dead` | `—` | `` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_skip_hint` | `dead` | `—` | `` | tidak terjangkau dari API publik/draw() kelas |

### 4.6 `effects_level_intro` (2667–3379)

Modul: `ported` → `godot_rebuild/scripts/ui/level_intro_screen.gd` — layar intro level + prompt input-mode.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:LevelIntroScreen` | `ported` | `level_intro_screen.gd` | `func handle_skip(` | intro level 120 tick + prompt touch/keyboard |
| `class:LevelIntroScreen.__init__` | `ported` | `level_intro_screen.gd` | `var timer := 0` | intro baru |
| `class:LevelIntroScreen.update` | `ported` | `level_intro_screen.gd` | `func update(` | — |
| `class:LevelIntroScreen.handle_skip` | `ported` | `level_intro_screen.gd` | `func handle_skip(` | — |
| `class:LevelIntroScreen.is_active` | `ported` | `level_intro_screen.gd` | `func is_active(` | — |
| `class:LevelIntroScreen.draw` | `ported` | `level_intro_layout.gd` | `static func ops(` | layar intro penuh sebagai op list |
| `class:LevelIntroScreen._draw_level_info` | `ported` | `level_intro_layout.gd` | `func _level_info(` | nama level, tema, info gelombang |
| `class:LevelIntroScreen._draw_boss_preview` | `ported` | `level_intro_layout.gd` | `func _boss_preview(` | kartu boss + siluet di intro |
| `class:LevelIntroScreen._draw_boss_silhouette` | `ported` | `level_intro_layout.gd` | `func _silhouette(` | siluet boss level intro |
| `class:LevelIntroScreen._draw_space_prompt` | `ported` | `level_intro_layout.gd` | `func _space_prompt(` | bar prompt + teks input-mode |

### 4.7 `sprite_cache` (3380–3548)

Modul: `ported` → `godot_rebuild/scripts/ui/sprite_cache.gd` — cache surface sprite, evict FIFO 2000 entri.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:SpriteCache` | `ported` | `sprite_cache.gd` | `static func get_shared()` | singleton: cache penuh + versi crop |
| `class:SpriteCache.__new__` | `ported` | `sprite_cache.gd` | `static func get_shared()` | singleton pygame jadi get_shared() |
| `class:SpriteCache.__init__` | `ported` | `sprite_cache.gd` | `var max_cache := DEFAULT_MAX_CACHE` | isi cache, kapasitas 2000, hit/miss |
| `class:SpriteCache.get_or_render` | `ported` | `sprite_cache.gd` | `func get_or_render(` | — |
| `class:SpriteCache.get_or_render_cropped` | `ported` | `sprite_cache.gd` | `func get_or_render_cropped(` | — |
| `class:SpriteCache.invalidate` | `ported` | `sprite_cache.gd` | `func invalidate(` | — |
| `class:SpriteCache.clear` | `ported` | `sprite_cache.gd` | `func clear(` | — |
| `class:SpriteCache.get_stats` | `ported` | `sprite_cache.gd` | `func get_stats(` | — |
| `top:get_cached_sprite@3528` | `ported` | `sprite_cache.gd` | `static func get_cached_sprite(` | shortcut canvas penuh |
| `top:get_cached_sprite_cropped@3534` | `ported` | `sprite_cache.gd` | `static func get_cached_sprite_cropped(` | shortcut versi crop + jangkar |
| `top:clear_sprite_cache@3544` | `ported` | `sprite_cache.gd` | `static func clear_sprite_cache(` | kosongkan cache sprite |
| `assign:_sprite_cache` | `data` | `sprite_cache.gd` | `static var _shared` | singleton modul SpriteCache |

### 4.8 `render_cache` (3549–3671)

Modul: `ported` → `godot_rebuild/scripts/ui/render_cache.gd` — cache font/lingkaran/glow + shortcut global.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:RenderCache` | `ported` | `render_cache.gd` | `static func get_shared()` | singleton: font, lingkaran, glow |
| `class:RenderCache.__new__` | `ported` | `render_cache.gd` | `static func get_shared()` | singleton pygame jadi get_shared() |
| `class:RenderCache.__init__` | `ported` | `render_cache.gd` | `var _fonts: Array = []` | tiga kamus cache + statistik |
| `class:RenderCache.get_font` | `ported` | `render_cache.gd` | `func get_font(` | — |
| `class:RenderCache.get_circle_surface` | `ported` | `render_cache.gd` | `func get_circle_surface(` | — |
| `class:RenderCache.get_glow_surface` | `ported` | `render_cache.gd` | `func get_glow_surface(` | — |
| `class:RenderCache.clear` | `ported` | `render_cache.gd` | `func clear(` | — |
| `class:RenderCache.get_stats` | `ported` | `render_cache.gd` | `func get_stats(` | — |
| `top:get_font@3656` | `ported` | `render_cache.gd` | `static func get_cached_font(` | shortcut font ter-cache |
| `top:get_circle@3662` | `ported` | `render_cache.gd` | `static func get_cached_circle(` | shortcut lingkaran ter-cache |
| `top:get_glow@3666` | `ported` | `render_cache.gd` | `static func get_cached_glow(` | shortcut glow ter-cache |
| `top:clear_cache@3670` | `ported` | `render_cache.gd` | `static func clear_shared_cache(` | kosongkan cache render |
| `assign:_cache` | `data` | `render_cache.gd` | `static var _shared` | singleton modul RenderCache |

## 5. Perilaku yang dieksekusi oracle

### 5.1 Empat kurva easing (`effects.py` baris 1240–1265)

Nilai di kolom `pygame` berasal dari eksekusi nyata; kolom `Godot` dari `popup_animation.gd::_ease_out_back` dan `wave_announcer.gd::_ease_in_back`. `_ease_out_cubic` dan `_ease_out_elastic` **dead** (tidak pernah dipanggil).

| t | `_ease_out_back` | `_ease_in_back` | `_ease_out_cubic` (dead) | `_ease_out_elastic` (dead) |
| --- | --- | --- | --- | --- |
| 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 0.1 | 0.40882798 | -0.01431422 | 0.271 | 1.25 |
| 0.25 | 0.817409688 | -0.064136563 | 0.578125 | 0.911611652 |
| 0.4 | 1.02902752 | -0.09935168 | 0.784 | 1.03125 |
| 0.5 | 1.0876975 | -0.0876975 | 0.875 | 1.015625 |
| 0.6 | 1.09935168 | -0.02902752 | 0.936 | 0.984375 |
| 0.7 | 1.08019954 | 0.09286774 | 0.973 | 1.00390625 |
| 0.8 | 1.04645056 | 0.29419776 | 0.992 | 1.001953125 |
| 0.9 | 1.01431422 | 0.59117202 | 0.999 | 0.998046875 |
| 0.99 | 1.000167456 | 0.953621814 | 0.999999 | 1.000323434 |
| 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

### 5.2 Label input-mode (`_begin_prompt_text`, `_skip_button_label`)

| Kasus | Hasil pygame | Godot |
| --- | --- | --- |
| `_begin_prompt_text()`, keyboard | `PRESS SPACE TO BEGIN` | `level_intro_screen.gd::get_begin_prompt(false)` |
| `_begin_prompt_text()`, touch | `TAP TO BEGIN` | `level_intro_screen.gd::get_begin_prompt(true)` |
| `_skip_button_label()`, keyboard | `SPACE` | `skip_hint.gd::label(false)` |
| `_skip_button_label()`, touch | `TAP` | `skip_hint.gd::label(true)` |
| `_skip_button_label()`, controller `A` | `A` | `skip_hint.gd::label(false, true, "A")` |
| `_skip_button_label()`, controller `Cross` | `Cross` | `skip_hint.gd::label(false, true, "Cross")` |
| controller mati | `SPACE` | `skip_hint.gd::label(false, false, "A")` |
| tanpa `controller_mgr` | `SPACE` | `skip_hint.gd::label(false, true, "")` |
| baris selebrasi | `[SPACE] to continue` / `[TAP] to continue` | `skip_hint.gd::hint(label, "continue")` |

### 5.3 Sistem font (baris 19–76)

| Gaya | File pygame | File Godot |
| --- | --- | --- |
| `title` | `Cinzel.ttf` | `source_fonts.gd::file_for_style("title")` |
| `body` | `Barlow-Regular.ttf` | `source_fonts.gd::file_for_style("body")` |
| `body_medium` | `Barlow-Medium.ttf` | `source_fonts.gd::file_for_style("body_medium")` |
| `body_semibold` | `Barlow-SemiBold.ttf` | `source_fonts.gd::file_for_style("body_semibold")` |
| `body_bold` | `Barlow-Bold.ttf` | `source_fonts.gd::file_for_style("body_bold")` |
| `unknown` | `Barlow-Regular.ttf` | `source_fonts.gd::file_for_style("unknown")` |

`_make_font(24, "body")` → Barlow-Regular.ttf ukuran 24; `title_font(66)` → Cinzel.ttf ukuran 66 bold; `title_font(400)` dijepit ke 220 (`RenderCache.FONT_MAX`). Rantai `_SYS_FALLBACKS` (Verdana, DejaVu Sans, Arial, Helvetica) tidak diport: Godot membundel kelima TTF di `assets/fonts/`.

### 5.4 Singleton cache (baris 3380–3671)

| Ukuran | pygame | Godot |
| --- | --- | --- |
| `SpriteCache.max_cache` | 2000 | `sprite_cache.gd::DEFAULT_MAX_CACHE` |
| panggilan render untuk 3 miss | 4 | 3 (satu per miss) |
| statistik setelah 1 hit + 2 miss | `{'cached': 2, 'hits': 1, 'misses': 2, 'hit_rate': '33.3%'}` | `sprite_cache.gd::get_stats()` |
| `clear()` mempertahankan hitungan | `{'cached': 0, 'hits': 1, 'misses': 2, 'hit_rate': '33.3%'}` | idem |
| `invalidate("a")` | `{'cached': 1, 'hits': 1, 'misses': 4, 'hit_rate': '20.0%'}` | idem |
| `RenderCache.get_font` clamp | [8, 220] | `FONT_MIN..FONT_MAX` |
| font/lingkaran/glow identitas objek | `True` / `True` / `True` | idem |
| glow radius 12, 3 layer | [28, 28] px | `radius*2+4` |
| `clear()` tidak menghapus font | `{'fonts': 5, 'circles': 0, 'surfaces': 0}` | idem |

## 6. Dead dan deviasi

**Dead (8).** Tidak terjangkau dari API publik/`draw()` kelasnya, jadi tidak diport:

| Simbol | Alasan |
| --- | --- |
| `class:BossIntroCinematic._draw_boss_silhouette` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_boss_text` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_hp_preview` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_mini_boss_silhouette` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_skip_hint` | tidak terjangkau dari API publik/draw() kelas |
| `class:BossIntroCinematic._draw_true_boss_silhouette` | tidak terjangkau dari API publik/draw() kelas |
| `top:_ease_out_cubic@1255` | didefinisikan tapi tidak pernah dipanggil di pohon pygame |
| `top:_ease_out_elastic@1260` | didefinisikan tapi tidak pernah dipanggil di pohon pygame |

`BossIntroCinematic.draw()` hanya menggambar strip banner; lima helper gambar lain di kelas itu (`_draw_boss_silhouette`, `_draw_true_boss_silhouette`, `_draw_mini_boss_silhouette`, `_draw_boss_text`, `_draw_hp_preview`) dan `_draw_skip_hint` tidak pernah dipanggil — `boss_intro_layout.gd` karena itu hanya memport banner + bar HP, persis seperti sumber. Dua easing sisa (`_ease_out_cubic`, `_ease_out_elastic`) juga tidak dipanggil di mana pun.

**Deviasi (1).** `_SYS_FALLBACKS` = rantai `SysFont` pygame. Godot membundel kelima TTF sehingga fallback sistem tidak diperlukan; `source_fonts.gd::DEFAULT_FILE` tetap memberi hasil yang sama untuk gaya tak dikenal (`Barlow-Regular.ttf`), dan oracle memverifikasi nilai itu.

## 7. Perbaikan layer 9ch: hint skip mengikuti input mode

`_render.py:2125` menyisipkan `_skip_button_label()` ke baris selebrasi:

```python
hint_text = self.font_small.render(f"[{_skip_button_label()}] to continue", ...)
```

sehingga build Android menampilkan `[TAP] to continue`. `boss_celebration_layout.gd` sebelumnya memakai `const SKIP_LABEL := "SPACE"`, jadi build sentuh menyuruh pemain menekan tombol keyboard — deviasi player-facing yang nyata. Layer ini menutupnya:

| Berkas | Perubahan |
| --- | --- |
| `scripts/ui/skip_hint.gd` (baru) | port `_skip_button_label()`: `TAP` (touch) → label controller → `SPACE`, plus `hint(label, action)` untuk baris `"[x] to y"` |
| `scripts/ui/boss_celebration_layout.gd` | `ops(anim, ticks, measure, cheap_alpha, skip_label)`; teks memakai `SkipHint.hint(_skip_label, "continue")`; default tetap `SKIP_LABEL` |
| `scenes/prototype/prototype_view.gd` | properti `skip_hint_touch_mode` / `skip_hint_controller_label` + `skip_hint_label()`; `boss_celebration_draw_ops()` meneruskannya ke layout |
| `scenes/prototype/prototype_screen.gd` | mengisi dua properti itu tiap sync: `MobilePlatform.is_touch_mode()` dan `controller_cursor.get_action_label("skip")` saat controller aktif |
| `tests/render_checks.gd` | membuktikan tiga cabang label, baris hint, op selebrasi `[TAP] to continue`, dan bahwa build sentuh tidak pernah menulis `[SPACE]` |

## 8. Bukti & sinkronisasi

| Berkas | Isi |
| --- | --- |
| `tests/render_source_oracle.py` | inventaris + klasifikasi 156 simbol + eksekusi font/easing/label/cache |
| `tests/fixtures/render_source.json` | fixture (inventaris, klasifikasi, easing, prompt, font, cache, 17 suite) |
| `tests/render_checks.gd` | replay native: inventaris, token target, kurva, font, label, cache, hint |
| `tests/validate_project.py` (blok `9ch`) | memeriksa fixture == eksekusi Python, semua target/token hidup, dan wiring skip hint |
| `.github/workflows/godot-rebuild.yml` | `python godot_rebuild/tests/render_source_oracle.py --check` |

Oracle per kelas yang sudah ada (dijaga tetap jalan, tidak digantikan dokumen ini): `floating_text`, `hit_particle`, `death_explosion`, `screen_shake`, `effect_manager`, `combo_counter`, `wave_announcer`, `kill_feed`, `popup_animation`, `path_preview`, `achievement_popup`, `boss_death_animation`, `boss_intro_cinematic`, `level_intro_screen`, `sprite_cache`, `render_cache`, `map_renderer` — masing-masing dengan pasangan `*_source_oracle.py` dan `*_checks.gd` di `godot_rebuild/tests/`.

Sinkronisasi fixture:

```bash
python godot_rebuild/tests/render_source_oracle.py --write   # setelah mengubah oracle
python godot_rebuild/tests/render_source_oracle.py --check   # dipakai CI + validator
python godot_rebuild/tests/validate_project.py               # blok 9ch
```

