# Peta cakupan `_render.py` → Godot

**Apa ini:** audit blok-per-blok `_render.py` (3.671 baris — gabungan 7 modul
lama: `map_renderer.py`, `effects.py`, `effects_death.py`, `effects_intro.py`,
`effects_level_intro.py`, `sprite_cache.py`, `render_cache.py`; lihat docstring
`:1-11`) terhadap port Godot di `godot/`. Dipakai untuk menjawab "blok
`_render.py` mana yang sudah pindah, mana yang tidak usah, mana yang belum"
tanpa menebak dari nama berkas.

**Cara baca:** setiap baris = blok pygame dengan rentang baris di `_render.py`,
padanannya di Godot, dan statusnya.

| Status | Arti |
|---|---|
| ✅ PORTED | Perilaku diport dan **dikunci fixture/oracle** (tes paritas menyebutnya) |
| 🟡 PARSIAL | Ada padanannya, tapi sebagian perilaku belum ada / belum diuji |
| ❌ BELUM | Tidak ada padanan di Godot |
| ⚪ N/A | Kode pygame-nya sendiri mati (tidak pernah dipakai) atau khusus engine pygame |

Oracle + fixture FASE 26: `tools/test_render_parity.py` →
`godot/tests/fixtures/render_fx.json`; replay headless:
`godot/tests/RenderFxParityTest.tscn`. Peta cakupan modul lain:
[`_core.py`](CORE_PY_COVERAGE.md) · [`_entity.py`](ENTITY_PY_COVERAGE.md) ·
[`_system.py`](SYSTEM_PY_COVERAGE.md); status paritas umum:
[GODOT_PARITY.md](GODOT_PARITY.md).

---

## 1. Font system — `_render.py:18-77`

| Blok | Padanan Godot | Status |
|---|---|---|
| `_FONT_DIR` + `_STYLE_FONT_MAP` (Cinzel + 4 weight Barlow, `:27-43`) | `godot/assets/fonts/*.ttf` (ikut repo) di-`preload` sebagai `FontFile` oleh tiap layar yang membutuhkannya | ✅ fontnya sama persis (5 berkas disalin apa adanya) |
| `_make_font` fallback SysFont → font bawaan (`:50-68`) | — (Godot tidak punya font sistem; `FontFile` langsung) | ⚪ mekanisme fallback khusus pygame |
| `get_font(size, style, bold)` ter-cache + clamp 8..220 (`:3656-3660`, `RenderCache.get_font` `:3573-3581`) | ukuran font literal per situs (`add_theme_font_size_override` / argumen `draw_string`) | 🟡 clamp 8..220 tidak direplikasi sebagai satu pintu; ukuran yang dipakai tiap layar sudah dikunci `UiHudParityTest` (fixture `match_parity.ui_hud`) |
| `title_font(size, bold=True)` (`:70-74`) | Cinzel di `LevelIntro.gd`, `BossIntroBanner.gd`, `BossDeathFX.gd`, `MainMenu.gd`, `ScreenTitle.gd`, `GameOverOverlay.gd` | ✅ |

## 2. `map_renderer.py` — `_render.py:80-282`

| Blok | Padanan Godot | Status |
|---|---|---|
| `MapRenderer.__init__` (tema, posisi toko, lane/river/dekor dari `map_components`) | `scenes/map/ArenaMap.gd` + `data/themes.json` + `data/map_bakes.json` | ✅ (Fase 3/7; 54 tema + 54 bake tekstur ikut repo) |
| `_render_static_map` 6 layer (`:143-186`) | tekstur bake tunggal per tema (`tools/convert_to_godot.py` menjalankan renderer pygame asli) | ✅ byte-per-byte dikunci `tools/visual_parity_audit.py` (FRESH-*) |
| `draw` + `ambient_tint` (`:190-221`) | `ArenaMap._draw` + `CanvasModulate`/`WorldEnvironment` | 🟡 tint dipetakan ke `modulate`, bukan `BLEND_RGB_MULT` per piksel — dicatat di `docs/AUDIT_PARITAS.md` |
| `get_lane_path(lane_name)` (`:223-231`) | `ArenaMap.get_lane_path` (port `PathGenerator` + `Curve2D`) | ✅ (fixture `render_fx.path_preview.paths` memakai titik PathGenerator ASLI: 111/65/101 titik) |
| `get_shop_positions` / `is_click_on_shop` / `get_clicked_shop` (`:233-281`) | `ArenaMap.get_clicked_shop` (radius 60 = `shop_size`) | ✅ (dikunci `UiHudParityTest`; lihat GODOT_PARITY "bangunan toko di map") |
| `dynamic` (DynamicRenderer partikel/cuaca) | `ArenaMap._apply_weather()` + 2 `CPUParticles2D` | ✅ gerak (bukan warna) direplikasi; lihat `godot/README.md` |

## 3. `effects.py` — `_render.py:283-1370`

| Blok | Padanan Godot | Status |
|---|---|---|
| `FloatingText` (`:283-417`) — gerak, drift, pop-in scale, pre-render teks | `scripts/utils/FloatingTextQueue.gd` (data) + `scenes/fx/WorldPopups.gd` (draw) + `scenes/fx/DamageNumber.gd` | ✅ (fixture `match_parity` + `system_perf`; raster font tidak diklaim identik) |
| **`HitParticle` (`:418-493`)** — gravitasi 0.15, gesekan 0.95, sprite pra-render 3·base px, alpha `int(255·sisa)`, ukuran `max(1, int(size·sisa))` | **`scripts/render/HitSpark.gd`** | ✅ **FASE 26** — fixture `render_fx.spark`: 3 skenario × 73 frame, jejak `draw.circle` + `transform.scale` + `blit` + `set_alpha` sungguhan |
| **`DeathExplosion` (`:494-571`)** — 8/15/25 partikel, palet tim, kilat pusat 8 frame | **`scripts/render/DeathBurst.gd`** | ✅ **FASE 26** — fixture `render_fx.burst`: 4 skenario (small/medium/large × 2 tim), 32 frame / 792 op + urutan konsumsi RNG |
| `ScreenShake` (`:572-600`) — decay 0.85, `max`, stop < 0.5 | `scenes/main/GameCamera.gd` | ✅ (dikunci temuan 7 `PARITY_AUDIT.md`; 1.0 trauma = 60 px) |
| `EffectManager` daftar `particles`/`explosions` + batas `MAX_PARTICLES 500` / `MAX_EXPLOSIONS 80` + `add_hit_particles` + `add_death_explosion` + `update`/`draw` (`:601-800`) | **`scripts/render/SparkField.gd`** (data, dimiliki `GameManager.spark_fx`) + **`scenes/fx/SparkLayer.gd`** (draw) | ✅ **FASE 26** — fixture `render_fx.hit` (4 skenario) + `render_fx.caps` (600→500 partikel, 90→80 ledakan, yang terbuang yang TERTUA) |
| `EffectManager` bagian lain: `add_damage_number`/`add_gold_popup`/`combo_counter`/`wave_announcer`/`achievement`/`shake_screen`/`get_shake_offset` (`:627-711`, `:802-838`) | `FloatingTextQueue` · `ComboCounter` · `HUD`/`WavePlate` · `AchievementPopup` · `GameCamera` | ✅ sudah diport sebelum FASE 26 (Fase 12-14, 23) |
| `EffectManager.path_preview` + `show_path_preview` (`:623`, `:784`, `:789`, `:797-799`) | **`scenes/fx/PathPreview.gd`** + `Main._show_path_preview()` dari `_on_wave_started` | ✅ **FASE 26** — fixture `render_fx.path_preview`: 130 frame state machine + 16 frame × 35 polygon |
| `ComboCounter` (`:840-989`) — max_timer 120, flash 20, bar 80 px | `scripts/utils/ComboCounter.gd` + `scenes/ui/ComboBadge.gd` | ✅ (fixture `match_parity.match_scoring`; quirk `max_combo` dibaca sebelum `add_kill` ikut dikunci) |
| `WaveAnnouncer` (`:990-1102`) — panel 400×80, slide ease-out-back, tahan, keluar | `scenes/ui/HUD.gd` + `scenes/ui/widgets/WavePlate.gd` + `scripts/utils/HudLayout.gd` | ✅ (fixture `match_parity.ui_hud`: 82 skenario draw) |
| `KillFeed` (`:1103-1201`) | — | ⚪ **tidak diport: dead code.** Dibuat (`:622`) dan di-`update` (`:783`), tapi `add_kill`/`draw` **nol call site** di seluruh repo — pygame sendiri tidak pernah menampilkannya (panel kanan diisi command saja, komentar `:817-826`). Dikunci `render_fx.dead.kill_feed_render.sites == []` |
| `PopupAnimation` (`:1202-1239`) | — | ⚪ **tidak diport: dead code.** `show()`/`hide()`/`update()` dipanggil `_core.py:2585/2598/2020`, tapi `get_scale()`/`get_offset_y()` — satu-satunya keluaran yang bisa digambar — **nol call site**. Dikunci `render_fx.dead.popup_animation_render.sites == []` |
| easing `_ease_out_back` / `_ease_in_back` / `_ease_out_cubic` / `_ease_out_elastic` (`:1240-1274`) | `HudLayout._ease_out_back` (c1 1.70158 identik) dipakai wave plate + achievement | ✅ untuk dua kurva yang benar-benar dipakai; `_ease_in_back`/`_ease_out_cubic`/`_ease_out_elastic` hanya dipakai layar cinematic yang memakai tween Godot | 
| **`PathPreview` (`:1275-1370`)** — 120 frame, fade in 20 / out 40, `alpha = int(200·ratio)`, `offset = int(t·2) % 20`, panah tiap 8 titik, pulse `(i//8 + offset//5) % 4` | **`scenes/fx/PathPreview.gd`** (`show_paths`/`tick`/`build_ops`) | ✅ **FASE 26** — fitur yang sebelumnya **hilang total** dari layar Godot (`PARITY_AUDIT.md` butir 4) |

## 4. `AchievementPopup` + helper prompt — `_render.py:1371-1621`

| Blok | Padanan Godot | Status |
|---|---|---|
| `AchievementPopup` (`:1371-1587`) — antrean, 180 frame, slide 300 px ease-out-back, gradien + border emas + ikon | `scenes/ui/AchievementPopup.gd` | ✅ (fixture `match_parity.match_scoring.achievement`: 3 kasus popup + 181 titik slide) |
| `_begin_prompt_text()` (`:1591-1600`) — "TAP TO BEGIN" di sentuh, "PRESS SPACE TO BEGIN" di keyboard | `LevelIntro.gd` menulis "PRESS SPACE TO BEGIN" tetap | 🟡 label tidak ikut mode input (sentuh tetap bisa tap; teksnya saja yang tidak berubah) |
| `_skip_button_label()` (`:1604-1621`) — 'TAP' / label controller / 'SPACE' | layar cinematic Godot menulis "SPACE" tetap | 🟡 sama seperti di atas; `ControllerManager.get_hints` sudah punya tabel label, tinggal disambung |

## 5. `effects_death.py` — `_render.py:1622-2151`

| Blok | Padanan Godot | Status |
|---|---|---|
| `BossDeathAnimation` (`:1622-2151`) — white flash 15f, 2-3 cincin, dissolve, 15/25 pecahan, 15/30 partikel roh, fase 60/90f **pause gameplay**, perayaan true boss 120f | `scenes/fx/BossDeathFX.gd` (dipanggil `Boss.die()`) | ✅ (Fase 5d; `CinematicTest` di CI) |

## 6. `effects_intro.py` — `_render.py:2152-2678`

| Blok | Padanan Godot | Status |
|---|---|---|
| `BossIntroCinematic` (`:2152-2678`) — strip 600×92 slide 100 frame, fade in 12f/out 20f, tag TRUE/MINI + warna `entrance_color` + HP bar preview, TIDAK pause | `scenes/ui/BossIntroBanner.gd` (dipicu `Main._boss_tick`) | ✅ (Fase 5d) |

## 7. `effects_level_intro.py` — `_render.py:2679-3391`

| Blok | Padanan Godot | Status |
|---|---|---|
| `LevelIntroScreen` (`:2679-3391`) — split-screen: angka level Cinzel 200 + nama + deskripsi + 5 bar kesulitan + VICTORY REWARD / STARTING GOLD / PASSIVE, kanan FINAL BOSS + siluet prosedural, tint tema, vignette, "PRESS SPACE TO BEGIN", **pause gameplay** | `scenes/ui/LevelIntro.gd` | ✅ (Fase 5d; rumus `compute_starting_gold` sama dengan `Game.reset`) |

## 8. `sprite_cache.py` — `_render.py:3392-3559`

| Blok | Padanan Godot | Status |
|---|---|---|
| `SpriteCache` singleton, cap 2000, evict tertua, `get_or_render` / `get_or_render_cropped` + statistik hit/miss (`:3392-3527`) | `scripts/render/BakedUnitDB.gd` + `BakedPropDB.gd` (manifest bake + tekstur lazy FIFO **64**) | ⚪ cache Surface adalah solusi masalah pygame (render prosedural per frame). Godot membaca strip PNG hasil bake; FIFO 64 membatasi tekstur hidup |
| `get_cached_sprite` / `get_cached_sprite_cropped` / `clear_sprite_cache` (`:3528-3559`) | — | ⚪ shortcut ke singleton di atas |

## 9. `render_cache.py` — `_render.py:3560-3671`

| Blok | Padanan Godot | Status |
|---|---|---|
| `RenderCache.get_font` (`:3573-3581`) | `FontFile` di-preload sekali per skrip (resource Godot sudah ter-cache engine) | ⚪ |
| `RenderCache.get_circle_surface` (`:3583-3610`) | `draw_circle` / `draw_arc` langsung | ⚪ Godot tidak butuh Surface per radius |
| `RenderCache.get_glow_surface` (`:3612-3635`) | `assets/shaders/bloom.gdshader` + `PointLight2D` | ⚪ glow 5 lapis pygame diganti 1 pass shader |
| `clear_cache()` (`:3641-3646`, `:3670`) | `BakedUnitDB` membuang tekstur saat ganti level | ⚪ |

---

## Temuan audit (tercatat, tidak "diperbaiki diam-diam")

1. **`PathPreview` benar-benar hilang dari Godot sebelum FASE 26.** Pygame
   memanggil `effects.show_path_preview([top, mid, bot])` setiap wave dimulai
   (`_core.py:1756-1762`) dan menggambarnya paling awal di
   `EffectManager.draw` (`:789`) — panah merah beranimasi 2 detik di sepanjang
   tiga lane. Tidak ada satu pun berkas Godot yang menyebutnya
   (`PARITY_AUDIT.md` butir 4). Kini diport penuh + dikunci fixture.
2. **`KillFeed` dan `PopupAnimation` bukan divergensi.** Keduanya dibuat dan
   di-update tetapi keluarannya tidak pernah digambar (lihat tabel §3). Klaim
   ini dijaga tool: kalau suatu hari pygame memanggil `kill_feed.draw` atau
   `popup_anim.get_scale`, `tools/test_render_parity.py` GAGAL dan port harus
   menyusul — bukan diam-diam basi.
3. **`add_hit_particles` pygame dipangkas adaptive quality.** Fungsi itu
   membaca `mobile.perf.Quality`; default desktop/HIGH adalah
   `particles=True`, `particle_ratio=0.70`, jadi jumlah sebenarnya di pygame
   adalah **4→3 (minion), 6→4 (boss), 10→7 (castle)**, bukan angka mentahnya.
   Port Godot memakai rasio **1.0** (jumlah penuh) karena lapisan adaptive
   quality belum diport (lihat [SYSTEM_PY_COVERAGE.md](SYSTEM_PY_COVERAGE.md)
   §3). Knob `SparkField.particle_ratio`/`particles_enabled` disediakan supaya
   port perf nanti tidak perlu menyentuh berkas ini. Faktanya direkam di
   fixture (`py_quality`) dan dikunci `RenderFxParityTest._test_wiring`.
4. **Percikan pukulan untuk minion/boss/castle BUKAN pelanggaran kontrak
   "serangan dasar tanpa impact FX".** Kontrak owner (dikunci
   `tools/test_basic_attack_no_impact_fx.py`) melarang *paket* FX hero
   (flash + shockwave + serpihan + shake + hit-stop lewat
   `notify_melee_impact`/`notify_projectile_impact`) pada serangan dasar, dan
   di Godot paket itu tetap skill-only (`Hero.play_hit_fx` dari
   `SkillBook._damage`). `EffectManager.add_hit_particles` adalah lapisan
   LAIN yang di pygame memang dipanggil `Minion.take_damage` (`_entity.py:5842`),
   `Boss.take_damage` (`base_boss.py:6057`), dan `Castle.take_damage`
   (`_entity.py:1816`) untuk **setiap** pukulan. `CombatSystem._hit_spark_count`
   mengembalikan **0 untuk hero dan menara** (keduanya tidak punya call site
   pygame), jadi tidak ada FX baru di jalur serangan dasar hero.
5. **`_fx_chain` (`hero_items.py:2728-2745`) belum diport.** Helper kilat
   berantai item (6 percikan biru per target + teks "ZAP!") dipanggil dari 8
   situs di `hero_items.py`; `ItemInventory.gd` sudah memport rantai
   damage-nya (`_chain_proc`) tapi belum FX-nya. Tercatat di
   `render_fx.call_sites.hit_particles` (kelas `HeroItemInventory`, count 6).
6. **Pusat sprite percikan bisa jatuh di setengah piksel.** Pygame mem-blit
   sprite hasil scale di `int(x) - ukuran*3//2`, sehingga pusat optisnya
   `posisi_blit + pusat_kanvas × faktor_skala` (base genap + ukuran gasal =
   offset 0,5 px). Port menyalin rumus itu apa adanya; jejak fixture yang
   menguncinya (contoh: partikel size 2 di x=642.0 digambar di 642.5).
7. **Titik panah `PathPreview` memakai floor pygame, dan `a − floor(b)` tidak
   sama dengan `a + floor(−b)`.** Ekspresi sumber
   `-cos_a*S//2 - sin_a*S//2` = `floor(−cos·S/2) − floor(sin·S/2)`; bentuk
   "lebih rapi" `floor(−cos·S/2) + floor(−sin·S/2)` meleset 1 px pada nilai
   non-bulat. Port memakai empat suku terpisah (`neg_cos_half`, `pos_sin_half`,
   …) dan kedua bentuk itu di-PIN tool oracle.

## Cara menjalankan

```bash
# 1) Oracle pygame (menulis/mengesahkan fixture + mengunci konstanta sumber .gd):
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_render_parity.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_render_parity.py --write-fixture

# 2) Replay Godot (butuh binary Godot; CI `godot-check.yml` langkah 4v):
export XDG_DATA_HOME="$(mktemp -d)"
godot --headless --path godot res://tests/RenderFxParityTest.tscn --quit-after 300
```

Sandbox tempat port ini dikerjakan tidak punya binary Godot, jadi replay di atas
hanya terbukti di CI: langkah 4v run `34560657146` **success** setelah dua run
sebelumnya menangkap `sqrtf()` (tidak ada di Godot 4) dan dua bug harness —
lihat `GODOT_PARITY.md` FASE 26 bagian Validasi.
