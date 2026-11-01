# Migrasi `_render.py` → Godot (`godot_rebuild/`)

Status: **native GDScript, tanpa Python saat runtime**. Python tetap menjadi
sumber kebenaran/oracle dan alat bake. Migrasi ini melanjutkan `main.py` (PR #377),
`_core.py` (PR #378), dan `_entity.py` (PR #379).

## Cakupan

| Sumber Python | Native Godot | Catatan |
|---|---|---|
| `_render.MapRenderer` (6 layer statis) | `scripts/render/MapView.gd` + `assets/maps/*.png` | 54 tema dibake 1280×720 oleh `tools/convert_to_godot.py --maps-png`; bukan TileSet karena 533/576 tile 40px unik. |
| `map_components.DynamicRenderer` | `MapView.draw_dynamic()` | Partikel firefly/snow/sand/ember/acid/ash/spirit, fog, rune sungai, glow/smoke toko, obor. Anchor sungai/obor/toko ikut dibake ke `map_bakes.json`. |
| `get_lane_path`, `get_shop_positions`, `is_click_on_shop`, `get_clicked_shop` | `MapView.get_lane_path/get_shop_positions/shop_at` | Lane dari `CoreData`; toko radiant (340,540) → item forge, dire (940,180) → hero shop, ukuran 60px. |
| font system (`get_font`, `title_font`, `_STYLE_FONT_MAP`) | `RenderCache.gd` | Cinzel + Barlow Regular/Medium/SemiBold/Bold; glyph diraster Godot saat draw, bukan Surface per-frame. |
| `RenderCache.get_circle/get_glow`, `SpriteCache` | `RenderCache.circle_texture/glow_texture`, `EntityVisuals` | Tekstur radial putih di-tint saat draw; sprite unit tetap strip bake dari migrasi entity. |
| `FloatingText`, `HitParticle`, `DeathExplosion`, `ScreenShake`, `EffectManager` | `CombatEffects.gd` | Cap 300 floating / 500 partikel / 80 ledakan; budget kualitas 8/16/32 damage number, rasio partikel 0.35/0.65/1.0. |
| `ComboCounter`, `WaveAnnouncer`, `PathPreview`, `AchievementPopup`, `PopupAnimation` | `CombatEffects.gd` | Timer 120/120/120/180 frame; easing popup `_ease_out_back`. |
| `KillFeed` | `CombatEffects.register_kill()` | **Sengaja no-op** secara default, mengikuti `draw_ui()` `_core.py` yang menghapus kill feed/combo notification atas permintaan user. |
| `_ease_out_back/_ease_in_back/_ease_out_cubic/_ease_out_elastic` | `RenderEasing.gd` | Rumus 1:1; sampel diuji terhadap oracle Python. |
| `LevelIntroScreen` | `RenderCinematics.gd` | Split-screen level/boss, fade 30 frame, blocking sampai Space/Enter/tap. |
| `BossIntroCinematic` | `RenderCinematics.gd` | 100 frame, blocking, skip-able; portrait memakai strip boss bake. |
| `BossDeathAnimation` | `RenderCinematics.gd` | 90 frame true boss / 60 mini, gelombang ledakan + flash + fragmen; selebrasi 120 frame (non-blocking). |
| `mobile.perf.Quality` | `RenderQuality.gd` + `GameSettings.render_quality` | Preset low/medium/high; `screen_shake_enabled` dan `damage_numbers_enabled` dihormati. |

## Arsitektur runtime

```
MatchModel.render_event(kind, data)
        │  damage / gold / popup / effect / shake / death / combo_kill /
        │  wave / path_preview / achievement / boss_intro / boss_death
        ▼
CoreGame._on_render_event()
        ├── CombatEffects   (floating text, sparks, explosions, shake, banners)
        ├── RenderCinematics(level intro, boss intro, boss death)
        └── MapView         (tema per level, partikel/fog dinamis)
                 ▲
ArenaView._draw()┘  world di-shake, UI tidak; cinematic overlay paling akhir
```

- `CoreGame.configure()` memilih tema dari `level_config.map_theme`, mengatur
  kualitas dari `GameSettings`, dan memulai `LevelIntroScreen`.
- `CoreGame.simulation_step()` berhenti memajukan `MatchModel` selama intro
  blocking; `cinematic_active()`/`skip_cinematic()` memenuhi kontrak `GameplayPort`
  yang sudah dipakai `Main.gd` (Space/tap/HUD skip).
- Klik toko pada peta membuka item forge/hero shop; Escape menutup popup.
- `MatchModel` tetap menyimpan array `effects/popups/shake` lama untuk kompatibilitas
  tes, tetapi renderer aktif sekarang adalah `CombatEffects`.

## Bake & kontrak data

```bash
# sekali / saat _render.py atau map_components berubah (butuh pygame-ce, numpy, Pillow)
python3 tools/prepare_godot_render.py --bake

# CI / verifikasi tanpa display stack
python3 tools/prepare_godot_render.py --check
python3 tools/test_godot_render_prepare.py
```

Artefak yang dilacak Git:

- `godot_rebuild/assets/maps/<tema>.png` — 54 tekstur statis opaque.
- `godot_rebuild/data/map_bakes.json` — manifest + anchor dinamis (river, torch,
  shop) + seed beku `MAP_BAKE_SEED`.
- `godot_rebuild/data/themes_raw.json` — palet/flag tema mentah (AST, tanpa pygame).
- `godot_rebuild/data/render_data.json` — kontrak AST: cap efek, timing, easing
  sampel, font map, posisi toko, preset kualitas, SHA-256 tiap PNG.

`export_map_bakes()` menelan exception dan exit 0; `prepare_godot_render.py`
**fail-closed** dengan memverifikasi jumlah tema, dimensi PNG, anchor, dan cakupan
semua `map_theme` level sebelum menulis kontrak.

## Integrasi CI

- `.github/workflows/godot-check.yml` dan `godot-rebuild.yml` menjalankan
  `prepare_godot_render.py --check` + `test_godot_render_prepare.py`, path filter
  mencakup `_render.py`, `map_components/**`, `mobile/perf.py`, dan tool render.
- `godot_rebuild/tests/validate_project.py` memverifikasi modul render, 54 bake,
  cap `EffectManager`, dan wiring `ArenaView`/`CoreGame`/`MatchModel`.
- `godot_rebuild/tests/run_all.gd` menambah `_test_render()` (easing, cache,
  MapView, budget efek, cinematic, intro pause, klik toko).

## Batasan yang jujur

- Visual GPU belum diverifikasi di perangkat nyata; suite headless memverifikasi
  state/API/budget, bukan pixel-perfect. Bake statis memakai seed beku sehingga
  speckle/jitter tidak berubah tiap match seperti Pygame asli.
- `ambient_tint` Pygame (blit SRCALPHA / BLEND_RGB_MULT) didekati dengan modulate
  tekstur multiplikatif; partikel/fog/obor adalah port native yang setara secara
  fungsi, bukan reproduksi vektor per-piksel.
- Rig/siluet vektor bespoke bos pada intro kematian diganti gelombang ledakan,
  fragmen, dan portrait strip bake; tidak semua detail partikel Pygame 1:1.
- Kill feed tetap disabled sesuai keputusan produk di `_core.draw_ui`.
- Audio cinematic belum dihubungkan ke `SoundManager` native pada migrasi ini;
  tidak ada klaim suara intro/kematian boss sudah parity.
- Item aura, top-up produksi, Play Games, Android/keystore/perangkat, dan output
  audio tetap di luar cakupan verifikasi render ini.
